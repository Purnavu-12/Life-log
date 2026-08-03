"use client"

/**
 * SentientSphere — a decorative animated sphere for the Neural Core.
 *
 * Originally used @react-three/fiber 8.x (bundles react-reconciler 0.27) +
 * three.js, but that throws "Cannot read properties of undefined (reading
 * 'ReactCurrentOwner')" at module-load time on React 18.3.1 — a known
 * incompatibility (see /memories/repo/threejs-react-matrix.md). Replaced with a
 * pure-CSS animated sphere: no fiber/three imports at all, so zero chance of
 * crashing the chat page. The SphereErrorBoundary in neural-monitor.tsx still
 * guards future dynamic imports.
 */

import { useEffect, useState } from "react"

export function SentientSphere() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <div
      className={
        "relative flex items-center justify-center rounded-full transition-opacity duration-300 " +
        (mounted ? "opacity-100" : "opacity-0")
      }
      style={{ width: 192, height: 192 }}
    >
      {/* Animated gradient base */}
      <div className="absolute inset-0 rounded-full bg-linear-to-br from-cyan-400/30 via-fuchsia-500/20 to-indigo-600/30 animate-pulse" />
      {/* Rotating wireframe ring */}
      <div
        className={
          "absolute inset-4 rounded-full border border-white/20 " +
          "before:absolute before:inset-3 before:rounded-full before:border before:border-white/10 " +
          "before:animate-[spin_12s_linear_infinite] " +
          "after:absolute after:inset-3 after:rounded-full after:border after:border-white/10 " +
          "after:animate-[spin_9s_linear_infinite-reverse]"
        }
      />
      <div className="absolute inset-0 rounded-full shadow-[0_0_40px_8px_rgba(34,211,227,0.25)] animate-pulse" />
    </div>
  )
}
