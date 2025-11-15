"""
LlamaIndex Gemini LLM wrapper for improved reliability.
Uses LlamaIndex's Gemini integration which has better timeout/retry handling.
Works with existing retrieval system.
"""
import asyncio
from typing import Dict, Any, Optional

# Try to import LlamaIndex - if not available, the module will be disabled
try:
    from llama_index.llms.gemini import Gemini as LlamaIndexGeminiLLM
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    LlamaIndexGeminiLLM = None
    print("[WARN] LlamaIndex not available - install with: pip install llama-index-core llama-index-llms-gemini")

from .config import (
    GEMINI_API_KEY, GEMINI_MODEL
)


class LlamaIndexGemini:
    """
    LlamaIndex Gemini LLM wrapper for better reliability.
    Uses LlamaIndex's Gemini integration which has better timeout/retry handling.
    Works with existing retrieval - just provides the LLM call.
    """
    
    def __init__(self):
        """Initialize LlamaIndex Gemini LLM."""
        if not LLAMAINDEX_AVAILABLE:
            raise ImportError("LlamaIndex is not installed. Install with: pip install llama-index-core llama-index-llms-gemini")
        
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        print("[LlamaIndex] Initializing Gemini LLM...")
        
        # Configure Gemini LLM with shorter timeout settings for faster responses
        model_name = GEMINI_MODEL.replace('models/', '') if GEMINI_MODEL.startswith('models/') else GEMINI_MODEL
        self.llm = LlamaIndexGeminiLLM(
            api_key=GEMINI_API_KEY,
            model_name=model_name,
            temperature=0.3,
            max_tokens=1024,  # Reduced for faster responses
            timeout=20.0,  # Shorter timeout - fail faster
            num_retries=1,  # Only 1 retry to avoid long waits
        )
        
        print("[LlamaIndex] Gemini LLM initialized successfully!")
    
    async def generate(self, prompt: str) -> str:
        """
        Generate answer using LlamaIndex Gemini with better error handling.
        Returns the generated text or None on error.
        """
        try:
            # Use asyncio.to_thread() for async execution with shorter timeout
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(self.llm.complete, prompt),
                    timeout=25.0  # Overall timeout - shorter for faster fallback
                )
            except AttributeError:
                # Python 3.7-3.8 fallback
                loop = asyncio.get_running_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, self.llm.complete, prompt),
                    timeout=25.0
                )
            
            if response and hasattr(response, 'text'):
                return response.text
            return None
            
        except asyncio.TimeoutError:
            print("[ERROR] LlamaIndex Gemini timeout after 25 seconds - using fallback")
            return None
        except Exception as e:
            print(f"[ERROR] LlamaIndex Gemini error: {e}")
            import traceback
            traceback.print_exc()
            return None


# Global instance
_llamaindex_gemini = None


def get_llamaindex_gemini() -> LlamaIndexGemini:
    """Get or create global LlamaIndex Gemini instance."""
    global _llamaindex_gemini
    if _llamaindex_gemini is None:
        _llamaindex_gemini = LlamaIndexGemini()
    return _llamaindex_gemini

