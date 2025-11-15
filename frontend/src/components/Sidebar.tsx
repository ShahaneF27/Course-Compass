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
  onNewFolder,
  onEditChat,
  onDeleteChat,
  onEditFolder,
  onDeleteFolder
}:{
  chats: Chat[]
  folders: Folder[]
  activeChatId: string | null
  onSelectChat:(id:string)=>void
  onNewChat:(title?:string, folderId?:string)=>void
  onNewFolder:(name?:string)=>void
  onEditChat?:(id:string, title:string)=>void
  onDeleteChat?:(id:string)=>void
  onEditFolder?:(id:string, name:string)=>void
  onDeleteFolder?:(id:string)=>void
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

      <div className="list" role="list" aria-label="Chat list">
        {folders.map(folder=> (
          <div key={folder.id} style={{marginBottom:16}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'12px 8px',fontWeight:700,fontSize:'14px',color:'var(--text)',borderBottom:'1px solid rgba(255,255,255,0.08)'}}>
              <div>{folder.name}</div>
              <div style={{display:'flex',gap:6}}>
                {onEditFolder && <button className="icon-btn" aria-label={`Edit folder ${folder.name}`} onClick={()=>{
                  const nv = prompt('Folder name', folder.name)
                  if(nv) onEditFolder(folder.id, nv)
                }}>✎</button>}
                {onDeleteFolder && <button className="icon-btn" aria-label={`Delete folder ${folder.name}`} onClick={()=>{
                  if(confirm('Delete folder? Chats will be ungrouped.')) onDeleteFolder(folder.id)
                }}>🗑</button>}
              </div>
            </div>
            {chats.filter(c=>c.folderId===folder.id).map(c=> (
              <div key={c.id} role="listitem" className={`list-item chat-under-folder ${c.id===activeChatId? 'active':''}`}>
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                  <div style={{flex:1,cursor:'pointer',fontSize:'13px',paddingLeft:'12px'}} onClick={()=>onSelectChat(c.id)}>{c.title}</div>
                  <div style={{display:'flex',gap:6}}>
                    {onEditChat && <button className="icon-btn" aria-label={`Edit chat ${c.title}`} onClick={()=>{
                      const nv = prompt('Chat title', c.title)
                      if(nv) onEditChat(c.id, nv)
                    }}>✎</button>}
                    {onDeleteChat && <button className="icon-btn" aria-label={`Delete chat ${c.title}`} onClick={()=>{
                      if(confirm('Delete chat?')) onDeleteChat(c.id)
                    }}>🗑</button>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}

        {ungrouped.length > 0 && (
          <div style={{marginBottom:16}}>
            <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'12px 8px',fontWeight:700,fontSize:'14px',color:'var(--text)',borderBottom:'1px solid rgba(255,255,255,0.08)'}}>
              <div>General</div>
            </div>
            {ungrouped.map(c=> (
              <div key={c.id} role="listitem" className={`list-item ${c.id===activeChatId? 'active':''}`}> 
                <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                  <div style={{flex:1,cursor:'pointer'}} onClick={()=>onSelectChat(c.id)}>{c.title}</div>
                  <div style={{display:'flex',gap:6}}>
                    {onEditChat && <button className="icon-btn" aria-label={`Edit chat ${c.title}`} onClick={()=>{
                      const nv = prompt('Chat title', c.title)
                      if(nv) onEditChat(c.id, nv)
                    }}>✎</button>}
                    {onDeleteChat && <button className="icon-btn" aria-label={`Delete chat ${c.title}`} onClick={()=>{
                      if(confirm('Delete chat?')) onDeleteChat(c.id)
                    }}>🗑</button>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{marginTop:'auto',fontSize:12,color:'var(--muted)'}}>Signed in as <strong style={{color:'var(--text)'}}>You</strong></div>
    </aside>
  )
}
