from collections import Counter

from outcomeeng_testing.harnesses.distribution import (
    SkillCollectionUnionCase,
    exercise_skill_collection_union,
)


def test_skill_collection_union_holds() -> None:
    def assert_union(case: SkillCollectionUnionCase) -> None:
        assert Counter(case.collected_dir_names) == Counter(
            skill_name
            for skill_names in case.plugin_skills.values()
            for skill_name in skill_names
        )

    exercise_skill_collection_union(assert_union)
