import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';
import HelplineCards from './HelplineCards';

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
      await apiClient.post('/patient/panic', { location_note: 'Panic SOS from platform' });
      setStatusMsg('Your counselor and on-call crisis team have been notified of your alert.');
    } catch {
      setStatusMsg('Local Crisis Numbers available below. (Offline Mode Active)');
    }
  };

  return (
    <>
      <div className="relative">
        <div
          aria-hidden="true"
          className="absolute inset-0 rounded-full bg-red-500/60 animate-ping"
        />
        <button
          onClick={handlePanicClick}
          aria-label="Panic SOS — immediately alert crisis support"
          className="relative flex h-14 w-14 items-center justify-center rounded-full bg-red-600 text-white shadow-lg cursor-pointer transition-all duration-200 hover:bg-red-700 hover:scale-105 hover:shadow-xl focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-red-500/50"
          title="Immediate Emergency & Crisis Support"
        >
          <span aria-hidden="true" className="text-2xl">🆘</span>
        </button>
      </div>

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
              If you are struggling or in immediate distress, you do not have to face it alone. These services are
              free, confidential, and available right now:
            </p>

            <div className="mb-6">
              <HelplineCards />
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

            <p className="mb-4 text-[11px] leading-relaxed text-gray-500">
              Mindora's automated safety system also alerts your emergency contact and on-call counselors if a serious
              risk is detected — but these hotlines are always the fastest route to a human being.
            </p>

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
