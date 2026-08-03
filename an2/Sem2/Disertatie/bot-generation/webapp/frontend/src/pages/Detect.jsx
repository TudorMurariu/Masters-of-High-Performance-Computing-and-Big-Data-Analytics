import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { botsApi, detectApi } from '../api/client'

export default function Detect() {
  const [botList,    setBots]  = useState([])
  const [loading,    setLoad]  = useState(true)
  const [runningAll, setAll]   = useState(false)
  const [runningId,  setOne]   = useState(null)

  const load = () => botsApi.list().then(b => { setBots(b); setLoad(false) })
  useEffect(() => { load() }, [])

  const detectOne = async (bot) => {
    setOne(bot.id)
    try {
      const r = await detectApi.one(bot.id)
      setBots(prev => prev.map(b => b.id === bot.id
        ? { ...b, detection_score: r.score, detection_label: r.label } : b))
    } finally { setOne(null) }
  }

  const detectAll = async () => {
    setAll(true)
    try {
      const results = await detectApi.all()
      const map = Object.fromEntries(results.map(r => [r.bot_id, r]))
      setBots(prev => prev.map(b => {
        const r = map[b.id]
        return r?.score != null ? { ...b, detection_score: r.score, detection_label: r.label } : b
      }))
    } finally { setAll(false) }
  }

  if (loading) return (
    <div className="text-center text-gray-400 dark:text-slate-500 py-16">Loading…</div>
  )

  const scanned    = botList.filter(b => b.detection_label != null)
  const flaggedBot = scanned.filter(b => b.detection_label === 'bot').length
  const flaggedHum = scanned.filter(b => b.detection_label === 'human').length

  return (
    <div>
      <div className="flex items-center justify-between py-3
                      border-b border-gray-200 dark:border-slate-700 mb-4">
        <h1 className="font-bold text-xl">🔍 Bot Detector</h1>
        <button onClick={detectAll} disabled={runningAll || botList.length === 0}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50
                           rounded-xl text-sm font-medium text-white">
          {runningAll ? '⏳ Running…' : 'Scan All'}
        </button>
      </div>

      {/* Summary cards */}
      {scanned.length > 0 && (
        <div className="grid grid-cols-3 gap-3 mb-5">
          {[
            {
              n: botList.length, label: 'Total',
              color: 'bg-gray-100 dark:bg-slate-800 border-gray-200 dark:border-slate-700',
            },
            {
              n: flaggedBot, label: 'Flagged Bot',
              color: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800/40 text-red-600 dark:text-red-300',
            },
            {
              n: flaggedHum, label: 'Flagged Human',
              color: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800/40 text-green-600 dark:text-green-300',
            },
          ].map(({ n, label, color }) => (
            <div key={label} className={`rounded-xl p-3 text-center border ${color}`}>
              <p className="text-2xl font-bold">{n}</p>
              <p className="text-xs mt-1 opacity-70">{label}</p>
            </div>
          ))}
        </div>
      )}

      {botList.length === 0 && (
        <p className="text-center text-gray-400 dark:text-slate-500 py-12 text-sm">
          No bots yet — <Link to="/generate" className="text-blue-500 dark:text-blue-400 hover:underline">generate one</Link>
        </p>
      )}

      <div className="space-y-2">
        {botList.map(bot => {
          const score   = bot.detection_score
          const label   = bot.detection_label
          const confPct = score != null
            ? (label === 'bot' ? score * 100 : (1 - score) * 100).toFixed(1)
            : null

          return (
            <div key={bot.id}
                 className="flex items-center gap-3 p-3
                            bg-gray-50 dark:bg-slate-800/60
                            rounded-xl border border-gray-200 dark:border-slate-700">
              {bot.profile_pic
                ? <img src={bot.profile_pic} className="w-10 h-10 rounded-full object-cover flex-shrink-0" />
                : <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center
                                  font-bold text-white flex-shrink-0">
                    {bot.display_name[0]}
                  </div>
              }

              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm text-gray-900 dark:text-slate-100 truncate">
                  {bot.display_name}
                </p>
                <p className="text-xs text-gray-500 dark:text-slate-400">
                  @{bot.username} · {bot.persona}
                </p>
              </div>

              {/* Confidence bar */}
              {confPct != null ? (
                <div className="w-32 flex-shrink-0">
                  <div className="flex justify-between text-xs mb-1">
                    <span className={label === 'bot' ? 'text-red-500 dark:text-red-400' : 'text-green-500 dark:text-green-400'}>
                      {label === 'bot' ? '🤖 Bot' : '👤 Human'}
                    </span>
                    <span className="text-gray-500 dark:text-slate-400">{confPct}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-500
                      ${label === 'bot' ? 'bg-red-500' : 'bg-green-500'}`}
                         style={{ width: `${confPct}%` }} />
                  </div>
                  <p className="text-xs text-gray-300 dark:text-slate-600 mt-0.5">confidence</p>
                </div>
              ) : (
                <span className="text-xs text-gray-400 dark:text-slate-500 w-28 text-center flex-shrink-0">
                  Not scanned
                </span>
              )}

              <button onClick={() => detectOne(bot)} disabled={runningId === bot.id}
                      className="flex-shrink-0 px-3 py-1.5
                                 border border-gray-300 dark:border-slate-600
                                 hover:border-gray-500 dark:hover:border-slate-400
                                 rounded-lg text-xs
                                 text-gray-600 dark:text-slate-300
                                 disabled:opacity-50">
                {runningId === bot.id ? '…' : 'Scan'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
