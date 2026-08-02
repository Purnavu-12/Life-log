"use client"

import { cn } from "@/lib/utils"
import { Check, Copy, Download, Share2 } from "lucide-react"
import { useState } from "react"
import { JSX } from "react/jsx-runtime" // Import JSX

interface StreamMessageProps {
  role: "user" | "assistant"
  content: string
  timestamp?: string
}

export function StreamMessage({ role, content, timestamp }: StreamMessageProps) {
  const [copied, setCopied] = useState(false)
  const [shared, setShared] = useState(false)
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  const handleDownload = () => {
    const blob = new Blob([content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `neural-core-response-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: "Neural Core Response",
          text: content,
        })
      } catch (err) {
        // User cancelled or share failed, fallback to copy
        await handleCopy()
      }
    } else {
      // Fallback: copy link/content to clipboard
      await navigator.clipboard.writeText(content)
      setShared(true)
      setTimeout(() => setShared(false), 2000)
    }
  }
  
  const isUser = role === "user"
  
  // Parse inline markdown (bold, italic, inline code)
  const parseInlineMarkdown = (text: string) => {
    const parts: (string | JSX.Element)[] = []
    let remaining = text
    let keyIndex = 0
    
    while (remaining.length > 0) {
      // Check for inline code first (highest priority)
      const inlineCodeMatch = remaining.match(/^`([^`]+)`/)
      if (inlineCodeMatch) {
        parts.push(
          <code key={keyIndex++} className="px-1.5 py-0.5 bg-muted text-accent text-[13px] font-mono rounded">
            {inlineCodeMatch[1]}
          </code>
        )
        remaining = remaining.slice(inlineCodeMatch[0].length)
        continue
      }
      
      // Check for bold (**text**)
      const boldMatch = remaining.match(/^\*\*([^*]+)\*\*/)
      if (boldMatch) {
        parts.push(
          <strong key={keyIndex++} className="font-semibold text-foreground">
            {boldMatch[1]}
          </strong>
        )
        remaining = remaining.slice(boldMatch[0].length)
        continue
      }
      
      // Check for italic (*text*)
      const italicMatch = remaining.match(/^\*([^*]+)\*/)
      if (italicMatch) {
        parts.push(
          <em key={keyIndex++} className="italic text-foreground/80">
            {italicMatch[1]}
          </em>
        )
        remaining = remaining.slice(italicMatch[0].length)
        continue
      }
      
      // Find next special character or add plain text
      const nextSpecial = remaining.search(/[`*]/)
      if (nextSpecial === -1) {
        parts.push(remaining)
        break
      } else if (nextSpecial === 0) {
        // Special char that didn't match patterns, treat as plain text
        parts.push(remaining[0])
        remaining = remaining.slice(1)
      } else {
        parts.push(remaining.slice(0, nextSpecial))
        remaining = remaining.slice(nextSpecial)
      }
    }
    
    return parts
  }
  
  // Simple markdown-like rendering for AI responses
  const renderContent = () => {
    if (isUser) {
      return <p className="text-[15px] leading-relaxed">{content}</p>
    }
    
    // Split content by code blocks and render
    const parts = content.split(/(```[\s\S]*?```)/g)
    
    return parts.map((part, index) => {
      if (part.startsWith("```")) {
        const codeContent = part.replace(/```\w*\n?/g, "").replace(/```$/, "")
        return (
          <div key={index} className="my-4 relative group">
            <pre className="code-block p-4 overflow-x-auto">
              <code className="text-[13px] text-muted-foreground">{codeContent}</code>
            </pre>
            <button
              onClick={handleCopy}
              className={cn(
                "absolute top-2 right-2 p-1.5 opacity-0 group-hover:opacity-100",
                "transition-all magnetic-hover",
                "text-muted-foreground hover:text-foreground"
              )}
              aria-label="Copy code"
            >
              {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        )
      }
      
      // Check for headers (## Header)
      const lines = part.split("\n")
      return lines.map((line, lineIndex) => {
        if (line.startsWith("## ")) {
          return (
            <h2 key={`${index}-${lineIndex}`} className="font-serif text-xl font-medium mt-6 mb-3 text-foreground">
              {parseInlineMarkdown(line.replace("## ", ""))}
            </h2>
          )
        }
        if (line.startsWith("# ")) {
          return (
            <h1 key={`${index}-${lineIndex}`} className="font-serif text-2xl font-medium mt-6 mb-3 text-foreground">
              {parseInlineMarkdown(line.replace("# ", ""))}
            </h1>
          )
        }
        if (line.startsWith("- ")) {
          return (
            <li key={`${index}-${lineIndex}`} className="text-[15px] leading-relaxed ml-4 text-foreground/90">
              {parseInlineMarkdown(line.replace("- ", ""))}
            </li>
          )
        }
        if (line.trim() === "") {
          return <div key={`${index}-${lineIndex}`} className="h-3" />
        }
        return (
          <p key={`${index}-${lineIndex}`} className="text-[15px] leading-relaxed text-foreground/90">
            {parseInlineMarkdown(line)}
          </p>
        )
      })
    })
  }
  
  return (
    <div
      className={cn(
        "animate-drift-up",
        isUser ? "flex flex-col items-end" : "flex flex-col items-start"
      )}
    >
      {/* Tag */}
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[10px] tracking-[0.15em] text-muted-foreground uppercase">
          {isUser ? "USER_01" : "NEURAL_CORE"}
        </span>
        {timestamp && (
          <span className="font-mono text-[10px] text-muted-foreground/50">
            {timestamp}
          </span>
        )}
      </div>
      
      {/* Content */}
      <div
        className={cn(
          "max-w-[85%]",
          isUser ? "text-right text-muted-foreground" : "text-left"
        )}
      >
        {renderContent()}
      </div>
      
      {/* Action buttons for AI messages */}
      {!isUser && (
        <div className="mt-3 flex items-center gap-1">
          <button
            onClick={handleCopy}
            className={cn(
              "flex items-center gap-1.5 px-2 py-1",
              "font-mono text-[10px] tracking-wider text-muted-foreground/60",
              "hover:text-muted-foreground transition-colors magnetic-hover"
            )}
          >
            {copied ? (
              <>
                <Check className="w-3 h-3" />
                <span>COPIED</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3" />
                <span>COPY</span>
              </>
            )}
          </button>
          
          <span className="text-muted-foreground/30">|</span>
          
          <button
            onClick={handleDownload}
            className={cn(
              "flex items-center gap-1.5 px-2 py-1",
              "font-mono text-[10px] tracking-wider text-muted-foreground/60",
              "hover:text-muted-foreground transition-colors magnetic-hover"
            )}
          >
            <Download className="w-3 h-3" />
            <span>DOWNLOAD</span>
          </button>
          
          <span className="text-muted-foreground/30">|</span>
          
          <button
            onClick={handleShare}
            className={cn(
              "flex items-center gap-1.5 px-2 py-1",
              "font-mono text-[10px] tracking-wider text-muted-foreground/60",
              "hover:text-muted-foreground transition-colors magnetic-hover"
            )}
          >
            {shared ? (
              <>
                <Check className="w-3 h-3" />
                <span>SHARED</span>
              </>
            ) : (
              <>
                <Share2 className="w-3 h-3" />
                <span>SHARE</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}
