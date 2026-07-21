# Save Your Finals

Vue + FastAPI starter for a Chinese study-tool landing page. The frontend is a Vue 3/Vite/Tailwind app, and the backend is a small FastAPI API scaffold.

## Scripts

```bash
npm install
npm run dev
npm run build
```

Run the API in a second terminal:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## PaddleOCR cloud OCR

The converter can use PaddleOCR cloud recognition when the user selects image/OCR processing.
Create `backend/.env` from `backend/.env.example`, then put your real token in it:

```powershell
cd backend
copy .env.example .env
notepad .env
uvicorn app.main:app --reload
```

Do not commit the PaddleOCR token to GitHub.

## Deploy to Zeabur

Deploy this repository as two Zeabur services from the same GitHub repo.

### 1. Backend service

Create a Python service and set the root directory to `backend`.

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
python start.py
```

Environment variables:

```bash
SAVEPLAN_JWT_SECRET=replace-with-a-long-random-secret
SAVEPLAN_DATA_DIR=/data
SAVEPLAN_PUBLIC_ORIGINS=https://your-frontend-domain.zeabur.app
PADDLEOCR_API_TOKEN=replace-with-your-token
PADDLEOCR_MODEL=PaddleOCR-VL-1.6
PADDLEOCR_JOB_URL=https://paddleocr.aistudio-app.com/api/v2/ocr/jobs
```

If you need uploads and the SQLite database to survive redeploys, mount a
persistent volume at `/data`.

After deploy, check:

```bash
https://your-backend-domain.zeabur.app/api/health
```

### 2. Frontend service

Create a Vite/Node.js static service and set the root directory to `frontend`.

Build command:

```bash
npm install && npm run build
```

Output directory:

```bash
dist
```

Environment variables:

```bash
VITE_API_BASE_URL=https://your-backend-domain.zeabur.app/api
```

After both services have their final domains, update
`SAVEPLAN_PUBLIC_ORIGINS` on the backend with the frontend origin, then
redeploy the backend.
