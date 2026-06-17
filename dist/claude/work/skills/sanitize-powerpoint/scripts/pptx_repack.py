#!/usr/bin/env python3
"""Content-surgical repackage of an extracted working directory into a .pptx.

Rebuilds the package from <workdir>, ordering members to match <original> so
[Content_Types].xml stays first and every untouched part keeps its position
and content. Then verifies the result.

Usage:
    python3 pptx_repack.py <original.pptx> <workdir> <out.pptx>

<workdir> must be a FULL extraction of <original> (the skill's workflow step 4),
with fixes applied in place. A part present in <original> but absent from
<workdir> is treated as a deliberate deletion; a part present only in <workdir>
is treated as a deliberate addition.

Exit codes: 0 = repacked and verified, 2 = bad input, 3 = verification failed.

Tested with:
- workdir = verbatim extraction         -> out has 0 changed parts
- workdir with one edited slideLayout   -> only that part reported changed
- workdir with one part deleted         -> member count drops by 1, reported
- malformed XML in a workdir part       -> verification fails, exit 3
"""

import os
import sys
import xml.etree.ElementTree as ET
import zipfile


def die(message, code=2):
    """Print an error to stderr and exit (2 = bad input, 3 = verification)."""
    print(message, file=sys.stderr)
    sys.exit(code)


def read_zip(path):
    """Return (ordered-member-list, {name: bytes}, {name: ZipInfo})."""
    try:
        with zipfile.ZipFile(path) as zf:
            order = [n for n in zf.namelist() if not n.endswith("/")]
            return (
                order,
                {n: zf.read(n) for n in order},
                {n: zf.getinfo(n) for n in order},
            )
    except FileNotFoundError:
        die(f"error: file not found: {path}")
    except (zipfile.BadZipFile, IsADirectoryError) as exc:
        die(f"error: not a readable .pptx (ZIP): {path} ({exc})")


def read_workdir(workdir):
    """Return {archive-relative-name: bytes} for every file under workdir."""
    if not os.path.isdir(workdir):
        die(f"error: workdir is not a directory: {workdir}")
    out = {}
    for root, _, files in os.walk(workdir):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, workdir).replace(os.sep, "/")
            with open(full, "rb") as fh:
                out[rel] = fh.read()
    return out


def verify(out_path, original_count):
    """Raise SystemExit(3) on any integrity or well-formedness failure."""
    with zipfile.ZipFile(out_path) as zf:
        bad = zf.testzip()
        if bad is not None:
            die(f"error: ZIP integrity check failed on member {bad}", 3)
        members = [n for n in zf.namelist() if not n.endswith("/")]
        if members[0] != "[Content_Types].xml":
            die("error: [Content_Types].xml is not the first member", 3)
        for name in members:
            if name.endswith((".xml", ".rels")):
                try:
                    ET.fromstring(zf.read(name))
                except ET.ParseError as exc:
                    die(f"error: malformed XML in {name}: {exc}", 3)
    print("  verified: ZIP integrity OK, all XML parts well-formed")
    print(f"  members: {len(members)} (original had {original_count})")


def main(argv):
    if len(argv) != 4:
        die("usage: pptx_repack.py <original.pptx> <workdir> <out.pptx>")
    original, workdir, out_path = argv[1], argv[2], argv[3]

    order, orig_data, orig_info = read_zip(original)
    work = read_workdir(workdir)

    orig_set = set(order)
    changed = sorted(n for n in order if n in work and orig_data[n] != work[n])
    removed = sorted(n for n in order if n not in work)
    added = sorted(n for n in work if n not in orig_set)

    final = [n for n in order if n in work] + added

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in final:
            if name in orig_info:
                info = orig_info[name]
                info.compress_type = (
                    zipfile.ZIP_STORED
                    if info.compress_type == zipfile.ZIP_STORED
                    else zipfile.ZIP_DEFLATED
                )
                zf.writestr(info, work[name])
            else:
                zf.writestr(name, work[name])

    print(f"repacked {out_path}")
    print(f"  unchanged: {len(final) - len(changed) - len(added)}")
    print(f"  changed:   {len(changed)}")
    for n in changed:
        print(f"    ~ {n}")
    for n in added:
        print(f"    + {n}")
    for n in removed:
        print(f"    - {n}")
    sys.stdout.flush()
    verify(out_path, len(order))

    if removed or added:
        print(
            "  note: member count changed — expected only if parts were "
            "deliberately added or removed (trim)."
        )


if __name__ == "__main__":
    main(sys.argv)
