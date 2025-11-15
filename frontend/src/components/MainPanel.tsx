import React, {useEffect, useRef, useState} from 'react'
import ChatList from './ChatList'
import InputBar from './InputBar'

type Msg = { id: string; role: 'user'|'ai'; text: string }

export default function MainPanel(){
  const [messages, setMessages] = useState<Msg[]>([
    {id: '1', role: 'ai', text: 'Hello — I can help you with course planning and Q&A.'},
    {id: '2', role: 'user', text: 'Hi! Can you summarize the syllabus?'}
  ])

  const chatRef = useRef<HTMLDivElement|null>(null)

  useEffect(()=>{
    // keep scroll at bottom when messages change
    const el = document.querySelector('.chat-list')
    if(el) el.scrollTop = el.scrollHeight
  },[messages])

  function handleSend(text:string){
    const id = String(Date.now())
    setMessages(prev => [...prev, {id, role:'user', text}])

    // simple mock AI response
    setTimeout(()=>{
      setMessages(prev => [...prev, {id: String(Date.now()+1), role:'ai', text: 'That sounds great — here is a short summary: ...'}])
    },700)
  }

  return (
    <main className="main" role="main">
      <header>
        <div className="logo-box" aria-hidden>CC</div>
        <div>
          <div className="greeting">Welcome back — Course Compass</div>
          <div style={{fontSize:12,color:'var(--muted)'}}>Select a chat or start a new one</div>
        </div>
      </header>

      <ChatList messages={messages} />

      <InputBar onSend={handleSend} />
    </main>
  )
}
