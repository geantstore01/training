from threading import BoundedSemaphore

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import HTTPException

HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, type=Type.ID)
SLOTS = BoundedSemaphore(2)
DUMMY_HASH = HASHER.hash("not-an-account-password-used-for-constant-work")


def hash_password(password: str) -> str:
    if not SLOTS.acquire(blocking=False):
        raise HTTPException(429, "Réessaie dans quelques instants.", headers={"Retry-After": "2"})
    try:
        return HASHER.hash(password)
    finally:
        SLOTS.release()


def verify_password(encoded: str | None, password: str) -> bool:
    if not SLOTS.acquire(blocking=False):
        raise HTTPException(429, "Réessaie dans quelques instants.", headers={"Retry-After": "2"})
    try:
        try:
            valid = HASHER.verify(encoded or DUMMY_HASH, password)
            return bool(encoded) and valid
        except (VerificationError, InvalidHashError):
            return False
    finally:
        SLOTS.release()
