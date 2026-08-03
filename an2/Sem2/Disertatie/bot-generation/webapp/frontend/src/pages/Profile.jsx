import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { botsApi, postsApi, chatApi } from '../api/client'
import PostCard from '../components/PostCard'

function getSessionId() {
  const KEY = 'botfarm_session_id'
  let id = localStorage.getItem(KEY)
  if (!id) { id = Math.random().toString(36).slice(2, 12); localStorage.setItem(KEY, id) }
  return id
}

export default function Profile() {
  const { username }          = useParams()
  const [bot,        setBot]  = useState(null)
  const [tab,        setTab]  = useState('posts')
  const [botPosts,   setBP]   = useState([])
  const [messages,   setMsgs] = useState([])
  const [input,      setInput]= useState('')
  const [chatBusy,   setBusy] = useState(false)
  const [loading,    setLd]   = useState(true)
  const bottomRef             = useRef(null)
  const pollRef               = useRef(null)
  const SESSION_ID            = getSessionId()

  useEffect(() => {
    setLd(true)
    botsApi.byUsername(username)
      .then(b => { setBot(b); setLd(false) })
      .catch(() => setLd(false))
  }, [username])

  useEffect(() => {
    if (!bot) return
    if (bot.pic_status === 'ready' || bot.pic_status === 'failed') {
      clearInterval(pollRef.current)
      return
    }
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

  useEffect(() => {
    if (!bot) return
    if (tab === 'posts') postsApi.forBot(bot.id).then(setBP)
    if (tab === 'chat')  chatApi.history(bot.id, SESSION_ID).then(setMsgs)
  }, [bot?.id, tab])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || chatBusy) return
    const msg = input.trim()
    setInput('')
    setMsgs(prev => [...prev, { role: 'user', content: msg }])
    setBusy(true)
    try {
      const resp = await chatApi.send(bot.id, msg, SESSION_ID)
      setMsgs(prev => [...prev, { role: 'assistant', content: resp.reply }])
    } catch {
      setMsgs(prev => [...prev, { role: 'assistant', content: '❌ Error – try again' }])
    }
    setBusy(false)
  }

  if (loading) return (
    <div className="text-center text-gray-400 dark:text-slate-500 py-20">Loading…</div>
  )
  if (!bot) return (
    <div className="text-center text-gray-400 dark:text-slate-500 py-20">Account not found</div>
  )

  const score   = bot.detection_score
  const label   = bot.detection_label
  const confPct = score != null
    ? (label === 'bot' ? score * 100 : (1 - score) * 100).toFixed(0)
    : null

  const ProfilePic = () => {
    if (bot.pic_status === 'pending') {
      return (
        <div className="w-24 h-24 rounded-full border-4 border-white dark:border-slate-900
                        bg-gray-200 dark:bg-slate-700
                        flex items-center justify-center" title="Generating picture…">
          <span className="animate-spin text-3xl">⏳</span>
        </div>
      )
    }
    if (bot.profile_pic) {
      return (
        <img
          src={`${bot.profile_pic}?t=${bot.pic_status}`}
          alt={bot.display_name}
          className="w-24 h-24 rounded-full border-4 border-white dark:border-slate-900 object-cover"
        />
      )
    }
    return (
      <div className="w-24 h-24 rounded-full border-4 border-white dark:border-slate-900
                      bg-blue-600 flex items-center justify-center font-bold text-white text-4xl">
        {bot.display_name[0]}
      </div>
    )
  }

  return (
    <div>
      {/* Profile header */}
      <div className="rounded-2xl border border-gray-200 dark:border-slate-700 overflow-hidden mb-4">
        <div className="h-24 bg-gradient-to-r
                        from-blue-100 via-gray-100 to-purple-100
                        dark:from-blue-900 dark:via-slate-800 dark:to-purple-900" />
        <div className="px-4 pb-4">
          <div className="flex items-end justify-between -mt-12 mb-3">
            <ProfilePic />
            {score != null && (
              <div className={`px-3 py-1.5 rounded-full text-sm font-mono mb-1
                ${label === 'bot'
                  ? 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800/50'
                  : 'bg-green-100 dark:bg-green-900/50 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800/50'}`}>
                {label === 'bot' ? '🤖 Bot' : '👤 Human'} · {confPct}% confidence
              </div>
            )}
          </div>

          <p className="font-bold text-xl">{bot.display_name}</p>
          <p className="text-gray-500 dark:text-slate-400 text-sm">
            @{bot.username} · <span className="capitalize">{bot.persona}</span>
            {bot.pic_status === 'pending' && (
              <span className="text-blue-500 dark:text-blue-400 animate-pulse ml-2">· 🎨 generating photo…</span>
            )}
          </p>
          <p className="text-gray-700 dark:text-slate-300 text-sm mt-2 leading-relaxed">{bot.bio}</p>

          <div className="flex gap-5 text-sm text-gray-500 dark:text-slate-400 mt-3">
            <span><b className="text-gray-900 dark:text-slate-100">{bot.followers_count.toLocaleString()}</b> Followers</span>
            <span><b className="text-gray-900 dark:text-slate-100">{bot.friends_count.toLocaleString()}</b> Following</span>
            <span><b className="text-gray-900 dark:text-slate-100">{bot.statuses_count.toLocaleString()}</b> Posts</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 dark:border-slate-700 mb-4">
        {[
          { key: 'posts', label: `Posts (${botPosts.length})` },
          { key: 'chat',  label: '💬 DM Chat' },
        ].map(({ key, label: lbl }) => (
          <button key={key} onClick={() => setTab(key)}
                  className={`flex-1 py-3 text-sm font-medium border-b-2 -mb-px
                    ${tab === key
                      ? 'border-blue-500 text-blue-500 dark:text-blue-400'
                      : 'border-transparent text-gray-400 dark:text-slate-500 hover:text-gray-700 dark:hover:text-slate-300'}`}>
            {lbl}
          </button>
        ))}
      </div>

      {/* Posts tab */}
      {tab === 'posts' && (
        botPosts.length === 0
          ? <p className="text-center text-gray-400 dark:text-slate-500 py-8 text-sm">No posts yet</p>
          : botPosts.map(p => <PostCard key={p.id} post={p} />)
      )}

      {/* Chat tab */}
      {tab === 'chat' && (
        <div id="chat" className="flex flex-col" style={{ height: '480px' }}>
          <div className="flex-1 overflow-y-auto space-y-3 pb-2 pr-1">
            {messages.length === 0 && (
              <p className="text-center text-gray-400 dark:text-slate-500 py-12 text-sm">
                Start a conversation with <b>{bot.display_name}</b>
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs lg:max-w-sm px-4 py-2.5 rounded-2xl text-sm leading-relaxed
                  ${m.role === 'user'
                    ? 'bg-blue-600 text-white rounded-br-sm'
                    : 'bg-gray-200 dark:bg-slate-700 text-gray-800 dark:text-slate-100 rounded-bl-sm'}`}>
                  {m.content}
                </div>
              </div>
            ))}
            {chatBusy && (
              <div className="flex justify-start">
                <div className="bg-gray-200 dark:bg-slate-700 px-4 py-2.5 rounded-2xl rounded-bl-sm
                                text-gray-500 dark:text-slate-400 text-sm">
                  <span className="animate-pulse">{bot.display_name} is typing…</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="flex gap-2 pt-3 border-t border-gray-200 dark:border-slate-700">
            <input value={input} onChange={e => setInput(e.target.value)}
                   onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
                   placeholder={`Message @${bot.username}…`}
                   className="flex-1 bg-gray-100 dark:bg-slate-800
                              border border-gray-300 dark:border-slate-600
                              rounded-xl px-4 py-2 text-sm
                              text-gray-900 dark:text-slate-100
                              placeholder-gray-400 dark:placeholder-slate-500
                              focus:outline-none focus:border-blue-500" />
            <button onClick={handleSend} disabled={chatBusy || !input.trim()}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50
                               rounded-xl text-sm font-medium text-white">
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
