import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { generateApi, botsApi } from '../api/client'
import api from '../api/client'

const PERSONAS = [
  { value: 'general',    label: 'General',    emoji: '👤', desc: 'Everyday person' },
  { value: 'political',  label: 'Political',  emoji: '🏛️', desc: 'News & politics' },
  { value: 'sports',     label: 'Sports',     emoji: '⚽', desc: 'Sports fan' },
  { value: 'news',       label: 'News',       emoji: '📰', desc: 'News sharer' },
  { value: 'influencer', label: 'Influencer', emoji: '✨', desc: 'Lifestyle content' },
  { value: 'conspiracy', label: 'Conspiracy', emoji: '🔍', desc: 'Alternative views' },
]

export default function Generate() {
  const [persona,     setPersona]     = useState('general')
  const [loading,     setLoading]     = useState(false)
  const [bot,         setBot]         = useState(null)
  const [error,       setError]       = useState('')
  const [modelStatus, setModelStatus] = useState(null)
  const pollRef = useRef(null)

  useEffect(() => {
    api.get('/generate/model-status').then(r => setModelStatus(r.data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (!bot) return
    if (bot.pic_status === 'ready' || bot.pic_status === 'failed') return

    pollRef.current = setInterval(async () => {
      try {
        const updated = await botsApi.getById(bot.id)
        if (updated.pic_status !== 'pending') {
          setBot(updated)
          clearInterval(pollRef.current)
        }
      } catch {/* ignore */}
    }, 3000)

    return () => clearInterval(pollRef.current)
  }, [bot?.id, bot?.pic_status])

  const handleGenerate = async () => {
    clearInterval(pollRef.current)
    setLoading(true)
    setError('')
    setBot(null)
    try {
      const newBot = await generateApi.bot(persona)
      setBot(newBot)
    } catch (e) {
      setError(e.response?.data?.error || 'Generation failed. Is Ollama running?')
    } finally {
      setLoading(false)
    }
  }

  const PicArea = () => {
    if (!bot) return null
    if (bot.pic_status === 'pending') {
      return (
        <div className="w-20 h-20 rounded-full border-4 border-white dark:border-slate-900
                        bg-gray-200 dark:bg-slate-700
                        flex items-center justify-center" title="Generating image…">
          <span className="animate-spin text-2xl">⏳</span>
        </div>
      )
    }
    if (bot.profile_pic) {
      return (
        <img
          src={`${bot.profile_pic}?t=${Date.now()}`}
          alt={bot.display_name}
          className="w-20 h-20 rounded-full border-4 border-white dark:border-slate-900 object-cover"
        />
      )
    }
    return (
      <div className="w-20 h-20 rounded-full border-4 border-white dark:border-slate-900
                      bg-blue-600 flex items-center justify-center font-bold text-white text-3xl">
        {bot.display_name[0]}
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto">
      <h1 className="font-bold text-xl px-4 py-3
                     border-b border-gray-200 dark:border-slate-700 mb-6">
        ✨ Generate Bot Account
      </h1>

      {/* Persona grid */}
      <p className="text-gray-500 dark:text-slate-400 text-sm mb-3">Choose a persona</p>
      <div className="grid grid-cols-3 gap-2 mb-6">
        {PERSONAS.map(p => (
          <button key={p.value} onClick={() => setPersona(p.value)}
                  className={`flex flex-col items-center p-3 rounded-xl border transition-all
                    ${persona === p.value
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300'
                      : 'border-gray-200 dark:border-slate-700 hover:border-gray-400 dark:hover:border-slate-500 text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200'}`}>
            <span className="text-2xl mb-1">{p.emoji}</span>
            <span className="text-xs font-semibold">{p.label}</span>
            <span className="text-xs text-gray-400 dark:text-slate-500 mt-0.5">{p.desc}</span>
          </button>
        ))}
      </div>

      {/* Generate button */}
      <button onClick={handleGenerate} disabled={loading}
              className="w-full py-3 bg-blue-600 hover:bg-blue-700 active:bg-blue-800
                         disabled:opacity-60 disabled:cursor-not-allowed rounded-xl
                         font-bold text-white text-sm">
        {loading ? '⏳ Generating profile…' : '✨ Generate New Bot'}
      </button>

      {/* Model status diagnostic */}
      {modelStatus && modelStatus.state === 'failed' && (
        <div className="mt-4 p-3 rounded-xl border border-yellow-500/50 dark:border-yellow-700/50
                        bg-yellow-50 dark:bg-yellow-900/20 text-xs space-y-1">
          <p className="text-yellow-600 dark:text-yellow-400 font-semibold">
            ⚠️ AI image model failed to load — profile pictures will be placeholder initials
          </p>
          <p className="text-yellow-700 dark:text-yellow-600 font-mono break-all">
            {modelStatus.error}
          </p>
          <p className="text-gray-500 dark:text-slate-400 mt-1">Missing packages:&nbsp;
            {Object.entries(modelStatus.packages || {})
              .filter(([, ok]) => !ok)
              .map(([pkg]) => pkg)
              .join(', ') || 'none detected'}
          </p>
          <p className="text-gray-500 dark:text-slate-400">
            Fix: run&nbsp;
            <code className="bg-gray-100 dark:bg-slate-800 px-1.5 py-0.5 rounded
                             text-gray-800 dark:text-slate-200">
              pip install diffusers transformers accelerate torch
            </code>
            &nbsp;in the same Python environment as Flask
            ({modelStatus.python?.split(/[/\\]/).slice(-3).join('/') || 'unknown'})
          </p>
        </div>
      )}
      {modelStatus && modelStatus.state === 'ready' && (
        <p className="text-xs text-green-600/70 mt-2 text-center">
          ✓ Image model ready ({modelStatus.device})
        </p>
      )}

      {error && <p className="text-red-500 dark:text-red-400 text-sm mt-3 text-center">{error}</p>}

      {/* Result card */}
      {bot && (
        <div className="mt-6 rounded-2xl border border-gray-200 dark:border-slate-700 overflow-hidden">
          {/* Banner */}
          <div className="h-20 bg-gradient-to-r
                          from-blue-100 via-gray-100 to-purple-100
                          dark:from-blue-900 dark:via-slate-800 dark:to-purple-900" />
          <div className="px-4 pb-4">
            <div className="flex items-end gap-3 -mt-10 mb-3">
              <PicArea />
              <div className="pb-1">
                <p className="font-bold text-lg">{bot.display_name}</p>
                <p className="text-gray-500 dark:text-slate-400 text-sm">@{bot.username}</p>
              </div>
            </div>

            <p className="text-gray-700 dark:text-slate-300 text-sm mb-3">{bot.bio}</p>

            <div className="flex gap-4 text-sm text-gray-500 dark:text-slate-400 mb-3">
              <span><b className="text-gray-900 dark:text-slate-100">{(bot.followers_count||0).toLocaleString()}</b> Followers</span>
              <span><b className="text-gray-900 dark:text-slate-100">{(bot.friends_count||0).toLocaleString()}</b> Following</span>
              <span><b className="text-gray-900 dark:text-slate-100">{(bot.statuses_count||0).toLocaleString()}</b> Posts</span>
            </div>

            {bot.pic_status === 'pending' && (
              <p className="text-xs text-blue-500 dark:text-blue-400 mb-3 animate-pulse">
                🎨 Generating AI profile picture… (5–10 s) — page will update automatically
              </p>
            )}
            {bot.pic_status === 'failed' && (
              <p className="text-xs text-yellow-600 dark:text-yellow-500 mb-3">
                ⚠️ Image model failed — showing placeholder avatar
              </p>
            )}

            <div className="flex gap-2">
              <Link to={`/profile/${bot.username}`}
                    className="flex-1 text-center py-2 border border-blue-500
                               text-blue-600 dark:text-blue-400 text-sm rounded-xl
                               hover:bg-blue-50 dark:hover:bg-blue-900/30 font-medium">
                View Profile →
              </Link>
              <button onClick={handleGenerate}
                      className="flex-1 py-2
                                 bg-gray-100 dark:bg-slate-700
                                 hover:bg-gray-200 dark:hover:bg-slate-600
                                 text-gray-800 dark:text-slate-100
                                 text-sm rounded-xl font-medium">
                Generate Another
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
