import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { setAccessToken } from '../lib/api'

export default function AuthGate({ children }) {
  const [session, setSession] = useState(undefined)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!supabase) { setSession(null); return }
    supabase.auth.getSession().then(({ data }) => {
      setAccessToken(data.session?.access_token || null)
      setSession(data.session)
    })
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, next) => {
      setAccessToken(next?.access_token || null)
      setSession(next)
    })
    return () => subscription.unsubscribe()
  }, [])

  if (session === undefined) return <div style={{ color: '#aaa', padding: 48 }}>Loading CreatorOS…</div>
  if (!supabase) return <div style={{ color: '#fca5a5', padding: 48 }}>CreatorOS is missing its Supabase sign-in configuration.</div>
  if (session) return <>{children}</>

  const submit = async (signup) => {
    setMessage('')
    const action = signup ? supabase.auth.signUp({ email, password }) : supabase.auth.signInWithPassword({ email, password })
    const { error } = await action
    setMessage(error ? error.message : signup ? 'Account created. Check your email if confirmation is enabled.' : '')
  }
  return <main style={{ maxWidth: 420, margin: '80px auto', padding: 24, color: '#eee', fontFamily: 'system-ui' }}>
    <h1>CreatorOS</h1><p style={{ color: '#999' }}>Sign in to keep your uploads and channel connection private.</p>
    <input placeholder="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} style={{ width: '100%', padding: 12, margin: '8px 0' }} />
    <input placeholder="Password (at least 6 characters)" type="password" value={password} onChange={e => setPassword(e.target.value)} style={{ width: '100%', padding: 12, margin: '8px 0' }} />
    <button onClick={() => submit(false)} style={{ padding: 12, marginRight: 8 }}>Sign in</button>
    <button onClick={() => submit(true)} style={{ padding: 12 }}>Create account</button>
    {message && <p style={{ color: '#fbbf24' }}>{message}</p>}
  </main>
}
