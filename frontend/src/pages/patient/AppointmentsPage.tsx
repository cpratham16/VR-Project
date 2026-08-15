import { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';

interface Appointment {
  id: string;
  patient_id: string;
  doctor_id?: string;
  scheduled_at: string;
  status: 'requested' | 'confirmed' | 'completed' | 'cancelled';
  reason?: string;
  created_at: string;
}

export default function PatientAppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [scheduledAt, setScheduledAt] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    setFetching(true);
    setError('');
    try {
      const res = await apiClient.get('/patient/appointments');
      setAppointments(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load appointments.');
    } finally {
      setFetching(false);
    }
  };

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!scheduledAt) {
      setError('Please select a date and time.');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/patient/appointments', {
        scheduled_at: new Date(scheduledAt).toISOString(),
        reason: reason
      });
      setSuccess('Appointment request submitted successfully!');
      setScheduledAt('');
      setReason('');
      await fetchAppointments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to book appointment.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'confirmed':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'requested':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'completed':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'cancelled':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Title */}
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <h2 className="text-2xl font-bold text-gray-800">Schedule Counseling Session</h2>
        <p className="text-sm text-gray-600 mt-1">
          Request a consultation slot with an assigned campus mental health doctor or counselor.
        </p>
      </div>

      {error && <div className="p-4 text-sm text-red-700 bg-red-100 rounded-lg">{error}</div>}
      {success && <div className="p-4 text-sm text-emerald-700 bg-emerald-100 rounded-lg">{success}</div>}

      {/* Booking Form */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
        <h3 className="text-lg font-semibold text-gray-800">Request New Slot</h3>
        <form onSubmit={handleBook} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Preferred Date & Time</label>
            <input
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              required
              className="w-full sm:w-80 px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-teal-500 focus:border-teal-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reason / Session Notes <span className="text-xs text-gray-400 font-normal">(Optional)</span>
            </label>
            <textarea
              rows={2}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Follow-up on PHQ-9 results, coping strategies, or stress management..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-teal-500 focus:border-teal-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 bg-teal-600 text-white font-medium text-sm rounded-md shadow hover:bg-teal-700 transition disabled:opacity-50"
          >
            {loading ? 'Submitting Request...' : 'Submit Appointment Request'}
          </button>
        </form>
      </div>

      {/* Appointment History List */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
        <h3 className="text-lg font-semibold text-gray-800">My Appointments</h3>

        {fetching ? (
          <p className="text-sm text-gray-500">Loading appointments...</p>
        ) : appointments.length === 0 ? (
          <p className="text-sm text-gray-400">No appointments requested yet.</p>
        ) : (
          <div className="divide-y divide-gray-100">
            {appointments.map((appt) => (
              <div key={appt.id} className="py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-semibold text-gray-800">
                      {new Date(appt.scheduled_at).toLocaleString(undefined, {
                        weekday: 'short',
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                    <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border capitalize ${getStatusBadge(appt.status)}`}>
                      {appt.status}
                    </span>
                  </div>
                  {appt.reason && <p className="text-xs text-gray-600 mt-1 italic">"{appt.reason}"</p>}
                </div>
                <span className="text-xs text-gray-400">Requested: {new Date(appt.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
