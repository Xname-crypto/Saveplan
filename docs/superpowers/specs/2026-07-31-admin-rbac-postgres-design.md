# Saveplan 管理员权限与 PostgreSQL 后端升级设计

## 背景

Saveplan 已有普通用户登录、转换记录、上传文件和积分相关业务，但后端仍以 SQLite 和大文件模块为主。为了上线后具备更好的安全性、权限控制和运维能力，后端需要引入 PostgreSQL、SQLAlchemy、Alembic 和 RBAC 管理员权限系统。

## 目标

- 使用 PostgreSQL 作为生产数据库。
- 使用 SQLAlchemy 2.x ORM 定义模型。
- 使用 Alembic 管理数据库迁移。
- 建立管理员独立登录入口，不与普通用户共用登录界面。
- 按模块四层约定组织后端代码。
- 引入 RBAC：管理员、角色、权限、角色权限、管理员角色。
- 引入审计日志，记录管理员登录、权限拒绝、积分调整等敏感操作。
- 保持现有普通用户 API 路径尽量不变，降低对前端的影响。

## 非目标

- 本阶段不重做管理员前端界面。
- 本阶段不直接删除旧的 `auth.py` 和 `conversions.py`。
- 本阶段不强制迁移线上已有 SQLite 数据，后续需要单独做数据迁移脚本。

## 架构

后端采用按业务模块竖切：

```text
backend/app/modules/<module>/
├─ controller.py
├─ service.py
├─ crud.py
├─ model.py
└─ schema.py
```

核心模块：

- `admin_auth`：管理员登录、管理员资料。
- `rbac`：角色、权限、默认权限种子。
- `audit_logs`：管理员操作审计。
- `users`：管理员查看用户与调整积分。
- `points`：积分流水。
- `conversions`：管理员查看转换记录。

## 权限模型

默认创建 `super_admin` 角色，并绑定所有默认权限：

- `admin:read`
- `admin:manage`
- `users:read`
- `users:update_points`
- `conversions:read`
- `conversions:delete`
- `rbac:read`
- `rbac:manage`
- `audit_logs:read`

管理接口通过 `require_permission("<permission>")` 进行校验。权限拒绝会写入审计日志。

## 数据库

生产环境配置：

```text
SAVEPLAN_DATABASE_URL=postgresql+psycopg://saveplan:password@host:5432/saveplan
```

本地开发保留 SQLite fallback，避免没有 PostgreSQL 时后端完全无法启动。生产部署必须显式配置 PostgreSQL。

## 验证

- Python 语法编译检查。
- 后端测试。
- 确认工作区只包含本次后端架构升级相关文件。
