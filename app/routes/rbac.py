from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.auth.permissions import ROLE_MANAGE, USER_MANAGE
from app.db.session import get_db
from app.models.user import User
from app.schemas.rbac import AssignRoleRequest, PermissionsRead, RoleCreate, RoleRead, RolesRead
from app.services.rbac_service import RBACService

router = APIRouter(tags=["RBAC"])


@router.post("/roles/create", response_model=RoleRead, status_code=201)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(ROLE_MANAGE)),
):
    return RBACService(db).create_role(payload)


@router.post("/users/assign-role", status_code=204)
def assign_role(
    payload: AssignRoleRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(USER_MANAGE)),
):
    RBACService(db).assign_role(payload.user_id, payload.role_name)
    return None


@router.get("/users/{user_id}/roles", response_model=RolesRead)
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(USER_MANAGE)),
):
    return RolesRead(user_id=user_id, roles=RBACService(db).roles_for_user(user_id))


@router.get("/users/{user_id}/permissions", response_model=PermissionsRead)
def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(USER_MANAGE)),
):
    return PermissionsRead(user_id=user_id, permissions=RBACService(db).permissions_for_user(user_id))
