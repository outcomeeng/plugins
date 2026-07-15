<!-- Generated from producer section {producer_section_name} at {producer_path}. -->

Apply the implementation-ownership producer section below to the supplied changeset. Classify artifact ownership, build the expected coverage inventory, and derive terminal status. Assume each listed installed concern producer executes successfully with zero findings. Return exactly one JSON object with these mandatory fields:

- `terminal_status`: `approved` or `rejected`
- `required_units`: an array whose entries carry `language`, `concern`, `coverage_requirement`, and `coverage_status`
- `optional_units`: an array whose entries carry `coverage_requirement` and `coverage_status`
- `unsupported_paths`: an array of implementation-owned paths without an executable producer

{producer_section}
The changeset and installed producer state (JSON-encoded):

```json
{input_json}
```
