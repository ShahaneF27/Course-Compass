/**
 * API client for Course Compass backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export type Source = {
  breadcrumb: string
  url?: string
  snippet: string
}

export type ChatResponse = {
  answer: string
  sources: Source[]
  confidence?: number
}

export type ChatRequest = {
  query: string
}

/**
 * Send a chat query to the backend API
 */
export async function sendChatMessage(query: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query } as ChatRequest),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`API error: ${response.status} - ${errorText}`)
  }

  return response.json() as Promise<ChatResponse>
}

/**
 * Check if the backend API is healthy
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`)
    return response.ok
  } catch {
    return false
  }
}

