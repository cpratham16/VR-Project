import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { useNavigate } from 'react-router-dom';

interface FlaggedPost {
  id: string;
  author_pseudonym: string;
  category: string;
  title: string;
  content: string;
  is_flagged: boolean;
  moderation_status: string;
  created_at: string;
}

export default function ModerationQueuePage() {
  const navigate = useNavigate();
  const [queue, setQueue] = useState<FlaggedPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState('');

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/doctor/moderation/queue');
      setQueue(res.data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const handleAction = async (postId: string, action: 'approve' | 'reject') => {
    try {
      await apiClient.post(`/doctor/moderation/posts/${postId}/action`, { action });
      setActionMsg(`Post has been ${action}d.`);
      setQueue((prev) => prev.filter((p) => p.id !== postId));
      setTimeout(() => setActionMsg(''), 2000);
    } catch {
      alert('Failed to perform action');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 px-4 py-4">
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">🛡️</span>
            <h1 className="text-2xl font-bold text-gray-900">Community Safety Moderation Queue</h1>
          </div>
          <p className="text-sm text-gray-600 mt-1">
            Review community posts automatically flagged for self-harm or distress language before they appear publicly.
          </p>
        </div>

        <button
          onClick={() => navigate('/doctor/dashboard')}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
        >
          ← Back to Triage
        </button>
      </div>

      {actionMsg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-xl text-center text-xs font-semibold">
          {actionMsg}
        </div>
      )}

      {loading ? (
        <div className="bg-white p-12 rounded-2xl text-center text-gray-400 text-sm">
          Loading moderation queue...
        </div>
      ) : queue.length === 0 ? (
        <div className="bg-white p-12 rounded-2xl text-center text-emerald-700 font-medium text-sm border border-emerald-100">
          ✓ Moderation queue is clean. No community posts pending review.
        </div>
      ) : (
        <div className="space-y-4">
          {queue.map((post) => (
            <div key={post.id} className="bg-white p-6 rounded-2xl shadow-sm border-2 border-amber-200 space-y-4">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className="bg-amber-100 text-amber-900 text-xs font-bold px-2.5 py-1 rounded-lg">
                    ⚠️ Flagged for Safety
                  </span>
                  <span className="bg-gray-100 text-gray-700 text-xs font-medium px-2.5 py-1 rounded-lg">
                    {post.category}
                  </span>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(post.created_at).toLocaleString()}
                </span>
              </div>

              <div>
                <h2 className="text-lg font-bold text-gray-900">{post.title}</h2>
                <div className="text-xs text-gray-500 mt-0.5">Author: <strong>{post.author_pseudonym}</strong></div>
              </div>

              <div className="bg-amber-50/50 border border-amber-100 p-4 rounded-xl text-sm text-gray-800 leading-relaxed font-sans">
                {post.content}
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => handleAction(post.id, 'reject')}
                  className="px-4 py-2 bg-red-50 hover:bg-red-100 text-red-700 rounded-xl text-xs font-bold transition cursor-pointer border border-red-200"
                >
                  Reject & Suppress Post
                </button>
                <button
                  onClick={() => handleAction(post.id, 'approve')}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition cursor-pointer shadow"
                >
                  Approve for Public Feed
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
