from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: str | None = None
    permissions: list[str] = []


class AssignRoleRequest(BaseModel):
    user_id: int
    role_name: str


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class PermissionsRead(BaseModel):
    user_id: int
    permissions: list[str]


class RolesRead(BaseModel):
    user_id: int
    roles: list[str]
