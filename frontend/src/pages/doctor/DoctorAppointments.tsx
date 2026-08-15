import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';

interface DoctorAppointment {
  id: string;
  patient_id: string;
  doctor_id?: string;
  scheduled_at: string;
  status: 'requested' | 'confirmed' | 'completed' | 'cancelled';
  reason?: string;
  created_at: string;
  patient_email?: string;
  patient_pseudonym?: string;
}

export default function DoctorAppointmentsPage() {
  const navigate = useNavigate();

  const [appointments, setAppointments] = useState<DoctorAppointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  useEffect(() => {
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.get('/doctor/appointments');
      setAppointments(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load appointments queue.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (apptId: string, newStatus: string) => {
    try {
      await apiClient.put(`/doctor/appointments/${apptId}/status`, { status: newStatus });
      await fetchAppointments();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update status');
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

  const filteredAppointments = appointments.filter((a) => {
    if (statusFilter === 'all') return true;
    return a.status === statusFilter;
  });

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Back Link */}
      <button
        onClick={() => navigate('/doctor/dashboard')}
        className="text-xs font-medium text-teal-700 hover:text-teal-800 flex items-center space-x-1"
      >
        <span>← Back to Clinical Triage</span>
      </button>

      {/* Title */}
      <div className="bg-white p-6 rounded-lg shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Counseling Schedule & Queue</h2>
          <p className="text-sm text-gray-600 mt-1">Review student appointment requests and confirm consultation times.</p>
        </div>

        {/* Filter */}
        <div className="flex flex-wrap gap-1">
          {['all', 'requested', 'confirmed', 'completed', 'cancelled'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 text-xs font-medium rounded-full border capitalize transition ${
                statusFilter === st
                  ? 'bg-teal-600 text-white border-teal-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {error && <div className="p-4 text-sm text-red-700 bg-red-100 rounded-lg">{error}</div>}

      {/* Appointments List / Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-gray-500 text-sm">Loading appointment queue...</div>
        ) : filteredAppointments.length === 0 ? (
          <div className="p-12 text-center text-gray-400 text-sm">No appointments in this queue category.</div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredAppointments.map((appt) => (
              <div key={appt.id} className="p-4 sm:p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-3">
                    <span className="font-semibold text-gray-900 text-base">
                      {appt.patient_pseudonym || 'Anonymous Student'}
                    </span>
                    <span className="text-xs text-gray-400">({appt.patient_email})</span>
                    <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full border capitalize ${getStatusBadge(appt.status)}`}>
                      {appt.status}
                    </span>
                  </div>

                  <p className="text-sm font-medium text-teal-800">
                    Scheduled Slot: {new Date(appt.scheduled_at).toLocaleString(undefined, {
                      weekday: 'short',
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>

                  {appt.reason && (
                    <p className="text-xs text-gray-600 italic bg-gray-50 p-2 rounded border border-gray-100 max-w-xl">
                      "{appt.reason}"
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  {appt.status === 'requested' && (
                    <button
                      onClick={() => handleUpdateStatus(appt.id, 'confirmed')}
                      className="px-3 py-1.5 bg-teal-600 text-white text-xs font-medium rounded hover:bg-teal-700 transition"
                    >
                      Confirm Slot
                    </button>
                  )}
                  {appt.status === 'confirmed' && (
                    <button
                      onClick={() => handleUpdateStatus(appt.id, 'completed')}
                      className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 transition"
                    >
                      Mark Completed
                    </button>
                  )}
                  {appt.status !== 'cancelled' && appt.status !== 'completed' && (
                    <button
                      onClick={() => handleUpdateStatus(appt.id, 'cancelled')}
                      className="px-3 py-1.5 bg-red-50 text-red-700 border border-red-200 text-xs font-medium rounded hover:bg-red-100 transition"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
