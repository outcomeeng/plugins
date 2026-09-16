"""Explicit authentication and native credential persistence for discovery."""

from __future__ import annotations

import fcntl
import json
import os
import stat
import subprocess
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol
from uuid import uuid4

from outcomeeng.distribution.installation import (
    CODEX_EXECUTABLE,
    CODEX_HOME_ENV,
    HOME_ENV,
)
from outcomeeng.validation.ci_gate import (
    CODEX_API_KEY_ENVIRONMENT,
    DISCOVERY_AUTH_MODE_ENVIRONMENT,
)

WORKSPACE_TOKEN_ENV = "CODEX_ACCESS_TOKEN"
API_LOGIN_FLAG = "--with-api-key"
WORKSPACE_LOGIN_FLAG = "--with-access-token"
AUTH_FILENAME = "auth.json"
CI_ENVIRONMENT = "CI"
"""The environment variable hosted runners set, which requires an explicit mode."""
SAVED_LOGIN_CHATGPT_MODE = "chatgpt"
"""The saved-login mode value for a ChatGPT subscription login."""
FILE_STORE_ARGS = ("-c", 'cli_auth_credentials_store="file"')
DISCOVERY_TIMEOUT_SECONDS = 600
LOCK_RETRY_SECONDS = 0.05
REDACTED_CREDENTIAL = "[REDACTED-CREDENTIAL]"
CREDENTIAL_ENVIRONMENTS = frozenset(
    (
        CODEX_API_KEY_ENVIRONMENT,
        WORKSPACE_TOKEN_ENV,
        "CODEX_API_KEY",
        "CODEX_AUTH_TOKEN",
        "CHATGPT_ACCESS_TOKEN",
    )
)


class AuthField(StrEnum):
    """Native saved-login document vocabulary."""

    TOKENS = "tokens"
    ACCOUNT_ID = "account_id"
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"
    MODE = "auth_mode"
    API_KEY = "OPENAI_API_KEY"


class NativeCommand(StrEnum):
    """Native authentication and session command vocabulary."""

    LOGIN = "login"
    LOGOUT = "logout"
    EXEC = "exec"


class AuthenticationMode(StrEnum):
    SUBSCRIPTION = "subscription"
    API = "api"
    WORKSPACE_TOKEN = "workspace-token"


class DiscoveryAuthenticationError(RuntimeError):
    """The selected authentication mechanism cannot safely run discovery."""


class SavedLoginCondition(StrEnum):
    """Unsupported saved-login states rejected before native execution."""

    MISSING = "missing"
    MALFORMED = "malformed"
    NON_SUBSCRIPTION = "non-subscription"


class SavedLoginError(DiscoveryAuthenticationError):
    """A saved-login rejection with its machine-readable condition."""

    def __init__(self, condition: SavedLoginCondition, message: str) -> None:
        super().__init__(message)
        self.condition = condition


class ProbeRunner(Protocol):
    """Native process boundary, including stdin and a bounded execution time."""

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        input_text: str | None,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]: ...


def run_probe_process(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    input_text: str | None,
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        input=input_text,
        timeout=timeout,
        capture_output=True,
        text=True,
        check=False,
    )


@dataclass
class CredentialRedactor:
    """Keep secret material private while scrubbing initial and rotated values."""

    values: set[str] = field(default_factory=set, repr=False)

    def add(self, value: str | None) -> None:
        if value:
            self.values.add(value)

    def read_document(self, path: Path) -> object:
        try:
            raw = path.read_text(encoding="utf-8")
            self.add(raw)
            document: object = json.loads(raw)
        except OSError:
            raise SavedLoginError(
                SavedLoginCondition.MISSING,
                "Saved login is missing or malformed; use the CLI to log in with the file credential store.",
            ) from None
        except ValueError:
            raise SavedLoginError(
                SavedLoginCondition.MALFORMED,
                "Saved login is missing or malformed; use the CLI to log in with the file credential store.",
            ) from None
        if isinstance(document, dict):
            key = document.get(AuthField.API_KEY)
            if isinstance(key, str):
                self.add(key)
            tokens = document.get(AuthField.TOKENS)
            if isinstance(tokens, dict):
                for value in tokens.values():
                    if isinstance(value, str):
                        self.add(value)
        return document

    def capture(self, path: Path) -> None:
        try:
            self.read_document(path)
        except DiscoveryAuthenticationError:
            pass

    def clean(self, text: str) -> str:
        for value in sorted(self.values, key=len, reverse=True):
            text = text.replace(value, REDACTED_CREDENTIAL)
        return text

    def clean_bytes(self, value: bytes | None) -> bytes | None:
        if value is None:
            return None
        for secret in sorted(self.values, key=len, reverse=True):
            value = value.replace(secret.encode(), REDACTED_CREDENTIAL.encode())
        return value


@dataclass(frozen=True)
class AuthenticationSelection:
    mode: AuthenticationMode
    credential: str | None = field(default=None, repr=False)
    saved_login: Path | None = None


def select_authentication(environment: Mapping[str, str]) -> AuthenticationSelection:
    selected = environment.get(DISCOVERY_AUTH_MODE_ENVIRONMENT)
    if selected is None and environment.get(CI_ENVIRONMENT, "").lower() not in (
        "",
        "0",
        "false",
    ):
        raise DiscoveryAuthenticationError(
            f"CI requires explicit {DISCOVERY_AUTH_MODE_ENVIRONMENT}."
        )
    try:
        mode = AuthenticationMode(
            selected if selected is not None else AuthenticationMode.SUBSCRIPTION
        )
    except ValueError:
        raise DiscoveryAuthenticationError(
            f"{DISCOVERY_AUTH_MODE_ENVIRONMENT} must be subscription, api, or workspace-token."
        ) from None
    if mode is AuthenticationMode.SUBSCRIPTION:
        home = environment.get(CODEX_HOME_ENV)
        if not home:
            parent = environment.get(HOME_ENV)
            if not parent:
                raise DiscoveryAuthenticationError(
                    "Subscription discovery requires CODEX_HOME or HOME."
                )
            home = str(Path(parent) / ".codex")
        return AuthenticationSelection(
            mode, saved_login=Path(home).absolute() / AUTH_FILENAME
        )
    variable = (
        CODEX_API_KEY_ENVIRONMENT
        if mode is AuthenticationMode.API
        else WORKSPACE_TOKEN_ENV
    )
    credential = environment.get(variable)
    if not credential or not credential.strip():
        raise DiscoveryAuthenticationError(
            f"{mode.value} discovery requires credential {variable}."
        )
    return AuthenticationSelection(mode, credential=credential)


def credential_free_environment(environment: Mapping[str, str]) -> dict[str, str]:
    return {
        name: value
        for name, value in environment.items()
        if name not in CREDENTIAL_ENVIRONMENTS
    }


@dataclass
class DiscoveryAuthentication:
    """Own one authentication interval, its process calls, and private captures."""

    selection: AuthenticationSelection
    runner: ProbeRunner
    redactor: CredentialRedactor = field(default_factory=CredentialRedactor)
    clock: Callable[[], float] = time.monotonic
    pause: Callable[[float], None] = time.sleep
    deadline: float = field(init=False)
    credential_files: set[Path] = field(default_factory=set, repr=False)

    def __post_init__(self) -> None:
        self.deadline = self.clock() + DISCOVERY_TIMEOUT_SECONDS
        self.redactor.add(self.selection.credential)
        if self.selection.saved_login is not None:
            self.credential_files.add(self.selection.saved_login)
            self._account(self.selection.saved_login)

    def _remaining(self) -> float:
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise DiscoveryAuthenticationError(
                "Discovery authentication exceeded the probe timeout."
            )
        return remaining

    def _capture_credentials(self) -> None:
        for path in self.credential_files:
            self.redactor.capture(path)

    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = self.runner(
                argv,
                cwd=cwd,
                env=credential_free_environment(env),
                input_text=input_text,
                timeout=self._remaining(),
            )
        except subprocess.TimeoutExpired as error:
            self._capture_credentials()
            error.output = self.redactor.clean_bytes(error.output)
            error.stderr = self.redactor.clean_bytes(error.stderr)
            error.cmd = tuple(self.redactor.clean(str(arg)) for arg in argv)
            raise
        except OSError as error:
            self._capture_credentials()
            raise DiscoveryAuthenticationError(
                self.redactor.clean(str(error))
            ) from None
        self._capture_credentials()
        return subprocess.CompletedProcess(
            tuple(argv),
            result.returncode,
            self.redactor.clean(result.stdout),
            self.redactor.clean(result.stderr),
        )

    def _account(self, path: Path) -> str:
        try:
            if not stat.S_ISREG(path.stat().st_mode):
                raise SavedLoginError(
                    SavedLoginCondition.MALFORMED,
                    "Subscription credentials must be a regular file.",
                )
        except OSError:
            raise SavedLoginError(
                SavedLoginCondition.MISSING,
                "Subscription discovery requires a saved file-backed ChatGPT login; keyring-only credentials are unsupported.",
            ) from None
        document = self.redactor.read_document(path)
        if not isinstance(document, dict):
            raise SavedLoginError(
                SavedLoginCondition.MALFORMED,
                "Subscription discovery requires a ChatGPT saved login.",
            )
        if document.get(AuthField.MODE) != SAVED_LOGIN_CHATGPT_MODE:
            raise SavedLoginError(
                SavedLoginCondition.NON_SUBSCRIPTION,
                "Subscription discovery requires a ChatGPT saved login.",
            )
        tokens = document.get(AuthField.TOKENS)
        if not isinstance(tokens, dict) or not all(
            isinstance(tokens.get(name), str) and tokens[name]
            for name in (
                AuthField.ACCESS_TOKEN,
                AuthField.REFRESH_TOKEN,
                AuthField.ID_TOKEN,
                AuthField.ACCOUNT_ID,
            )
        ):
            raise SavedLoginError(
                SavedLoginCondition.MALFORMED,
                "Saved ChatGPT login lacks required tokens or account identity.",
            )
        return str(tokens[AuthField.ACCOUNT_ID])

    def _check_write_through(self, *, cwd: Path, env: Mapping[str, str]) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            owner = root / "owner.json"
            consumer = root / "consumer"
            consumer.mkdir()
            owner.write_text("{}", encoding="utf-8")
            owner.chmod(0o600)
            identity = owner.stat()
            link = consumer / AUTH_FILENAME
            link.symlink_to(owner)
            fabricated = uuid4().hex
            self.redactor.add(fabricated)
            result = self.run(
                (
                    CODEX_EXECUTABLE,
                    *FILE_STORE_ARGS,
                    NativeCommand.LOGIN,
                    API_LOGIN_FLAG,
                ),
                cwd=cwd,
                env={**env, CODEX_HOME_ENV: str(consumer)},
                input_text=fabricated,
            )
            document = self.redactor.read_document(owner)
            after = owner.stat()
            if (
                result.returncode != 0
                or not link.is_symlink()
                or link.resolve() != owner
                or (identity.st_dev, identity.st_ino) != (after.st_dev, after.st_ino)
                or not isinstance(document, dict)
                or document.get(AuthField.API_KEY) != fabricated
            ):
                raise DiscoveryAuthenticationError(
                    "The CLI credential writer cannot preserve the saved-login link; subscription discovery is unsupported by this CLI."
                )

    @contextmanager
    def authenticated_home(
        self,
        home: Path,
        *,
        cwd: Path,
        env: Mapping[str, str],
    ) -> Iterator[subprocess.CompletedProcess[str]]:
        home.mkdir(parents=True, exist_ok=True)
        self.credential_files.add(home / AUTH_FILENAME)
        if self.selection.mode is not AuthenticationMode.SUBSCRIPTION:
            flag = (
                API_LOGIN_FLAG
                if self.selection.mode is AuthenticationMode.API
                else WORKSPACE_LOGIN_FLAG
            )
            result = self.run(
                (CODEX_EXECUTABLE, *FILE_STORE_ARGS, NativeCommand.LOGIN, flag),
                cwd=cwd,
                env=env,
                input_text=self.selection.credential,
            )
            if result.returncode != 0:
                raise DiscoveryAuthenticationError(
                    f"{self.selection.mode.value} login failed ({result.returncode}): {result.stderr}"
                )
            yield result
            return
        self._check_write_through(cwd=cwd, env=env)
        selected = self.selection.saved_login
        if selected is None:
            raise DiscoveryAuthenticationError(
                "Subscription login path is unavailable."
            )
        canonical = selected.resolve(strict=True)
        with canonical.open("rb") as handle:
            while True:
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    self.pause(min(LOCK_RETRY_SECONDS, self._remaining()))
            try:
                identity = os.fstat(handle.fileno())
                account = self._account(selected)
                link = home / AUTH_FILENAME
                if link.exists() or link.is_symlink():
                    raise DiscoveryAuthenticationError(
                        "Disposable home already contains credentials before subscription linking."
                    )
                self._check_identity(selected, canonical, identity, account)
                link.symlink_to(canonical)
                try:
                    yield subprocess.CompletedProcess((), 0, "", "")
                finally:
                    self._capture_credentials()
                    self._check_identity(selected, canonical, identity, account)
                    if not link.is_symlink() or link.resolve() != canonical:
                        raise DiscoveryAuthenticationError(
                            "Saved-login link was replaced; no credential restoration was attempted."
                        )
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _check_identity(
        self,
        selected: Path,
        canonical: Path,
        identity: os.stat_result,
        account: str,
    ) -> None:
        try:
            current = selected.stat()
            unchanged = (
                selected.resolve(strict=True) == canonical
                and (current.st_dev, current.st_ino)
                == (identity.st_dev, identity.st_ino)
                and self._account(selected) == account
            )
        except OSError:
            unchanged = False
        if not unchanged:
            raise DiscoveryAuthenticationError(
                "Saved login or account was replaced; no credential restoration was attempted."
            )
