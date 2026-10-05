"""Archive exact research sources and build identity before the full matrix."""

import hashlib
import json
import zipfile
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / "evidence/native_vwap_2026_v3/build"
    files = [root / "mql5/Experts/LorentzianVWAPAudit.mq5"]
    files += list((root / "mql5/Include").glob("*.mqh"))
    files += [
        p
        for p in (root / "vendor/official_mql5").rglob("*")
        if p.is_file() and p.suffix != ".ex5"
    ]
    manifest = {}
    for f in files:
        manifest[f.relative_to(root).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    # Compare vendored release source against its pinned upstream checkout.
    for f in (root / "vendor/official_mql5/indicators").rglob("*"):
        if not f.is_file() or f.suffix == ".ex5":
            continue
        relative = f.relative_to(root / "vendor/official_mql5")
        origin = root / "local_data/upstream-official-vwap/ports/mql5" / relative
        if f.read_bytes() != origin.read_bytes():
            raise ValueError(f"Official source changed: {relative}")
    for f in [
        root / "mql5/Experts/LorentzianVWAPAudit.ex5",
        root
        / "vendor/official_mql5/indicators/LorentzianClassification"
        / "LorentzianClassification.ex5",
    ]:
        manifest[f.relative_to(root).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    with zipfile.ZipFile(target / "source_vwap_v3.zip", "x", zipfile.ZIP_DEFLATED) as archive:
        for f in files:
            archive.write(f, f.relative_to(root).as_posix())
    (target / "sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Archived {len(files)} source files; official source byte identity PASS")


if __name__ == "__main__":
    main()
