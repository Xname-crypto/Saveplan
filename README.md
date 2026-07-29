# Save Your Finals

> 面向学生与备考用户的题库整理、资料转换与复习资料导出平台。

![Vue](https://img.shields.io/badge/Vue-3.5.21-42b883)
![Vite](https://img.shields.io/badge/Vite-7.x-646cff)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.13-009688)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Database](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Deploy](https://img.shields.io/badge/Deploy-Zeabur-black)

## 项目简介

Save Your Finals 是一个前后端分离的题库导入助手，帮助用户把 PDF、Word、TXT 或粘贴的试卷文本整理成结构化题目，并进一步进行校对、导出和复习资料管理。

项目当前已覆盖登录注册、文件上传、文本解析、历史记录、个人中心、积分扣除、隐私条款、服务条款和帮助支持等核心流程，适合继续扩展为面向学生、备考用户或小型学习社区的在线工具。

## 核心能力

- 用户账号：注册、登录、登录态校验、找回密码和重置密码。
- 资料导入：支持 PDF、DOC、DOCX、TXT 文件上传。
- 文本转换：支持直接粘贴试卷文本并按固定格式解析。
- 题目校对：对识别后的题干、选项、答案和解析进行人工校对。
- 导出资料：导出适合后续复习整理的结构化文本。
- 历史记录：保存用户转换过的文件、题目数量、状态和时间。
- 积分系统：创建转换任务时扣除积分，并展示剩余积分。
- 个人中心：展示用户资料、头像、兴趣标签、积分和转换记录。
- 法律与支持：内置隐私政策、服务条款、问题反馈和帮助支持弹窗。
- 社区维护：邀请有能力或有技术的同学加入维护，联系项目创建者 XuBuoJun(许博钧)。

## 技术栈

### 前端

- Vue 3
- Vite
- TypeScript
- Tailwind CSS
- lucide-vue-next
- GSAP

### 后端

- FastAPI
- Pydantic
- SQLite
- python-multipart
- pypdf
- requests
- python-dotenv

### 部署

- Zeabur 前端静态服务
- Zeabur 后端 Python 服务
- 自定义域名：`saveplan.vip`

## 仓库结构

```text
Saveplan/
├─ frontend/                 Vue 3 + Vite 前端应用
│  ├─ public/                静态资源、视频、图标、头像
│  ├─ src/
│  │  ├─ components/         公共组件
│  │  ├─ services/           authClient、conversionClient 等接口封装
│  │  ├─ views/              首页、转换页、价格页、个人中心、登录注册页
│  │  └─ router/             前端路由
│  └─ package.json
├─ backend/                  FastAPI 后端服务
│  ├─ app/
│  │  ├─ auth.py             用户注册、登录、会话、密码重置
│  │  ├─ conversions.py      文件上传、文本解析、转换历史、积分扣除
│  │  ├─ config.py           后端配置
│  │  ├─ main.py             FastAPI 应用入口
│  │  └─ kshuati_converter.py
│  ├─ requirements.txt
│  └─ start.py
├─ server/                   旧版或辅助服务代码
├─ CHANGELOG.md              项目更新日志
├─ package.json              前端工作区脚本
└─ README.md
```

## 功能页面

| 页面 | 说明 |
| --- | --- |
| 首页 | 项目介绍、学习流程、核心能力和用户反馈展示 |
| 转换页 | 上传文件、粘贴试卷文本、历史记录、题目校对和导出 |
| 价格页 | 展示不同套餐和常见问题 |
| 登录页 | 用户登录入口 |
| 注册页 | 用户注册、身份信息和头像选择 |
| 找回密码 | 邮箱找回与重置密码流程 |
| 个人中心 | 用户资料、积分、上传文件历史和转换记录 |
| 帮助支持 | 客服邮箱、问题反馈、社区维护邀请 |

## 本地运行

### 1. 安装前端依赖

```powershell
cd G:\Saveplan
npm install
```

### 2. 启动前端

```powershell
npm run dev
```

默认访问：

```text
http://localhost:5173
```

### 3. 启动后端

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

## 环境变量

后端环境变量请从示例文件复制：

```powershell
cd G:\Saveplan\backend
copy .env.example .env
notepad .env
```

常用变量：

```bash
SAVEPLAN_JWT_SECRET=替换为足够长的随机密钥
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

不要把真实 `.env`、JWT 密钥、PaddleOCR Token 或其他私密配置提交到 GitHub。

## Zeabur 部署

建议在 Zeabur 中拆成两个服务部署。

### 后端服务

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python start.py
```

后端健康检查：

```text
https://你的后端域名/api/health
```

### 前端服务

```text
Root Directory: frontend
Build Command: npm install && npm run build
Output Directory: dist
```

前端环境变量：

```text
VITE_API_BASE_URL=https://你的后端域名/api
```

## 数据与安全

- 用户密码使用 PBKDF2 哈希保存。
- 登录状态由后端签发 Token 并进行有效期校验。
- 普通用户只能读取和管理自己的转换记录。
- 积分余额由后端保存，转换任务创建时由后端扣除。
- 上传文件和转换媒体文件保存在后端数据目录中。
- 生产环境必须配置强随机 `SAVEPLAN_JWT_SECRET`。

## 后续规划

- 管理员独立后台：用户管理、积分管理、转换记录管理。
- 套餐与支付：将价格页套餐与真实积分/订单系统打通。
- OCR 增强：接入更稳定的云端 OCR 与图片题识别流程。
- 导出格式：支持更多刷题软件、Anki、Markdown 和结构化文件格式。
- 数据库升级：根据生产规模从 SQLite 平滑迁移到 PostgreSQL 或 MySQL。
- 审计日志：记录管理员操作、积分调整和异常转换任务。

## 更新日志

每次修改项目后，请同步更新 [CHANGELOG.md](CHANGELOG.md)，再提交到 GitHub。这样以后在 GitHub 上查看项目历史时，可以直接看到每次改了什么。

推荐提交流程：

```powershell
git status
git add README.md CHANGELOG.md 其他修改文件
git commit -m "简短说明本次修改"
git push origin v2-mobile-responsive
```

## 联系与社区维护

如果你在使用过程中遇到问题，或希望加入项目维护，可以通过以下方式联系：

- 客服邮箱：`2132984349@qq.com`
- 项目创建者：`XuBuoJun(许博钧)`

我们诚邀有能力或有技术的同学加入这个社区，一起维护、完善和扩展 Save Your Finals。
