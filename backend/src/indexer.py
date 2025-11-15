"""Vector indexing - chunks documents and creates embeddings."""
import json
from pathlib import Path
from typing import List
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from tqdm import tqdm

from .config import (
    DOCS_JSONL_PATH, CHROMA_PATH, COLLECTION_NAME,
    EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP
)
from .models import Document, Chunk


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> List[tuple]:
    """
    Split text into overlapping chunks with table-aware and slide-aware splitting.
    Tables and slides are kept intact and not split across chunks.
    Returns list of (chunk_text, start_char, end_char) tuples.
    """
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if overlap is None:
        overlap = CHUNK_OVERLAP
    
    chunks = []
    
    import re
    
    # Find all table boundaries
    table_pattern = r'\[TABLE \d+\]'
    end_table_pattern = r'\[END TABLE\]'
    
    # Find positions of table starts and ends
    table_starts = [(m.start(), m.end()) for m in re.finditer(table_pattern, text)]
    table_ends = [(m.start(), m.end()) for m in re.finditer(end_table_pattern, text)]
    
    # Create ranges for tables
    table_ranges = []
    for start_pos, start_end in table_starts:
        for end_pos, end_end in table_ends:
            if end_pos > start_pos:
                table_ranges.append((start_pos, end_end))
                break
    
    # Find all slide boundaries (for presentation PDFs)
    slide_pattern = r'\[SLIDE \d+[^\]]*\]'
    slide_matches = list(re.finditer(slide_pattern, text))
    
    # Create ranges for slides (from [SLIDE X] to next [SLIDE X] or end of text)
    slide_ranges = []
    for i, match in enumerate(slide_matches):
        start_pos = match.start()
        if i + 1 < len(slide_matches):
            end_pos = slide_matches[i + 1].start()
        else:
            # Last slide goes to end of text
            end_pos = len(text)
        slide_ranges.append((start_pos, end_pos))
    
    def is_in_protected_region(pos: int) -> tuple:
        """
        Check if position is inside a table or slide.
        Returns (is_protected, region_type, end_pos) tuple.
        """
        # Check tables first (higher priority)
        for start, end in table_ranges:
            if start <= pos < end:
                return (True, 'table', end)
        
        # Check slides
        for start, end in slide_ranges:
            if start <= pos < end:
                return (True, 'slide', end)
        
        return (False, None, pos)
    
    # Chunk the text
    start = 0
    
    while start < len(text):
        # Check if we're starting inside a protected region (table or slide)
        is_protected, region_type, region_end = is_in_protected_region(start)
        
        if is_protected:
            # Include the entire region (table or slide) in one chunk
            chunk = text[start:region_end]
            if chunk.strip():
                chunks.append((chunk, start, region_end))
            start = region_end
            continue
        
        # Normal chunking
        end = start + chunk_size
        
        # If chunk would split a protected region, extend to include the whole region
        if end < len(text):
            is_protected_at_end, _, region_end_at_end = is_in_protected_region(end)
            if is_protected_at_end:
                # Extend chunk to include the whole region, but cap at reasonable size
                max_extend = min(region_end_at_end, start + chunk_size * 2)  # Don't extend more than 2x chunk size
                end = max_extend
        
        chunk = text[start:end]
        
        if chunk.strip():  # Only add non-empty chunks
            chunks.append((chunk, start, end))
        
        # Move start position with overlap
        start += chunk_size - overlap
        
        # Prevent infinite loop
        if start >= len(text):
            break
    
    return chunks


def load_documents(jsonl_path: Path) -> List[Document]:
    """Load documents from JSONL file."""
    documents = []
    
    if not jsonl_path.exists():
        print(f"Error: {jsonl_path} not found. Run ingest.py first.")
        return documents
    
    print(f"Loading documents from {jsonl_path}...")
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                doc_dict = json.loads(line)
                documents.append(Document(**doc_dict))
    
    return documents


def create_chunks(documents: List[Document]) -> List[Chunk]:
    """Create chunks from documents."""
    all_chunks = []
    
    print("Chunking documents...")
    for doc_idx, doc in enumerate(tqdm(documents, desc="Chunking")):
        text_chunks = chunk_text(doc.text, CHUNK_SIZE, CHUNK_OVERLAP)
        
        for chunk_idx, (chunk_text_content, start_char, end_char) in enumerate(text_chunks):
            chunk = Chunk(
                text=chunk_text_content,
                breadcrumb=doc.breadcrumb,
                source_file=doc.source_file,
                chunk_id=chunk_idx,
                start_char=start_char,
                end_char=end_char
            )
            all_chunks.append(chunk)
    
    return all_chunks


def embed_chunks(chunks: List[Chunk], model: SentenceTransformer = None) -> List[List[float]]:
    """Generate embeddings for chunks."""
    if model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}...")
        model = SentenceTransformer(EMBEDDING_MODEL)
    
    print("Generating embeddings...")
    texts = [chunk.text for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    return embeddings.tolist()


def store_in_chroma(chunks: List[Chunk], embeddings: List[List[float]]):
    """Store chunks and embeddings in ChromaDB."""
    print(f"Storing {len(chunks)} chunks in ChromaDB...")
    
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Get or create collection
    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        # Delete all documents from existing collection
        all_ids = collection.get()['ids']
        if all_ids:
            collection.delete(ids=all_ids)
        print(f"Creating new collection: {COLLECTION_NAME}")
        collection = client.create_collection(COLLECTION_NAME)
    except Exception as e:
        # Collection doesn't exist or other error, create new
        try:
            collection = client.create_collection(COLLECTION_NAME)
            print(f"Created new collection: {COLLECTION_NAME}")
        except Exception as create_error:
            # If creation fails, it might already exist - try to get it
            collection = client.get_collection(COLLECTION_NAME)
            # Delete all and recreate
            all_ids = collection.get()['ids']
            if all_ids:
                collection.delete(ids=all_ids)
    
    # Prepare data for ChromaDB
    ids = [f"{i}" for i in range(len(chunks))]
    texts = [chunk.text for chunk in chunks]
    metadatas = [
        {
            "breadcrumb": chunk.breadcrumb,
            "source_file": chunk.source_file,
            "chunk_id": str(chunk.chunk_id),
            "start_char": str(chunk.start_char),
            "end_char": str(chunk.end_char),
        }
        for chunk in chunks
    ]
    
    # Add to collection
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    
    print(f"[SUCCESS] Stored {len(chunks)} chunks in collection '{COLLECTION_NAME}'")
    print(f"[SUCCESS] ChromaDB persisted to: {CHROMA_PATH}")


def main():
    """Main indexing function."""
    print("=" * 60)
    print("Course Compass - Vector Indexing")
    print("=" * 60)
    
    # Load documents
    documents = load_documents(DOCS_JSONL_PATH)
    
    if not documents:
        print("No documents found. Please run ingest.py first.")
        return
    
    # Create chunks
    chunks = create_chunks(documents)
    print(f"Created {len(chunks)} chunks from {len(documents)} documents")
    
    # Generate embeddings
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = embed_chunks(chunks, model)
    
    # Store in ChromaDB
    store_in_chroma(chunks, embeddings)
    
    print("\n[SUCCESS] Indexing complete!")


if __name__ == "__main__":
    main()

