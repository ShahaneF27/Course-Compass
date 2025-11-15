import React from 'react'

type Props = {
  role: 'user' | 'ai'
  children: React.ReactNode
}

export default function MessageBubble({role, children}: Props){
  return (
    <div className={`bubble ${role}`} role="article" aria-label={`${role} message`}>
      <div>{children}</div>
    </div>
  )
}
