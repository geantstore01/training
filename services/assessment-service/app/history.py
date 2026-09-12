"""Read-only navigation. Lessons, attempts, mastery and RLS use the shared APIs."""
from fastapi import APIRouter, Depends
from shared.security.api import current_principal
from shared.security.tokens import Principal
from shared.history.catalogue import public_catalogue

router=APIRouter(prefix="/history",tags=["history"])

@router.get("/catalogue")
def catalogue(principal:Principal=Depends(current_principal)):
    return public_catalogue()
