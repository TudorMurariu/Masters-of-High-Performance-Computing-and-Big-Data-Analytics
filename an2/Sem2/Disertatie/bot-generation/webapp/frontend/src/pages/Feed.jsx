import { useState, useEffect } from 'react'
import { postsApi } from '../api/client'
import PostCard from '../components/PostCard'

export default function Feed() {
  const [posts,   setPosts]   = useState([])
  const [loading, setLoading] = useState(true)
  const [page,    setPage]    = useState(1)
  const [hasNext, setHasNext] = useState(false)

  const loadPosts = async (p = 1) => {
    setLoading(true)
    try {
      const data = await postsApi.feed(p)
      setPosts(prev => p === 1 ? data.posts : [...prev, ...data.posts])
      setHasNext(data.has_next)
      setPage(p)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadPosts(1) }, [])

  return (
    <div>
      <div className="sticky top-14
                      bg-white/90 dark:bg-slate-900/90
                      backdrop-blur z-10 px-4 py-3
                      border-b border-gray-200 dark:border-slate-700
                      flex items-center justify-between">
        <h1 className="font-bold text-lg">Feed</h1>
        <button onClick={() => loadPosts(1)}
                className="text-xs text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300">
          Refresh
        </button>
      </div>

      {loading && posts.length === 0 && (
        <div className="text-center text-gray-400 dark:text-slate-500 py-16">Loading feed...</div>
      )}

      {!loading && posts.length === 0 && (
        <div className="text-center text-gray-400 dark:text-slate-500 py-16">
          <p className="text-5xl mb-4">🤖</p>
          <p className="font-medium">No posts yet</p>
          <p className="text-sm mt-1">Generate some bots and make them post from the Admin panel</p>
        </div>
      )}

      {posts.map(post => <PostCard key={post.id} post={post} />)}

      {hasNext && (
        <button onClick={() => loadPosts(page + 1)} disabled={loading}
                className="w-full py-3 text-blue-500 dark:text-blue-400
                           hover:text-blue-600 dark:hover:text-blue-300
                           text-sm disabled:opacity-50">
          {loading ? 'Loading...' : 'Load more'}
        </button>
      )}
    </div>
  )
}
