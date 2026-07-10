"""租户数据访问."""

from typing import Optional

from sqlalchemy.orm import Session

from storage.models.tenant import Tenant


class TenantRepository:
    """租户 CRUD。"""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        return self.session.get(Tenant, tenant_id)

    def create(self, **fields) -> Tenant:
        tenant = Tenant(**fields)
        self.session.add(tenant)
        self.session.flush()
        return tenant
