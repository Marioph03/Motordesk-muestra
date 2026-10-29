"""Evita incluir texto UTF-8 mal decodificado en el backend."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1] / "app"
EXTENSIONS = {".py"}
INVALID_MARKERS = (chr(195) + chr(402), chr(195) + chr(162), chr(65533))


def main() -> int:
    invalid_files: list[Path] = []

    for path in ROOT.rglob("*"):
        if path.suffix not in EXTENSIONS or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        if any(marker in content for marker in INVALID_MARKERS):
            invalid_files.append(path.relative_to(ROOT.parent))

    if invalid_files:
        print("Se han detectado caracteres con codificación incorrecta:")
        for path in invalid_files:
            print(f" - {path}")
        return 1

    print("Codificación de texto del backend correcta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
