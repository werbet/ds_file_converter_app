# Data File Converter Web App

This project allows users to upload a Spyder .py file and convert it to a Jupyter Notebook (.ipynb) via a web interface.

## Structure
- `backend/` - FastAPI Python backend for file upload, conversion, and download
- `src/` - React frontend (Vite)

## Quick Start

### Backend
```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```
npm install
npm run dev
```

---

See the PRD for requirements and future plans.
