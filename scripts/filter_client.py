from __future__ import annotations

import argparse
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "mods_all"
DEST = ROOT / "data" / "mods"

CLIENT_KEYWORDS = (
    "org/lwjgl",
    "net/minecraft/client",
    "com/mojang/blaze3d",
)

CLIENT_NAMES = (
    "iris",
    "sodium",
    "embeddium",
    "oculus",
    "entity_model_features",
    "entity_texture_features",
    "entityculling",
    "notenoughanimations",
    "chat_heads",
    "cherishedworlds",
    "fpsreducer",
    "highlighter",
    "smoothswapping",
    "sound-physics",
)

TOML_FILES = (
    "META-INF/neoforge.mods.toml",
    "META-INF/mods.toml",
)


def read_text(zf: zipfile.ZipFile, name: str) -> str | None:
    try:
        return zf.read(name).decode(errors="ignore")
    except KeyError:
        return None


def has_client_side_only(toml: str) -> bool:
    txt = toml.lower()

    # displayTest="IGNORE_SERVER_ONLY"
    if "ignoreserveronly" in txt:
        return True

    # side="CLIENT"
    if re.search(r'side\s*=\s*"client"', txt):
        return True

    return False


def inspect_jar(path: Path):
    reason = None

    try:
        with zipfile.ZipFile(path) as jar:

            for file in TOML_FILES:
                text = read_text(jar, file)
                if text and has_client_side_only(text):
                    return False, f"{file}: client-only"

            names = {n.lower() for n in jar.namelist()}

            for keyword in CLIENT_KEYWORDS:
                if any(keyword in n for n in names):
                    reason = f"contains {keyword}"
                    return False, reason

    except Exception as e:
        return False, f"invalid jar ({e})"

    lower = path.name.lower()

    for keyword in CLIENT_NAMES:
        if keyword in lower:
            return False, f"filename contains '{keyword}'"

    return True, "common/server mod"


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if not SOURCE.exists():
        raise SystemExit(f"{SOURCE} does not exist")

    DEST.mkdir(parents=True, exist_ok=True)

    for file in DEST.glob("*.jar"):
        file.unlink()

    kept = 0
    skipped = 0

    for jar in sorted(SOURCE.glob("*.jar")):

        keep, reason = inspect_jar(jar)

        if keep:
            shutil.copy2(jar, DEST / jar.name)
            kept += 1
            print(f"[KEEP] {jar.name}")
        else:
            skipped += 1
            print(f"[SKIP] {jar.name} -> {reason}")

    print()
    print(f"Kept    : {kept}")
    print(f"Skipped : {skipped}")


if __name__ == "__main__":
    main()