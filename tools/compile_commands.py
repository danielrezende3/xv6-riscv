"""Generate clangd's compilation database from a Make dry run."""

import json
from pathlib import Path
import shlex
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent.parent
    make = shlex.split(sys.argv[1]) if len(sys.argv) > 1 else ["make"]
    result = subprocess.run(
        [*make, "-Bn", "kernel/kernel", "fs.img"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )
    entries = []
    for line in result.stdout.splitlines():
        arguments = shlex.split(line)
        if not arguments:
            continue
        compiler = Path(arguments[0]).name
        if compiler not in ("cc", "gcc", "clang") and not compiler.endswith(
            ("-gcc", "-clang")
        ):
            continue
        for argument in arguments[1:]:
            # Generated assembly (user/usys.S) may not exist before the build.
            if Path(argument).suffix not in (".c", ".S"):
                continue
            entries.append(
                {"directory": str(root), "file": argument, "arguments": arguments}
            )

    if not entries:
        raise SystemExit("No compiler commands found; database was not changed.")
    output = root / "compile_commands.json"
    output.write_text(json.dumps(entries, indent=2) + "\n")
    print(f"Generated {output.name} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
