import './App.css'
import Sidebar from './components/Sidebar'
import MainPanel from './components/MainPanel'
import { useEffect, useState } from 'react'
import { sendChatMessage } from './api'

type Msg = { id: string; role: 'user'|'ai'; text: string }
type Chat = { id: string; title: string; folderId?: string; messages: Msg[] }
type Folder = { id: string; name: string }

const STORAGE_KEY = 'course-compass:v1'

function App(){
  const [chats, setChats] = useState<Chat[]>([])
  const [folders, setFolders] = useState<Folder[]>([])
  const [activeChatId, setActiveChatId] = useState<string | null>(null)

  // load from localStorage on mount
  useEffect(()=>{
    try{
      const raw = localStorage.getItem(STORAGE_KEY)
      if(raw){
        const parsed = JSON.parse(raw)
        setChats(parsed.chats || [])
        setFolders(parsed.folders || [])
        setActiveChatId(parsed.activeChatId ?? (parsed.chats && parsed.chats[0]?.id) ?? null)
        return
      }
    }catch(e){
      console.error('load error', e)
    }

    // default initial content when none exists
    const initialChat: Chat = { id: String(Date.now()), title: 'Welcome', messages: [
      { id: 'm1', role: 'ai', text: 'Hello — I can help you with course planning and Q&A.' }
    ]}
    setChats([initialChat])
    setActiveChatId(initialChat.id)
  },[])

  // persist whenever chats/folders/activeChatId change
  useEffect(()=>{
    try{
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ chats, folders, activeChatId }))
    }catch(e){ console.error('save error', e) }
  },[chats, folders, activeChatId])

  function addFolder(name?: string){
    const n = name ?? prompt('Folder name') ?? 'New Folder'
    const folder: Folder = { id: String(Date.now()), name: n }
    setFolders(prev => [...prev, folder])
    return folder
  }

  function addChat(title?: string, folderId?: string){
    const t = title ?? prompt('Chat title') ?? 'New Chat'
    const chat: Chat = { id: String(Date.now()), title: t, folderId, messages: [] }
    setChats(prev => [...prev, chat])
    setActiveChatId(chat.id)
    return chat
  }

  function editChat(id:string, newTitle:string){
    setChats(prev => prev.map(c => c.id === id ? { ...c, title: newTitle } : c))
  }

  function deleteChat(id:string){
    setChats(prev => prev.filter(c => c.id !== id))
    if(activeChatId === id){
      const remaining = chats.filter(c=>c.id !== id)
      setActiveChatId(remaining[0]?.id ?? null)
    }
  }

  function editFolder(id:string, newName:string){
    setFolders(prev => prev.map(f => f.id === id ? { ...f, name: newName } : f))
  }

  function deleteFolder(id:string){
    // remove folder and ungroup chats
    setFolders(prev => prev.filter(f => f.id !== id))
    setChats(prev => prev.map(c => c.folderId === id ? { ...c, folderId: undefined } : c))
  }

  function selectChat(id:string){
    setActiveChatId(id)
  }

  async function addMessageToChat(chatId:string, text:string){
    const userMsg: Msg = { id: String(Date.now()), role: 'user', text }
    setChats(prev => prev.map(c => c.id === chatId ? { ...c, messages: [...c.messages, userMsg] } : c))

    // Show loading indicator
    const loadingMsg: Msg = { id: `loading-${Date.now()}`, role: 'ai', text: '...' }
    setChats(prev => prev.map(c => c.id === chatId ? { ...c, messages: [...c.messages, loadingMsg] } : c))

    try {
      // Call backend API
      const response = await sendChatMessage(text)
      
      // Format answer with sources if available
      let answerText = response.answer
      if (response.sources && response.sources.length > 0) {
        const sourcesList = response.sources.map((s, i) => 
          `\n[Source ${i+1}: ${s.breadcrumb}]`
        ).join('')
        answerText = answerText + sourcesList
      }

      const aiMsg: Msg = { id: String(Date.now()+1), role: 'ai', text: answerText }
      setChats(prev => prev.map(c => 
        c.id === chatId 
          ? { ...c, messages: c.messages.filter(m => m.id !== loadingMsg.id).concat(aiMsg) }
          : c
      ))
    } catch (error) {
      console.error('API error:', error)
      const errorMsg: Msg = { 
        id: String(Date.now()+1), 
        role: 'ai', 
        text: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please make sure the backend is running on ${import.meta.env.VITE_API_URL || 'http://localhost:8000'}.` 
      }
      setChats(prev => prev.map(c => 
        c.id === chatId 
          ? { ...c, messages: c.messages.filter(m => m.id !== loadingMsg.id).concat(errorMsg) }
          : c
      ))
    }
  }

  const activeChat = chats.find(c => c.id === activeChatId) ?? null

  return (
    <div className="app-root">
      <Sidebar
        chats={chats}
        folders={folders}
        activeChatId={activeChatId}
        onSelectChat={selectChat}
        onNewChat={(title, folderId)=> addChat(title, folderId)}
        onNewFolder={(name)=> addFolder(name)}
        onEditChat={(id:string,title:string)=> editChat(id,title)}
        onDeleteChat={(id:string)=> deleteChat(id)}
        onEditFolder={(id:string,name:string)=> editFolder(id,name)}
        onDeleteFolder={(id:string)=> deleteFolder(id)}
      />

      <MainPanel
        chat={activeChat}
        onSend={(text:string)=>{ if(activeChat) addMessageToChat(activeChat.id, text) }}
      />
    </div>
  )
}

export default App
