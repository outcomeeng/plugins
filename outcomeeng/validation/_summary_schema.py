"""JSON summary schema contract for validation recipe runs."""

from __future__ import annotations

from typing import cast

from outcomeeng.validation._engine import (
    PHASE_COMPLETE,
    PHASE_PREFLIGHT,
    PHASE_RECIPE,
    RUN_FAIL_STATUS,
    RUN_PASS_STATUS,
    SUMMARY_KEY_ARGV,
    SUMMARY_KEY_DURATION_SECONDS,
    SUMMARY_KEY_EXIT_CODE,
    SUMMARY_KEY_EXCERPT,
    SUMMARY_KEY_LABEL,
    SUMMARY_KEY_LOG_PATH,
    SUMMARY_KEY_PHASE,
    SUMMARY_KEY_PURPOSE,
    SUMMARY_KEY_RECIPE,
    SUMMARY_KEY_RECIPES,
    SUMMARY_KEY_STATUS,
    SUMMARY_KEY_STEPS,
    SUMMARY_KEY_SUMMARY_PATH,
    SUMMARY_KEY_VERIFICATION_TYPE,
)
from outcomeeng.validation._steps import (
    PURPOSE_CONFORMANCE,
    PURPOSE_CORRECTNESS,
    RECIPE_AD_HOC,
    RECIPE_CHECK,
    RECIPE_TEST,
    RECIPE_VALIDATION,
    VERIFICATION_TYPE_TESTING,
    VERIFICATION_TYPE_VALIDATION,
)

type JsonValue = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)
type JsonSchema = dict[str, JsonValue]

PRIMITIVE_RECIPE_NAMES = (RECIPE_VALIDATION, RECIPE_TEST)
STEP_RECIPE_NAMES = (*PRIMITIVE_RECIPE_NAMES, RECIPE_AD_HOC)
PRIMITIVE_VERIFICATION_TYPES = (
    VERIFICATION_TYPE_VALIDATION,
    VERIFICATION_TYPE_TESTING,
)
PRIMITIVE_PURPOSES = (PURPOSE_CONFORMANCE, PURPOSE_CORRECTNESS)
SUMMARY_PHASES = (PHASE_COMPLETE, PHASE_PREFLIGHT, PHASE_RECIPE)
STEP_PHASES = (PHASE_PREFLIGHT, PHASE_RECIPE)
RUN_STATUSES = (RUN_PASS_STATUS, RUN_FAIL_STATUS)

PASS_STEP_SCHEMA: JsonSchema = {
    "type": "object",
    "required": [
        SUMMARY_KEY_RECIPE,
        SUMMARY_KEY_PHASE,
        SUMMARY_KEY_LABEL,
        SUMMARY_KEY_ARGV,
        SUMMARY_KEY_STATUS,
        SUMMARY_KEY_DURATION_SECONDS,
        SUMMARY_KEY_EXIT_CODE,
    ],
    "properties": {
        SUMMARY_KEY_RECIPE: {"enum": list(STEP_RECIPE_NAMES)},
        SUMMARY_KEY_PHASE: {"enum": list(STEP_PHASES)},
        SUMMARY_KEY_LABEL: {"type": "string"},
        SUMMARY_KEY_ARGV: {"type": "array", "items": {"type": "string"}},
        SUMMARY_KEY_STATUS: {"const": RUN_PASS_STATUS},
        SUMMARY_KEY_DURATION_SECONDS: {"type": "integer"},
        SUMMARY_KEY_EXIT_CODE: {"type": "integer"},
    },
    "additionalProperties": False,
}

FAIL_STEP_SCHEMA: JsonSchema = {
    "type": "object",
    "required": [
        SUMMARY_KEY_RECIPE,
        SUMMARY_KEY_PHASE,
        SUMMARY_KEY_LABEL,
        SUMMARY_KEY_ARGV,
        SUMMARY_KEY_STATUS,
        SUMMARY_KEY_DURATION_SECONDS,
        SUMMARY_KEY_EXIT_CODE,
        SUMMARY_KEY_LOG_PATH,
        SUMMARY_KEY_EXCERPT,
    ],
    "properties": {
        SUMMARY_KEY_RECIPE: {"enum": list(STEP_RECIPE_NAMES)},
        SUMMARY_KEY_PHASE: {"enum": list(STEP_PHASES)},
        SUMMARY_KEY_LABEL: {"type": "string"},
        SUMMARY_KEY_ARGV: {"type": "array", "items": {"type": "string"}},
        SUMMARY_KEY_STATUS: {"const": RUN_FAIL_STATUS},
        SUMMARY_KEY_DURATION_SECONDS: {"type": "integer"},
        SUMMARY_KEY_EXIT_CODE: {"type": "integer"},
        SUMMARY_KEY_LOG_PATH: {"type": "string"},
        SUMMARY_KEY_EXCERPT: {"type": "string"},
    },
    "additionalProperties": False,
}

STEP_SCHEMA: JsonSchema = {"anyOf": [PASS_STEP_SCHEMA, FAIL_STEP_SCHEMA]}


def _primitive_summary_schema(*, require_summary_path: bool) -> JsonSchema:
    required = [
        SUMMARY_KEY_RECIPE,
        SUMMARY_KEY_VERIFICATION_TYPE,
        SUMMARY_KEY_PURPOSE,
        SUMMARY_KEY_PHASE,
        SUMMARY_KEY_STATUS,
        SUMMARY_KEY_EXIT_CODE,
        SUMMARY_KEY_DURATION_SECONDS,
        SUMMARY_KEY_STEPS,
    ]
    if require_summary_path:
        required.append(SUMMARY_KEY_SUMMARY_PATH)
    return cast(
        "JsonSchema",
        {
            "type": "object",
            "required": required,
            "properties": {
                SUMMARY_KEY_RECIPE: {"enum": list(PRIMITIVE_RECIPE_NAMES)},
                SUMMARY_KEY_VERIFICATION_TYPE: {
                    "enum": list(PRIMITIVE_VERIFICATION_TYPES)
                },
                SUMMARY_KEY_PURPOSE: {"enum": list(PRIMITIVE_PURPOSES)},
                SUMMARY_KEY_PHASE: {"enum": list(SUMMARY_PHASES)},
                SUMMARY_KEY_STATUS: {"enum": list(RUN_STATUSES)},
                SUMMARY_KEY_EXIT_CODE: {"type": "integer"},
                SUMMARY_KEY_DURATION_SECONDS: {"type": "integer"},
                SUMMARY_KEY_STEPS: {"type": "array", "items": STEP_SCHEMA},
                SUMMARY_KEY_SUMMARY_PATH: {"type": "string"},
            },
            "additionalProperties": False,
        },
    )


PRIMITIVE_SUMMARY_SCHEMA: JsonSchema = _primitive_summary_schema(
    require_summary_path=True
)
EMBEDDED_PRIMITIVE_SUMMARY_SCHEMA: JsonSchema = _primitive_summary_schema(
    require_summary_path=False
)

AD_HOC_SUMMARY_SCHEMA: JsonSchema = {
    "type": "object",
    "required": [
        SUMMARY_KEY_RECIPE,
        SUMMARY_KEY_VERIFICATION_TYPE,
        SUMMARY_KEY_PURPOSE,
        SUMMARY_KEY_PHASE,
        SUMMARY_KEY_STATUS,
        SUMMARY_KEY_EXIT_CODE,
        SUMMARY_KEY_DURATION_SECONDS,
        SUMMARY_KEY_STEPS,
        SUMMARY_KEY_SUMMARY_PATH,
    ],
    "properties": {
        SUMMARY_KEY_RECIPE: {"const": RECIPE_AD_HOC},
        SUMMARY_KEY_VERIFICATION_TYPE: {"const": None},
        SUMMARY_KEY_PURPOSE: {"const": None},
        SUMMARY_KEY_PHASE: {"enum": list(SUMMARY_PHASES)},
        SUMMARY_KEY_STATUS: {"enum": list(RUN_STATUSES)},
        SUMMARY_KEY_EXIT_CODE: {"type": "integer"},
        SUMMARY_KEY_DURATION_SECONDS: {"type": "integer"},
        SUMMARY_KEY_STEPS: {"type": "array", "items": STEP_SCHEMA},
        SUMMARY_KEY_SUMMARY_PATH: {"type": "string"},
    },
    "additionalProperties": False,
}

CHECK_SUMMARY_SCHEMA: JsonSchema = {
    "type": "object",
    "required": [
        SUMMARY_KEY_RECIPE,
        SUMMARY_KEY_VERIFICATION_TYPE,
        SUMMARY_KEY_PURPOSE,
        SUMMARY_KEY_PHASE,
        SUMMARY_KEY_STATUS,
        SUMMARY_KEY_EXIT_CODE,
        SUMMARY_KEY_DURATION_SECONDS,
        SUMMARY_KEY_RECIPES,
        SUMMARY_KEY_STEPS,
        SUMMARY_KEY_SUMMARY_PATH,
    ],
    "properties": {
        SUMMARY_KEY_RECIPE: {"const": RECIPE_CHECK},
        SUMMARY_KEY_VERIFICATION_TYPE: {"const": None},
        SUMMARY_KEY_PURPOSE: {"const": None},
        SUMMARY_KEY_PHASE: {"enum": list(SUMMARY_PHASES)},
        SUMMARY_KEY_STATUS: {"enum": list(RUN_STATUSES)},
        SUMMARY_KEY_EXIT_CODE: {"type": "integer"},
        SUMMARY_KEY_DURATION_SECONDS: {"type": "integer"},
        SUMMARY_KEY_RECIPES: {
            "type": "array",
            "items": EMBEDDED_PRIMITIVE_SUMMARY_SCHEMA,
        },
        SUMMARY_KEY_STEPS: {"type": "array", "items": STEP_SCHEMA},
        SUMMARY_KEY_SUMMARY_PATH: {"type": "string"},
    },
    "additionalProperties": False,
}

GATE_SUMMARY_SCHEMA: JsonSchema = {
    "anyOf": [PRIMITIVE_SUMMARY_SCHEMA, CHECK_SUMMARY_SCHEMA, AD_HOC_SUMMARY_SCHEMA]
}


def _schema_list(schema: JsonSchema, key: str) -> list[object]:
    return cast("list[object]", schema[key])


def _schema_mapping(schema: JsonSchema, key: str) -> dict[str, JsonSchema]:
    return cast("dict[str, JsonSchema]", schema[key])


def assert_json_schema(instance: object, schema: JsonSchema, path: str = "$") -> None:
    """Assert that a JSON-loaded value conforms to the supported schema subset."""

    if "anyOf" in schema:
        errors: list[str] = []
        for index, option in enumerate(cast("list[JsonSchema]", schema["anyOf"])):
            try:
                assert_json_schema(instance, option, path)
            except AssertionError as exc:
                errors.append(f"anyOf[{index}]: {exc}")
            else:
                return
        raise AssertionError(f"{path}: matched no anyOf branch: {'; '.join(errors)}")

    if "const" in schema:
        assert instance == schema["const"], f"{path}: expected {schema['const']!r}"

    if "enum" in schema:
        enum_values = _schema_list(schema, "enum")
        assert instance in enum_values, f"{path}: expected one of {enum_values!r}"

    schema_type = schema.get("type")
    if schema_type == "object":
        assert isinstance(instance, dict), f"{path}: expected object"
        object_instance = cast("dict[str, object]", instance)
        required = cast("list[str]", schema.get("required", []))
        missing = sorted(key for key in required if key not in object_instance)
        assert not missing, f"{path}: missing required keys {missing}"
        properties = _schema_mapping(schema, "properties")
        if schema.get("additionalProperties") is False:
            extra = sorted(set(object_instance) - set(properties))
            assert not extra, f"{path}: unexpected keys {extra}"
        for key, subschema in properties.items():
            if key in object_instance:
                assert_json_schema(object_instance[key], subschema, f"{path}.{key}")
        return

    if schema_type == "array":
        assert isinstance(instance, list), f"{path}: expected array"
        item_schema = cast("JsonSchema", schema["items"])
        for index, item in enumerate(instance):
            assert_json_schema(item, item_schema, f"{path}[{index}]")
        return

    if schema_type == "string":
        assert isinstance(instance, str), f"{path}: expected string"
        return

    if schema_type == "integer":
        assert isinstance(instance, int) and not isinstance(instance, bool), (
            f"{path}: expected integer"
        )
        return
