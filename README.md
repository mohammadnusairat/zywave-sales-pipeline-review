# Zywave Sales Pipeline Review App

A full-stack app for analyzing sales pipeline movement, risk, review priorities, and recommended actions from uploaded Excel data.

## Tech Stack

- React frontend
- FastAPI backend
- Python data processing
- Excel input/output workflow

## Features

- Upload Excel pipeline data
- Generate completed analysis file
- View risk scoring and decision brief
- Review opportunity-level insights
- Download processed Excel output

## Running Locally

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

*Authorered by Mohammad Nusairat in April, 2026*