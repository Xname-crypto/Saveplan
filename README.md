# Save Your Finals

Save Your Finals 是一个面向学生和备考用户的题库整理与资料转换工具。项目支持登录注册、资料上传、OCR/AI 转换、题目校对、导出复习资料，并已按前后端分离方式部署到 Zeabur。

## 项目结构

```text
frontend/  Vue 3 + Vite 前端页面
backend/   FastAPI 后端接口
server/    旧版/辅助服务代码
```

## 本地运行

安装依赖并启动前端：

```bash
npm install
npm run dev
```

另开一个终端启动后端：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 环境变量

后端环境变量请从示例文件复制：

```powershell
cd backend
copy .env.example .env
notepad .env
```

不要把真实的 `.env`、JWT 密钥、PaddleOCR Token 或其他私密配置提交到 GitHub。

常用变量：

```bash
SAVEPLAN_JWT_SECRET=替换为足够长的随机密钥
SAVEPLAN_DATA_DIR=/data
SAVEPLAN_PUBLIC_ORIGINS=https://saveplan.vip,https://www.saveplan.vip
PADDLEOCR_API_TOKEN=替换为真实 Token
PADDLEOCR_MODEL=PaddleOCR-VL-1.6
PADDLEOCR_JOB_URL=https://paddleocr.aistudio-app.com/api/v2/ocr/jobs
```

## 部署到 Zeabur

这个仓库在 Zeabur 中建议拆成两个服务部署。

后端服务：

```bash
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: python start.py
```

后端健康检查：

```text
https://你的后端域名/api/health
```

前端服务：

```bash
Root Directory: frontend
Build Command: npm install && npm run build
Output Directory: dist
```

前端环境变量：

```bash
VITE_API_BASE_URL=https://你的后端域名/api
```

## 更新日志

每次修改项目后，请同步更新 [CHANGELOG.md](CHANGELOG.md)，再提交到 GitHub。这样以后在 GitHub 上查看项目历史时，可以直接看到每次改了什么。

推荐提交流程：

```powershell
git status
git add README.md CHANGELOG.md 其他修改文件
git commit -m "简短说明本次修改"
git push origin main
```
