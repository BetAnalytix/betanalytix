import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Interface correspondant à la table 'public.profiles'
export type Profile = {
  id: string
  username: string | null
  balance: number
  currency: string
  updated_at: string
}

// Interface correspondant à la table 'public.bets'
export type Bet = {
  id: string
  created_at: string
  user_id: string
  match_name: string
  prediction: '1' | 'X' | '2'
  odds: number
  stake: number
  status: 'PENDING' | 'WON' | 'LOST' | 'VOID'
  pnl: number
}

// Types utilitaires pour les insertions (sans les champs auto-générés)
export type InsertProfile = Partial<Profile> & { id: string }
export type InsertBet = Omit<Bet, 'id' | 'created_at' | 'pnl'>
