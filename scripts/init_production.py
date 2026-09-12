"""Initialize private directories and local secrets without printing credentials."""
from pathlib import Path
import os
import secrets


def main():
    root = Path(__file__).resolve().parents[1]
    os.umask(0o077)
    secret_dir = root / "secrets"
    secret_dir.mkdir(exist_ok=True, mode=0o700)
    for name, value in {"grafana_password":secrets.token_urlsafe(36), "sentry_dsn":""}.items():
        target = secret_dir / name
        if not target.exists():
            target.write_text(value + "\n")
            target.chmod(0o444)
    for name in "auth user class curriculum content exercise assessment tutor retrieval speech notification analytics admin safety ai-router".split():
        directory = root / "runtime/telemetry" / (name + "-service")
        directory.mkdir(parents=True, exist_ok=True)
        directory.chmod(0o750)
        if os.name == "posix": os.chown(directory,10001,10001)
    for name in ("runtime", "runtime/telemetry", "runtime/metrics"):
        (root/name).mkdir(parents=True,exist_ok=True)
        (root/name).chmod(0o755)
    acme = root / "runtime/acme"
    acme.mkdir(exist_ok=True)
    acme.chmod(0o700)
    if os.name == "posix": os.chown(acme,10001,10001)
    print("Production directories and secrets initialized; no credential printed.")


if __name__ == "__main__": main()
