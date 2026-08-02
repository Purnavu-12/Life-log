"use client"

import { useState, useCallback } from "react"
import { ConversationStream, Message } from "./conversation-stream"
import { CommandDock } from "./command-dock"
import { LatentSidebar, Conversation } from "./latent-sidebar"
import { Layers, Moon, Sun } from "lucide-react"
import { useTheme } from "@/components/theme-provider"

// Mock conversations for history
const mockConversations: Conversation[] = [
  {
    id: "conv-1",
    title: "Neural Network Architecture",
    preview: "Discussion about building scalable AI interfaces with modular patterns...",
    date: "Today",
    messages: [
      {
        id: "conv1-user-1",
        role: "user",
        content: "How should I structure a neural network for image classification?",
        timestamp: "14:23"
      },
      {
        id: "conv1-ai-1",
        role: "assistant",
        content: "## Neural Network Architecture for Image Classification\n\nWhen building an image classification network, consider these layers:\n\n- **Convolutional layers** for feature extraction\n- **Pooling layers** for dimensionality reduction\n- **Dense layers** for final classification\n\n```typescript\nconst model = sequential([\n  conv2d({ filters: 32, kernelSize: 3 }),\n  maxPooling2d({ poolSize: 2 }),\n  flatten(),\n  dense({ units: 128, activation: 'relu' }),\n  dense({ units: numClasses, activation: 'softmax' })\n]);\n```\n\nThis architecture balances accuracy and computational efficiency.",
        timestamp: "14:24"
      },
      {
        id: "conv1-user-2",
        role: "user",
        content: "What about transfer learning?",
        timestamp: "14:26"
      },
      {
        id: "conv1-ai-2",
        role: "assistant",
        content: "## Transfer Learning Approach\n\nTransfer learning allows you to leverage pre-trained models:\n\n- Use models like ResNet, VGG, or EfficientNet as a base\n- Freeze early layers to preserve learned features\n- Fine-tune later layers for your specific task\n\nThis significantly reduces training time and data requirements while often achieving better results than training from scratch.",
        timestamp: "14:27"
      }
    ]
  },
  {
    id: "conv-2",
    title: "State Management Patterns",
    preview: "Exploring reactive patterns and signal-based state handling...",
    date: "Yesterday",
    messages: [
      {
        id: "conv2-user-1",
        role: "user",
        content: "What's the best approach for state management in a React app?",
        timestamp: "09:15"
      },
      {
        id: "conv2-ai-1",
        role: "assistant",
        content: "## Modern State Management\n\nThe landscape has evolved significantly. Here are current best practices:\n\n- **Local state**: useState for component-specific data\n- **Shared state**: Context API or Zustand for app-wide state\n- **Server state**: React Query or SWR for API data\n- **URL state**: Router params for shareable state\n\nChoose based on your specific needs rather than adopting one solution for everything.",
        timestamp: "09:16"
      }
    ]
  },
  {
    id: "conv-3",
    title: "API Design Best Practices",
    preview: "RESTful conventions and GraphQL considerations for scalable APIs...",
    date: "Jan 15",
    messages: [
      {
        id: "conv3-user-1",
        role: "user",
        content: "Should I use REST or GraphQL for my new project?",
        timestamp: "16:42"
      },
      {
        id: "conv3-ai-1",
        role: "assistant",
        content: "## REST vs GraphQL\n\nBoth have their place. Consider these factors:\n\n**REST is better when:**\n- You have simple, well-defined resources\n- Caching is critical\n- Team is familiar with REST patterns\n\n**GraphQL excels when:**\n- Clients need flexible data fetching\n- You have complex, nested relationships\n- Multiple clients need different data shapes\n\nFor most projects, REST remains the simpler choice with proven patterns.",
        timestamp: "16:43"
      }
    ]
  },
  {
    id: "conv-4",
    title: "Performance Optimization",
    preview: "Strategies for improving web application performance metrics...",
    date: "Jan 12",
    messages: [
      {
        id: "conv4-user-1",
        role: "user",
        content: "My React app is slow. How can I optimize it?",
        timestamp: "11:30"
      },
      {
        id: "conv4-ai-1",
        role: "assistant",
        content: "## React Performance Optimization\n\nStart by identifying bottlenecks with React DevTools Profiler. Common optimizations:\n\n- **Memoization**: Use React.memo, useMemo, useCallback strategically\n- **Code splitting**: Lazy load routes and heavy components\n- **Virtualization**: Use react-window for long lists\n- **Bundle analysis**: Identify and remove unused dependencies\n\nRemember: measure first, optimize second. Premature optimization is the root of all evil.",
        timestamp: "11:31"
      }
    ]
  },
  {
    id: "conv-5",
    title: "TypeScript Generics",
    preview: "Deep dive into advanced TypeScript patterns and type inference...",
    date: "Jan 10",
    messages: [
      {
        id: "conv5-user-1",
        role: "user",
        content: "Can you explain TypeScript generics with practical examples?",
        timestamp: "20:15"
      },
      {
        id: "conv5-ai-1",
        role: "assistant",
        content: "## TypeScript Generics Explained\n\nGenerics enable reusable, type-safe code:\n\n```typescript\n// Generic function\nfunction identity<T>(arg: T): T {\n  return arg;\n}\n\n// Generic interface\ninterface Repository<T> {\n  find(id: string): Promise<T>;\n  save(item: T): Promise<void>;\n}\n\n// Generic constraint\nfunction getProperty<T, K extends keyof T>(obj: T, key: K) {\n  return obj[key];\n}\n```\n\nGenerics shine when building libraries, utilities, and data structures that work with multiple types.",
        timestamp: "20:17"
      }
    ]
  }
]

// Mock AI responses for new messages
const mockResponses = [
  "## Understanding Your Request\n\nI've analyzed your query and identified the key components. Here's my interpretation:\n\n- The core intent appears to be exploratory\n- Context suggests a need for detailed explanation\n- I'll provide structured, actionable insights\n\nLet me elaborate on the specifics below.",

  "The architecture you're describing follows a modular pattern. Each component operates independently while maintaining coherent state through a centralized store.\n\n## Key Considerations\n\n- Separation of concerns is paramount\n- Event-driven communication reduces coupling\n- Type safety ensures reliability at scale\n\nThis approach scales elegantly as complexity grows.",

  "## Code Implementation\n\nHere's how you might structure this:\n\n```typescript\ninterface NeuralConfig {\n  threshold: number;\n  layers: number;\n  activation: 'relu' | 'sigmoid' | 'tanh';\n}\n\nconst initializeCore = (config: NeuralConfig) => {\n  return new NeuralProcessor(config);\n};\n```\n\nThe implementation prioritizes clarity and extensibility.",

  "I see what you're working toward. The solution involves three interconnected layers:\n\n- Input processing and validation\n- Core transformation logic\n- Output formatting and delivery\n\nEach layer can be optimized independently while preserving the overall data flow integrity."
]

export function NeuralCore() {
  const { theme, toggleTheme } = useTheme()
  const [conversations, setConversations] = useState<Conversation[]>(mockConversations)
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
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
    setMessages([])
    setSidebarOpen(false)
  }, [])
  
  const handleSubmit = useCallback(() => {
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
    
    // Simulate AI response
    const delay = 1500 + Math.random() * 1500
    setTimeout(() => {
      const responseIndex = Math.floor(Math.random() * mockResponses.length)
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: mockResponses[responseIndex],
        timestamp: generateTimestamp()
      }
      
      const updatedMessages = [...newMessages, assistantMessage]
      setMessages(updatedMessages)
      setIsThinking(false)
      
      // Update or create conversation in history
      if (activeConversation) {
        // Update existing conversation
        setConversations(prev => prev.map(conv => 
          conv.id === activeConversation.id 
            ? { ...conv, messages: updatedMessages, preview: userMessage.content }
            : conv
        ))
        setActiveConversation(prev => prev ? { ...prev, messages: updatedMessages } : null)
      } else {
        // Create new conversation
        const newConversation: Conversation = {
          id: `conv-${Date.now()}`,
          title: userMessage.content.slice(0, 40) + (userMessage.content.length > 40 ? "..." : ""),
          preview: assistantMessage.content.slice(0, 80) + "...",
          date: "Today",
          messages: updatedMessages
        }
        setConversations(prev => [newConversation, ...prev])
        setActiveConversation(newConversation)
      }
    }, delay)
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
