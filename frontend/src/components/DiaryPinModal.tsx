import { useState, useEffect, useRef } from 'react';
import { apiClient } from '../api/client';
import { Button, Input } from './ui';

interface DiaryPinModalProps {
  isOpen: boolean;
  onClose: () => void;
  onVerify: () => void;
  mode?: 'verify' | 'setup' | 'change';
}

export default function DiaryPinModal({ isOpen, onClose, onVerify, mode = 'verify' }: DiaryPinModalProps) {
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  // const [pinStatus, setPinStatus] = useState<'checking' | 'has_pin' | 'no_pin'>('checking');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen, mode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (mode === 'setup' || mode === 'change') {
      if (pin.length < 4 || pin.length > 8) {
        setError('PIN must be 4-8 digits');
        return;
      }
      if (pin !== confirmPin) {
        setError('PINs do not match');
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === 'verify') {
        await apiClient.post('/patient/diary/privacy/pin/verify', { pin });
        onVerify();
      } else if (mode === 'setup') {
        await apiClient.post('/patient/diary/privacy/pin', { pin });
        onVerify();
      } else if (mode === 'change') {
        await apiClient.put('/patient/diary/privacy/pin', { pin });
        onClose();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pin-modal-title"
    >
      <div className="w-full max-w-md rounded-2xl border border-[#e8e4df] bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-center gap-3">
          <span
            aria-hidden="true"
            className="flex h-11 w-11 items-center justify-center rounded-md bg-muted text-2xl"
          >
            🔒
          </span>
          <div>
            <h2 id="pin-modal-title" className="font-display text-xl font-bold text-foreground">
              {mode === 'verify' ? 'Enter Diary PIN' : mode === 'setup' ? 'Set Diary PIN' : 'Change Diary PIN'}
            </h2>
            <p className="text-sm text-muted-foreground">
              {mode === 'verify' 
                ? 'Enter your 4-8 digit PIN to access your diary'
                : mode === 'setup'
                ? 'Create a 4-8 digit PIN to protect your diary'
                : 'Enter your new 4-8 digit PIN'}
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 text-sm text-red-700 bg-red-100 rounded-lg" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            ref={inputRef}
            type="password"
            label="PIN"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            placeholder="Enter PIN"
            inputMode="numeric"
            pattern="[0-9]*"
            required
            autoComplete="off"
            autoFocus
          />
          {(mode === 'setup' || mode === 'change') && (
            <Input
              type="password"
              label="Confirm PIN"
              value={confirmPin}
              onChange={(e) => setConfirmPin(e.target.value)}
              placeholder="Confirm PIN"
              inputMode="numeric"
              pattern="[0-9]*"
              required
              autoComplete="off"
            />
          )}

          <div className="flex justify-end space-x-3 pt-2">
            <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={loading}>
              {mode === 'verify' ? 'Unlock' : mode === 'setup' ? 'Set PIN' : 'Change PIN'}
            </Button>
          </div>
        </form>

        {(mode === 'verify' || mode === 'change') && (
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Don't have a PIN? <button onClick={onClose} className="text-accent hover:underline">Cancel</button>
          </p>
        )}
      </div>
    </div>
  );
}