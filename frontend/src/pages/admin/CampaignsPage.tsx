import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';

interface Recipient {
  id: string;
  user_id: string;
  email: string;
  status: string;
  sent_at?: string;
  error_message?: string;
}

interface Campaign {
  id: string;
  title: string;
  subject: string;
  body_html: string;
  audience_type: string;
  delivery_channels: string;
  status: string;
  scheduled_at?: string;
  sent_at?: string;
  created_at: string;
  recipient_count?: number;
  recipients?: Recipient[];
}

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);

  // Form state
  const [title, setTitle] = useState('');
  const [subject, setSubject] = useState('');
  const [bodyHtml, setBodyHtml] = useState('');
  const [audienceType, setAudienceType] = useState('all');
  const [deliveryChannels, setDeliveryChannels] = useState('email,in_app');

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.get('/campaigns');
      setCampaigns(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    try {
      await apiClient.post('/campaigns', {
        title,
        subject,
        body_html: bodyHtml,
        audience_type: audienceType,
        delivery_channels: deliveryChannels,
      });
      setSuccessMsg('Campaign created successfully in draft mode.');
      setShowCreateModal(false);
      setTitle('');
      setSubject('');
      setBodyHtml('');
      setAudienceType('all');
      fetchCampaigns();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create campaign');
    }
  };

  const handleSendCampaign = async (campaignId: string) => {
    if (!confirm('Are you sure you want to dispatch this communication campaign now?')) return;
    setError('');
    setSuccessMsg('');
    try {
      const res = await apiClient.post(`/campaigns/${campaignId}/send`);
      setSuccessMsg(`Campaign dispatched to ${res.data.recipient_count} verified opt-in recipient(s).`);
      fetchCampaigns();
      if (selectedCampaign && selectedCampaign.id === campaignId) {
        setSelectedCampaign(res.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send campaign');
    }
  };

  const handleViewDetails = async (campaignId: string) => {
    try {
      const res = await apiClient.get(`/campaigns/${campaignId}`);
      setSelectedCampaign(res.data);
    } catch {
      alert('Failed to load campaign details');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header Bar */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Communication Campaigns</h2>
          <p className="text-sm text-gray-600 mt-1">
            Create, schedule, and dispatch non-clinical campus announcements and wellness newsletters.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-accent text-white text-xs font-bold rounded-md hover:bg-teal-700 transition"
        >
          + Create New Campaign
        </button>
      </div>

      {/* Privacy Safeguard Banner (N8 Compliance) */}
      <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-lg flex items-start gap-3">
        <span className="text-lg">[PRIVACY]</span>
        <div className="text-xs text-emerald-900 space-y-1">
          <span className="font-bold">DPDP & Clinical Privacy Safeguards Enforced:</span>
          <p>
            Audience selection is strictly limited to non-clinical role classifications (All, Students, Doctors, Admins).
            Clinical indicators (assessment scores, mood data, diary text) are completely isolated and barred from campaign targeting.
            Recipients who have opted out via communication preferences are automatically excluded.
          </p>
        </div>
      </div>

      {error && <div className="p-4 text-sm text-red-700 bg-red-100 rounded-lg">{error}</div>}
      {successMsg && <div className="p-4 text-sm text-emerald-700 bg-emerald-100 rounded-lg">{successMsg}</div>}

      {/* Campaign List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-500 text-sm">Loading campaigns...</div>
        ) : campaigns.length === 0 ? (
          <div className="p-12 text-center text-gray-400 text-sm">No communication campaigns created yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-600">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 font-semibold">Title & Subject</th>
                  <th className="px-6 py-3 font-semibold">Audience</th>
                  <th className="px-6 py-3 font-semibold">Status</th>
                  <th className="px-6 py-3 font-semibold">Recipients</th>
                  <th className="px-6 py-3 font-semibold">Created / Sent Date</th>
                  <th className="px-6 py-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {campaigns.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 font-medium text-gray-900">
                      <div>{c.title}</div>
                      <div className="text-xs text-gray-400 font-normal">Subject: {c.subject}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-teal-50 text-teal-800 border border-teal-200 capitalize">
                        {c.audience_type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2 py-0.5 text-xs font-bold rounded ${
                          c.status === 'sent'
                            ? 'bg-emerald-100 text-emerald-800'
                            : c.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {c.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs font-semibold text-gray-700">
                      {c.recipient_count ?? 0} users
                    </td>
                    <td className="px-6 py-4 text-xs text-gray-500">
                      {c.sent_at
                        ? `Sent: ${new Date(c.sent_at).toLocaleString()}`
                        : `Created: ${new Date(c.created_at).toLocaleDateString()}`}
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        onClick={() => handleViewDetails(c.id)}
                        className="px-2.5 py-1 bg-gray-100 text-gray-700 hover:bg-gray-200 text-xs font-medium rounded"
                      >
                        Details
                      </button>
                      {c.status !== 'sent' && (
                        <button
                          onClick={() => handleSendCampaign(c.id)}
                          className="px-3 py-1 bg-emerald-600 text-white hover:bg-emerald-700 text-xs font-bold rounded shadow-sm"
                        >
                          Send Now
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Campaign Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-xl w-full p-6 space-y-5 shadow-xl">
            <div className="flex justify-between items-center border-b border-gray-100 pb-3">
              <h3 className="text-lg font-bold text-gray-800">Create Communication Campaign</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-gray-400 hover:text-gray-600 font-bold">
                x
              </button>
            </div>

            <form onSubmit={handleCreateCampaign} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-gray-700 mb-1">Campaign Title (Internal Reference)</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Midterm Stress Support Outreach"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-accent focus:border-accent"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Email Subject Line</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Free Counseling & VR Workshops Available This Week"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-accent focus:border-accent"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Audience Targeting (Privacy Safeguarded)</label>
                <select
                  value={audienceType}
                  onChange={(e) => setAudienceType(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded bg-white text-gray-700"
                >
                  <option value="all">All Registered Accounts (Students + Staff)</option>
                  <option value="students">Student Members Only</option>
                  <option value="doctors">Clinical Staff & Doctors Only</option>
                  <option value="admins">Administrators Only</option>
                </select>
                <p className="text-[11px] text-gray-400 mt-1">
                  * Targeting by clinical criteria (PHQ-9 score, mood logs, etc.) is strictly disabled.
                </p>
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Delivery Channels</label>
                <select
                  value={deliveryChannels}
                  onChange={(e) => setDeliveryChannels(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded bg-white text-gray-700"
                >
                  <option value="email,in_app">Email + In-App Notification</option>
                  <option value="email">Email Only</option>
                  <option value="in_app">In-App Notification Only</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Body Content (HTML / Text)</label>
                <textarea
                  rows={5}
                  required
                  placeholder="Enter campaign body content..."
                  value={bodyHtml}
                  onChange={(e) => setBodyHtml(e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded focus:ring-accent focus:border-accent font-mono text-xs"
                ></textarea>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-accent text-white font-bold rounded hover:bg-teal-700">
                  Save as Draft
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Campaign Details & Recipient Log Modal */}
      {selectedCampaign && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6 space-y-5 shadow-xl max-h-[90vh] overflow-y-auto text-xs">
            <div className="flex justify-between items-start border-b border-gray-100 pb-3">
              <div>
                <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-teal-100 text-teal-800 rounded">
                  {selectedCampaign.status}
                </span>
                <h3 className="text-lg font-bold text-gray-800 mt-1">{selectedCampaign.title}</h3>
                <p className="text-gray-500">Subject: {selectedCampaign.subject}</p>
              </div>
              <button onClick={() => setSelectedCampaign(null)} className="text-gray-400 hover:text-gray-600 font-bold">
                x
              </button>
            </div>

            <div className="space-y-3 bg-gray-50 p-4 rounded border border-gray-200">
              <div className="grid grid-cols-2 gap-2 text-gray-600">
                <div>
                  <span className="font-semibold text-gray-800">Target Audience:</span> {selectedCampaign.audience_type}
                </div>
                <div>
                  <span className="font-semibold text-gray-800">Channels:</span> {selectedCampaign.delivery_channels}
                </div>
                <div>
                  <span className="font-semibold text-gray-800">Created:</span>{' '}
                  {new Date(selectedCampaign.created_at).toLocaleString()}
                </div>
                <div>
                  <span className="font-semibold text-gray-800">Sent:</span>{' '}
                  {selectedCampaign.sent_at ? new Date(selectedCampaign.sent_at).toLocaleString() : 'Not sent yet'}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-bold text-gray-800">Campaign Body Preview</h4>
              <div className="p-3 border border-gray-200 rounded bg-white text-gray-700 font-mono whitespace-pre-wrap">
                {selectedCampaign.body_html}
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-bold text-gray-800">
                Recipient Log ({selectedCampaign.recipients?.length || 0})
              </h4>
              {!selectedCampaign.recipients || selectedCampaign.recipients.length === 0 ? (
                <p className="text-gray-400 italic">No recipient logs found (campaign has not been dispatched).</p>
              ) : (
                <div className="max-h-48 overflow-y-auto border border-gray-200 rounded">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-gray-100 text-gray-500 uppercase">
                      <tr>
                        <th className="p-2">Email</th>
                        <th className="p-2">Status</th>
                        <th className="p-2">Sent Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {selectedCampaign.recipients.map((r) => (
                        <tr key={r.id}>
                          <td className="p-2 text-gray-800 font-medium">{r.email}</td>
                          <td className="p-2">
                            <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-800 text-[10px] rounded font-bold">
                              {r.status}
                            </span>
                          </td>
                          <td className="p-2 text-gray-400">
                            {r.sent_at ? new Date(r.sent_at).toLocaleTimeString() : '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="flex justify-between items-center border-t border-gray-100 pt-3">
              {selectedCampaign.status !== 'sent' ? (
                <button
                  onClick={() => handleSendCampaign(selectedCampaign.id)}
                  className="px-4 py-1.5 bg-emerald-600 text-white font-bold rounded hover:bg-emerald-700"
                >
                  Send Campaign Now
                </button>
              ) : (
                <span className="text-xs text-emerald-600 font-bold">[COMPLETED] Dispatched</span>
              )}
              <button
                onClick={() => setSelectedCampaign(null)}
                className="px-4 py-1.5 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
