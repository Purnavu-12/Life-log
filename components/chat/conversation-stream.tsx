"use client"

import { useEffect, useRef } from "react"
import { StreamMessage } from "./stream-message"
import { NeuralMonitor } from "./neural-monitor"

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp?: string
}

interface ConversationStreamProps {
  messages: Message[]
  isThinking?: boolean
}

export function ConversationStream({ messages, isThinking = false }: ConversationStreamProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isThinking])
  
  const isEmpty = messages.length === 0
  
  return (
    <div className="flex-1 overflow-y-auto scrollbar-neural px-6 md:px-16 lg:px-24">
      {/* Neural Monitor - Always visible at top */}
      <NeuralMonitor isThinking={isThinking} />
      
      {isEmpty ? (
        <div className="flex flex-col items-center justify-center py-16 stagger-children">
          <p className="font-serif text-2xl text-foreground/80 mb-2">
            Welcome to the Neural Core
          </p>
          <p className="text-sm text-muted-foreground max-w-md text-center leading-relaxed">
            A new kind of intelligence, ready to assist. Begin your discourse below.
          </p>
        </div>
      ) : (
        <div className="space-y-10 pb-8">
          {messages.map((message) => (
            <StreamMessage
              key={message.id}
              role={message.role}
              content={message.content}
              timestamp={message.timestamp}
            />
          ))}
          
          {/* Thinking indicator */}
          {isThinking && (
            <div className="animate-drift-up">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-mono text-[10px] tracking-[0.15em] text-muted-foreground uppercase">
                  NEURAL_CORE
                </span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                <span className="w-1.5 h-1.5 rounded-full bg-primary/80 animate-pulse" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          )}
        </div>
      )}
      
      <div ref={bottomRef} />
    </div>
  )
}
