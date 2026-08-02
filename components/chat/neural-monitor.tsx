"use client"

import { SentientSphere } from "./sentient-sphere"

interface NeuralMonitorProps {
  isThinking?: boolean
}

export function NeuralMonitor({ isThinking = false }: NeuralMonitorProps) {
  return (
    <div className="flex flex-col items-center gap-4 py-8">
      {/* Sentient Sphere */}
      <div className="relative w-48 h-48">
        <SentientSphere />
      </div>
      
      {/* Status text */}
      <div className="flex items-center gap-2">
        <span className="font-mono text-[10px] tracking-[0.2em] text-muted-foreground uppercase">
          {isThinking ? "Processing" : "Neural Core Active"}
        </span>
        {isThinking && (
          <span className="flex gap-0.5">
            <span className="w-1 h-1 rounded-full bg-[#3B82F6] animate-pulse" />
            <span className="w-1 h-1 rounded-full bg-[#6366F1] animate-pulse" style={{ animationDelay: "150ms" }} />
            <span className="w-1 h-1 rounded-full bg-[#8B5CF6] animate-pulse" style={{ animationDelay: "300ms" }} />
          </span>
        )}
      </div>
    </div>
  )
}
