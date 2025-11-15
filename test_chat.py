"""Quick test script for Course Compass API."""
import requests
import json

API_URL = "http://localhost:8000"

def test_chat(query: str):
    """Test the /chat endpoint."""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"query": query},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Answer:")
            print(f"{data['answer']}\n")
            
            print(f"Sources ({len(data['sources'])}):")
            for i, source in enumerate(data['sources'], 1):
                print(f"\n  {i}. {source['breadcrumb']}")
                if source.get('url'):
                    print(f"     URL: {source['url']}")
                print(f"     Snippet: {source['snippet'][:150]}...")
            
            if data.get('confidence'):
                print(f"\nConfidence: {data['confidence']:.2f}")
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to API.")
        print("Make sure the server is running: uvicorn backend.app:app --reload --port 8000")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("Course Compass - Terminal Test")
    print("="*60)
    print("Make sure the API server is running first!")
    print("Run: uvicorn backend.app:app --reload --port 8000")
    print("="*60)
    
    # Test queries
    test_queries = [
        "What is this course about?",
        "What is the course schedule?",
        "Where can I find the syllabus?",
        "What are the course requirements?",
    ]
    
    for query in test_queries:
        test_chat(query)
        input("\nPress Enter to test next query (or Ctrl+C to exit)...")

