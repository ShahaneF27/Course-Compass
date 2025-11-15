# Setup Guide

Complete step-by-step setup instructions for Course Compass.

## Prerequisites

### Required Software

- **Python 3.9+**
  ```bash
  python --version
  ```

- **Node.js 18+**
  ```bash
  node --version
  ```

- **npm or yarn**
  ```bash
  npm --version
  ```

### Git

- Git installed and configured
- Repository cloned locally

## Step 1: Python Virtual Environment

### Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your terminal prompt.

### Verify Activation

```bash
which python  # Should point to .venv/bin/python (macOS/Linux)
where python  # Should point to .venv\Scripts\python.exe (Windows)
```

## Step 2: Install Backend Dependencies

```bash
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Verify Installation

```bash
python -c "import fastapi, chromadb, sentence_transformers; print('All packages installed!')"
```

## Step 3: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### Verify Installation

```bash
cd frontend
npm list --depth=0
cd ..
```

## Step 4: Configure Environment Variables

### Backend Configuration

Create `backend/.env`:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# ChromaDB Collection
COLLECTION_NAME=canvas_chunks

# Data Paths (relative to backend/)
DATA_RAW_PATH=data/raw
DATA_INDEX_PATH=data/index

# Optional: Claude API Key (for advanced answer generation)
# CLAUDE_API_KEY=your_key_here
```

### Frontend Configuration

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

**Note**: Use `backend/.env.example` and `frontend/.env.example` as templates.

## Step 5: Add Course Files

### Directory Structure

Organize your course files in `backend/data/raw/`:

```
backend/data/raw/
├── Week_01/
│   ├── reading_guide.md
│   └── syllabus_overview.pdf
├── Week_02/
│   ├── policy_memo_rubric.pdf
│   └── memo_brief.md
├── Week_03/
│   └── supply_and_demand_notes.md
└── csv/
    ├── grades.csv
    ├── assignments.csv
    └── roster.csv
```

### Supported File Formats

- **Markdown** (`.md`) - Direct text extraction
- **Text** (`.txt`) - Direct text extraction
- **PDF** (`.pdf`) - Text extraction via PyPDF
- **CSV** (`.csv`) - Converted to text documents

### Breadcrumb Heuristics

Files are organized into breadcrumbs based on folder structure:
- `Week_01/reading_guide.md` → `Modules > Week_01 > reading_guide`
- `Week_02/policy_memo_rubric.pdf` → `Modules > Week_02 > policy_memo_rubric`

## Step 6: Build the Index

### Ingest Course Files

```bash
python backend/src/ingest.py
```

This will:
- Process all files in `backend/data/raw/`
- Extract text from supported formats
- Generate breadcrumbs from directory structure
- Create `backend/data/index/docs.jsonl`

### Create Vector Index

```bash
python backend/src/indexer.py
```

This will:
- Chunk documents (1200 chars, 200 overlap)
- Generate embeddings using all-MiniLM-L6-v2
- Store in ChromaDB collection `canvas_chunks`
- Persist to `backend/data/index/chroma/`

**Expected output:**
```
Processing 50 documents...
Chunking documents...
Generating embeddings...
Storing in ChromaDB...
Index created successfully!
```

## Step 7: Run the Application

### Start Backend API

**Terminal 1:**
```bash
# Activate venv if not already active
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Start FastAPI server
uvicorn backend.app:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Start Frontend Dev Server

**Terminal 2:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## Step 8: Verify Installation

### Test Backend API

1. **Open API docs**: http://localhost:8000/docs
2. **Test `/chat` endpoint**:
   ```json
   {
     "query": "Where is the syllabus?"
   }
   ```

### Test Frontend

1. **Open frontend**: http://localhost:5173
2. **Try a test query**: "Where is the assignment rubric?"
3. **Verify citations appear** in the sources panel

## Troubleshooting

### Python Issues

**Problem**: `pip: command not found`
- **Solution**: Use `python -m pip` instead

**Problem**: `ModuleNotFoundError: No module named 'fastapi'`
- **Solution**: Verify virtual environment is activated

**Problem**: ChromaDB errors
- **Solution**: Ensure `backend/data/index/chroma/` directory exists and is writable

### Node Issues

**Problem**: `npm: command not found`
- **Solution**: Install Node.js from nodejs.org

**Problem**: `EACCES` permission errors
- **Solution**: Use `sudo npm install` (macOS/Linux) or run terminal as admin (Windows)

### Port Conflicts

**Problem**: Port 8000 already in use
- **Solution**: Change port in `uvicorn` command: `--port 8001`

**Problem**: Port 5173 already in use
- **Solution**: Vite will automatically use the next available port

### Data Issues

**Problem**: No files found during ingestion
- **Solution**: Verify files are in `backend/data/raw/` with correct extensions

**Problem**: Empty index after indexing
- **Solution**: Check `backend/data/index/docs.jsonl` exists and has content

## Next Steps

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Check API documentation at http://localhost:8000/docs
- Add your course files and rebuild the index

## Getting Help

- Check the [README.md](README.md) for quick reference
- Review error messages in terminal output
- Verify all prerequisites are installed correctly

---

Happy hacking! 🚀

