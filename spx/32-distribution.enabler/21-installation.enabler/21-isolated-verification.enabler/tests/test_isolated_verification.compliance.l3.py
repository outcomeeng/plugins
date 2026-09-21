"""Network-backed real isolated-state boundary evidence."""

import os
import stat

from outcomeeng_testing.harnesses.installation import observe_real_installation


def test_isolated_installation_preserves_persistent_agent_state() -> None:
    observation = observe_real_installation()

    assert observation.first_exit_code == os.EX_OK, observation.first_stderr
    assert observation.second_exit_code == os.EX_OK, observation.second_stderr
    permission_bits = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
    assert not observation.persistent_mode_first & permission_bits
    assert not observation.persistent_mode_second & permission_bits
    assert observation.persistent_initial == observation.persistent_first
    assert observation.persistent_initial == observation.persistent_second
