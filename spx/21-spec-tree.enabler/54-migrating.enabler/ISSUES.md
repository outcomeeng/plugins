# Issues: Migrating

## The link-conversion script is plugin-local debt toward an SPX CLI command

**Evidence:** The conversion ships as one standalone script of about 320 lines. [`spx/12-shipped-scripting.adr.md`](spx/12-shipped-scripting.adr.md) lets a generic shipped script beyond fifty lines stand only as debt: its logic moves into the agent-neutral SPX CLI once it proves its value, and a script that never proves its value is removed. The conversion is generic. It reads a product root and carries no agent-specific logic.

**Impact:** A consumer repository cannot version the script independently, and a repair reaches it only through a marketplace release.

**Settlement condition:** The script proves its value in use, its logic moves into an SPX CLI command that carries its own tests, and the skill keeps its instruction and no script; or the script never proves its value and is removed.
