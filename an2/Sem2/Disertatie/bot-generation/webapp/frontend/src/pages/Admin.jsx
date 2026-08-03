import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { authApi, botsApi, postsApi, generateApi, scheduleApi } from '../api/client'

// ── Helpers ──────────────────────────────────────────────────────────────────

function countdown(nextPostAt) {
  if (!nextPostAt) return 'first post pending…'
  const diff = Math.floor((new Date(nextPostAt) - Date.now()) / 1000)
  if (diff <= 0) return 'posting now…'
  if (diff < 60)   return `${diff}s`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`
  const h = Math.floor(diff / 3600)
  const m = Math.floor((diff % 3600) / 60)
  return `${h}h ${m}m`
}

function humanInterval(seconds) {
  if (seconds < 60)   return `${seconds}s`
  if (seconds < 3600) return `${seconds / 60}m`
  return `${seconds / 3600}h`
}

// ── SchedulePanel ─────────────────────────────────────────────────────────────

function SchedulePanel({ bot }) {
  const [schedules,    setSchedules]    = useState([])
  const [loadingSched, setLoadingSched] = useState(true)
  const [creating,     setCreating]     = useState(false)
  const [stopping,     setStopping]     = useState(null)
  const [tick,         setTick]         = useState(0)

  const [intervalNum,  setNum]      = useState(1)
  const [intervalUnit, setUnit]     = useState('hours')
  const [postType,     setPostType] = useState('text')
  const [topic,        setTopic]    = useState('')

  useEffect(() => {
    const t = setInterval(() => setTick(n => n + 1), 1000)
    return () => clearInterval(t)
  }, [])

  const load = useCallback(async () => {
    try {
      const rows = await scheduleApi.forBot(bot.id)
      setSchedules(rows)
    } catch { /* ignore */ }
    setLoadingSched(false)
  }, [bot.id])

  useEffect(() => { load() }, [load])

  const toSeconds = () => {
    const n = Math.max(1, Number(intervalNum))
    if (intervalUnit === 'seconds') return Math.max(5, n)
    if (intervalUnit === 'minutes') return Math.max(1, n) * 60
    return Math.max(1, n) * 3600
  }

  const handleCreate = async () => {
    setCreating(true)
    try {
      const sched = await scheduleApi.create({
        bot_id:           bot.id,
        interval_seconds: toSeconds(),
        post_type:        postType,
        topic:            topic || null,
      })
      setSchedules(prev => [sched, ...prev])
      setTopic('')
    } catch (e) {
      alert(e.response?.data?.error || 'Failed to create schedule')
    } finally { setCreating(false) }
  }

  const handleStop = async (schedId) => {
    setStopping(schedId)
    try {
      await scheduleApi.stop(schedId)
      setSchedules(prev => prev.filter(s => s.id !== schedId))
    } catch { /* ignore */ }
    setStopping(null)
  }

  const unitOptions = [
    { value: 'seconds', label: 'sec', min: 5 },
    { value: 'minutes', label: 'min', min: 1 },
    { value: 'hours',   label: 'hrs', min: 1 },
  ]

  return (
    <div className="mt-3 pt-3 border-t border-gray-200 dark:border-slate-700/60">
      <p className="text-xs text-gray-500 dark:text-slate-400 font-semibold mb-2 uppercase tracking-wide">
        ⏱ Auto-post Schedule
      </p>

      {/* Create form */}
      <div className="flex flex-wrap gap-2 mb-3">
        {/* Interval */}
        <div className="flex rounded-lg overflow-hidden border border-gray-300 dark:border-slate-600 text-xs">
          <input
            type="number" min="1" value={intervalNum}
            onChange={e => setNum(Math.max(1, Number(e.target.value)))}
            className="w-14 bg-gray-100 dark:bg-slate-700
                       text-gray-900 dark:text-slate-100
                       px-2 py-1.5 text-center
                       focus:outline-none focus:bg-gray-200 dark:focus:bg-slate-600"
          />
          <select
            value={intervalUnit}
            onChange={e => setUnit(e.target.value)}
            className="bg-gray-100 dark:bg-slate-700
                       text-gray-900 dark:text-slate-100
                       px-2 py-1.5 focus:outline-none
                       border-l border-gray-300 dark:border-slate-600 cursor-pointer">
            {unitOptions.map(u => (
              <option key={u.value} value={u.value}>{u.label}</option>
            ))}
          </select>
        </div>

        {/* Post type */}
        <div className="flex rounded-lg overflow-hidden border border-gray-300 dark:border-slate-600 text-xs">
          {['text', 'video'].map(t => (
            <button
              key={t}
              onClick={() => setPostType(t)}
              className={`px-3 py-1.5
                ${postType === t
                  ? (t === 'video' ? 'bg-purple-700 text-white' : 'bg-blue-700 text-white')
                  : 'bg-gray-100 dark:bg-slate-700 text-gray-500 dark:text-slate-400 hover:bg-gray-200 dark:hover:bg-slate-600'}`}>
              {t === 'text' ? '📝 Text' : '🎥 Video'}
            </button>
          ))}
        </div>

        {/* Topic */}
        <input
          value={topic}
          onChange={e => setTopic(e.target.value)}
          placeholder="Topic (optional)"
          className="flex-1 min-w-24
                     bg-gray-100 dark:bg-slate-700
                     border border-gray-300 dark:border-slate-600
                     rounded-lg px-3 py-1.5 text-xs
                     text-gray-900 dark:text-slate-100
                     placeholder-gray-400 dark:placeholder-slate-500
                     focus:outline-none focus:border-blue-500"
        />

        {/* Start */}
        <button
          onClick={handleCreate}
          disabled={creating}
          className="px-3 py-1.5 bg-green-700 hover:bg-green-600 disabled:opacity-50
                     rounded-lg text-xs font-medium text-white flex-shrink-0">
          {creating ? '…' : '▶ Start'}
        </button>
      </div>

      {/* Active schedules */}
      {loadingSched
        ? <p className="text-xs text-gray-400 dark:text-slate-500 animate-pulse">Loading…</p>
        : schedules.length === 0
          ? <p className="text-xs text-gray-400 dark:text-slate-600 italic">No active schedules</p>
          : (
            <div className="space-y-1.5">
              {schedules.map(s => (
                <div key={s.id}
                     className="flex items-center gap-2
                                bg-gray-100 dark:bg-slate-700/50
                                rounded-lg px-3 py-2 text-xs">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                    s.running ? 'bg-green-400 animate-pulse' : 'bg-gray-300 dark:bg-slate-500'
                  }`} />

                  <span className="text-gray-700 dark:text-slate-300 font-medium">
                    every {humanInterval(s.interval_seconds)}
                  </span>
                  <span className={`px-1.5 py-0.5 rounded text-xs ${
                    s.post_type === 'video'
                      ? 'bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300'
                      : 'bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-300'
                  }`}>
                    {s.post_type === 'video' ? '🎥' : '📝'} {s.post_type}
                  </span>
                  {s.topic && (
                    <span className="text-gray-400 dark:text-slate-500 truncate max-w-24" title={s.topic}>
                      "{s.topic}"
                    </span>
                  )}

                  <span className="ml-auto text-gray-500 dark:text-slate-400 tabular-nums flex-shrink-0">
                    {s.running ? `next: ${countdown(s.next_post_at)}` : '⏸ stopped'}
                  </span>

                  <button
                    onClick={() => handleStop(s.id)}
                    disabled={stopping === s.id}
                    className="flex-shrink-0 px-2 py-0.5 border border-red-300 dark:border-red-900/60
                               hover:border-red-500 text-red-500 dark:text-red-400 rounded
                               disabled:opacity-40">
                    {stopping === s.id ? '…' : '⏹'}
                  </button>
                </div>
              ))}
            </div>
          )
      }
    </div>
  )
}

// ── Main Admin page ───────────────────────────────────────────────────────────

export default function Admin() {
  const [isAdmin,      setAdmin]    = useState(false)
  const [password,     setPwd]      = useState('')
  const [loginErr,     setLErr]     = useState('')
  const [botList,      setBots]     = useState([])
  const [posting,      setPosting]  = useState(null)
  const [videoPosting, setVPosting] = useState(null)
  const [regenning,    setRegenning]= useState(null)
  const [topics,       setTopics]   = useState({})
  const [openSched,    setOpenSched]= useState(new Set())
  const pollRefs = useRef({})

  useEffect(() => {
    authApi.status().then(s => {
      if (s.is_admin) { setAdmin(true); loadBots() }
    })
    return () => Object.values(pollRefs.current).forEach(clearInterval)
  }, [])

  const loadBots = () => botsApi.list().then(bots => {
    setBots(bots)
    bots.forEach(b => b.pic_status === 'pending' && startPicPoll(b.id))
  })

  const startPicPoll = (botId) => {
    if (pollRefs.current[botId]) return
    pollRefs.current[botId] = setInterval(async () => {
      try {
        const updated = await botsApi.getById(botId)
        if (updated.pic_status !== 'pending') {
          setBots(prev => prev.map(b => b.id === botId ? updated : b))
          clearInterval(pollRefs.current[botId])
          delete pollRefs.current[botId]
        }
      } catch { /* ignore */ }
    }, 3000)
  }

  const handleLogin = async (e) => {
    e.preventDefault()
    try { await authApi.login(password); setAdmin(true); loadBots() }
    catch { setLErr('Wrong password') }
  }
  const handleLogout = async () => {
    await authApi.logout()
    setAdmin(false); setBots([])
    Object.values(pollRefs.current).forEach(clearInterval)
    pollRefs.current = {}
  }

  const handlePost = async (botId) => {
    setPosting(botId)
    try { await postsApi.generate(botId, topics[botId] || null); await loadBots() }
    finally { setPosting(null) }
  }

  const handleVideoPost = async (botId) => {
    setVPosting(botId)
    try { await postsApi.generateVideo(botId, topics[botId] || null); await loadBots() }
    finally { setVPosting(null) }
  }

  const handleRegenPic = async (botId) => {
    setRegenning(botId)
    try {
      await generateApi.regenPic(botId)
      setBots(prev => prev.map(b => b.id === botId ? { ...b, pic_status: 'pending' } : b))
      startPicPoll(botId)
    } finally { setRegenning(null) }
  }

  const handleDelete = async (botId) => {
    if (!window.confirm('Delete this bot and all its posts?')) return
    clearInterval(pollRefs.current[botId])
    delete pollRefs.current[botId]
    await botsApi.delete(botId)
    setBots(prev => prev.filter(b => b.id !== botId))
  }

  const handleToggle = async (botId) => {
    const r = await botsApi.toggle(botId)
    setBots(prev => prev.map(b => b.id === botId ? { ...b, is_active: r.is_active } : b))
  }

  const toggleSchedPanel = (botId) => {
    setOpenSched(prev => {
      const s = new Set(prev)
      s.has(botId) ? s.delete(botId) : s.add(botId)
      return s
    })
  }

  /* ── Login screen ── */
  if (!isAdmin) return (
    <div className="max-w-sm mx-auto mt-16">
      <div className="text-center mb-8">
        <p className="text-5xl mb-3">⚙️</p>
        <h1 className="text-2xl font-bold">Admin Panel</h1>
        <p className="text-gray-500 dark:text-slate-400 text-sm mt-1">Bot Farm control centre</p>
      </div>
      <form onSubmit={handleLogin} className="space-y-3">
        <input type="password" value={password} onChange={e => setPwd(e.target.value)}
               placeholder="Admin password"
               className="w-full bg-gray-100 dark:bg-slate-800
                          border border-gray-300 dark:border-slate-600
                          rounded-xl px-4 py-3
                          text-gray-900 dark:text-slate-100
                          placeholder-gray-400 dark:placeholder-slate-500
                          focus:outline-none focus:border-blue-500" />
        {loginErr && <p className="text-red-500 dark:text-red-400 text-sm text-center">{loginErr}</p>}
        <button type="submit"
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-bold text-white">
          Login
        </button>
      </form>
      <p className="text-center text-gray-400 dark:text-slate-600 text-xs mt-4">
        Default password: botfarm2024
      </p>
    </div>
  )

  /* ── Dashboard ── */
  const totalPosts = botList.reduce((s, b) => s + b.post_count, 0)

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between py-3
                      border-b border-gray-200 dark:border-slate-700 mb-5">
        <h1 className="font-bold text-xl">⚙️ Admin Dashboard</h1>
        <div className="flex gap-2">
          <Link to="/generate"
                className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm text-white font-medium">
            + New Bot
          </Link>
          <button onClick={handleLogout}
                  className="px-3 py-1.5
                             border border-gray-300 dark:border-slate-600
                             hover:border-gray-500 dark:hover:border-slate-400
                             rounded-lg text-sm text-gray-500 dark:text-slate-400">
            Logout
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {[
          { n: botList.length,                          label: 'Bots',        sub: 'created' },
          { n: botList.filter(b => b.is_active).length, label: 'Active',      sub: 'bots' },
          { n: totalPosts,                              label: 'Total Posts', sub: 'generated' },
        ].map(({ n, label, sub }) => (
          <div key={label} className="bg-gray-50 dark:bg-slate-800
                                      rounded-xl p-3 text-center
                                      border border-gray-200 dark:border-slate-700">
            <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{n}</p>
            <p className="text-xs text-gray-700 dark:text-slate-300 font-medium mt-0.5">{label}</p>
            <p className="text-xs text-gray-400 dark:text-slate-500">{sub}</p>
          </div>
        ))}
      </div>

      {botList.length === 0 && (
        <div className="text-center text-gray-400 dark:text-slate-500 py-10">
          <p className="text-4xl mb-3">🤖</p>
          <p>No bots yet.</p>
          <Link to="/generate" className="text-blue-500 dark:text-blue-400 hover:underline text-sm">
            Generate your first bot →
          </Link>
        </div>
      )}

      {/* Bot cards */}
      <div className="space-y-3">
        {botList.map(bot => (
          <div key={bot.id} className="bg-gray-50 dark:bg-slate-800
                                       rounded-xl border border-gray-200 dark:border-slate-700 p-4">
            {/* Avatar + info */}
            <div className="flex items-center gap-3 mb-3">
              <div className="relative flex-shrink-0">
                {bot.pic_status === 'pending'
                  ? <div className="w-11 h-11 rounded-full
                                    bg-gray-200 dark:bg-slate-700
                                    border border-gray-300 dark:border-slate-600
                                    flex items-center justify-center">
                      <span className="animate-spin text-base">⏳</span>
                    </div>
                  : bot.profile_pic
                    ? <img src={`${bot.profile_pic}?t=${bot.pic_status}`}
                           className="w-11 h-11 rounded-full object-cover" alt="" />
                    : <div className="w-11 h-11 rounded-full bg-blue-600 flex items-center
                                      justify-center font-bold text-white">
                        {bot.display_name[0]}
                      </div>
                }
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="font-semibold text-sm">{bot.display_name}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    bot.is_active
                      ? 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400'
                      : 'bg-gray-100 dark:bg-slate-700 text-gray-400 dark:text-slate-500'
                  }`}>
                    {bot.is_active ? '● Active' : '○ Paused'}
                  </span>
                  {bot.pic_status === 'pending' && (
                    <span className="text-xs px-2 py-0.5 rounded-full
                                     bg-blue-100 dark:bg-blue-900/40
                                     text-blue-600 dark:text-blue-400 animate-pulse">
                      🎨 generating…
                    </span>
                  )}
                  {bot.detection_label && (() => {
                    const conf = bot.detection_label === 'bot'
                      ? bot.detection_score * 100
                      : (1 - bot.detection_score) * 100
                    return (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        bot.detection_label === 'bot'
                          ? 'bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400'
                          : 'bg-green-100 dark:bg-green-900/40 text-green-600 dark:text-green-400'
                      }`}>
                        {bot.detection_label === 'bot' ? '🤖' : '👤'} {conf.toFixed(0)}%
                      </span>
                    )
                  })()}
                </div>
                <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">
                  @{bot.username} · {bot.persona} · {bot.post_count} posts
                </p>
              </div>
            </div>

            {/* Topic input */}
            <input value={topics[bot.id] || ''}
                   onChange={e => setTopics(t => ({ ...t, [bot.id]: e.target.value }))}
                   placeholder="Post topic (optional)"
                   className="w-full bg-gray-100 dark:bg-slate-700/60
                              border border-gray-300 dark:border-slate-600
                              rounded-lg px-3 py-1.5 mb-2 text-xs
                              text-gray-900 dark:text-slate-100
                              placeholder-gray-400 dark:placeholder-slate-500
                              focus:outline-none focus:border-blue-500" />

            {/* Action buttons */}
            <div className="flex flex-wrap gap-2">
              <button onClick={() => handlePost(bot.id)} disabled={posting === bot.id}
                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50
                                 rounded-lg text-xs font-medium text-white">
                {posting === bot.id ? '…' : '📝 Text Post'}
              </button>

              <button onClick={() => handleVideoPost(bot.id)} disabled={videoPosting === bot.id}
                      className="px-3 py-1.5 bg-purple-700 hover:bg-purple-600 disabled:opacity-50
                                 rounded-lg text-xs font-medium text-white"
                      title="Generate a short AI video post (LTX-Video)">
                {videoPosting === bot.id ? '⏳ Queuing…' : '🎥 Video Post'}
              </button>

              <button
                onClick={() => toggleSchedPanel(bot.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium
                  ${openSched.has(bot.id)
                    ? 'bg-yellow-100 dark:bg-yellow-700/60 text-yellow-700 dark:text-yellow-300 border border-yellow-200 dark:border-yellow-700/60'
                    : 'border border-gray-300 dark:border-slate-600 hover:border-yellow-500 dark:hover:border-yellow-600 text-gray-500 dark:text-slate-400 hover:text-yellow-600 dark:hover:text-yellow-400'}`}>
                ⏱ Schedule
              </button>

              <Link to={`/profile/${bot.username}`}
                    className="px-3 py-1.5
                               border border-gray-300 dark:border-slate-600
                               hover:border-gray-500 dark:hover:border-slate-400
                               rounded-lg text-xs text-gray-500 dark:text-slate-400">
                View
              </Link>

              <button onClick={() => handleRegenPic(bot.id)}
                      disabled={regenning === bot.id || bot.pic_status === 'pending'}
                      title="Regenerate profile picture with AI"
                      className="px-3 py-1.5
                                 border border-gray-300 dark:border-slate-600
                                 hover:border-blue-400 dark:hover:border-blue-500
                                 disabled:opacity-40 rounded-lg text-xs
                                 text-gray-500 dark:text-slate-400
                                 hover:text-blue-500 dark:hover:text-blue-400">
                {regenning === bot.id || bot.pic_status === 'pending' ? '⏳' : '🎨 Regen Pic'}
              </button>

              <button onClick={() => handleToggle(bot.id)}
                      className="px-3 py-1.5
                                 border border-gray-300 dark:border-slate-600
                                 hover:border-gray-500 dark:hover:border-slate-400
                                 rounded-lg text-xs text-gray-500 dark:text-slate-400">
                {bot.is_active ? 'Pause' : 'Resume'}
              </button>

              <button onClick={() => handleDelete(bot.id)}
                      className="px-3 py-1.5 border border-red-200 dark:border-red-900/60
                                 hover:border-red-500 rounded-lg text-xs text-red-500 dark:text-red-400">
                Delete
              </button>
            </div>

            {openSched.has(bot.id) && <SchedulePanel bot={bot} />}
          </div>
        ))}
      </div>
    </div>
  )
}
