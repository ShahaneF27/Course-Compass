# Contributing Guide

Developer documentation and architecture overview for Course Compass.

## Architecture Overview

### System Components

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│  FastAPI API │─────▶│  Retriever  │
│   (React)   │◀─────│   (Backend)  │◀─────│  (Hybrid)   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │                       │
                            │                       ▼
                            │              ┌──────────────┐
                            │              │   ChromaDB   │
                            │              │  (Vector DB) │
                            │              └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    Indexer   │
                    │  (Embedding) │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │    Ingest    │
                    │  (File Proc) │
                    └──────────────┘
```

### Data Flow

1. **Ingestion** (`ingest.py`): Raw files → `docs.jsonl`
2. **Indexing** (`indexer.py`): `docs.jsonl` → Chunks → Embeddings → ChromaDB
3. **Retrieval** (`retriever.py`): Query → Vector Search + BM25 → Top Results
4. **API** (`app.py`): Query → Retrieval → Answer + Citations
5. **Frontend**: User Query → API Call → Display Answer + Sources

## Code Structure

### Backend (`backend/`)

```
backend/
├── app.py                 # FastAPI routes and middleware
├── src/
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic schemas
│   ├── ingest.py          # File processing pipeline
│   ├── indexer.py         # Embedding and indexing
│   ├── retriever.py       # Hybrid search implementation
│   └── utils/
│       └── __init__.py    # Helper functions
└── data/
    ├── raw/               # Input files (gitignored)
    └── index/             # Generated index (gitignored)
```

### Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── App.jsx            # Main application component
│   ├── main.jsx           # Entry point
│   ├── api.js             # API client (axios/fetch)
│   └── components/
│       ├── Chat.jsx       # Chat interface
│       └── Sources.jsx    # Citations panel
└── package.json
```

## Development Setup

### Prerequisites

1. Follow [SETUP.md](SETUP.md) for initial setup
2. Ensure all dependencies are installed
3. Have test course files ready in `backend/data/raw/`

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Follow existing code style
   - Add comments for complex logic
   - Update docstrings

3. **Test locally**
   ```bash
   # Backend
   python backend/src/ingest.py
   python backend/src/indexer.py
   uvicorn backend.app:app --reload

   # Frontend
   cd frontend && npm run dev
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

### Python

- Follow PEP 8
- Use type hints where possible
- Docstrings for all functions/classes
- Maximum line length: 100 characters

**Example:**
```python
def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Number of overlapping characters between chunks
    
    Returns:
        List of text chunks
    """
    # Implementation
```

### JavaScript/React

- Use ES6+ syntax
- Functional components with hooks
- PropTypes or TypeScript (if added)
- Consistent formatting (Prettier recommended)

**Example:**
```jsx
const Chat = ({ onSendMessage }) => {
  const [query, setQuery] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSendMessage(query);
    setQuery('');
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Component JSX */}
    </form>
  );
};
```

## Adding New Features

### Adding File Format Support

**File**: `backend/src/ingest.py`

1. Add extraction function:
   ```python
   def extract_from_new_format(file_path: str) -> str:
       # Extract text from new format
       pass
   ```

2. Update `extract_text_from_file()`:
   ```python
   elif file_path.endswith('.newformat'):
       return extract_from_new_format(file_path)
   ```

3. Update documentation in README.md

### Adding Search Methods

**File**: `backend/src/retriever.py`

1. Implement new search method
2. Integrate into `hybrid_search()`
3. Update scoring/reranking logic

### Adding API Endpoints

**File**: `backend/app.py`

1. Define route:
   ```python
   @app.post("/new-endpoint")
   async def new_endpoint(request: RequestModel):
       # Implementation
       return response
   ```

2. Add to API documentation
3. Update frontend API client if needed

## Testing Guidelines

### Manual Testing Checklist

- [ ] Ingest processes all file types correctly
- [ ] Indexer creates embeddings and stores in ChromaDB
- [ ] Retriever returns relevant results
- [ ] API returns correct response format
- [ ] Frontend displays answer and citations
- [ ] Citations show correct breadcrumbs
- [ ] Error handling works (empty queries, no results, etc.)

### Test Queries

```python
test_queries = [
    "Where is the syllabus?",
    "What is the assignment rubric?",
    "How do I submit my homework?",
    "When is the exam?",
    "What are the grading criteria?",
]
```

## Configuration

### Environment Variables

All configuration should use environment variables via `config.py`:

```python
# backend/src/config.py
import os
from pathlib import Path

DATA_RAW_PATH = Path(os.getenv("DATA_RAW_PATH", "data/raw"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
```

### Constants

- Chunk size: 1200 characters
- Chunk overlap: 200 characters
- Top results: 6 chunks
- Final citations: 2-3 sources

## Performance Considerations

### Indexing

- Process files in batches for large datasets
- Use batch embedding for efficiency
- Persist ChromaDB to disk

### Retrieval

- Cache embedding model (load once)
- Use async FastAPI for concurrent requests
- Limit chunk size for faster search

### Frontend

- Debounce search input
- Show loading states
- Lazy load components if needed

## Common Issues

### Issue: Import errors

**Solution**: Ensure virtual environment is activated and packages installed

### Issue: ChromaDB collection not found

**Solution**: Run `indexer.py` to create the collection

### Issue: Empty search results

**Solution**: Verify index was built correctly and contains data

### Issue: Breadcrumbs not formatted correctly

**Solution**: Check `build_breadcrumb()` function in `ingest.py`

## Pull Request Guidelines

1. **Clear description** of changes
2. **Test locally** before submitting
3. **Update documentation** if adding features
4. **Keep commits focused** (one feature per PR)
5. **Reference issues** if applicable

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🙏

