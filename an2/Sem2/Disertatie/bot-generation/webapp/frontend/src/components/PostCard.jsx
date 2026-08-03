import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { postsApi } from '../api/client'

function timeAgo(iso) {
  const s = (Date.now() - new Date(iso)) / 1000
  if (s < 60)    return `${Math.floor(s)}s`
  if (s < 3600)  return `${Math.floor(s / 60)}m`
  if (s < 86400) return `${Math.floor(s / 3600)}h`
  return `${Math.floor(s / 86400)}d`
}

export default function PostCard({ post: initialPost, showDetection = false }) {
  const [post,    setPost]    = useState(initialPost)
  const [likes,   setLikes]   = useState(initialPost.likes)
  const [reposts, setReposts] = useState(initialPost.reposts)
  const { bot }               = post

  // ── Poll video status until ready / failed ──────────────────────────────
  useEffect(() => {
    if (post.media_type !== 'video') return
    if (post.post_status === 'ready' || post.post_status === 'failed') return

    const timer = setInterval(async () => {
      try {
        const status = await postsApi.status(post.id)
        if (status.post_status !== 'pending') {
          setPost(p => ({
            ...p,
            post_status: status.post_status,
            media_path:  status.media_path,
          }))
          clearInterval(timer)
        }
      } catch {/* ignore */}
    }, 4000)

    return () => clearInterval(timer)
  }, [post.id, post.post_status])

  const score   = bot.detection_score
  const label   = bot.detection_label
  const confPct = score != null
    ? (label === 'bot' ? score * 100 : (1 - score) * 100).toFixed(0)
    : null

  /* ── Media area ─────────────────────────────────────────────────────── */
  const MediaArea = () => {
    if (post.post_status === 'pending' && post.media_type === 'video') {
      return (
        <div className="mt-2 rounded-xl w-full h-28
                        bg-gray-100 dark:bg-slate-800
                        border border-gray-200 dark:border-slate-700
                        flex flex-col items-center justify-center gap-2
                        text-gray-400 dark:text-slate-400">
          <span className="animate-spin text-2xl">⏳</span>
          <span className="text-xs animate-pulse">Generating video…</span>
        </div>
      )
    }

    if (post.media_type === 'video' && post.media_path) {
      return (
        <video
          src={`${post.media_path}?t=${post.post_status}`}
          controls
          className="mt-2 rounded-xl w-full max-h-56 bg-black"
        />
      )
    }

    return null
  }

  return (
    <article className="border-b border-gray-200 dark:border-slate-700/60
                        px-4 py-3
                        hover:bg-gray-50 dark:hover:bg-slate-800/30
                        transition-colors">
      <div className="flex gap-3">
        {/* Avatar */}
        <Link to={`/profile/${bot.username}`} className="flex-shrink-0 mt-0.5">
          {bot.profile_pic
            ? <img src={bot.profile_pic} alt={bot.display_name}
                   className="w-11 h-11 rounded-full object-cover" />
            : <div className="w-11 h-11 rounded-full bg-blue-600 flex items-center justify-center
                              font-bold text-white text-lg">
                {bot.display_name[0]}
              </div>
          }
        </Link>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <Link to={`/profile/${bot.username}`}
                  className="font-bold text-gray-900 dark:text-slate-100 hover:underline text-sm">
              {bot.display_name}
            </Link>
            <span className="text-gray-400 dark:text-slate-500 text-sm">@{bot.username}</span>
            <span className="text-gray-300 dark:text-slate-600 text-xs">·</span>
            <span className="text-gray-400 dark:text-slate-500 text-xs">{timeAgo(post.created_at)}</span>

            {post.media_type === 'video' && (
              <span className="text-xs text-purple-500 dark:text-purple-400 ml-1">🎥</span>
            )}

            {/* Detection badge */}
            {showDetection && score != null && (
              <span className={`ml-auto text-xs font-mono px-2 py-0.5 rounded-full
                ${label === 'bot'
                  ? 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400'
                  : 'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400'}`}>
                {label === 'bot' ? '🤖 Bot' : '👤 Human'} {confPct}%
              </span>
            )}
          </div>

          {/* Content */}
          <p className="text-gray-800 dark:text-slate-200 text-sm leading-relaxed mt-1">
            {post.content}
          </p>

          {/* Video / pending indicator */}
          <MediaArea />

          {/* Actions */}
          <div className="flex gap-5 mt-2.5 text-gray-400 dark:text-slate-500 text-xs">
            <button onClick={() => postsApi.like(post.id).then(r => setLikes(r.likes))}
                    className="hover:text-pink-500 dark:hover:text-pink-400 flex items-center gap-1">
              ♥ {likes}
            </button>
            <button onClick={() => postsApi.repost(post.id).then(r => setReposts(r.reposts))}
                    className="hover:text-green-500 dark:hover:text-green-400 flex items-center gap-1">
              🔁 {reposts}
            </button>
            <Link to={`/profile/${bot.username}#chat`}
                  className="hover:text-blue-500 dark:hover:text-blue-400">
              💬 Reply
            </Link>
          </div>
        </div>
      </div>
    </article>
  )
}
