from contextlib import contextmanager
from uuid import UUID

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session


@contextmanager
def tenant_session(engine: Engine, tenant_id: UUID):
    """Le tenant doit provenir du JWT vérifié, jamais d'un paramètre non authentifié.

    SET LOCAL est transactionnel : aucun contexte ne survit dans le pool.
    Les endpoints métier et leur authentification seront livrés au module suivant.
    """
    tenant = UUID(str(tenant_id))
    with Session(engine) as session, session.begin():
        session.execute(text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": str(tenant)})
        yield session
