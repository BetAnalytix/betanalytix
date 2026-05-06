'use client'

import { useState } from 'react'
import { supabase } from '@/lib/supabase'
import { useRouter } from 'next/navigation'
import Image from 'next/image'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [isSignUp, setIsSignUp] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setMessage(null)

    try {
      if (isSignUp) {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              username: username,
            },
          },
        })
        if (error) throw error
        setMessage('Vérifiez votre email pour confirmer l\'inscription !')
      } else {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })
        if (error) throw error
        router.push('/')
        router.refresh()
      }
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-[#141414] border border-[#262626] rounded-2xl p-8 shadow-2xl">
        
        {/* Logo & Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-16 h-16 bg-[#1a1a1a] border border-[#262626] rounded-xl flex items-center justify-center mb-4 overflow-hidden">
             <Image 
                src="/LogoBetAnalytix.jpeg" 
                alt="Logo" 
                width={64} 
                height={64}
                className="object-cover"
             />
          </div>
          <h1 className="text-2xl font-bold font-syne tracking-tight">
            BetAnalytix <span className="text-[#00ff88]">v0.1</span>
          </h1>
          <p className="text-gray-400 text-sm mt-2">
            {isSignUp ? 'Créez votre compte investisseur' : 'Connectez-vous à votre dashboard'}
          </p>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-sm p-3 rounded-lg mb-6 text-center">
            {error}
          </div>
        )}

        {message && (
          <div className="bg-[#00ff88]/10 border border-[#00ff88]/20 text-[#00ff88] text-sm p-3 rounded-lg mb-6 text-center">
            {message}
          </div>
        )}

        <form onSubmit={handleAuth} className="space-y-4">
          {isSignUp && (
            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-gray-500 mb-1.5 ml-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-[#0a0a0a] border border-[#262626] rounded-xl px-4 py-3 focus:outline-none focus:border-[#00ff88] transition-colors text-sm"
                placeholder="Votre pseudo"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-gray-500 mb-1.5 ml-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-[#0a0a0a] border border-[#262626] rounded-xl px-4 py-3 focus:outline-none focus:border-[#00ff88] transition-colors text-sm"
              placeholder="votre@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-gray-500 mb-1.5 ml-1">Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[#0a0a0a] border border-[#262626] rounded-xl px-4 py-3 focus:outline-none focus:border-[#00ff88] transition-colors text-sm"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-[#00ff88] text-black font-bold py-3 rounded-xl hover:bg-[#00dd77] transition-all transform active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 mt-2"
          >
            {loading ? 'Traitement...' : isSignUp ? "S'inscrire" : 'Se connecter'}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-[#262626] text-center">
          <button
            onClick={() => setIsSignUp(!isSignUp)}
            className="text-gray-400 text-sm hover:text-white transition-colors"
          >
            {isSignUp ? 'Déjà un compte ? Connectez-vous' : "Pas de compte ? Créer un profil"}
          </button>
        </div>

        {/* Footer info */}
        <div className="mt-8 flex justify-center gap-4 text-[10px] font-mono text-gray-600 uppercase tracking-widest">
            <span>Secured by Supabase</span>
            <span>•</span>
            <span>AI Driven Analysis</span>
        </div>
      </div>
    </div>
  )
}
