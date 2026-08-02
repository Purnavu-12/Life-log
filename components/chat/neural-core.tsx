"use client"

import { useState, useCallback } from "react"
import { ConversationStream, Message } from "./conversation-stream"
import { CommandDock } from "./command-dock"
import { LatentSidebar, Conversation } from "./latent-sidebar"
import { Layers, Moon, Sun } from "lucide-react"
import { useTheme } from "@/components/theme-provider"
import { api } from "@/lib/api"
import { useAuth } from "@/context/AuthContext"

// Initial conversation for new users
const initialConversation: Conversation = {
  id: "conv-welcome",
  title: "Welcome to Neural Core",
  preview: "Ask me about your memories, assignments, deadlines...",
  date: "Today",
  messages: [
    {
      id: "welcome-1",
      role: "assistant",
      content: "Hello! I'm your LifeLog AI assistant. Ask me anything about your memories, assignments, deadlines, or any information you've captured. I'll search your audio recordings and provide answers based on what you've recorded.",
      timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })
    }
  ]
}

export function NeuralCore() {
  const { theme, toggleTheme } = useTheme()
  const { user, isAuthenticated } = useAuth()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>(initialConversation.messages)
  const [inputValue, setInputValue] = useState("")
  const [isThinking, setIsThinking] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  
  const generateTimestamp = () => {
    const now = new Date()
    return now.toLocaleTimeString("en-US", { 
      hour: "2-digit", 
      minute: "2-digit",
      hour12: false 
    })
  }
  
  const handleSelectConversation = useCallback((conversation: Conversation) => {
    setActiveConversation(conversation)
    setMessages(conversation.messages)
  }, [])
  
  const handleNewConversation = useCallback(() => {
    setActiveConversation(null)
    setMessages(initialConversation.messages)
    setSidebarOpen(false)
  }, [])
  
  const handleSubmit = useCallback(async () => {
    if (!inputValue.trim() || isThinking) return
    
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: inputValue.trim(),
      timestamp: generateTimestamp()
    }
    
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInputValue("")
    setIsThinking(true)
    
    try {
      // Search memories with the user's query
      const response = await api.searchMemories(inputValue.trim(), 0.5)
      
      let assistantContent = 'I couldn\'t find any relevant information in your memories.'
      
      if (response.results && response.results.length > 0) {
        const bestResult = response.results[0]
        const queryLower = inputValue.toLowerCase()
        const contentLower = bestResult.content.toLowerCase()
        
        // Try to extract direct answers for common questions
        if (queryLower.includes('when') && queryLower.includes('assignment') && queryLower.includes('due')) {
          const dateMatch = bestResult.content.match(/(\d{1,2}(?:st|nd|rd|th)?|January|February|March|April|May|June|July|August|September|October|November|December|\d{1,2}\/\d{1,2}\/\d{4})/i)
          if (dateMatch) {
            assistantContent = `The assignment is due on **${dateMatch[0]}**.`
          }
        } else if (queryLower.includes('how many') && queryLower.includes('pages')) {
          const pageMatch = bestResult.content.match(/(\d+)\s*(?:pages?|page)/i)
          if (pageMatch) {
            assistantContent = `The assignment requires **${pageMatch[1]} pages**.`
          }
        } else if (queryLower.includes('assignment') && (queryLower.includes('due') || queryLower.includes('submission'))) {
          const dateMatch = bestResult.content.match(/(\d{1,2}(?:st|nd|rd|th)?|\d{1,2}\/\d{1,2})/i)
          const pageMatch = bestResult.content.match(/(\d+)\s*(?:pages?|page)/i)
          
          if (dateMatch && pageMatch) {
            assistantContent = `The assignment is due on **${dateMatch[0]}** and requires **${pageMatch[1]} pages**.`
          } else if (dateMatch) {
            assistantContent = `The assignment is due on **${dateMatch[0]}**.`
          } else if (pageMatch) {
            assistantContent = `The assignment requires **${pageMatch[1]} pages**.`
          }
        }
        
        // If no specific extraction, use the memory content with summary
        if (assistantContent === 'I couldn\'t find any relevant information in your memories.') {
          const summary = bestResult.summary || ''
          const contentPreview = bestResult.content.length > 300 
            ? bestResult.content.substring(0, 300) + '...' 
            : bestResult.content
          
          assistantContent = `Based on your memory:\n\n**${summary || 'Relevant memory found:'}**\n\n${contentPreview}`
        }
        
        // Add contextual information
        if (bestResult.tags && bestResult.tags.length > 0) {
          assistantContent += `\n\n**Tags:** ${bestResult.tags.join(', ')}`
        }
        if (bestResult.date) {
          assistantContent += `\n**Date:** ${bestResult.date}`
        }
      }
      
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: assistantContent,
        timestamp: generateTimestamp()
      }
      
      const updatedMessages = [...newMessages, assistantMessage]
      setMessages(updatedMessages)
      setIsThinking(false)
      
      // Update or create conversation in history
      if (activeConversation) {
        setConversations(prev => prev.map(conv => 
          conv.id === activeConversation.id 
            ? { ...conv, messages: updatedMessages, preview: userMessage.content }
            : conv
        ))
        setActiveConversation(prev => prev ? { ...prev, messages: updatedMessages } : null)
      } else {
        const newConversation: Conversation = {
          id: `conv-${Date.now()}`,
          title: userMessage.content.slice(0, 40) + (userMessage.content.length > 40 ? "..." : ""),
          preview: assistantContent.slice(0, 80) + "...",
          date: "Today",
          messages: updatedMessages
        }
        setConversations(prev => [newConversation, ...prev])
        setActiveConversation(newConversation)
      }
      
    } catch (error) {
      const errorMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: 'Sorry, I encountered an error while searching your memories. Please try again.',
        timestamp: generateTimestamp()
      }
      setMessages(prev => [...prev, errorMessage])
      setIsThinking(false)
    }
  }, [inputValue, isThinking, messages, activeConversation])
  
  return (
    <div className="h-screen flex flex-col bg-background relative overflow-hidden">
      {/* Noise overlay */}
      <div className="noise-overlay" aria-hidden="true" />
      
      {/* Header */}
      <header className="flex items-center justify-between px-6 md:px-16 lg:px-24 py-4 border-b border-border">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[11px] tracking-[0.2em] text-foreground uppercase">
            Neural_Core
          </span>
          <span className="font-mono text-[9px] text-muted-foreground/50">
            //
          </span>
          <span className="font-mono text-[9px] text-muted-foreground/50 uppercase truncate max-w-[200px]">
            {activeConversation ? activeConversation.title : "New Conversation"}
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="flex items-center justify-center w-8 h-8 text-muted-foreground hover:text-foreground transition-colors magnetic-hover"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? (
              <Sun className="w-4 h-4" />
            ) : (
              <Moon className="w-4 h-4" />
            )}
          </button>
          
          {/* History button */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 text-muted-foreground hover:text-foreground transition-colors magnetic-hover"
            aria-label="Open history sidebar"
          >
            <Layers className="w-4 h-4" />
            <span className="font-mono text-[10px] tracking-wider uppercase hidden sm:inline">
              History
            </span>
            {conversations.length > 0 && (
              <span className="ml-1 px-1.5 py-0.5 bg-violet-500/20 text-violet-400 font-mono text-[9px]">
                {conversations.length}
              </span>
            )}
          </button>
        </div>
      </header>
      
      {/* Main content */}
      <ConversationStream 
        messages={messages} 
        isThinking={isThinking} 
      />
      
      {/* Command dock */}
      <CommandDock
        value={inputValue}
        onChange={setInputValue}
        onSubmit={handleSubmit}
        isThinking={isThinking}
        disabled={isThinking}
      />
      
      {/* History sidebar */}
      <LatentSidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        conversations={conversations}
        activeConversationId={activeConversation?.id ?? null}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />
    </div>
  )
}
