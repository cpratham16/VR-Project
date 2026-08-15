import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';

export default function PanicModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const closeModal = () => setIsOpen(false);

  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeModal();
    };
    document.addEventListener('keydown', onKeyDown);
    closeButtonRef.current?.focus();
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [isOpen]);

  const handlePanicClick = async () => {
    setIsOpen(true);
    try {
      await apiClient.post('/patient/panic', { location_note: 'Campus Emergency Request' });
      setStatusMsg('Campus Doctor & Crisis Team have been notified of your alert.');
    } catch {
      setStatusMsg('Local Crisis Numbers available below. (Offline Mode Active)');
    }
  };

  return (
    <>
      <button
        onClick={handlePanicClick}
        aria-label="Panic SOS — immediately alert crisis support"
        className="bg-red-600 hover:bg-red-700 text-white font-bold px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 animate-pulse cursor-pointer"
        title="Immediate Emergency & Crisis Support"
      >
        <span aria-hidden="true" className="text-xl">🆘</span> Panic SOS
      </button>

      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="panic-dialog-title"
        >
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border-4 border-red-500">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span aria-hidden="true" className="text-3xl">🚨</span>
                <h2 id="panic-dialog-title" className="text-2xl font-bold text-red-600">Immediate Crisis Support</h2>
              </div>
              <button
                ref={closeButtonRef}
                onClick={closeModal}
                aria-label="Close crisis support dialog"
                className="text-gray-600 hover:text-gray-900 text-2xl font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-gray-700 text-sm mb-4">
              If you are in immediate distress or feel unsafe, please connect with one of the emergency services below:
            </p>

            <div className="space-y-3 mb-6">
              <div className="bg-red-50 p-4 rounded-xl border border-red-200">
                <div className="font-semibold text-red-900">Campus Emergency Line</div>
                <div className="text-2xl font-black text-red-700">1800-999-0000</div>
                <div className="text-xs text-red-600">24/7 Campus Medical & Counselor Response</div>
              </div>

              <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
                <div className="font-semibold text-blue-900">Tele-MANAS National Helpline</div>
                <div className="text-2xl font-black text-blue-700">14416 / 1800-599-0019</div>
                <div className="text-xs text-blue-600">Toll-free 24/7 Mental Health Support</div>
              </div>

              <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-200">
                <div className="font-semibold text-emerald-900">Student Crisis Contact</div>
                <div className="text-2xl font-black text-emerald-700">+91 98765 43210</div>
                <div className="text-xs text-emerald-600">Direct On-Call Campus Counselor</div>
              </div>
            </div>

            {statusMsg && (
              <div
                role="status"
                aria-live="polite"
                className="p-3 bg-gray-100 rounded-lg text-center text-xs font-semibold text-gray-700 mb-4"
              >
                {statusMsg}
              </div>
            )}

            <button
              onClick={closeModal}
              className="w-full py-3 bg-gray-800 hover:bg-gray-900 text-white font-bold rounded-lg"
            >
              I Understand — Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}
