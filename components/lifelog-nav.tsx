'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Menu, X, Home, Upload, Search, Settings, Brain } from 'lucide-react'
import { cn } from '@/lib/utils'

export function LifeLogNav() {
  const [isOpen, setIsOpen] = useState(false)
  const pathname = usePathname()

  const isActive = (href: string) => pathname === href

  const links = [
    { href: '/', icon: Brain, label: 'Neural Core', className: 'text-sm' },
    { href: '/dashboard', icon: Home, label: 'Dashboard' },
    { href: '/upload', icon: Upload, label: 'Upload' },
    { href: '/search', icon: Search, label: 'Search' },
    { href: '/settings', icon: Settings, label: 'Settings' },
  ]

  return (
    <nav className="border-b bg-background/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="font-serif font-bold text-lg">
            LifeLog
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {links.map(({ href, icon: Icon, label }) => (
              <Link key={href} href={href}>
                <Button
                  variant={isActive(href) ? 'default' : 'ghost'}
                  size="sm"
                  className={cn('gap-2', isActive(href) && 'bg-primary text-primary-foreground')}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Button>
              </Link>
            ))}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="md:hidden p-2 hover:bg-accent rounded-lg"
          >
            {isOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden border-t py-2 space-y-1">
            {links.map(({ href, icon: Icon, label }) => (
              <Link key={href} href={href}>
                <Button
                  variant={isActive(href) ? 'default' : 'ghost'}
                  size="sm"
                  className="w-full justify-start gap-2"
                  onClick={() => setIsOpen(false)}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Button>
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  )
}
