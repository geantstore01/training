"""Build a source release with checksums, excluding secrets, runtime data and dependencies."""
from pathlib import Path
import hashlib
import json
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {".git", ".venv", "__pycache__", ".pytest_cache", "secrets", "certs", "backups",
    "artifacts", "runtime", "node_modules", ".next", "test-results", "playwright-report"}


def main():
    destination = ROOT / "artifacts/educapilote-module11.zip"
    destination.parent.mkdir(exist_ok=True)
    manifest = {}
    with ZipFile(destination,"w",compression=ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT)
            if path.is_symlink() or not path.is_file() or any(p in EXCLUDE or p.endswith(".egg-info") for p in relative.parts): continue
            if path.name.startswith(".env") and not path.name.endswith(".example"): continue
            if path.suffix in {".pyc", ".tsbuildinfo"}: continue
            data = path.read_bytes()
            name = relative.as_posix()
            manifest[name] = hashlib.sha256(data).hexdigest()
            entry = ZipInfo(name,date_time=(2026,1,1,0,0,0))
            entry.external_attr = 0o644 << 16
            entry.compress_type = ZIP_DEFLATED
            archive.writestr(entry,data)
        archive.writestr("SOURCE-SHA256.json",json.dumps(manifest,indent=2,sort_keys=True))
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix(".zip.sha256").write_text(digest + "  " + destination.name + "\n",encoding="utf-8")
    print(f"{destination}: {len(manifest)} files, SHA256 {digest}")


if __name__ == "__main__": main()
