# K8s AIOps Dashboard

## Backend setup

```bash
cd backend
pip install fastapi uvicorn websockets
python main.py
```

Runs on `http://localhost:8000`

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173`

Both must run simultaneously for the dashboard to work.
