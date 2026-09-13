"""Complete native configuration checked through independent parsers."""

import json
import tomllib
from dataclasses import asdict

import yaml
from outcomeeng.distribution.build import make_jinja_environment

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.profiles import (
    AGENT_PROFILES,
    AgentProfile,
    ProfileSyntax,
    render_profile_configuration,
)


def test_native_serialization_preserves_every_present_control() -> None:
    for target in Target:
        for profile in AgentProfile:
            rendered = render_profile_configuration(target, profile)
            parsed = (
                tomllib.loads(rendered)
                if target is Target.CODEX
                else yaml.safe_load(rendered)
            )
            assert parsed == {
                field: value
                for field, value in asdict(AGENT_PROFILES[target][profile]).items()
                if value is not None
            }


def test_each_serialization_tracks_the_injected_profile() -> None:
    for target in Target:
        for profile in AgentProfile:
            for replacement in AGENT_PROFILES[target].values():
                profiles = {
                    **AGENT_PROFILES,
                    target: {**AGENT_PROFILES[target], profile: replacement},
                }
                for syntax in ProfileSyntax:
                    rendered = render_profile_configuration(
                        target, profile, syntax=syntax, profiles=profiles
                    )
                    if syntax is ProfileSyntax.JSON:
                        parsed = json.loads(rendered)
                    elif syntax is ProfileSyntax.TOML:
                        parsed = tomllib.loads(rendered)
                    else:
                        parsed = yaml.safe_load(rendered)
                    assert parsed == {
                        field: value
                        for field, value in asdict(replacement).items()
                        if value is not None
                    }


def test_template_configuration_tracks_every_injected_native_profile() -> None:
    for target in Target:
        for profile in AgentProfile:
            for replacement in AGENT_PROFILES[target].values():
                profiles = {
                    **AGENT_PROFILES,
                    target: {**AGENT_PROFILES[target], profile: replacement},
                }
                environment = make_jinja_environment(profiles=profiles)
                template = environment.from_string("{{! profile_config(profile) !}}")
                rendered = template.render(target=target.value, profile=profile)
                parsed = (
                    tomllib.loads(rendered)
                    if target is Target.CODEX
                    else yaml.safe_load(rendered)
                )
                assert parsed == {
                    field: value
                    for field, value in asdict(replacement).items()
                    if value is not None
                }
