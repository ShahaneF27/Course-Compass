import React from 'react'
import MessageBubble from './MessageBubble'

type Msg = { id: string; role: 'user'|'ai'; text: string }

export default function ChatList({messages}:{messages:Msg[]}){
  return (
    <div className="chat-list" role="log" aria-live="polite">
      {messages.map(m=> (
        <div key={m.id}>
          <MessageBubble role={m.role}>{m.text}</MessageBubble>
        </div>
      ))}
    </div>
  )
}
