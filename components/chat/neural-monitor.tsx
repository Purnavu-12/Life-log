"use client"

import dynamic from "next/dynamic"
import { Component, ReactNode, useEffect, useState } from "react"

// The SentientSphere renders a three.js <Canvas> which is incompatible with SSR
// / static prerendering (@react-three/fiber needs React DOM internals that are
// unavailable during prerender). Load it client-side only.
const SentientSphere = dynamic(() => import("./sentient-sphere").then((m) => m.SentientSphere), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full rounded-full bg-linear-to-br from-primary/20 to-accent/20 animate-pulse" />
  ),
})

// A decorative three.js canvas should never be able to take down the whole chat
// page. If it throws at runtime, fall back to a graceful placeholder.
class SphereErrorBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { ok: boolean }> {
  state = { ok: true }
  static getDerivedStateFromError() { return { ok: false } }
  componentDidCatch(error: unknown, info: unknown) {
    console.warn("[NeuralMonitor] SentientSphere failed to render", error, info)
  }
  render() {
    return this.state.ok ? <>{this.props.children}</> : <>{this.props.fallback}</>
  }
}

const SphereFallback = () => (
  <div className="flex h-full w-full items-center justify-center rounded-full bg-linear-to-br from-primary/10 to-accent/10 ring-1 ring-dashed ring-border/40" />
)

interface NeuralMonitorProps {
  isThinking?: boolean
}

export function NeuralMonitor({ isThinking = false }: NeuralMonitorProps) {
  // Only mount the three.js canvas after the browser has painted once. This
  // avoids React/Next dev-mode reconciler timing issues during the first
  // render of the dynamic import.
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <div className="flex flex-col items-center gap-4 py-8">
      {/* Sentient Sphere */}
      <div className="relative w-48 h-48">
        {mounted ? (
          <SphereErrorBoundary fallback={<SphereFallback />}>
            <SentientSphere />
          </SphereErrorBoundary>
        ) : (
          <div className="w-full h-full rounded-full bg-linear-to-br from-primary/20 to-accent/20 animate-pulse" />
        )}
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
