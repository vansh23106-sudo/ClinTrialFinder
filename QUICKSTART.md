# Quick Start Guide

## 1. Prerequisites

- Python 3.10 or higher
- Neo4j database running (default: `bolt://localhost:7687`)
- FAISS index files in `data/` directory
- Git

## 2. Clone & Setup

```bash
git clone https://github.com/yourusername/clinical-trials-matcher.git
cd "Clinical Trials"
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Neo4j credentials
```

## 4. Run Backend (Terminal 1)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be at: `http://localhost:8000`

## 5. Run Frontend (Terminal 2)

```bash
cd app/static
python -m http.server 8001
```

Open in browser: `http://localhost:8001/index.html`

## 6. Test

1. Fill in patient data (Age, Gender, BMI, HbA1c, etc.)
2. Set API URL to: `http://127.0.0.1:8000/match-trials`
3. Click "Find Matching Trials"
4. View results with match scores and explanations

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
→ Run: `pip install -r requirements.txt`

### "Failed to connect to Neo4j"
→ Check NEO4J_URI and credentials in `.env`

### "CORS error in browser console"
→ Backend CORS is configured. Ensure frontend URL is http://localhost:8001

### "No results found"
→ Check Neo4j database has trial data and FAISS indexes exist in `data/` folder

## Next Steps

- Read the [README.md](../README.md) for full documentation
- Check [CONTRIBUTING.md](../CONTRIBUTING.md) to contribute
- Explore the API docs at http://localhost:8000/docs
