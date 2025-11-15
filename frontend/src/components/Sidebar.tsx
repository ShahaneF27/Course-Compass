import React from 'react'

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
  function handleNewChat(){
    const title = prompt('Chat title') || undefined
    onNewChat(title)
  }

  function handleNewFolder(){
    const name = prompt('Folder name') || undefined
    if(name) onNewFolder(name)
  }

  const ungrouped = chats.filter(c=>!c.folderId)

  return (
    <aside className="sidebar" role="navigation" aria-label="Sidebar">
      <div className="actions">
        <button className="btn primary" aria-label="New chat" onClick={handleNewChat}>+ New Chat</button>
        <button className="btn" aria-label="New folder" onClick={handleNewFolder}>+ New Folder</button>
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
