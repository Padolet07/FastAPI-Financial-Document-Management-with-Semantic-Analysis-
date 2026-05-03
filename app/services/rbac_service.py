from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.permissions import ALL_PERMISSIONS, DEFAULT_ROLE_PERMISSIONS
from app.auth.dependencies import get_user_permissions
from app.models.rbac import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.schemas.rbac import RoleCreate


class RBACService:
    def __init__(self, db: Session):
        self.db = db

    def ensure_permission(self, name: str) -> Permission:
        permission = self.db.query(Permission).filter(Permission.name == name).first()
        if permission:
            return permission
        permission = Permission(name=name, description=f"Allows {name}")
        self.db.add(permission)
        self.db.flush()
        return permission

    def create_role(self, payload: RoleCreate) -> Role:
        role = self.db.query(Role).filter(Role.name == payload.name).first()
        if role:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
        role = Role(name=payload.name, description=payload.description)
        self.db.add(role)
        self.db.flush()
        for permission_name in payload.permissions:
            permission = self.ensure_permission(permission_name)
            self.db.add(RolePermission(role_id=role.id, permission_id=permission.id))
        self.db.commit()
        self.db.refresh(role)
        return role

    def assign_role(self, user_id: int, role_name: str) -> None:
        user = self.db.get(User, user_id)
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if not user or not role:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or role not found")
        exists = self.db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role.id).first()
        if not exists:
            self.db.add(UserRole(user_id=user_id, role_id=role.id))
            self.db.commit()

    def roles_for_user(self, user_id: int) -> list[str]:
        rows = (
            self.db.query(Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        return [row[0] for row in rows]

    def permissions_for_user(self, user_id: int) -> list[str]:
        return sorted(get_user_permissions(self.db, user_id))

    def seed_defaults(self) -> None:
        for permission_name in ALL_PERMISSIONS:
            self.ensure_permission(permission_name)
        self.db.flush()
        for role_name, permission_names in DEFAULT_ROLE_PERMISSIONS.items():
            role = self.db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = Role(name=role_name, description=f"Default {role_name} role")
                self.db.add(role)
                self.db.flush()
            existing = {rp.permission.name for rp in role.permissions}
            for permission_name in permission_names:
                if permission_name not in existing:
                    permission = self.ensure_permission(permission_name)
                    self.db.add(RolePermission(role_id=role.id, permission_id=permission.id))
        self.db.commit()
