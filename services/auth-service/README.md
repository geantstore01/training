# auth-service — module 2

Code : `app/main.py`, `app/routes.py`, `app/schemas.py`.
JWT RS256, refresh Redis atomique, sessions révocables et Argon2id.
Contrat : `openapi.json`. Compte PostgreSQL et Redis : `edu_auth`.

Le protocole, les endpoints et la rotation des clés sont documentés dans
[`docs/module2.md`](../../docs/module2.md).
