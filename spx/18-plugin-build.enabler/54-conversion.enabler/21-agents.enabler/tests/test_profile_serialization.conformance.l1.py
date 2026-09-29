"""Complete native configuration checked through independent parsers."""

import json
import tomllib
from dataclasses import asdict

import yaml
from outcomeeng.distribution.build import make_jinja_environment

from outcomeeng.distribution.contracts import (
    BUILD_TARGET_VARIABLE,
    PROFILE_CONFIG_GLOBAL,
    Target,
    format_template_call,
)
from outcomeeng.distribution.profiles import (
    AGENT_PROFILES,
    NATIVE_PROFILE_SYNTAX,
    ProfileSyntax,
    render_profile_configuration,
)
from outcomeeng.models import AgentProfile


def _parse(syntax: ProfileSyntax, rendered: str) -> object:
    if syntax is ProfileSyntax.JSON:
        return json.loads(rendered)
    if syntax is ProfileSyntax.TOML:
        return tomllib.loads(rendered)
    return yaml.safe_load(rendered)


def test_native_serialization_preserves_every_present_control() -> None:
    cases = tuple((target, profile) for target in Target for profile in AgentProfile)

    assert cases
    for target, profile in cases:
        rendered = render_profile_configuration(target, profile)
        parsed = _parse(NATIVE_PROFILE_SYNTAX[target], rendered)
        assert parsed == {
            field: value
            for field, value in asdict(AGENT_PROFILES[target][profile]).items()
            if value is not None
        }


def test_each_serialization_tracks_the_injected_profile() -> None:
    cases = tuple(
        (target, profile, replacement, syntax)
        for target in Target
        for profile in AgentProfile
        for replacement in AGENT_PROFILES[target].values()
        for syntax in ProfileSyntax
    )

    assert cases
    for target, profile, replacement, syntax in cases:
        profiles = {
            **AGENT_PROFILES,
            target: {**AGENT_PROFILES[target], profile: replacement},
        }
        rendered = render_profile_configuration(
            target, profile, syntax=syntax, profiles=profiles
        )
        parsed = _parse(syntax, rendered)
        assert parsed == {
            field: value
            for field, value in asdict(replacement).items()
            if value is not None
        }


def test_template_configuration_tracks_every_injected_native_profile() -> None:
    cases = tuple(
        (target, profile, replacement)
        for target in Target
        for profile in AgentProfile
        for replacement in AGENT_PROFILES[target].values()
    )

    assert cases
    for target, profile, replacement in cases:
        profiles = {
            **AGENT_PROFILES,
            target: {**AGENT_PROFILES[target], profile: replacement},
        }
        environment = make_jinja_environment(profiles=profiles)
        template = environment.from_string(
            format_template_call(PROFILE_CONFIG_GLOBAL, profile)
        )
        rendered = template.render({BUILD_TARGET_VARIABLE: target.value})
        parsed = _parse(NATIVE_PROFILE_SYNTAX[target], rendered)
        assert parsed == {
            field: value
            for field, value in asdict(replacement).items()
            if value is not None
        }
