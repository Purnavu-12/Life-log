"use client"

import { cn } from "@/lib/utils"
import { X, Plus, MessageSquare } from "lucide-react"

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
}

export interface Conversation {
  id: string
  title: string
  preview: string
  date: string
  messages: Message[]
}

interface LatentSidebarProps {
  isOpen: boolean
  onClose: () => void
  conversations: Conversation[]
  activeConversationId: string | null
  onSelectConversation: (conversation: Conversation) => void
  onNewConversation: () => void
}

export function LatentSidebar({ 
  isOpen, 
  onClose, 
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation
}: LatentSidebarProps) {
  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div
        className={cn(
          "fixed right-0 top-0 h-full w-80 z-50",
          "bg-background border-l border-border",
          "transform transition-transform duration-300 ease-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <span className="font-mono text-[10px] tracking-[0.2em] text-muted-foreground uppercase">
            History
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={onNewConversation}
              className="p-1.5 text-muted-foreground hover:text-foreground transition-colors magnetic-hover"
              aria-label="New conversation"
              title="New conversation"
            >
              <Plus className="w-4 h-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-muted-foreground hover:text-foreground transition-colors magnetic-hover"
              aria-label="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        {/* Conversations List */}
        <div className="overflow-y-auto h-[calc(100%-60px)] scrollbar-neural">
          {conversations.length === 0 ? (
            <div className="p-4 text-center">
              <MessageSquare className="w-8 h-8 mx-auto mb-3 text-muted-foreground/30" />
              <p className="text-[12px] text-muted-foreground/50">
                No conversations yet
              </p>
              <p className="text-[11px] text-muted-foreground/30 mt-1">
                Start a new conversation to begin
              </p>
            </div>
          ) : (
            <div className="p-2">
              {conversations.map((conversation) => (
                <button
                  key={conversation.id}
                  onClick={() => {
                    onSelectConversation(conversation)
                    onClose()
                  }}
                  className={cn(
                    "w-full text-left p-4 mb-2 rounded transition-all duration-200",
                    "hover:bg-muted/50",
                    activeConversationId === conversation.id
                      ? "bg-muted border-l-2 border-violet-500/70"
                      : "border-l-2 border-transparent"
                  )}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span className="text-[15px] text-foreground font-medium truncate flex-1">
                      {conversation.title}
                    </span>
                    <span className="text-[11px] text-muted-foreground font-mono shrink-0">
                      {conversation.date}
                    </span>
                  </div>
                  <p className="text-[13px] text-muted-foreground line-clamp-2 leading-relaxed">
                    {conversation.preview}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
