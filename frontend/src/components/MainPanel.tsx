import React, {useEffect} from 'react'
import ChatList from './ChatList'
import InputBar from './InputBar'

type Msg = { id: string; role: 'user'|'ai'; text: string }
type Chat = { id: string; title: string; folderId?: string; messages: Msg[] }

export default function MainPanel({chat, onSend}:{chat: Chat | null, onSend:(text:string)=>void}){
  useEffect(()=>{
    const el = document.querySelector('.chat-list')
    if(el) el.scrollTop = el.scrollHeight
  },[chat?.messages?.length])

  if(!chat) return (
    <main className="main" role="main">
      <header>
        <div className="logo-box" aria-hidden>CC</div>
        <div>
          <div className="greeting">Welcome back — Course Compass</div>
          <div style={{fontSize:12,color:'var(--muted)'}}>Select a chat or start a new one</div>
        </div>
      </header>
      <div style={{flex:1,display:'flex',alignItems:'center',justifyContent:'center',color:'var(--muted)'}}>
        No chat selected
      </div>
    </main>
  )

  return (
    <main className="main" role="main">
      <header>
        <div className="logo-box" aria-hidden>CC</div>
        <div>
          <div className="greeting">{chat.title}</div>
          <div style={{fontSize:12,color:'var(--muted)'}}>{chat.messages.length} messages</div>
        </div>
      </header>

      <ChatList messages={chat.messages} />

      <InputBar onSend={onSend} />
    </main>
  )
}
