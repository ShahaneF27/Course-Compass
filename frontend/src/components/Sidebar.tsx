import React, {useState, useRef, useEffect} from 'react'

type Msg = { id: string; role: 'user'|'ai'; text: string }
type Chat = { id: string; title: string; folderId?: string; messages: Msg[] }
type Folder = { id: string; name: string }

export default function Sidebar({
  chats,
  folders,
  activeChatId,
  onSelectChat,
  onNewChat,
  onNewFolder
}:{
  chats: Chat[]
  folders: Folder[]
  activeChatId: string | null
  onSelectChat:(id:string)=>void
  onNewChat:(title?:string, folderId?:string)=>void
  onNewFolder:(name?:string)=>void
}){
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [selectedFolder, setSelectedFolder] = useState<string>('')
  const inputRef = useRef<HTMLInputElement|null>(null)

  useEffect(()=>{
    if(showForm && inputRef.current){
      inputRef.current.focus()
    }
  },[showForm])

  function openForm(){
    setTitle('')
    setSelectedFolder('')
    setShowForm(true)
  }

  function handleCreate(e?:React.FormEvent){
    e?.preventDefault()
    if(!title.trim()) return
    const folderId = selectedFolder || undefined
    onNewChat(title.trim(), folderId)
    setShowForm(false)
  }

  function handleCancel(){
    setShowForm(false)
  }

  function handleNewFolder(){
    const name = prompt('Folder name') || undefined
    if(name) onNewFolder(name)
  }

  const ungrouped = chats.filter(c=>!c.folderId)

  return (
    <aside className="sidebar" role="navigation" aria-label="Sidebar">
      <div className="actions">
        {!showForm ? (
          <>
            <button className="btn primary" aria-label="New chat" onClick={openForm}>+ New Chat</button>
            <button className="btn" aria-label="New folder" onClick={handleNewFolder}>+ New Folder</button>
          </>
        ) : (
          <form className="new-chat-form" onSubmit={handleCreate}>
            <input ref={inputRef} className="new-chat-input" aria-label="Chat title" placeholder="Chat title" value={title} onChange={e=>setTitle(e.target.value)} />
            <select className="new-chat-select" aria-label="Folder" value={selectedFolder} onChange={e=>setSelectedFolder(e.target.value)}>
              <option value="">No folder</option>
              {folders.map(f=> <option key={f.id} value={f.id}>{f.name}</option>)}
            </select>
            <div className="form-actions">
              <button type="submit" className="btn primary">Create</button>
              <button type="button" className="btn" onClick={handleCancel}>Cancel</button>
            </div>
          </form>
        )}
      </div>

      <div style={{marginTop:8,fontSize:12,color:'var(--muted)'}}>Chats</div>
      <div className="list" role="list" aria-label="Chat list">
        {folders.map(folder=> (
          <div key={folder.id} style={{marginBottom:8}}>
            <div style={{fontSize:12,color:'var(--muted)',padding:'6px 8px'}}>{folder.name}</div>
            {chats.filter(c=>c.folderId===folder.id).map(c=> (
              <div key={c.id} role="listitem" className={`list-item ${c.id===activeChatId? 'active':''}`} onClick={()=>onSelectChat(c.id)}>{c.title}</div>
            ))}
          </div>
        ))}

        {ungrouped.map(c=> (
          <div key={c.id} role="listitem" className={`list-item ${c.id===activeChatId? 'active':''}`} onClick={()=>onSelectChat(c.id)}>{c.title}</div>
        ))}
      </div>

      <div style={{marginTop:'auto',fontSize:12,color:'var(--muted)'}}>Signed in as <strong style={{color:'var(--text)'}}>You</strong></div>
    </aside>
  )
}
