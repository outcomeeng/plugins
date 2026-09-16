"""Disposable credential files and controlled native-process failures.

Controlled runners expose native command interactions, refresh races, and
failures under the interaction, concurrency, and failure-simulation exceptions.
All file writes are real; credential payloads are inert fixtures.
"""

from __future__ import annotations

import json
import fcntl
import shutil
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.installation import (
    CODEX_EXECUTABLE,
    CODEX_HOME_ENV,
    HOME_ENV,
)
from outcomeeng.validation.ci_gate import (
    CODEX_API_KEY_ENVIRONMENT,
    DISCOVERY_AUTH_MODE_ENVIRONMENT,
    JUST_BINARY,
)
from outcomeeng_testing.harnesses.discovery_auth import (
    AuthField,
    CI_ENVIRONMENT,
    NativeCommand,
    SavedLoginCondition,
    AUTH_FILENAME,
    WORKSPACE_TOKEN_ENV,
    AuthenticationMode,
    DiscoveryAuthentication,
    select_authentication,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "discovery_auth"
API_FIXTURE_PATH = FIXTURE_ROOT / "api.json"
SESSION_COMMAND = (CODEX_EXECUTABLE, NativeCommand.EXEC)
NATIVE_FAILURE_EXIT_CODE = 17


class NativeFault(StrEnum):
    INSTALL_FAILURE = "install-failure"
    REPLACE_LINK = "replace-link"
    REPLACE_FILE = "replace-file"
    SWITCH_ACCOUNT = "switch-account"
    LOGIN_FAILURE = "login-failure"
    TIMEOUT = "timeout"
    INCOMPATIBLE_WRITER = "incompatible-writer"


@dataclass(frozen=True)
class NativeCall:
    argv: tuple[str, ...]
    home: Path
    environment: Mapping[str, str]
    input_text: str | None = field(repr=False)


@dataclass
class NativeCredentialRunner:
    """Record command shape and reproduce native writer or failure behavior."""

    refreshed: str
    fault: NativeFault | None = None
    calls: list[NativeCall] = field(default_factory=list)

    def __call__(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        env: Mapping[str, str],
        input_text: str | None,
        timeout: float,
    ) -> subprocess.CompletedProcess[str]:
        home = Path(env[CODEX_HOME_ENV])
        self.calls.append(NativeCall(tuple(argv), home, dict(env), input_text))
        if argv[0] == JUST_BINARY:
            return subprocess.CompletedProcess(
                argv, NATIVE_FAILURE_EXIT_CODE, "", "installation failed"
            )
        target = home / AUTH_FILENAME
        if NativeCommand.LOGIN in argv:
            if self.fault is NativeFault.LOGIN_FAILURE:
                return subprocess.CompletedProcess(
                    argv, NATIVE_FAILURE_EXIT_CODE, "", input_text or ""
                )
            if self.fault is NativeFault.INCOMPATIBLE_WRITER:
                target.unlink(missing_ok=True)
            target.write_text(
                json.dumps({AuthField.API_KEY: input_text}), encoding="utf-8"
            )
            return subprocess.CompletedProcess(argv, 0, input_text or "", "")
        if self.fault is NativeFault.REPLACE_LINK:
            target.unlink()
        elif self.fault is NativeFault.REPLACE_FILE:
            canonical = target.resolve()
            replacement = canonical.with_suffix(".replacement")
            replacement.write_text(self.refreshed, encoding="utf-8")
            replacement.replace(canonical)
        target.write_text(self.refreshed, encoding="utf-8")
        if self.fault is NativeFault.SWITCH_ACCOUNT:
            document = json.loads(self.refreshed)
            document[AuthField.TOKENS][AuthField.ACCOUNT_ID] += "-other"
            target.write_text(json.dumps(document), encoding="utf-8")
        echo = " ".join(json.loads(self.refreshed)[AuthField.TOKENS].values())
        if self.fault is NativeFault.TIMEOUT:
            raise subprocess.TimeoutExpired(
                argv, timeout, output=echo.encode(), stderr=echo.encode()
            )
        return subprocess.CompletedProcess(argv, 0, echo, echo)


@dataclass
class AuthenticationCase:
    auth: DiscoveryAuthentication
    runner: NativeCredentialRunner
    home: Path
    saved: Path
    environment: dict[str, str]
    original_environment: dict[str, str]
    initial: str
    refreshed: str


@contextmanager
def authentication_case(
    mode: AuthenticationMode = AuthenticationMode.SUBSCRIPTION,
    *,
    fault: NativeFault | None = None,
    explicit_mode: bool = True,
) -> Iterator[AuthenticationCase]:
    initial = (FIXTURE_ROOT / "chatgpt.json").read_text(encoding="utf-8")
    refreshed = (FIXTURE_ROOT / "refreshed.json").read_text(encoding="utf-8")
    api = json.loads(API_FIXTURE_PATH.read_text(encoding="utf-8"))[AuthField.API_KEY]
    with TemporaryDirectory() as directory:
        root = Path(directory).resolve()
        selected_home = root / "saved"
        selected_home.mkdir()
        saved = selected_home / AUTH_FILENAME
        saved.write_text(initial, encoding="utf-8")
        saved.chmod(0o600)
        original = {
            HOME_ENV: str(root),
            CODEX_HOME_ENV: str(selected_home),
            DISCOVERY_AUTH_MODE_ENVIRONMENT: mode.value,
            CODEX_API_KEY_ENVIRONMENT: api,
            WORKSPACE_TOKEN_ENV: json.loads(initial)[AuthField.TOKENS][
                AuthField.ACCESS_TOKEN
            ],
        }
        if not explicit_mode:
            del original[DISCOVERY_AUTH_MODE_ENVIRONMENT]
        runner = NativeCredentialRunner(refreshed, fault)
        auth = DiscoveryAuthentication(select_authentication(original), runner)
        home = root / "disposable"
        home.mkdir()
        yield AuthenticationCase(
            auth,
            runner,
            home,
            saved,
            {**original, CODEX_HOME_ENV: str(home)},
            original,
            initial,
            refreshed,
        )


def missing_credential_environment(mode: AuthenticationMode) -> dict[str, str]:
    """Select a mode while supplying only the other mode's credential."""
    document = json.loads(API_FIXTURE_PATH.read_text(encoding="utf-8"))
    other = (
        WORKSPACE_TOKEN_ENV
        if mode is AuthenticationMode.API
        else CODEX_API_KEY_ENVIRONMENT
    )
    return {
        DISCOVERY_AUTH_MODE_ENVIRONMENT: mode.value,
        other: document[AuthField.API_KEY],
    }


def ci_without_authentication_mode() -> dict[str, str]:
    return {CI_ENVIRONMENT: "true"}


@dataclass
class AdvancingClock:
    elapsed: float = 0

    def __call__(self) -> float:
        return self.elapsed

    def advance(self, seconds: float) -> None:
        self.elapsed += seconds


@contextmanager
def lock_contention_case() -> Iterator[AuthenticationCase]:
    with authentication_case() as case:
        clock = AdvancingClock()
        case.auth = DiscoveryAuthentication(
            select_authentication(case.original_environment),
            case.runner,
            clock=clock,
            pause=clock.advance,
        )
        with case.saved.open("rb") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield case
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)


@contextmanager
def invalid_saved_login(fault: SavedLoginCondition) -> Iterator[AuthenticationCase]:
    with authentication_case() as case:
        if fault is SavedLoginCondition.MISSING:
            case.saved.unlink()
        elif fault is SavedLoginCondition.MALFORMED:
            case.saved.write_text(
                case.initial[: len(case.initial) // 2], encoding="utf-8"
            )
        else:
            shutil.copyfile(API_FIXTURE_PATH, case.saved)
        yield case


def dispose_authenticated_home(case: AuthenticationCase) -> None:
    """Remove disposable installation state using the same tree-removal semantics."""
    shutil.rmtree(case.home)
