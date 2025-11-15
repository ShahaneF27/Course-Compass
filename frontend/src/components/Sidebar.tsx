import React from 'react'

export default function Sidebar(){
  return (
    <aside className="sidebar" role="navigation" aria-label="Sidebar">
      <div className="actions">
        <button className="btn primary" aria-label="New chat">+ New Chat</button>
        <button className="btn" aria-label="New folder">+ New Folder</button>
      </div>

      <div style={{marginTop:8,fontSize:12,color:'var(--muted)'}}>Chats</div>
      <div className="list" role="list" aria-label="Chat list">
        <div className="list-item" role="listitem">Course Q&A</div>
        <div className="list-item" role="listitem">Study Planner</div>
        <div className="list-item" role="listitem">Draft Notes</div>
      </div>

      <div style={{marginTop:'auto',fontSize:12,color:'var(--muted)'}}>Signed in as <strong style={{color:'var(--text)'}}>You</strong></div>
    </aside>
  )
}
