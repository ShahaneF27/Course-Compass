import React, {useState} from 'react'

export default function InputBar({onSend}:{onSend:(text:string)=>void}){
  const [text,setText] = useState('')

  function handleSend(){
    const t = text.trim()
    if(!t) return
    onSend(t)
    setText('')
  }

  function onKey(e:React.KeyboardEvent<HTMLTextAreaElement>){
    if(e.key === 'Enter' && !e.shiftKey){
      e.preventDefault();handleSend()
    }
  }

  return (
    <div className="input-bar" role="region" aria-label="Message input">
      <textarea aria-label="Message" placeholder="Type a message..." value={text} onChange={e=>setText(e.target.value)} onKeyDown={onKey}></textarea>
      <button className="send" onClick={handleSend} aria-label="Send message">Send</button>
    </div>
  )
}
