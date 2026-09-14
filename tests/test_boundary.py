import re
import subprocess
import sys
from pathlib import Path

import cullen._cli

CLI_ROOT = Path(cullen._cli.__file__).parent

INTERNAL_IMPORT = re.compile(r"^\s*from cullen\.(?!_cli)|^\s*import cullen\.(?!_cli)")


class TestBoundary:
    def test_sdk_imports_without_cli_dependencies(self) -> None:
        code = "import sys; sys.modules['typer'] = None; sys.modules['rich'] = None; import cullen"

        subprocess.run([sys.executable, "-c", code], check=True)

    def test_cli_uses_only_public_api(self) -> None:
        offenders = [
            f"{file.relative_to(CLI_ROOT)}:{number}: {line.strip()}"
            for file in CLI_ROOT.rglob("*.py")
            for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), start=1)
            if INTERNAL_IMPORT.match(line)
        ]

        assert offenders == []
