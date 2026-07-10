from outcomeeng_testing.harnesses.thread_store_portability import (
    TestAgentsDoNotReferenceConcreteBackends as _AgentsDoNotReferenceConcreteBackends,
    TestBackendModulesDoNotRedefineBranchSlug as _BackendModulesDoNotRedefineBranchSlug,
    TestThreadStoreScriptsImportOnlyStdlib as _ThreadStoreScriptsImportOnlyStdlib,
    TestVerificationSkillsDoNotImportBackendsDirectly as _VerificationSkillsDoNotImportBackendsDirectly,
)


def test_thread_store_scripts_import_only_stdlib() -> None:
    _ThreadStoreScriptsImportOnlyStdlib().test_no_third_party_or_outcomeeng_imports()


def test_thread_store_scripts_do_not_import_outcomeeng() -> None:
    _ThreadStoreScriptsImportOnlyStdlib().test_no_outcomeeng_imports()


def test_verification_skills_do_not_import_backends_directly() -> None:
    _VerificationSkillsDoNotImportBackendsDirectly().test_no_verification_skill_imports_concrete_backend()


def test_agents_do_not_reference_concrete_backends() -> None:
    _AgentsDoNotReferenceConcreteBackends().test_no_agent_names_concrete_backend()


def test_backend_modules_do_not_redefine_branch_slug() -> None:
    _BackendModulesDoNotRedefineBranchSlug().test_no_backend_module_defines_branch_slug()
