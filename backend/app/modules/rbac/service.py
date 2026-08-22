from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from .crud import RbacCrud
from .model import Permission, Role


DEFAULT_PERMISSIONS = [
    ("admin:read", "查看管理员", "admin", "查看管理员账号与后台会话。"),
    ("admin:manage", "管理管理员", "admin", "创建、停用或调整管理员。"),
    ("dashboard:read", "查看概览", "dashboard", "查看后台概览统计和最近动态。"),
    ("users:read", "查看用户", "users", "查看普通用户列表和用户详情。"),
    ("users:create", "创建用户", "users", "新建普通用户账号。"),
    ("users:update", "编辑用户", "users", "编辑普通用户资料。"),
    ("users:update_points", "调整积分", "users", "调整普通用户积分。"),
    ("users:delete", "删除用户", "users", "删除普通用户账号。"),
    ("conversions:read", "查看转换记录", "conversions", "查看用户转换任务和上传记录。"),
    ("conversions:delete", "删除转换记录", "conversions", "删除异常或违规转换任务。"),
    ("rbac:read", "查看权限", "rbac", "查看角色与权限配置。"),
    ("rbac:manage", "管理权限", "rbac", "维护角色、权限、菜单和按钮权限。"),
    ("audit_logs:read", "查看审计日志", "audit", "查看管理员操作日志。"),
    ("redeem_codes:read", "查看兑换码", "redeem_codes", "查看兑换码列表和状态。"),
    ("redeem_codes:manage", "管理兑换码", "redeem_codes", "创建、停用和管理兑换码。"),
    ("broadcasts:read", "查看公告", "broadcasts", "查看站内公告和弹窗消息。"),
    ("broadcasts:manage", "管理公告", "broadcasts", "发布、停用或撤销公告。"),
]


class RbacService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.crud = RbacCrud(db)

    def ensure_default_rbac(self) -> Role:
        permissions: list[Permission] = []
        for code, name, group, description in DEFAULT_PERMISSIONS:
            permission = self.crud.get_permission_by_code(code)
            if permission is None:
                permission = self.crud.create_permission(
                    Permission(
                        id=str(uuid.uuid4()),
                        code=code,
                        name=name,
                        group=group,
                        description=description,
                    )
                )
            permissions.append(permission)

        role = self.crud.get_role_by_code("super_admin")
        if role is None:
            role = self.crud.create_role(
                Role(
                    id=str(uuid.uuid4()),
                    code="super_admin",
                    name="超级管理员",
                    description="拥有 Saveplan 管理后台全部权限。",
                )
            )
        role.permissions = permissions
        self.db.flush()
        return role

    def list_permissions(self) -> list[Permission]:
        return self.crud.list_permissions()

    def list_roles(self) -> list[Role]:
        return self.crud.list_roles()
