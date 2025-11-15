"""Hybrid search retriever - combines vector and BM25 search."""
from typing import List, Dict, Tuple
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from .config import (
    CHROMA_PATH, COLLECTION_NAME, EMBEDDING_MODEL,
    TOP_K, MAX_SOURCES, LOW_CONFIDENCE_THRESHOLD
)


class Retriever:
    """Hybrid retriever combining vector search and BM25."""
    
    def __init__(self):
        """Initialize retriever with ChromaDB and embedding model."""
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.client.get_collection(COLLECTION_NAME)
        except Exception as e:
            raise ValueError(
                f"Collection '{COLLECTION_NAME}' not found. Please run indexer.py first."
            ) from e
        
        # Load embedding model
        print(f"Loading embedding model: {EMBEDDING_MODEL}...")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Build BM25 index from all documents
        print("Building BM25 index...")
        all_docs = self.collection.get()
        self.documents = all_docs['documents']
        self.metadatas = all_docs['metadatas']
        
        # Tokenize documents for BM25
        tokenized_docs = [doc.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        
        print("[SUCCESS] Retriever initialized")
    
    def vector_search(self, query: str, top_k: int = None) -> List[Dict]:
        """Vector similarity search using ChromaDB."""
        if top_k is None:
            top_k = TOP_K
        
        # Generate query embedding with normalized embeddings
        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)[0].tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                # ChromaDB returns cosine distance (0=identical, ~2=opposite)
                # Convert to similarity (1=identical, 0=opposite)
                distance = results['distances'][0][i] if results['distances'] else 1.0
                similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0)))  # Clamp to [0, 1]
                
                formatted_results.append({
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': similarity,
                    'type': 'vector'
                })
        
        return formatted_results
    
    def bm25_search(self, query: str, top_k: int = None) -> List[Dict]:
        """BM25 keyword search."""
        if top_k is None:
            top_k = TOP_K
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Format results
        formatted_results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include documents with score > 0
                formatted_results.append({
                    'text': self.documents[idx],
                    'metadata': self.metadatas[idx],
                    'score': float(scores[idx]),
                    'type': 'bm25'
                })
        
        return formatted_results
    
    def hybrid_search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Combine vector and BM25 search results.
        Returns reranked and merged results.
        """
        if top_k is None:
            top_k = TOP_K
        
        # Perform both searches
        vector_results = self.vector_search(query, top_k * 2)  # Get more for reranking
        bm25_results = self.bm25_search(query, top_k * 2)
        
        # Normalize scores safely
        def _normalize_scores(results):
            """Normalize scores to [0, 1] range, handling empty/edge cases."""
            if not results:
                return {}
            
            scores = [r['score'] for r in results]
            if not scores:
                return {}
            
            max_score = max(scores)
            min_score = min(scores)
            
            if max_score == min_score or max_score == 0:
                # All scores same or zero - return neutral 0.5
                return {i: 0.5 for i in range(len(results))}
            
            # Normalize to [0, 1]
            normalized = {}
            for i, score in enumerate(scores):
                normalized[i] = (score - min_score) / (max_score - min_score)
            
            return normalized
        
        # Apply normalization
        v_normalized = _normalize_scores(vector_results)
        b_normalized = _normalize_scores(bm25_results)
        
        for i, r in enumerate(vector_results):
            r['normalized_score'] = v_normalized.get(i, 0.0)
        
        for i, r in enumerate(bm25_results):
            r['normalized_score'] = b_normalized.get(i, 0.0)
        
        # Keyword boost for specific query types
        query_lower = query.strip().lower()
        keyword_boost = 0.0
        
        # Boost for location queries
        if query_lower.startswith(("where", "which module", "find")):
            keyword_boost = 0.15
        # Boost for materials/books queries
        elif any(keyword in query_lower for keyword in ["material", "book", "textbook", "required", "course pack"]):
            keyword_boost = 0.20  # Higher boost for materials queries
            # Additional boost for chunks containing materials-related terms
            for result in vector_results:
                result_text = result.get('text', '').lower()
                if any(term in result_text for term in ["table", "material", "book", "fundamentals", "course pack", "lab access"]):
                    result['normalized_score'] = min(1.0, result.get('normalized_score', 0.0) + 0.25)
            
            for result in bm25_results:
                result_text = result.get('text', '').lower()
                if any(term in result_text for term in ["table", "material", "book", "fundamentals", "course pack", "lab access"]):
                    result['normalized_score'] = min(1.0, result.get('normalized_score', 0.0) + 0.25)
        
        # Merge results by text (deduplicate)
        merged = {}
        
        # Add vector results (weight: 0.6)
        for result in vector_results:
            text = result['text']
            if text not in merged:
                merged[text] = {
                    **result,
                    'hybrid_score': result.get('normalized_score', 0.0) * 0.6
                }
            else:
                merged[text]['hybrid_score'] += result.get('normalized_score', 0.0) * 0.6
        
        # Add BM25 results (weight: 0.4)
        for result in bm25_results:
            text = result['text']
            if text not in merged:
                merged[text] = {
                    **result,
                    'hybrid_score': result.get('normalized_score', 0.0) * 0.4
                }
            else:
                merged[text]['hybrid_score'] += result.get('normalized_score', 0.0) * 0.4
        
        # Apply keyword boost and clamp scores
        for key in merged:
            merged[key]['hybrid_score'] = max(0.0, min(1.0, merged[key]['hybrid_score'] + keyword_boost))
        
        # Convert to list and sort by hybrid score
        final_results = list(merged.values())
        final_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return final_results[:top_k]
    
    def retrieve(self, query: str, top_k: int = None) -> Tuple[List[Dict], float]:
        """
        Main retrieval function.
        Returns (results, confidence_score) where confidence is top hit's score [0, 1].
        """
        if top_k is None:
            top_k = TOP_K
        
        results = self.hybrid_search(query, top_k)
        
        # Calculate confidence from top score (not average) - clamped to [0, 1]
        if results:
            top_score = results[0].get('hybrid_score', 0.0)
            confidence = max(0.0, min(1.0, top_score))  # Clamp to [0, 1]
        else:
            confidence = 0.0
        
        return results, confidence
    
    def get_all_chunks(self) -> List[Dict]:
        """Get all chunks from the collection (for full context to Gemini)."""
        all_results = []
        
        for i in range(len(self.documents)):
            all_results.append({
                'text': self.documents[i],
                'metadata': self.metadatas[i] if self.metadatas and i < len(self.metadatas) else {},
                'score': 1.0,  # All chunks treated equally when sending all
                'type': 'all'
            })
        
        return all_results


# Global retriever instance (lazy-loaded)
_retriever_instance = None


def get_retriever() -> Retriever:
    """Get or create global retriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance

