# Course Compass 🧭

A smart course helper chatbot that combs through course files to answer questions about assignments, coursework, grades, and lectures. Built for hackathons with FastAPI and React.

## ✨ Features

- **Multi-format Support**: Ingest Markdown, PDF, CSV, and text files from your Canvas exports
- **Hybrid Search**: Combines vector similarity (embeddings) with BM25 keyword search for accurate results
- **Smart Citations**: Always provides 2-3 sources with breadcrumb paths like `Modules > Week_02 > Policy Memo Rubric`
- **Fast Answers**: Quick retrieval and concise responses to course-related questions
- **Beautiful UI**: Clean React interface with chat and sources panel

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Course-Compass
   ```

2. **Set up Python backend**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r backend/requirements.txt
   ```

3. **Set up React frontend**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Add your course files**
   - Drop course exports into `backend/data/raw/`
   - Organize by week: `Week_01/`, `Week_02/`, etc.

5. **Build the index**
   ```bash
   python backend/src/ingest.py
   python backend/src/indexer.py
   ```

6. **Run the application**
   ```bash
   # Terminal 1: Start backend API
   uvicorn backend.app:app --reload --port 8000

   # Terminal 2: Start frontend dev server
   cd frontend
   npm run dev
   ```

7. **Open your browser**
   - Frontend: http://localhost:5173
   - API docs: http://localhost:8000/docs

## 📖 Usage

### Example Questions

- **"Where is the Policy Memo rubric?"** → Shows `Modules > Week_02 > Policy Memo Rubric`
- **"What economic principle explains price rising when supply falls?"** → Supply & demand answer + Week_03 notes citation
- **"How do I start the Log Analysis Lab?"** → Step-by-step instructions + assignment page citation

### API Endpoint

**POST `/chat`**

Request:
```json
{
  "query": "Where is the assignment rubric?"
}
```

Response:
```json
{
  "answer": "The assignment rubric can be found in Week 2 materials...",
  "sources": [
    {
      "breadcrumb": "Modules > Week_02 > Policy Memo Rubric",
      "url": "https://canvas.example.com/modules/week2/rubric",
      "snippet": "The policy memo should be 3-5 pages..."
    }
  ]
}
```

## 📁 Project Structure

```
Course-Compass/
├── backend/
│   ├── app.py              # FastAPI main application
│   ├── requirements.txt    # Python dependencies
│   ├── src/
│   │   ├── config.py       # Configuration
│   │   ├── models.py       # Pydantic schemas
│   │   ├── ingest.py       # Data ingestion
│   │   ├── indexer.py      # Vector indexing
│   │   └── retriever.py    # Hybrid search
│   └── data/
│       ├── raw/            # Your course files here
│       └── index/          # Generated index (gitignored)
├── frontend/
│   ├── src/
│   │   ├── App.jsx         # Main chat interface
│   │   ├── api.js          # API client
│   │   └── components/     # React components
│   └── package.json
└── README.md
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, ChromaDB, sentence-transformers, rank-bm25
- **Frontend**: React, Vite
- **ML**: all-MiniLM-L6-v2 embeddings, hybrid search

## 📝 Documentation

- **[SETUP.md](SETUP.md)** - Detailed installation and configuration guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Developer guide and architecture

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🎯 Demo Script (5 minutes)

1. **"Where is the Policy Memo rubric?"** → Shows Modules > Week 2 > Writing Rubric citation
2. **"What economic principle explains price rising when supply falls?"** → Short supply & demand answer + Week 3 notes citation
3. **"How do I start the Log Analysis Lab?"** → Steps + assignment page citation

---

Built with ❤️ for hackathons and course management
