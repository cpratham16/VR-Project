import { useCallback, useEffect, useRef, useState } from 'react';

export interface HeartRateData {
  heartRate: number;
  hrvRmssd: number;
}

interface BluetoothRemoteGATTCharacteristic {
  startNotifications(): Promise<BluetoothRemoteGATTCharacteristic>;
  addEventListener(type: string, listener: (e: any) => void): void;
}

interface BluetoothRemoteGATTServer {
  connected: boolean;
  connect(): Promise<BluetoothRemoteGATTServer>;
  disconnect(): void;
  getPrimaryService(service: string): Promise<{ getCharacteristic(char: string): Promise<BluetoothRemoteGATTCharacteristic> }>;
}

interface BluetoothDevice {
  name?: string;
  gatt?: BluetoothRemoteGATTServer;
}

declare global {
  interface Navigator {
    bluetooth?: {
      requestDevice(options: {
        filters: { services: string[] }[];
        optionalServices: string[];
      }): Promise<BluetoothDevice>;
    };
  }
}

const HEART_RATE_SERVICE = 'heart_rate';
const HEART_RATE_MEASUREMENT = 'heart_rate_measurement';

export type HeartRateStatus = 'idle' | 'connecting' | 'connected' | 'simulated' | 'error';

export function useHeartRateMonitor() {
  const [status, setStatus] = useState<HeartRateStatus>('idle');
  const [heartRate, setHeartRate] = useState<number>(72);
  const [hrvRmssd, setHrvRmssd] = useState<number>(48);
  const [deviceName, setDeviceName] = useState<string>('');
  const [error, setError] = useState<string>('');

  const rrIntervals = useRef<{ t: number; v: number }[]>([]);
  const deviceRef = useRef<BluetoothDevice | null>(null);
  const simTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const simStage = useRef(0);

  const stopSimulator = () => {
    if (simTimer.current) {
      clearInterval(simTimer.current);
      simTimer.current = null;
    }
  };

  const startSimulator = () => {
    setStatus('simulated');
    setDeviceName('Simulated Monitor');
    stopSimulator();

    // Resting baseline with periodic stress spikes to mimic exposure stages
    simTimer.current = setInterval(() => {
      const now = Date.now();
      const phase = Math.floor(now / 8000) % 4;
      let hr = 70 + Math.sin(now / 2500) * 4;
      if (phase === 2) {
        hr += 22; // stress spike during an exposure step
      }
      const rr = 60 / hr; // seconds per beat
      setHeartRate(Math.round(hr));
      setHrvRmssd(Math.round(rr * 1000) / 10);
      simStage.current += 1;
    }, 1000);
  };

  const connect = useCallback(async () => {
    setError('');
    const bt = navigator.bluetooth;
    if (!bt) {
      startSimulator();
      return;
    }

    setStatus('connecting');
    try {
      const device = await bt.requestDevice({
        filters: [{ services: [HEART_RATE_SERVICE] }],
        optionalServices: [HEART_RATE_SERVICE],
      });
      deviceRef.current = device;
      setDeviceName(device.name || 'Heart Rate Monitor');

      if (!device.gatt) {
        throw new Error('Device has no GATT server');
      }
      const server = await device.gatt.connect();
      const service = await server.getPrimaryService(HEART_RATE_SERVICE);
      const characteristic = await service.getCharacteristic(HEART_RATE_MEASUREMENT);

      characteristic.addEventListener('characteristicvaluechanged', (event: any) => {
        const value: DataView = event.target.value;
        if (!value) return;
        const flags = value.getUint8(0);
        const hr16 = flags & 0x01;
        let hr: number;
        if (hr16) {
          hr = value.getUint16(1, /* littleEndian */ true);
        } else {
          hr = value.getUint8(1);
        }
        setHeartRate(hr);

        // RR intervals in seconds are present when flags bit 4 (0x10) is set
        const hasRR = flags & 0x10;
        if (hasRR) {
          const rrSamples: number[] = [];
          for (let i = 2; i + 2 <= value.byteLength; i += 2) {
            rrSamples.push(value.getUint16(i, true));
          }
          const now = Date.now();
          const window = rrIntervals.current.filter((t) => now - t.t <= 60000);
          rrSamples.forEach((sample) => window.push({ t: now, v: sample / 1024 }));
          rrIntervals.current = window.slice(-64);
          const diffs: number[] = [];
          for (let i = 1; i < window.length; i++) {
            diffs.push(Math.abs(window[i].v - window[i - 1].v));
          }
          if (diffs.length > 0) {
            const meanSquared = diffs.reduce((a, b) => a + b * b, 0) / diffs.length;
            setHrvRmssd(Math.round(Math.sqrt(meanSquared) * 1000) / 10);
          }
        }
      });

      await characteristic.startNotifications();
      setStatus('connected');
    } catch (e: any) {
      setStatus('error');
      setError(e?.message || 'Unable to connect to heart rate monitor');
    }
  }, []);

  const disconnect = useCallback(() => {
    stopSimulator();
    const device = deviceRef.current;
    if (device?.gatt?.connected) {
      device.gatt.disconnect();
    }
    deviceRef.current = null;
    setStatus('idle');
    setDeviceName('');
    setHeartRate(72);
    setHrvRmssd(48);
  }, []);

  useEffect(() => {
    return () => {
      stopSimulator();
      const device = deviceRef.current;
      if (device?.gatt?.connected) {
        device.gatt.disconnect();
      }
    };
  }, []);

  return { status, heartRate, hrvRmssd, deviceName, error, connect, disconnect };
}
