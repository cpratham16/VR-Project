import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';

interface ResourceProgress {
  id: string;
  resource_id: string;
  saved_for_later: boolean;
  progress_percent: number;
  is_completed: boolean;
}

interface Resource {
  id: string;
  title: string;
  description?: string;
  resource_type: string;
  category: string;
  file_url?: string;
  thumbnail_url?: string;
  author?: string;
  is_published: boolean;
  progress?: ResourceProgress;
}

export default function WellnessLibraryPage() {
  const [resources, setResources] = useState<Resource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [savedOnly, setSavedOnly] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');

  const [selectedResource, setSelectedResource] = useState<Resource | null>(null);
  const [readingProgress, setReadingProgress] = useState<number>(0);

  useEffect(() => {
    fetchLibrary();
  }, [categoryFilter, savedOnly]);

  const fetchLibrary = async () => {
    setLoading(true);
    setError('');
    try {
      const catParam = categoryFilter !== 'all' ? `&category=${categoryFilter}` : '';
      const savedParam = savedOnly ? `&saved_only=true` : '';
      const res = await apiClient.get(`/resources/my-library?${catParam}${savedParam}`);
      setResources(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load library resources');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSave = async (resourceId: string, currentSaved: boolean) => {
    try {
      await apiClient.post(`/resources/${resourceId}/progress`, {
        saved_for_later: !currentSaved,
      });
      fetchLibrary();
    } catch {
      alert('Failed to update saved status');
    }
  };

  const handleOpenReader = (resource: Resource) => {
    setSelectedResource(resource);
    setReadingProgress(resource.progress?.progress_percent || 0);
  };

  const handleUpdateProgress = async (resourceId: string, percent: number) => {
    try {
      await apiClient.post(`/resources/${resourceId}/progress`, {
        progress_percent: percent,
        is_completed: percent >= 100,
      });
      fetchLibrary();
      if (selectedResource && selectedResource.id === resourceId) {
        setSelectedResource((prev) =>
          prev
            ? {
                ...prev,
                progress: {
                  id: prev.progress?.id || '',
                  resource_id: resourceId,
                  saved_for_later: prev.progress?.saved_for_later || false,
                  progress_percent: percent,
                  is_completed: percent >= 100,
                },
              }
            : null
        );
      }
    } catch {
      alert('Failed to update progress');
    }
  };

  const filteredResources = resources.filter((r) => {
    const term = searchTerm.toLowerCase();
    const titleMatch = r.title.toLowerCase().includes(term);
    const authorMatch = (r.author || '').toLowerCase().includes(term);
    return titleMatch || authorMatch;
  });

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Student Wellness Library</h2>
          <p className="text-sm text-gray-600 mt-1">
            Explore curated mental health guides, self-help books, articles, and audio-visual tools.
          </p>
        </div>
        <button
          onClick={() => setSavedOnly(!savedOnly)}
          className={`px-4 py-2 text-sm rounded-md font-medium border transition ${
            savedOnly
              ? 'bg-accent text-white border-teal-600 shadow-sm'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
          }`}
        >
          {savedOnly ? 'Show All Resources' : 'Saved for Later'}
        </button>
      </div>

      {/* Filter and Control Bar */}
      <div className="bg-white p-4 rounded-lg shadow-sm flex flex-col md:flex-row justify-between gap-4 border border-gray-200">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold text-gray-500">Categories:</span>
          {['all', 'anxiety', 'mindfulness', 'sleep', 'academic', 'general'].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1 text-xs font-medium rounded-full border transition capitalize ${
                categoryFilter === cat
                  ? 'bg-accent text-white border-teal-600 shadow-sm'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <input
          type="text"
          placeholder="Search by title or author..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-3 py-1.5 border border-gray-300 rounded-md text-xs w-full md:w-64 focus:ring-accent focus:border-accent"
        />
      </div>

      {error && <div className="p-4 text-sm text-red-700 bg-red-100 rounded-lg">{error}</div>}

      {/* Resource Grid */}
      {loading ? (
        <div className="bg-white p-12 text-center text-gray-500 text-sm rounded-lg border border-gray-200">
          Loading library resources...
        </div>
      ) : filteredResources.length === 0 ? (
        <div className="bg-white p-12 text-center text-gray-400 text-sm rounded-lg border border-gray-200">
          No resources found matching your search or category filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredResources.map((res) => {
            const isSaved = res.progress?.saved_for_later || false;
            const progressPct = res.progress?.progress_percent || 0;
            const isCompleted = res.progress?.is_completed || false;

            return (
              <div
                key={res.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col justify-between overflow-hidden hover:shadow-md transition"
              >
                <div className="p-5 space-y-3">
                  <div className="flex justify-between items-start gap-2">
                    <span className="px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                      {res.category} | {res.resource_type}
                    </span>
                    <button
                      onClick={() => handleToggleSave(res.id, isSaved)}
                      className={`text-xs px-2 py-1 rounded transition ${
                        isSaved
                          ? 'bg-amber-100 text-amber-800 font-bold border border-amber-300'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                      title={isSaved ? 'Remove from Saved' : 'Save for Later'}
                    >
                      {isSaved ? '[SAVED]' : '+ Save'}
                    </button>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-gray-800 line-clamp-1">{res.title}</h3>
                    {res.author && <p className="text-xs text-gray-500 mt-0.5">By {res.author}</p>}
                  </div>

                  <p className="text-xs text-gray-600 line-clamp-3">
                    {res.description || 'No description provided.'}
                  </p>

                  {/* Progress Indicator */}
                  <div className="space-y-1 pt-2">
                    <div className="flex justify-between items-center text-[11px] font-medium text-gray-500">
                      <span>Reading Progress</span>
                      {isCompleted ? (
                        <span className="text-emerald-600 font-bold">[COMPLETED]</span>
                      ) : (
                        <span>{progressPct}%</span>
                      )}
                    </div>
                    <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden border border-gray-200">
                      <div
                        className={`h-full transition-all duration-300 ${
                          isCompleted ? 'bg-emerald-500' : 'bg-teal-600'
                        }`}
                        style={{ width: `${progressPct}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 border-t border-gray-100 flex justify-between items-center">
                  {res.file_url ? (
                    <a
                      href={res.file_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-teal-700 hover:underline font-semibold"
                    >
                      Download Document
                    </a>
                  ) : (
                    <span className="text-xs text-gray-400">Digital Resource</span>
                  )}

                  <button
                    onClick={() => handleOpenReader(res)}
                    className="px-3 py-1.5 bg-accent text-white text-xs font-semibold rounded hover:bg-teal-700 transition"
                  >
                    Open Resource
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Resource Reader Modal */}
      {selectedResource && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6 space-y-6 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start">
              <div>
                <span className="px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider rounded-full bg-teal-50 text-teal-700 border border-teal-200">
                  {selectedResource.category} | {selectedResource.resource_type}
                </span>
                <h3 className="text-xl font-bold text-gray-800 mt-2">{selectedResource.title}</h3>
                {selectedResource.author && (
                  <p className="text-xs text-gray-500 mt-0.5">Author: {selectedResource.author}</p>
                )}
              </div>
              <button
                onClick={() => setSelectedResource(null)}
                className="text-gray-400 hover:text-gray-600 text-lg font-bold"
              >
                x
              </button>
            </div>

            <div className="space-y-4 text-sm text-gray-700 leading-relaxed border-y border-gray-100 py-4">
              <p>{selectedResource.description || 'No detailed content available for this resource.'}</p>
              {selectedResource.file_url && (
                <div className="p-3 bg-muted rounded-md flex items-center justify-between border border-[#e8e4df]">
                  <span className="text-xs font-medium text-gray-700">Attached File / Document</span>
                  <a
                    href={selectedResource.file_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 bg-accent text-white text-xs font-semibold rounded hover:bg-teal-700"
                  >
                    View File
                  </a>
                </div>
              )}
            </div>

            {/* Reading Progress Controls */}
            <div className="space-y-3 bg-gray-50 p-4 rounded-lg border border-gray-200">
              <div className="flex justify-between items-center text-xs font-semibold text-gray-700">
                <span>Update Reading Progress</span>
                <span>{readingProgress}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                step="10"
                value={readingProgress}
                onChange={(e) => setReadingProgress(Number(e.target.value))}
                className="w-full accent-accent"
              />
              <div className="flex justify-between items-center pt-2">
                <button
                  onClick={() => handleUpdateProgress(selectedResource.id, readingProgress)}
                  className="px-4 py-1.5 bg-accent text-white text-xs font-semibold rounded hover:bg-teal-700"
                >
                  Save Progress
                </button>
                <button
                  onClick={() => handleUpdateProgress(selectedResource.id, 100)}
                  className="px-4 py-1.5 bg-emerald-600 text-white text-xs font-semibold rounded hover:bg-emerald-700"
                >
                  Mark as Completed (100%)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
