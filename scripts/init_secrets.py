"""Génère des secrets locaux sans écraser un secret existant ni l'afficher."""
import os
import secrets
from pathlib import Path

SERVICES = "auth user class curriculum content exercise assessment tutor retrieval speech notification analytics admin safety ai_router".split()
root = Path(__file__).resolve().parents[1] / "secrets"
root.mkdir(mode=0o700, exist_ok=True)
for name in ["postgres_password", "redis_password", "db_migrator", *[f"db_{s}" for s in SERVICES]]:
    target = root / name
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        continue
    with os.fdopen(fd, "w") as f:
        f.write(secrets.token_hex(32) + "\n")
    # Le dossier hôte est privé (0700). Chaque conteneur ne monte que ses secrets.
    # Compose local ignore uid/gid/mode sur les secrets de type fichier.
    os.chmod(target, 0o444)
print("Secrets disponibles dans secrets/ (valeurs non affichées).")
