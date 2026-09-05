import { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import { Card, Button, Badge } from '../../../components/ui';

interface Comment {
  id: string;
  parent_id?: string | null;
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

const CATEGORIES = ['All', 'Academic Stress', 'Exam Anxiety', 'Peer Support', 'General Wellness'];
const MAX_DEPTH = 8;

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

export default function CommunityPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
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
  const [replyTo, setReplyTo] = useState<string | null>(null);
  const [newComment, setNewComment] = useState('');
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const catParam = selectedCategory !== 'All' ? `?category=${encodeURIComponent(selectedCategory)}` : '';
        const searchParam = searchTerm ? `${catParam ? '&' : '?'}search=${encodeURIComponent(searchTerm)}` : '';
        const res = await apiClient.get(`/community/posts${catParam}${searchParam}`);
        if (!cancelled) {
          setPosts(Array.isArray(res.data) ? res.data : []);
        }
      } catch (err: any) {
        if (!cancelled) {
          setPosts([]);
          setError(
            err.response?.status === 401
              ? 'Your session has expired — please log in again to see the community.'
              : err.response?.data?.detail || 'Could not load discussions. Please try again.'
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [selectedCategory, searchTerm]);

  const refreshPosts = async () => {
    try {
      const catParam = selectedCategory !== 'All' ? `?category=${encodeURIComponent(selectedCategory)}` : '';
      const searchParam = searchTerm ? `${catParam ? '&' : '?'}search=${encodeURIComponent(searchTerm)}` : '';
      const res = await apiClient.get(`/community/posts${catParam}${searchParam}`);
      setPosts(Array.isArray(res.data) ? res.data : []);
    } catch {
      /* keep current list; error state already surfaced on initial load */
    }
  };

  const toggleCollapse = (id: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const countSubtree = (comments: Comment[], id: string): number => {
    let n = 0;
    for (const c of comments) {
      if (c.parent_id === id) {
        n += 1 + countSubtree(comments, c.id);
      }
    }
    return n;
  };

  const renderThread = (
    comments: Comment[],
    parentId: string | null,
    depth: number,
    onReply: (id: string, depth: number) => void
  ) => {
    const children = comments.filter((c) => c.parent_id === parentId);
    if (children.length === 0) return null;

    return children.map((c) => {
      const isCollapsed = collapsed.has(c.id);
      const hiddenCount = countSubtree(comments, c.id);
      const railTone = depth % 2 === 0 ? 'border-[#e8e4df]' : 'border-accent/25';

      return (
        <div key={c.id} className={depth > 0 ? `border-l-2 ${railTone} pl-4 ml-3 mt-3` : 'mt-3'}>
          <div className="group">
            {/* Meta row */}
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <button
                onClick={() => toggleCollapse(c.id)}
                aria-label={isCollapsed ? `Expand reply thread (${hiddenCount} hidden)` : 'Collapse reply thread'}
                className="w-6 h-5 shrink-0 cursor-pointer rounded-sm border border-[#e8e4df] bg-white font-mono text-[10px] font-bold text-muted-foreground transition-colors hover:border-accent hover:text-accent"
              >
                {isCollapsed ? `[+${hiddenCount || ''}]` : '[–]'}
              </button>
              <span className="font-semibold text-slate-800">{c.author_pseudonym}</span>
              <span aria-hidden="true" className="h-0.5 w-0.5 rotate-45 bg-accent" />
              <span>{timeAgo(c.created_at)}</span>
            </div>

            {/* Body */}
            {!isCollapsed && (
              <>
                <p className="mt-1 text-sm leading-relaxed text-slate-700">{c.content}</p>
                <div className="flex items-center gap-4 mt-1">
                  {depth < MAX_DEPTH && (
                    <button
                      onClick={() => onReply(c.id, depth)}
                      className="text-[11px] font-semibold tracking-wide text-accent hover:underline underline-offset-2 cursor-pointer"
                    >
                      Reply
                    </button>
                  )}
                  {depth >= MAX_DEPTH && (
                    <span className="text-[10px] italic text-muted-foreground">max depth</span>
                  )}
                </div>

                {replyTo === c.id && (
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      handleAddComment(e as unknown as React.FormEvent);
                    }}
                    className="mt-2 flex gap-2"
                  >
                    <input
                      type="text"
                      autoFocus
                      required
                      value={newComment}
                      onChange={(e) => setNewComment(e.target.value)}
                      placeholder={`Reply to ${c.author_pseudonym}...`}
                      className="flex-1 rounded-md border border-[#e8e4df] bg-white px-3 py-2 text-xs shadow-none transition-all focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15"
                    />
                    <Button size="sm" type="submit">Reply</Button>
                    <Button size="sm" variant="ghost" type="button" onClick={() => setReplyTo(null)}>Cancel</Button>
                  </form>
                )}
              </>
            )}
          </div>

          {/* Subtree */}
          {!isCollapsed && renderThread(comments, c.id, depth + 1, onReply)}
        </div>
      );
    });
  };

  const openPost = (post: Post) => {
    setActivePost(post);
    setReplyTo(null);
    setNewComment('');
    setCollapsed(new Set());
  };

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
        refreshPosts();
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
        content: newComment.trim(),
        parent_id: replyTo
      });
      setNewComment('');
      setReplyTo(null);
      // Refresh post detail
      const res = await apiClient.get(`/community/posts/${activePost.id}`);
      if (res.data && Array.isArray(res.data.comments)) {
        setActivePost(res.data);
      }
      refreshPosts();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add comment');
    }
  };

  const startReply = (id: string) => {
    setReplyTo(id);
    setNewComment('');
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-4">
      {/* Header */}
      <Card variant="default" className="p-6">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <span className="small-caps text-accent">Community</span>
            <h1 className="mt-1 font-display text-3xl font-medium text-foreground">Peer Support</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Connect with peers safely. All posts are 100% pseudonymous.
            </p>
          </div>

          <Button onClick={() => setIsCreating(true)}>✍️ Create Discussion</Button>
        </div>
      </Card>

      {error && (
        <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-800">
          {error}
        </div>
      )}

      {/* Filter & Search Bar */}
      <Card variant="default" className="p-4">
        <div className="flex flex-col justify-between gap-4 sm:flex-row">
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`cursor-pointer rounded-md px-3 py-1.5 font-mono text-[11px] font-medium uppercase tracking-[0.08em] transition-colors duration-200 ${
                  selectedCategory === cat
                    ? 'bg-accent text-white'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
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
            className="h-9 rounded-md border border-[#e8e4df] bg-white px-4 text-xs shadow-none transition-all focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15 sm:w-64"
          />
        </div>
      </Card>

      {/* Posts List */}
      <div className="space-y-4">
        {loading ? (
          <Card variant="default" className="p-12 text-center text-sm text-muted-foreground">
            Loading discussions...
          </Card>
        ) : error && posts.length === 0 ? (
          <Card variant="outline" className="p-12 text-center text-sm text-muted-foreground">
            Discussions unavailable — see the notice above.
          </Card>
        ) : posts.length === 0 ? (
          <Card variant="outline" className="p-12 text-center text-sm text-muted-foreground">
            No community discussions found in this category. Be the first to start a topic!
          </Card>
        ) : (
          posts.map((post) => (
            <Card
              key={post.id}
              hoverEffect
              accentTop
              onClick={() => openPost(post)}
              className="cursor-pointer space-y-3 p-6"
            >
              <div className="flex items-center justify-between">
                <Badge variant="primary" size="sm">{post.category}</Badge>
                <span className="font-mono text-[11px] uppercase tracking-[0.08em] text-muted-foreground">
                  {timeAgo(post.created_at)}
                </span>
              </div>

              <h2 className="font-display text-lg font-semibold text-foreground">{post.title}</h2>
              <p className="line-clamp-2 text-sm leading-relaxed text-muted-foreground">{post.content}</p>

              <div className="flex items-center justify-between border-t border-[#e8e4df] pt-2 text-xs text-muted-foreground">
                <span className="font-semibold text-slate-700">👤 {post.author_pseudonym}</span>
                <span>💬 {post.comment_count} Comments</span>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Create Post Modal */}
      {isCreating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-lg border border-[#e8e4df] bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-xl font-semibold text-foreground">Start a Discussion</h2>
              <button onClick={() => setIsCreating(false)} className="cursor-pointer text-xl font-bold text-muted-foreground hover:text-foreground">✕</button>
            </div>

            <div className="mb-4 flex items-center justify-between rounded-md border border-accent/30 bg-accent-muted p-3 text-xs text-foreground">
              <span>Your Identity: <strong>Pseudonymous</strong></span>
              <Badge variant="primary" size="sm" dot>Protected</Badge>
            </div>

            <form onSubmit={handleCreatePost} className="space-y-4">
              <div>
                <label className="mb-1 block font-mono text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Topic Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Dealing with mid-term exam stress"
                  className="w-full rounded-md border border-[#e8e4df] bg-white px-4 py-2.5 text-sm shadow-none transition-all focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15"
                />
              </div>

              <div>
                <label className="mb-1 block font-mono text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="h-12 w-full cursor-pointer appearance-none rounded-md border border-[#e8e4df] bg-white px-4 text-sm shadow-none focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15"
                >
                  {CATEGORIES.filter((c) => c !== 'All').map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="mb-1 block font-mono text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">Message Content</label>
                <textarea
                  required
                  rows={4}
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="Share your thoughts or ask for peer guidance..."
                  className="w-full resize-y rounded-md border border-[#e8e4df] bg-white px-4 py-2.5 text-sm shadow-none transition-all focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15"
                />
              </div>

              {postMsg && (
                <div className="rounded-md bg-muted p-3 text-center text-xs font-semibold text-slate-700">
                  {postMsg}
                </div>
              )}

              <button
                type="submit"
                className="min-h-[44px] w-full cursor-pointer rounded-md bg-accent py-3 font-semibold text-white transition-all duration-200 hover:bg-accent-secondary motion-safe:hover:-translate-y-0.5"
              >
                Post Anonymously
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Active Post & Comments Modal */}
      {activePost && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-lg border border-[#e8e4df] bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <Badge variant="primary" size="sm">{activePost.category}</Badge>
                <h2 className="mt-2 font-display text-xl font-semibold text-foreground">{activePost.title}</h2>
                <div className="mt-1 font-mono text-[11px] uppercase tracking-[0.08em] text-muted-foreground">
                  by {activePost.author_pseudonym} · {timeAgo(activePost.created_at)}
                </div>
              </div>
              <button onClick={() => setActivePost(null)} className="cursor-pointer text-2xl font-bold text-muted-foreground hover:text-foreground">✕</button>
            </div>

            <div className="mb-4 overflow-y-auto whitespace-pre-wrap rounded-md bg-muted p-4 text-sm leading-relaxed text-slate-700">
              {activePost.content}
            </div>

            {/* Comments Thread */}
            <div className="mb-4 flex-1 overflow-y-auto pr-1">
              <div className="rule-line mb-3" aria-hidden="true" />
              <h3 className="small-caps mb-2 text-muted-foreground">
                {activePost.comments?.length ?? 0} Replies · Threaded
              </h3>
              {(!activePost.comments || activePost.comments.length === 0) ? (
                <div className="py-2 text-xs italic text-muted-foreground">No comments yet. Start the conversation below.</div>
              ) : (
                renderThread(activePost.comments, null, 0, startReply)
              )}
            </div>

            {/* Top-level comment form */}
            <form onSubmit={handleAddComment} className="flex gap-2 border-t border-[#e8e4df] pt-3">
              <input
                type="text"
                required
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder={replyTo ? 'Continue the thread...' : 'Write a supportive reply...'}
                className="h-10 flex-1 rounded-md border border-[#e8e4df] bg-white px-4 text-xs shadow-none transition-all focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15"
              />
              <Button size="sm" type="submit">
                {replyTo ? 'Send Reply' : 'Comment'}
              </Button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
