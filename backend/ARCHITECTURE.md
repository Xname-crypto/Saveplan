# Saveplan 后端架构约定

Saveplan 后端从管理员后台与权限系统开始，统一采用“按业务模块竖切 + 模块内四层”的组织方式。该约定参考 `rebort-hub/fastapiwebadmin` 和 FastApiAdmin 的后台管理结构，用于支撑 PostgreSQL、SQLAlchemy、Alembic、RBAC 权限系统和审计日志。

## 模块四层约定

每个业务模块都放在 `backend/app/modules/<module_name>/` 下，默认包含以下文件：

```text
controller.py   # 接口层：FastAPI 路由、请求依赖、响应模型
service.py      # 业务层：业务规则、权限流程、事务编排
crud.py         # 数据访问层：SQLAlchemy 查询和持久化
model.py        # 模型层：SQLAlchemy ORM 表结构
schema.py       # DTO 层：Pydantic 入参和出参模型
```

约束：

- `controller.py` 不直接写 SQL，也不直接处理复杂业务。
- `service.py` 可以调用多个 `crud.py`，负责事务提交、审计日志和业务判断。
- `crud.py` 只负责数据库读写，不写权限判断和业务流程。
- `model.py` 只定义 SQLAlchemy ORM 模型与关系。
- `schema.py` 只定义 Pydantic 请求和响应结构。

## 核心目录

```text
backend/app/
├─ core/                 # JWT、安全、RBAC 依赖、通用异常
├─ database/             # SQLAlchemy Base、Engine、Session
├─ modules/
│  ├─ admin_auth/        # 管理员独立登录
│  ├─ auth/              # 普通用户注册、登录、密码重置
│  ├─ audit_logs/        # 管理员操作审计
│  ├─ conversions/       # 转换记录管理
│  ├─ points/            # 积分流水
│  ├─ rbac/              # 角色和权限
│  └─ users/             # 普通用户管理
└─ main.py               # 应用入口与路由挂载
```

## 权限标准

管理员后台必须使用独立登录入口：

```text
POST /api/admin/auth/login
GET  /api/admin/auth/me
```

管理接口必须使用权限依赖：

```python
require_permission("users:read")
require_permission("users:update_points")
require_permission("conversions:read")
require_permission("audit_logs:read")
```

默认权限：

| 权限码 | 说明 |
| --- | --- |
| `admin:read` | 查看管理员 |
| `admin:manage` | 管理管理员 |
| `users:read` | 查看普通用户 |
| `users:update_points` | 调整用户积分 |
| `conversions:read` | 查看转换记录 |
| `conversions:delete` | 删除转换记录 |
| `rbac:read` | 查看角色权限 |
| `rbac:manage` | 管理角色权限 |
| `audit_logs:read` | 查看审计日志 |

## 普通用户认证

普通用户认证模块位于：

```text
backend/app/modules/auth/
```

对外接口保持不变：

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/forgot-password
POST /api/auth/reset-password
GET  /api/auth/me
```

`backend/app/auth.py` 只保留兼容入口，向旧转换模块继续暴露 `AuthUser`、`get_current_user` 和旧 SQLite `get_connection()`。转换模块完成迁移后，这个兼容层可以进一步瘦身。

## 数据库与迁移

生产环境使用 PostgreSQL：

```text
SAVEPLAN_DATABASE_URL=postgresql+psycopg://saveplan:password@host:5432/saveplan
```

迁移命令：

```powershell
cd G:\Saveplan\backend
alembic -c alembic.ini upgrade head
```

本地开发可以保留 SQLite fallback，但部署到 Zeabur 时必须配置 PostgreSQL 数据库地址。

## 管理员初始化

首次启动前配置：

```text
SAVEPLAN_ADMIN_EMAIL=admin@saveplan.vip
SAVEPLAN_ADMIN_PASSWORD=replace-with-a-strong-admin-password
SAVEPLAN_ADMIN_USERNAME=Saveplan Admin
```

首次启动会创建默认 RBAC 权限、`super_admin` 角色，并在没有管理员账号时创建一个超级管理员。
