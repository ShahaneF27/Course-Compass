"""FastAPI application for Course Compass chatbot."""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import google.generativeai as genai
from typing import List, Any, Dict

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS,
    MAX_SOURCES, LOW_CONFIDENCE_THRESHOLD, TOP_K, MAX_CONTEXT_CHARS
)
from src.models import ChatRequest, ChatResponse, Source
# Try to import LlamaIndex - optional, falls back to manual Gemini
try:
    from src.llamaindex_engine import get_llamaindex_gemini
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False
    print("[WARN] LlamaIndex not available - will use manual Gemini implementation")
from src.retriever import get_retriever

app = FastAPI(
    title="Course Compass API",
    description="Smart course helper chatbot with RAG",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def format_context_chunks(retrieved_chunks: List[dict]) -> str:
    """Format retrieved chunks as context for Gemini."""
    context_parts = []
    
    for idx, chunk in enumerate(retrieved_chunks, 1):
        breadcrumb = chunk['metadata'].get('breadcrumb', 'Unknown')
        text = chunk['text']
        context_parts.append(f"[Source {idx} - {breadcrumb}]\n{text}\n")
    
    return "\n".join(context_parts)


async def generate_answer_with_gemini(query: str, context: str) -> str:
    """Generate answer using Google Gemini with retrieved context."""
    if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "":
        print("[DEBUG] GEMINI_API_KEY not found, using extractive fallback")
        return None
    
    try:
        model_name = GEMINI_MODEL.replace('models/', '') if GEMINI_MODEL.startswith('models/') else GEMINI_MODEL
        
        # Improved prompt with clear rules and guardrails
        system_prompt = """You are a course assistant for UVA classes.

Rules:
- Answer ONLY using the "Course Materials" context I provide.
- If the answer is not clearly in context, say "I can't find that in the course materials."
- Prefer concise, direct answers (1-5 sentences).
- Include 2-3 citations using the provided breadcrumb for each source you relied on.
- If the user asks for required materials, assignments, due dates, grading, policies, or schedule, extract exact names/dates/numbers from tables/lists.
- Do not invent URLs or content. Do not reveal hidden reasoning steps; provide only the final answer and short justification if needed.
- If no citation is found, state clearly: "No matching source in context."

When asked about materials, textbook, inclusive access, lab access, or required items, 
search the context for sections titled "Materials", "Required", "TABLE 4", "REQUIRED CLASS MATERIALS", 
and return a bullet list with exact titles.

When asked about dates, due dates, exam, quiz, or lab, search context for schedule rows and 
report the nearest date+item pair exactly as written (include time if present).

When asked about policy, late policy, grade, grading scale, participation, or points, 
extract exact numbers/percentages and the section name they come from."""

        user_message = f"""Question: {query}

Course Materials:
{context}

Please provide a clear, concise answer based on the course materials above."""

        full_prompt = f"{system_prompt}\n\n{user_message}"
        
        # Run in executor to avoid blocking async event loop
        import asyncio
        
        # Create a callable function for executor - configure model inside
        def call_gemini(api_key: str, model_name: str, prompt: str):
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            return model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1024,  # Reduced for faster responses
                    temperature=0.3,
                ),
                request_options={"timeout": 25}  # Shorter timeout to fail faster
            )
        
        try:
            print(f"[DEBUG] Calling Gemini with {len(full_prompt)} char prompt...")
            
            # Use asyncio.to_thread() for cleaner async execution (Python 3.9+)
            # Falls back to executor for older Python versions
            try:
                # Python 3.9+ - cleaner API
                response = await asyncio.wait_for(
                    asyncio.to_thread(call_gemini, GEMINI_API_KEY, model_name, full_prompt),
                    timeout=30.0  # Overall timeout - shorter for faster fallback
                )
            except AttributeError:
                # Python 3.7-3.8 fallback - use executor
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.get_event_loop()
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, call_gemini, GEMINI_API_KEY, model_name, full_prompt),
                    timeout=30.0  # Overall timeout - shorter for faster fallback
                )
            
            print("[DEBUG] Gemini call completed successfully")
            
            if response.text:
                print(f"[DEBUG] Gemini response: {len(response.text)} chars")
                return response.text
            else:
                # Try to extract from candidates
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    return part.text
                print("[WARN] Gemini response has no text")
                return None  # Return None to trigger fallback
                
        except asyncio.TimeoutError:
            print(f"[ERROR] Gemini API timeout after 30 seconds - using extractive fallback")
            print(f"[DEBUG] Prompt size: {len(full_prompt)} chars, Context: {len(context)} chars")
            return None
        except Exception as api_error:
            error_type = type(api_error).__name__
            print(f"[ERROR] Gemini API error ({error_type}): {api_error}")
            import traceback
            traceback.print_exc()
            return None  # Return None, don't call extractive here
    
    except Exception as e:
        print(f"[ERROR] Error calling Gemini API: {e}")
        import traceback
        traceback.print_exc()
        return None  # Return None to trigger fallback


def generate_extractive_answer(context: str) -> str:
    """Generate extractive answer from top chunk (fallback)."""
    # Simple extractive approach: use first chunk
    if not context:
        return "I couldn't find relevant information to answer your question."
    
    # Check if TABLE 4 with materials is in context
    if "TABLE 4" in context and "REQUIRED CLASS MATERIALS" in context:
        # Try to extract materials from TABLE 4
        idx = context.find("TABLE 4")
        if idx != -1:
            table_section = context[idx:idx+1000]  # Get TABLE 4 section
            # Look for bullet points with materials
            lines = table_section.split('\n')
            materials = []
            in_table = False
            for line in lines:
                if "TABLE 4" in line:
                    in_table = True
                    continue
                if "[END TABLE]" in line:
                    break
                
                # Check for bullet point (try different characters)
                bullet_chars = ["•", "•", "\u2022", "-", "*"]
                found_bullet = False
                material = ""
                for bullet in bullet_chars:
                    if bullet in line:
                        found_bullet = True
                        material = line.split(bullet, 1)[-1].strip()
                        break
                
                if in_table and found_bullet:
                    if material and material.lower() not in ["required", "class material"]:
                        materials.append(material)
            
            if materials:
                # Return materials as numbered list
                result = "\n".join([f"{i+1}. {m}" for i, m in enumerate(materials)])
                return result
    
    lines = context.split('\n')
    # Take first meaningful chunk (skip source header)
    answer_lines = []
    for line in lines[:5]:  # Take first few lines
        if line.strip() and not line.startswith('['):
            answer_lines.append(line)
    
    if answer_lines:
        answer = ' '.join(answer_lines)
        # Truncate if too long
        if len(answer) > 500:
            answer = answer[:500] + "..."
        return answer
    
    return "I couldn't find a clear answer in the course materials."


def create_sources(retrieved_chunks: List[dict], max_sources: int = None) -> List[Source]:
    """Create source citations from retrieved chunks."""
    if max_sources is None:
        max_sources = MAX_SOURCES
    
    sources = []
    seen_breadcrumbs = set()
    
    for chunk in retrieved_chunks[:max_sources]:
        metadata = chunk.get('metadata', {})
        breadcrumb = metadata.get('breadcrumb', 'Unknown')
        
        # Deduplicate by breadcrumb
        if breadcrumb in seen_breadcrumbs:
            continue
        seen_breadcrumbs.add(breadcrumb)
        
        # Get snippet (first 200 chars of chunk)
        snippet = chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
        
        # Get URL from metadata if available
        url = None
        if 'url' in metadata:
            url = metadata['url']
        
        source = Source(
            breadcrumb=breadcrumb,
            url=url,
            snippet=snippet
        )
        sources.append(source)
        
        if len(sources) >= max_sources:
            break
    
    return sources


def generate_low_confidence_message() -> str:
    """Generate helpful message when confidence is low."""
    return (
        "I couldn't find a clear answer to your question in the course materials. "
        "Try rephrasing your question or searching for specific topics like assignments, "
        "lectures, or course policies."
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Course Compass API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint - shows index status."""
    try:
        from src.config import CHROMA_PATH, COLLECTION_NAME
        retriever = get_retriever()
        return {
            "status": "healthy",
            "chunks": len(retriever.documents),
            "collection": COLLECTION_NAME,
            "chroma_path": str(CHROMA_PATH),
            "embedding_model": "all-MiniLM-L6-v2"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/debug/retrieve")
def debug_retrieve(q: str = Query(..., description="Your query"), k: int = 8):
    """
    Inspect retriever output: scores, breadcrumbs, and small previews.
    Shows what chunks retrieval finds for a query.
    """
    try:
        retriever = get_retriever()
        top_chunks, confidence = retriever.retrieve(q, top_k=k)
        
        items = []
        for i, chunk in enumerate(top_chunks, 1):
            text = chunk['text']
            # Get hybrid_score from chunk dict (it's in the chunk returned by hybrid_search)
            chunk_score = chunk.get('hybrid_score', 0.0)
            items.append({
                "rank": i,
                "score": round(float(chunk_score), 3),
                "breadcrumb": chunk.get('metadata', {}).get('breadcrumb', 'Unknown'),
                "length": len(text),
                "contains_TABLE_4": ("TABLE 4" in text) or ("REQUIRED CLASS MATERIALS" in text),
                "preview": text[:250].replace('\n', ' ')
            })
        
        return {
            "query": q,
            "k": k,
            "confidence": round(float(confidence), 3),
            "hits": len(items),
            "items": items
        }
    except Exception as e:
        import traceback
        return {"error": str(e), "traceback": traceback.format_exc()[:500]}


@app.get("/debug/context")
def debug_context(q: str = Query(...), k: int = 8, cap: int = 15000):
    """
    Shows the exact context that would be sent to Gemini.
    Helps verify TABLE 4 is included before LLM call.
    """
    try:
        retriever = get_retriever()
        top_chunks, confidence = retriever.retrieve(q, top_k=k)
        
        # SAME building logic as /chat (keep in sync!)
        blocks = []
        total = 0
        for i, chunk in enumerate(top_chunks, 1):
            bc = chunk.get('metadata', {}).get('breadcrumb', 'Unknown')
            block = f"[Source {i} - {bc}]\n{chunk['text']}\n"
            if total + len(block) > cap:
                # Try to fit part of chunk if room
                remaining = cap - total
                if remaining > 200:
                    block = f"[Source {i} - {bc}]\n{chunk['text'][:remaining-50]}...\n"
                    blocks.append(block)
                break
            blocks.append(block)
            total += len(block)
        
        ctx = "".join(blocks)
        return {
            "query": q,
            "k": k,
            "cap": cap,
            "context_length": len(ctx),
            "has_TABLE_4": ("TABLE 4" in ctx) or ("REQUIRED CLASS MATERIALS" in ctx),
            "confidence": round(float(confidence), 3),
            "preview": ctx[:1000]  # Preview first 1000 chars
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/debug/gemini")
def debug_gemini():
    """
    Minimal sanity check for Gemini API key/model.
    Proves Gemini works independently of retrieval.
    """
    try:
        if not GEMINI_API_KEY:
            return {"ok": False, "error": "GEMINI_API_KEY missing"}
        
        genai.configure(api_key=GEMINI_API_KEY)
        model_name = GEMINI_MODEL.replace('models/', '') if GEMINI_MODEL.startswith('models/') else GEMINI_MODEL
        model = genai.GenerativeModel(model_name)
        
        # Simple test prompt
        prompt = "Say 'hello' and then list 3 UVA schools."
        resp = model.generate_content(prompt)
        text = getattr(resp, 'text', None)
        
        if not text:
            # Try to get text from candidates
            if hasattr(resp, 'candidates') and resp.candidates:
                for candidate in resp.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                text = part.text
                                break
        
        if not text:
            return {"ok": False, "error": "No text in response", "raw": str(resp)[:200]}
        
        return {"ok": True, "model": model_name, "sample": text[:200]}
    except Exception as e:
        import traceback
        return {"ok": False, "error": str(e), "traceback": traceback.format_exc()[:500]}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Takes a query and returns an answer with citations using RAG.
    """
    try:
        # Get retriever
        retriever = get_retriever()
        
        # 1) Retrieve top-k chunks
        top_chunks, confidence = retriever.retrieve(request.query, top_k=TOP_K)
        confidence = float(confidence) if confidence else 0.0
        
        if not top_chunks:
            return ChatResponse(
                answer="I couldn't find relevant information to answer your question in the course materials.",
                sources=[],
                confidence=0.0
            )
        
        # 2) Build bounded context (same as /debug/context)
        blocks = []
        total = 0
        CAP = MAX_CONTEXT_CHARS
        for i, chunk in enumerate(top_chunks, 1):
            bc = chunk.get('metadata', {}).get('breadcrumb', 'Unknown')
            block = f"[Source {i} - {bc}]\n{chunk['text']}\n"
            if total + len(block) > CAP:
                # Try to fit part of chunk if room
                remaining = CAP - total
                if remaining > 200:
                    block = f"[Source {i} - {bc}]\n{chunk['text'][:remaining-50]}...\n"
                    blocks.append(block)
                break
            blocks.append(block)
            total += len(block)
        
        context = "".join(blocks)
        
        # 3) Guardrails: if retrieval succeeded but context is empty, fail loudly
        if top_chunks and not context:
            print("[ERROR] Retrieval returned chunks but context is empty (formatting bug).")
        
        # Debug: Single line per query with key info
        has_table4 = ("TABLE 4" in context) or ("REQUIRED CLASS MATERIALS" in context)
        print(f"[DEBUG] q='{request.query}' conf={round(confidence,3)} ctx_len={len(context)} has_TABLE_4={has_table4}")
        
        # Hardcoded grading scale and assignment weights (for quick fallback)
        GRADING_SCALE = {
            "A": 93,
            "A-": 90,
            "B+": 87,
            "B": 83,
            "B-": 80,
            "C+": 77,
            "C": 73,
            "C-": 70,
            "D+": 67,
            "D": 63,
            "D-": 60,
            "F": 0  # < 60
        }
        
        GRADED_ACTIVITIES = {
            "Participation / Contribution to Class Learning": 10,
            "In class quizzes": 10,
            "Labs (Lab Quizzes)": 10,
            "Cases": 20,
            "Group Tests": 25,
            "Final Exam": 25
        }
        TOTAL_POINTS = 100
        
        # Check if this is a grading query that can use hardcoded data (skip LLM for speed)
        query_lower = request.query.lower()
        
        # More specific queries first to avoid false matches
        is_grade_threshold_query = any(kw in query_lower for kw in ["what grade", "what is the grading scale", "what is the grade scale", "grading scale", "grade scale", "grade threshold", "counts as", "threshold", "a=", "b=", "c=", "93", "90", "87", "83", "80"])
        
        # Weight/points queries - exclude "late" and "policy" to avoid false matches
        is_weight_query = ("late" not in query_lower and "policy" not in query_lower) and any(kw in query_lower for kw in ["weight", "worth", "how many points", "what is worth", "how many", "exam worth", "worth points", "points is"])
        
        # General grading query (broader)
        is_grading_query = any(kw in query_lower for kw in ["grade", "grading", "a", "b", "c", "d", "f", "percentage", "points", "assignment"])
        
        # Quick hardcoded answers for specific grading queries (skip LLM)
        answer = None
        if is_grade_threshold_query:
            grade_lines = []
            for grade, threshold in GRADING_SCALE.items():
                if grade == "F":
                    grade_lines.append(f"{grade}: < 60%")
                else:
                    grade_lines.append(f"{grade}: {threshold}%")
            answer = "Grading Scale:\n" + "\n".join([f"  {line}" for line in grade_lines])
            print("[DEBUG] Using hardcoded grading scale (skipped LLM)")
        elif is_weight_query:
            activity_lines = []
            for activity, points in GRADED_ACTIVITIES.items():
                percentage = (points / TOTAL_POINTS) * 100
                activity_lines.append(f"  {activity}: {points} points ({percentage:.0f}%)")
            answer = "Graded Activities (Total: 100 points):\n" + "\n".join(activity_lines)
            print("[DEBUG] Using hardcoded assignment weights (skipped LLM)")
        
        # 4) Try LlamaIndex Gemini first (better reliability), fall back to manual Gemini
        sources_from_llm = []
        
        # Try LlamaIndex Gemini first (better timeout/retry handling) - only if we don't have hardcoded answer
        if answer is None and LLAMAINDEX_AVAILABLE:
            try:
                llamaindex_gemini = get_llamaindex_gemini()
                
                # Build prompt same as manual Gemini
                system_prompt = """You are a course assistant for UVA classes.

Rules:
- Answer ONLY using the "Course Materials" context I provide.
- If the answer is not clearly in context, say "I can't find that in the course materials."
- Prefer concise, direct answers (1-5 sentences).
- Include 2-3 citations using the provided breadcrumb for each source you relied on.
- If the user asks for required materials, assignments, due dates, grading, policies, or schedule, extract exact names/dates/numbers from tables/lists.
- Do not invent URLs or content. Do not reveal hidden reasoning steps; provide only the final answer and short justification if needed.
- If no citation is found, state clearly: "No matching source in context."

When asked about materials, textbook, inclusive access, lab access, or required items, 
search the context for sections titled "Materials", "Required", "TABLE 4", "REQUIRED CLASS MATERIALS", 
and return a bullet list with exact titles.

When asked about dates, due dates, exam, quiz, or lab, search context for schedule rows and 
report the nearest date+item pair exactly as written (include time if present).

When asked about policy, late policy, grade, grading scale, participation, or points, 
extract exact numbers/percentages and the section name they come from."""

                user_message = f"""Question: {request.query}

Course Materials:
{context}

Please provide a clear, concise answer based on the course materials above."""

                full_prompt = f"{system_prompt}\n\n{user_message}"
                
                answer = await llamaindex_gemini.generate(full_prompt)
                
                if answer and answer.strip():
                    print(f"[DEBUG] LlamaIndex Gemini answer: {len(answer)} chars")
                else:
                    print("[WARN] LlamaIndex Gemini returned empty text")
                    answer = None
            except Exception as e:
                print(f"[WARN] LlamaIndex Gemini failed, falling back to manual Gemini: {e}")
                # Fall through to manual Gemini
        
        # Fallback: Try manual Gemini if LlamaIndex didn't work or isn't available
        if answer is None:
            try:
                answer = await generate_answer_with_gemini(request.query, context)
                if not answer or not answer.strip():
                    print("[WARN] Gemini returned empty text; will use extractive fallback.")
                    answer = None
            except Exception as e:
                print(f"[ERROR] Gemini exception: {e}")
                import traceback
                traceback.print_exc()
                answer = None
        
        # 5) Fallback: extractive from top chunks (table-aware for materials/grading, general for others)
        if answer is None:
            print("[DEBUG] Using extractive fallback")
            primary = top_chunks[0]['text'] if top_chunks else ""
            
            # Check query type for specialized extraction
            query_lower = request.query.lower()
            is_materials_query = any(kw in query_lower for kw in ["material", "book", "textbook", "required", "lab access", "course pack", "inclusive access"])
            is_grading_query = any(kw in query_lower for kw in ["grade", "grading", "grading scale", "a", "b", "c", "d", "f", "93", "90", "percentage", "threshold", "what grade", "counts as", "assignment", "weight", "points", "worth"])
            
            if is_materials_query and ("REQUIRED CLASS MATERIALS" in primary or "TABLE 4" in primary):
                # Specialized extraction for materials from TABLE 4
                snippet = primary
                if "REQUIRED CLASS MATERIALS" in primary:
                    start = primary.find("REQUIRED CLASS MATERIALS")
                    snippet = primary[start:start+800]
                elif "TABLE 4" in primary:
                    start = primary.find("TABLE 4")
                    snippet = primary[start:start+800]
                
                # Try to extract materials from snippet
                materials = []
                lines = snippet.split('\n')
                in_table = False
                for line in lines:
                    if "TABLE 4" in line or "REQUIRED CLASS MATERIALS" in line:
                        in_table = True
                        continue
                    if "[END TABLE]" in line:
                        break
                    
                    # Check for bullet points (try different characters)
                    bullet_chars = ["•", "•", "\u2022", "-", "*"]
                    found_bullet = False
                    material = ""
                    for bullet in bullet_chars:
                        if bullet in line:
                            found_bullet = True
                            material = line.split(bullet, 1)[-1].strip()
                            break
                    
                    if in_table and found_bullet:
                        if material and material.lower() not in ["required", "class material"]:
                            materials.append(material)
                
                if materials:
                    answer = "\n".join([f"{i+1}. {m}" for i, m in enumerate(materials)])
                else:
                    answer = snippet.strip()[:800] or "I couldn't find relevant information to answer your question."
            
            elif is_grading_query:
                # General grading query - try to extract from document first, then use hardcoded
                snippet = primary
                if "GRADING SCALE" in primary:
                    start = primary.find("GRADING SCALE")
                    snippet = primary[start:start+800]
                elif "Grading Scale" in primary:
                    start = primary.find("Grading Scale")
                    snippet = primary[start:start+800]
                elif "GRADING SCALE:" in primary:
                    start = primary.find("GRADING SCALE:")
                    snippet = primary[start:start+800]
                elif any(x in primary.upper() for x in ["A:", "B:", "C:", "D:", "F:"]):
                    # Search for grade patterns in primary chunk
                    lines = primary.split('\n')
                    snippet_lines = []
                    for line in lines:
                        if any(x in line.upper() for x in ["A:", "B:", "C:", "D:", "F:", "GRADE", "THRESHOLD"]):
                            snippet_lines.append(line)
                    snippet = "\n".join(snippet_lines[:20])
                
                # Try to extract grade: threshold pairs from document
                grades = []
                lines = snippet.split('\n')
                in_grading = False
                for line in lines:
                    line_upper = line.upper()
                    if "GRADING SCALE" in line_upper:
                        in_grading = True
                        continue
                    if "[END TABLE]" in line or "[END GRADING]" in line:
                        break
                    
                    # Look for patterns like "A: 93" or "A | 93" or "A  93"
                    if in_grading or any(x in line_upper for x in ["A:", "B:", "C:", "D:", "F:"]):
                        # Try colon separator
                        if ":" in line:
                            parts = line.split(":", 1)
                            if len(parts) == 2:
                                grade = parts[0].strip()
                                threshold = parts[1].strip()
                                if grade and threshold and any(c.isdigit() for c in threshold):
                                    grades.append(f"{grade}: {threshold}")
                        # Try pipe separator
                        elif "|" in line:
                            parts = line.split("|", 1)
                            if len(parts) == 2:
                                grade = parts[0].strip()
                                threshold = parts[1].strip()
                                if grade and threshold and any(c.isdigit() for c in threshold):
                                    grades.append(f"{grade}: {threshold}")
                
                if grades:
                    answer = "\n".join(grades)
                else:
                    # Fallback to hardcoded grading scale
                    grade_lines = []
                    for grade, threshold in GRADING_SCALE.items():
                        if grade == "F":
                            grade_lines.append(f"{grade}: < 60%")
                        else:
                            grade_lines.append(f"{grade}: {threshold}%")
                    answer = "Grading Scale:\n" + "\n".join([f"  {line}" for line in grade_lines])
                    print("[DEBUG] Using hardcoded grading scale fallback (document extraction failed)")
            
            else:
                # General extractive fallback - extract relevant section based on query keywords
                query_words = set(query_lower.split())
                
                # Find the most relevant section in the primary chunk
                lines = primary.split('\n')
                relevant_lines = []
                section_score = 0
                best_section = []
                best_score = 0
                
                for line in lines:
                    line_lower = line.lower()
                    # Score line based on keyword matches
                    line_score = sum(1 for word in query_words if word in line_lower)
                    
                    # Track best section (consecutive lines with matches)
                    if line_score > 0:
                        relevant_lines.append(line)
                        section_score += line_score
                    else:
                        if section_score > best_score:
                            best_score = section_score
                            best_section = relevant_lines.copy()
                        relevant_lines = []
                        section_score = 0
                
                # Final check
                if section_score > best_score:
                    best_section = relevant_lines
                else:
                    best_section = best_section if best_score > 0 else relevant_lines
                
                if best_section:
                    # Take up to 10 relevant lines, trim to reasonable length
                    answer = "\n".join(best_section[:10]).strip()
                    if len(answer) > 800:
                        answer = answer[:800] + "..."
                else:
                    # Fallback: first meaningful lines from primary chunk
                    answer_lines = []
                    for line in lines[:10]:
                        if line.strip() and not line.startswith('[') and not line.startswith('Source'):
                            answer_lines.append(line)
                    if answer_lines:
                        answer = "\n".join(answer_lines).strip()[:800] or "I couldn't find relevant information to answer your question."
                    else:
                        answer = primary[:800] or "I couldn't find relevant information to answer your question."
        
        # 6) Build sources from chunks
        sources = []
        seen = set()
        for chunk in top_chunks[:MAX_SOURCES]:
            bc = chunk.get('metadata', {}).get('breadcrumb', 'Unknown')
            if bc in seen:
                continue
            seen.add(bc)
            text = chunk['text']
            sources.append(Source(
                breadcrumb=bc,
                url=chunk.get('metadata', {}).get('url'),
                snippet=(text[:200] + "...") if len(text) > 200 else text
            ))
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=confidence
        )
    
    except ValueError as e:
        # Retriever not initialized
        raise HTTPException(
            status_code=503,
            detail=f"Retriever not initialized: {str(e)}. Please run ingest.py and indexer.py first."
        )
    except Exception as e:
        print(f"[ERROR] Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

