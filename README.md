# Save Your Finals

<div align="center">
  <strong>基于 FastAPI + Vue3 的题库导入与复习资料转换平台</strong>
  <br />
  <br />
  <img alt="Vue" src="https://img.shields.io/badge/Vue-3.5.21-42b883" />
  <img alt="Vite" src="https://img.shields.io/badge/Vite-7.x-646cff" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5.7-blue" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115.13-009688" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue" />
  <img alt="SQLite" src="https://img.shields.io/badge/Database-SQLite-lightgrey" />
  <img alt="Zeabur" src="https://img.shields.io/badge/Deploy-Zeabur-black" />
</div>

---

## 项目简介

Save Your Finals 是一个面向学生、备考用户和小型学习社区的题库导入助手。项目支持将 PDF、Word、TXT 文件或直接粘贴的试卷文本整理为结构化题目，并进一步完成校对、导出、历史记录管理和积分扣除。

当前项目采用前后端分离架构：前端负责完整的网页交互、移动端适配、登录注册、转换工作台和个人中心；后端负责用户认证、转换任务、上传文件、积分流水、数据存储和接口权限校验。

核心能力：

- 支持注册、登录、找回密码、重置密码和登录态校验。
- 支持文件上传与试卷文本粘贴两种导入方式。
- 支持题干、选项、答案、解析等结构化题目整理。
- 支持转换历史、上传文件记录、扣除积分和剩余积分展示。
- 支持个人中心头像、资料、兴趣标签和历史记录展示。
- 内置隐私政策、服务条款、帮助支持和社区维护邀请。
- 已部署到 Zeabur，并支持自定义域名 `saveplan.vip`。

---

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、Vite、TypeScript、Tailwind CSS、lucide-vue-next、GSAP、OGL |
| 后端 | FastAPI、Uvicorn、Pydantic、SQLAlchemy 2.x、Alembic、python-multipart、pypdf、requests、python-dotenv |
| 数据库 | PostgreSQL（生产推荐），本地开发保留 SQLite fallback |
| 认证与安全 | PBKDF2 密码哈希、JWT/Token 登录态、RBAC 权限、管理员独立登录、审计日志、CORS 来源控制、用户数据隔离 |
| 部署 | Zeabur 前端静态服务、Zeabur Python 后端服务、自定义域名 `saveplan.vip` |
| 工程管理 | npm、pip、requirements.txt、CHANGELOG.md、v2-mobile-responsive 分支 |

---

## 仓库结构

```text
Saveplan/
├─ frontend/                         # 前端应用（Vue 3 / Vite / TypeScript）
│  ├─ public/                        # 静态资源、视频首帧图、头像、站点图标
│  │  ├─ hero/                       # 首页展示资源
│  │  ├─ stitch/                     # 项目视觉资源与预设头像
│  │  └─ video/                      # 登录、注册、找回密码等页面视频资源
│  ├─ src/
│  │  ├─ components/                 # 公共组件、弹窗、页脚、输入控件和视觉组件
│  │  ├─ router/                     # 前端路由与页面访问控制
│  │  ├─ services/                   # authClient、conversionClient 等接口封装
│  │  ├─ views/                      # 首页、转换页、价格页、个人中心、登录注册页
│  │  ├─ App.vue                     # 前端根组件
│  │  └─ main.ts                     # Vue 应用入口
│  ├─ package.json                   # 前端依赖与构建脚本
│  └─ vite.config.ts                 # Vite 构建配置
│
├─ backend/                          # 后端服务（Python / FastAPI）
│  ├─ app/
│  │  ├─ main.py                     # FastAPI 应用入口、路由挂载和健康检查
│  │  ├─ auth.py                     # 用户注册、登录、会话、密码重置和积分字段
│  │  ├─ conversions.py              # 文件上传、文本解析、转换历史和积分扣除
│  │  ├─ config.py                   # 环境变量、数据目录、CORS 来源等配置
│  │  └─ kshuati_converter.py        # 题目格式转换与解析逻辑
│  ├─ .env.example                   # 后端环境变量示例，不包含真实密钥
│  ├─ requirements.txt               # Python 依赖
│  └─ start.py                       # Zeabur 后端启动入口
│
├─ server/                           # 历史服务或辅助服务代码
├─ configs/                          # 项目辅助配置
├─ saveplan-deploy/                  # 部署相关辅助文件
├─ CHANGELOG.md                      # 中文更新日志，每次修改都需要追加记录
├─ package.json                      # 工作区脚本
├─ package-lock.json                 # npm 锁定文件
└─ README.md                         # GitHub 项目展示说明
```

---

## 功能模块

| 模块 | 说明 |
| --- | --- |
| 首页 | 展示项目定位、学习流程、效率指标、用户反馈和视频视觉资源 |
| 转换工作台 | 提供上传文件、粘贴试卷文本、历史记录切换、题目校对和导出流程 |
| 账号系统 | 提供登录、注册、找回密码、重置密码和未登录访问保护 |
| 个人中心 | 展示用户资料、头像、积分余额、上传文件历史和转换记录 |
| 价格页面 | 展示套餐卡片、常见问题和移动端紧凑价格布局 |
| 法律与支持 | 提供隐私政策、服务条款、帮助支持、问题反馈和社区维护邀请 |
| 后端接口 | 提供认证、用户资料、转换任务、积分扣除、历史记录和健康检查接口 |

---

## 前端开发规范

- 页面优先保持项目当前的暖色、学习感和轻量卡片风格。
- 移动端页面不只做纵向堆叠，需要根据手机宽度重新组织信息密度。
- 转换页、价格页、登录注册页和首页模块都需要分别考虑手机端交互。
- 按钮、卡片、弹窗和表单控件需要保持统一圆角、阴影、边框和选中态。
- 修改 UI 后建议在桌面端、平板端和手机端分别检查布局是否溢出。

常用命令：

```powershell
cd G:\Saveplan
npm install
npm run dev
npm run build
```

---

## 后端开发规范

- 所有需要登录的接口必须从请求中校验用户身份。
- 管理后台接口必须使用独立管理员登录和 RBAC 权限校验。
- 普通用户认证已迁移到 `backend/app/modules/auth/`，对外 API 路径保持 `/api/auth/*` 不变。
- 新增后端模块必须遵循 `controller.py -> service.py -> crud.py -> model.py` 的模块四层约定，详见 [backend/ARCHITECTURE.md](backend/ARCHITECTURE.md)。
- 积分扣除、转换历史和上传文件记录由后端保存，前端只负责展示。
- 不要把真实 `.env`、JWT 密钥、OCR Token 或其他私密配置提交到 GitHub。
- 生产环境必须配置强随机 `SAVEPLAN_JWT_SECRET` 和正确的 `SAVEPLAN_PUBLIC_ORIGINS`。
- 新增接口时需要同步更新前端 `services/` 中的请求封装。

后端常用命令：

```powershell
cd G:\Saveplan\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## 快速开始

### 1. 克隆仓库

```powershell
git clone https://github.com/Xname-crypto/Saveplan.git
cd Saveplan
```

### 2. 安装前端依赖

```powershell
npm install
```

### 3. 启动前端

```powershell
npm run dev
```

默认访问地址：

```text
http://localhost:5173
```

### 4. 启动后端

另开一个终端：

```powershell
cd G:\Saveplan\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

默认后端地址：

```text
http://127.0.0.1:8000/api
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

---

## 环境变量

后端环境变量请从示例文件复制：

```powershell
cd G:\Saveplan\backend
copy .env.example .env
notepad .env
```

常用后端变量：

```bash
SAVEPLAN_DATABASE_URL=postgresql+psycopg://saveplan:password@localhost:5432/saveplan
SAVEPLAN_JWT_SECRET=替换为足够长的随机密钥
SAVEPLAN_ADMIN_JWT_SECRET=替换为另一段足够长的随机密钥
SAVEPLAN_ADMIN_EMAIL=admin@saveplan.vip
SAVEPLAN_ADMIN_PASSWORD=替换为强管理员密码
SAVEPLAN_DATA_DIR=/data
SAVEPLAN_PUBLIC_ORIGINS=https://saveplan.vip,https://www.saveplan.vip
PADDLEOCR_API_TOKEN=替换为真实 Token
PADDLEOCR_MODEL=PaddleOCR-VL-1.6
PADDLEOCR_JOB_URL=https://paddleocr.aistudio-app.com/api/v2/ocr/jobs
```

前端生产环境变量：

```bash
VITE_API_BASE_URL=https://你的后端域名/api
```

---

## 数据库与存储

- 生产环境推荐使用 PostgreSQL 保存用户、积分、转换记录、管理员、角色权限和审计日志。
- 本地开发在未配置 `SAVEPLAN_DATABASE_URL` 时会 fallback 到 SQLite，方便快速调试。
- 上传文件和转换相关文件保存到后端数据目录中。
- Zeabur 部署时建议将 `SAVEPLAN_DATA_DIR` 指向持久化目录，例如 `/data`。
- 数据库结构通过 Alembic 迁移维护。

迁移命令：

```powershell
cd G:\Saveplan\backend
alembic -c alembic.ini upgrade head
```

---

## 生产部署

建议在 Zeabur 中拆成两个服务：一个前端静态服务，一个后端 Python 服务。

### 后端服务

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python start.py
```

后端部署后先检查：

```text
https://你的后端域名/api/health
```

### 前端服务

```text
Root Directory: frontend
Build Command: npm install && npm run build
Output Directory: dist
```

前端服务需要配置：

```text
VITE_API_BASE_URL=https://你的后端域名/api
```

自定义域名：

```text
saveplan.vip
```

---

## 常见问题

### 这个项目是否需要后端？

需要。登录注册、用户资料、转换记录、上传文件、积分扣除和接口权限校验都依赖后端服务。

### 为什么未登录用户不能进入转换界面？

转换任务会产生用户数据和积分扣除。为了避免数据归属混乱，转换页需要登录后访问。

### GitHub 每次修改都要写更新日志吗？

是的。项目约定每次重要修改都同步更新 [CHANGELOG.md](CHANGELOG.md)，方便在 GitHub 上查看 v2 版本演进记录。

### 管理员后台现在是否已经完成？

当前项目已有后端接口和数据基础，但独立管理员后台仍属于后续规划。未来可以用于用户管理、积分管理、转换记录审核和系统配置。

---

## 系统截图

项目已经包含首页、转换页、价格页、登录注册页和个人中心等页面。后续可以在 `docs/screenshots/` 中补充 GitHub 展示截图，让仓库首页更直观。

---

## 后续规划

- 独立管理员后台：用户管理、积分调整、转换记录管理、系统配置和审计日志。
- 套餐与支付：将价格页套餐与真实积分、订单和支付系统打通。
- OCR 增强：接入更稳定的云端 OCR 与图片题识别流程。
- 导出格式：支持 Markdown、Anki、刷题软件导入格式和结构化文件。
- 数据库升级：根据生产规模从 SQLite 平滑迁移到 PostgreSQL 或 MySQL。
- 项目截图：补充桌面端、平板端和手机端的 GitHub README 展示图。

---

## 更新日志

项目修改记录统一维护在 [CHANGELOG.md](CHANGELOG.md)。

推荐提交流程：

```powershell
git status
git add README.md CHANGELOG.md 其他修改文件
git commit -m "简短说明本次修改"
git push origin v2-mobile-responsive
```

---

## 开源协议

当前仓库暂未指定开源协议。正式公开协作前，建议补充 License 文件，明确允许使用、修改、分发和商业使用的范围。

---

## 相关链接

- 线上网站：[https://saveplan.vip](https://saveplan.vip)
- GitHub 仓库：[https://github.com/Xname-crypto/Saveplan](https://github.com/Xname-crypto/Saveplan)
- 项目创建者：`XuBuoJun(许博钧)`
- 联系邮箱：`2132984349@qq.com`

我们诚邀有能力或有技术的同学加入这个社区，一起维护、完善和扩展 Save Your Finals。
