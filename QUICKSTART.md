# Quick Start Guide

## 🚀 3-Minute Setup

### 1. Install Dependencies

**Backend:**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r backend/requirements.txt
```

**Frontend:**
```bash
cd frontend
npm create vite@latest . -- --template react
npm install
cd ..
```

### 2. Add Course Files

Drop your course exports into `backend/data/raw/`:
```
backend/data/raw/
├── Week_01/
│   ├── reading_guide.md
│   └── syllabus.pdf
├── Week_02/
│   └── rubric.pdf
└── ...
```

### 3. Build Index

```bash
python backend/src/ingest.py
python backend/src/indexer.py
```

### 4. Run Application

**Terminal 1 (Backend):**
```bash
uvicorn backend.app:app --reload --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### 5. Open Browser

- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

## 📝 Next Steps

- Read [SETUP.md](SETUP.md) for detailed instructions
- Read [README.md](README.md) for features and API docs
- Read [CONTRIBUTING.md](CONTRIBUTING.md) for development

---

**That's it!** Start asking questions about your course materials. 🎓

