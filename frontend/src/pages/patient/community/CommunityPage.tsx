import { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';

interface Comment {
  id: string;
  author_pseudonym: string;
  content: string;
  created_at: string;
}

interface Post {
  id: string;
  author_pseudonym: string;
  category: string;
  title: string;
  content: string;
  created_at: string;
  comment_count: number;
  comments: Comment[];
}

export default function CommunityPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Create Post Modal State
  const [isCreating, setIsCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState('General Wellness');
  const [newContent, setNewContent] = useState('');
  const [postMsg, setPostMsg] = useState('');

  // Selected Post Modal State
  const [activePost, setActivePost] = useState<Post | null>(null);
  const [newComment, setNewComment] = useState('');

  const categories = ['All', 'Academic Stress', 'Exam Anxiety', 'Peer Support', 'General Wellness'];

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const catParam = selectedCategory !== 'All' ? `?category=${encodeURIComponent(selectedCategory)}` : '';
      const searchParam = searchTerm ? `${catParam ? '&' : '?'}search=${encodeURIComponent(searchTerm)}` : '';
      const res = await apiClient.get(`/community/posts${catParam}${searchParam}`);
      setPosts(res.data);
    } catch {
      // Error handling
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, [selectedCategory, searchTerm]);

  const handleCreatePost = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) return;

    try {
      const res = await apiClient.post('/community/posts', {
        title: newTitle.trim(),
        category: newCategory,
        content: newContent.trim()
      });

      if (res.data.moderation_status === 'flagged_pending') {
        setPostMsg('Your post has been submitted for counselor safety review before appearing in the feed.');
      } else {
        setPostMsg('Post published successfully!');
        fetchPosts();
      }
      setTimeout(() => {
        setIsCreating(false);
        setNewTitle('');
        setNewContent('');
        setPostMsg('');
      }, 1500);
    } catch {
      setPostMsg('Failed to publish post');
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activePost || !newComment.trim()) return;

    try {
      await apiClient.post(`/community/posts/${activePost.id}/comments`, {
        content: newComment.trim()
      });
      setNewComment('');
      // Refresh post detail
      const res = await apiClient.get(`/community/posts/${activePost.id}`);
      setActivePost(res.data);
      fetchPosts();
    } catch {
      alert('Failed to add comment');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 px-4 py-4">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">👥</span>
            <h1 className="text-2xl font-bold text-gray-900">Student Peer Support Community</h1>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            Connect with campus peers safely. All posts are 100% pseudonymous.
          </p>
        </div>

        <button
          onClick={() => setIsCreating(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-5 py-2.5 rounded-xl shadow cursor-pointer flex items-center gap-2"
        >
          <span>✍️</span> Create Discussion
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col sm:flex-row justify-between gap-4">
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder="Search discussions..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-4 py-1.5 border border-gray-300 rounded-xl text-xs sm:w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Posts List */}
      <div className="space-y-4">
        {loading ? (
          <div className="bg-white p-12 rounded-2xl text-center text-gray-400 text-sm">
            Loading discussions...
          </div>
        ) : posts.length === 0 ? (
          <div className="bg-white p-12 rounded-2xl text-center text-gray-400 text-sm">
            No community discussions found in this category. Be the first to start a topic!
          </div>
        ) : (
          posts.map((post) => (
            <div
              key={post.id}
              onClick={() => setActivePost(post)}
              className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:border-blue-300 transition cursor-pointer space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-1 rounded-lg">
                  {post.category}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(post.created_at).toLocaleDateString()}
                </span>
              </div>

              <h2 className="text-lg font-bold text-gray-900">{post.title}</h2>
              <p className="text-sm text-gray-600 line-clamp-2">{post.content}</p>

              <div className="flex items-center justify-between pt-2 border-t border-gray-50 text-xs text-gray-500">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-700">👤 {post.author_pseudonym}</span>
                </div>
                <div>💬 {post.comment_count} Comments</div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Post Modal */}
      {isCreating && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">Start a Discussion</h2>
              <button onClick={() => setIsCreating(false)} className="text-gray-400 text-xl font-bold">✕</button>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-xl p-3 mb-4 text-xs text-blue-900 flex items-center justify-between">
              <span>Your Identity: <strong>Pseudonymous</strong></span>
              <span className="bg-blue-200 text-blue-800 px-2 py-0.5 rounded font-mono">Protected</span>
            </div>

            <form onSubmit={handleCreatePost} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Topic Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Dealing with mid-term exam stress"
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm bg-white"
                >
                  {categories.filter((c) => c !== 'All').map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">Message Content</label>
                <textarea
                  required
                  rows={4}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="Share your thoughts or ask for peer guidance..."
                  className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {postMsg && (
                <div className="p-3 bg-gray-100 rounded-xl text-center text-xs font-semibold text-gray-700">
                  {postMsg}
                </div>
              )}

              <button
                type="submit"
                className="w-full py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold cursor-pointer"
              >
                Post Anonymously
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Active Post & Comments Modal */}
      {activePost && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl max-h-[85vh] flex flex-col">
            <div className="flex justify-between items-start mb-4">
              <div>
                <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-1 rounded-lg">
                  {activePost.category}
                </span>
                <h2 className="text-xl font-bold text-gray-900 mt-2">{activePost.title}</h2>
                <div className="text-xs text-gray-400 mt-1">
                  Posted by <strong>{activePost.author_pseudonym}</strong> on {new Date(activePost.created_at).toLocaleString()}
                </div>
              </div>
              <button onClick={() => setActivePost(null)} className="text-gray-400 text-2xl font-bold">✕</button>
            </div>

            <div className="text-sm text-gray-700 bg-gray-50 p-4 rounded-xl mb-4 leading-relaxed overflow-y-auto">
              {activePost.content}
            </div>

            {/* Comments Thread */}
            <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                Replies ({activePost.comments ? activePost.comments.length : 0})
              </h3>
              {(!activePost.comments || activePost.comments.length === 0) ? (
                <div className="text-xs text-gray-400 italic py-2">No comments yet.</div>
              ) : (
                activePost.comments.map((c) => (
                  <div key={c.id} className="bg-white border border-gray-100 p-3 rounded-xl shadow-xs">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span className="font-semibold text-gray-800">👤 {c.author_pseudonym}</span>
                      <span>{new Date(c.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-xs text-gray-700">{c.content}</p>
                  </div>
                ))
              )}
            </div>

            {/* Add Comment Form */}
            <form onSubmit={handleAddComment} className="flex gap-2 pt-2 border-t border-gray-100">
              <input
                type="text"
                required
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write a supportive reply..."
                className="flex-1 border border-gray-300 rounded-xl px-4 py-2 text-xs focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-xl text-xs cursor-pointer"
              >
                Reply
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
