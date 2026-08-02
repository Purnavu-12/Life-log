'use client'

import { createContext, useContext, useState, ReactNode } from 'react'

interface User {
  id: string
  email: string
  username: string
  full_name?: string
  is_active: boolean
  created_at: string
  last_login?: string
}

const LOCAL_USER: User = {
  id: 'local-user',
  email: 'local@lifelog.ai',
  username: 'local',
  full_name: 'Local User',
  is_active: true,
  created_at: new Date().toISOString(),
}

interface AuthContextType {
  user: User
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string, full_name?: string) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user] = useState<User>(LOCAL_USER)

  const login = async () => {}
  const register = async () => {}
  const logout = () => {}
  const refreshUser = async () => {}

  const value: AuthContextType = {
    user,
    isAuthenticated: true,
    isLoading: false,
    error: null,
    login,
    register,
    logout,
    refreshUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export { AuthContext }
