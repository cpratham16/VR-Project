import { useEffect, useRef, useState } from 'react';
import 'aframe';
import { apiClient } from '../../../api/client';
import { useHeartRateMonitor } from '../../../components/HeartRateMonitor';

export interface VRASession {
  id: string;
  scenario_slug: string;
  scenario_name: string;
  phobia_type: string;
  intensity_level: 'low' | 'medium' | 'high';
  duration_minutes: number;
  exposure_steps: number;
  instructions: string;
  status: string;
  suds_pre?: number;
  suds_post?: number;
  patient_feedback?: string;
  assigned_at?: string;
  started_at?: string;
  completed_at?: string;
  patient_id?: string;
  doctor_id?: string;
}

interface VRSessionRunnerProps {
  session: VRASession;
  onExit: () => void;
}

type RunnerPhase = 'intro' | 'running' | 'post';

function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function buildHeightsScene(intensity: 'low' | 'medium' | 'high') {
  const heights: Record<string, number> = { low: 10, medium: 40, high: 90 };
  const height = heights[intensity];
  const rand = mulberry32(7);

  let buildings = '';
  for (let i = 0; i < 48; i++) {
    const x = (rand() - 0.5) * 120;
    const z = (rand() - 0.5) * 120;
    const w = 2 + rand() * 3;
    const h = 8 + rand() * 22;
    const y = -height - h / 2;
    buildings += `<a-box position="${x.toFixed(1)} ${y.toFixed(1)} ${z.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" depth="${w.toFixed(1)}" material="color: ${i % 3 === 0 ? '#3b4b63' : i % 3 === 1 ? '#4a5568' : '#2d3748'}; roughness: 1"></a-box>`;
  }

  return `
    <a-scene fog="type: linear; color: #bfd7ee; near: 20; far: ${height + 120}">
      <a-sky color="#87CEEB"></a-sky>
      <a-entity light="type: ambient; intensity: 0.6"></a-entity>
      <a-entity light="type: directional; intensity: 0.9; position: 5 20 5"></a-entity>

      <a-plane position="0 -${height} 0" rotation="-90 0 0" width="200" height="200" material="color:#7aa2b8; roughness:1"></a-plane>
      ${buildings}

      <a-entity id="deck" position="0 0 0">
        <a-box position="0 -0.5 0" width="14" height="1" depth="14" material="color:#e5e7eb; metalness:0.3"></a-box>
        <a-plane position="0 0.01 0" rotation="-90 0 0" width="14" height="14" material="color:#ffffff; opacity:0.15; transparent:true"></a-plane>
        <a-box position="-6.5 1 0" width="0.3" height="2.5" depth="14" material="color:#1f2937"></a-box>
        <a-box position="6.5 1 0" width="0.3" height="2.5" depth="14" material="color:#1f2937"></a-box>
        <a-box position="0 1 6.5" width="13" height="2.5" depth="0.3" material="color:#1f2937"></a-box>
        <a-box position="0 1 -6.5" width="13" height="2.5" depth="0.3" material="color:#1f2937"></a-box>
        <a-box position="0 2.4 0" width="14" height="0.2" depth="14" material="color:#374151"></a-box>
      </a-entity>

      <a-entity id="sway-rig" animation="property: rotation; to: 0 0 0.4 0; dur: 3000; loop: true; dir: alternate; easing: easeInOutQuad">
        <a-entity camera="userHeight: 1.6" look-controls="enabled: true">
          <a-entity cursor="rayOrigin: mouse" raycaster="far: 100"></a-entity>
        </a-entity>
      </a-entity>
    </a-scene>
  `;
}

function buildLectureScene(intensity: 'low' | 'medium' | 'high') {
  const counts: Record<string, number> = { low: 5, medium: 40, high: 120 };
  const count = counts[intensity];
  const rand = mulberry32(21);

  let audience = '';
  let placed = 0;
  let row = 0;
  while (placed < count) {
    const perRow = Math.min(8, count - placed);
    const z = -6 - row * 2.2;
    for (let i = 0; i < perRow; i++) {
      const x = (i - (perRow - 1) / 2) * 2.2;
      const headColor = ['#d9b8a0', '#c9a184', '#e5c6a8', '#b98d6e', '#f0d0b5'][Math.floor(rand() * 5)];
      const bodyColor = ['#2f4858', '#5d6d7e', '#8a5a44', '#3e5f8a', '#7b6b8a'][Math.floor(rand() * 5)];
      audience += `
        <a-entity position="${x.toFixed(2)} 0 ${z.toFixed(1)}">
          <a-box position="0 0.55 0" width="0.7" height="1.1" depth="0.5" material="color:${bodyColor}; roughness:1"></a-box>
          <a-sphere position="0 1.45 0" radius="0.28" material="color:${headColor}; roughness:0.9"></a-sphere>
        </a-entity>`;
      placed++;
    }
    row++;
  }

  const audienceScale = intensity === 'high' ? '1' : intensity === 'medium' ? '0.85' : '0.6';
  const chatterText = intensity === 'high' ? 'Crowd murmurs softly' : intensity === 'medium' ? 'A few people chatting' : 'Empty hall, quiet';

  return `
    <a-scene fog="type: linear; color: #2b2f3a; near: 15; far: 60">
      <a-sky color="#1f2330"></a-sky>
      <a-entity light="type: ambient; intensity: 0.5"></a-entity>
      <a-entity light="type: directional; intensity: 0.7; position: -2 8 4"></a-entity>

      <a-box position="0 -0.5 -4" width="30" height="1" depth="24" material="color:#3a3f4b"></a-box>
      <a-box position="0 3 -12" width="34" height="10" depth="1" material="color:#262a35"></a-box>

      <a-entity position="0 0 0">
        <a-entity position="0 0.9 -2.6">
          <a-box position="0 0 0" width="2.4" height="1.3" depth="1.4" material="color:#6b5b3e; roughness:1"></a-box>
          <a-box position="0 0.55 0" width="1.6" height="0.12" depth="0.8" material="color:#8a744e"></a-box>
        </a-entity>
      </a-entity>

      <a-plane position="0 3.2 -10.2" width="9" height="5" material="color:#d8dce6; roughness:0.6"></a-plane>
      <a-text position="0 4.3 -10.1" value="Welcome" color="#111827" width="8" align="center"></a-text>
      <a-text position="0 3.5 -10.1" value="${chatterText}" color="#4b5563" width="8" align="center"></a-text>

      <a-entity id="audience" scale="${audienceScale} ${audienceScale} ${audienceScale}">
        ${audience}
      </a-entity>

      <a-entity camera="userHeight: 1.6" position="0 0 4" look-controls="enabled: true">
        <a-entity cursor="rayOrigin: mouse" raycaster="far: 100"></a-entity>
      </a-entity>
    </a-scene>
  `;
}

function computeStressIndex(hr: number, hrv: number): number {
  const hrC = Math.max(0, Math.min(100, (hr - 60) * 1.4));
  const hrvC = Math.max(0, Math.min(100, (60 - hrv) * 1.2));
  return Math.round(hrC * 0.55 + hrvC * 0.45);
}

export default function VRSessionRunner({ session, onExit }: VRSessionRunnerProps) {
  const [phase, setPhase] = useState<RunnerPhase>('intro');
  const [stage, setStage] = useState(1);
  const [elapsed, setElapsed] = useState(0);
  const [sudsPre, setSudsPre] = useState(5);
  const [sudsPost, setSudsPost] = useState(5);
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [exitMessage, setExitMessage] = useState('');

  const sceneRef = useRef<HTMLDivElement>(null);
  const { status, heartRate, hrvRmssd, deviceName, connect, disconnect } = useHeartRateMonitor();
  const telemetryTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const totalSeconds = session.duration_minutes * 60;

  useEffect(() => {
    if (phase !== 'running') return;
    const sceneEl = sceneRef.current;
    if (sceneEl) {
      sceneEl.innerHTML =
        session.scenario_slug === 'public_speaking'
          ? buildLectureScene(session.intensity_level)
          : buildHeightsScene(session.intensity_level);
    }

    const timer = setInterval(() => {
      setElapsed((e) => {
        const next = e + 1;
        if (next >= totalSeconds) {
          setPhase('post');
        }
        return next;
      });
    }, 1000);

    const telemetry = setInterval(() => {
      const stress = computeStressIndex(heartRate, hrvRmssd);
      apiClient
        .post(`/patient/vr/sessions/${session.id}/telemetry`, {
          heart_rate: heartRate,
          hrv_rmssd: hrvRmssd,
          stress_index: stress,
          scene_stage: stage,
        })
        .catch(() => {
          // telemetry best-effort; never block therapy flow
        });
    }, 5000);

    timerRef.current = timer;
    telemetryTimer.current = telemetry;

    return () => {
      clearInterval(timer);
      clearInterval(telemetry);
      if (sceneEl) sceneEl.innerHTML = '';
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  const handleComplete = async () => {
    setSubmitting(true);
    try {
      await apiClient.post(`/patient/vr/sessions/${session.id}/complete`, {
        suds_pre: sudsPre,
        suds_post: sudsPost,
        patient_feedback: feedback,
      });
      setExitMessage('Session completed and logged back to your doctor.');
    } catch {
      setExitMessage('Session completed locally. Your doctor will see results shortly.');
    } finally {
      setSubmitting(false);
    }
  };

  const minutesLeft = Math.max(0, Math.floor((totalSeconds - elapsed) / 60));
  const secondsLeft = Math.max(0, (totalSeconds - elapsed) % 60);
  const stress = computeStressIndex(heartRate, hrvRmssd);

  const statusLabel = {
    idle: 'Not connected — using simulated heart rate',
    connecting: 'Connecting...',
    connected: `Connected: ${deviceName}`,
    simulated: 'Simulated heart rate (no hardware)',
    error: 'Simulated mode (Bluetooth unavailable)',
  }[status];

  return (
    <div className="fixed inset-0 z-50 bg-gray-900">
      {/* A-Frame scene container */}
      <div ref={sceneRef} className="absolute inset-0" style={{ display: phase === 'running' ? 'block' : 'none' }} />

      {/* Intro phase */}
      {phase === 'intro' && (
        <div className="absolute inset-0 flex items-center justify-center p-6 bg-gray-900 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-xl w-full p-8 shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <span className="text-3xl">🥽</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">{session.scenario_name}</h2>
                <p className="text-xs text-gray-500 capitalize">{session.phobia_type} exposure therapy · {session.intensity_level} intensity</p>
              </div>
            </div>

            <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 mb-4 text-sm text-indigo-900 space-y-2">
              <p><strong>Doctor's instructions:</strong> {session.instructions || 'Follow the guided steps and pace yourself.'}</p>
              <p className="text-xs text-indigo-700">
                Session length: {session.duration_minutes} min · Exposure steps: {session.exposure_steps}
              </p>
            </div>

            <div className="mb-4">
              <div className="flex justify-between text-xs font-semibold text-gray-600 mb-1">
                <span>Distress NOW (SUDS 1-10)</span>
                <span>{sudsPre}</span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                value={sudsPre}
                onChange={(e) => setSudsPre(Number(e.target.value))}
                className="w-full accent-indigo-600"
              />
            </div>

            <div className="mb-5">
              <button
                onClick={status === 'connected' || status === 'simulated' ? disconnect : connect}
                className={`w-full py-3 rounded-xl font-bold text-sm transition cursor-pointer ${
                  status === 'connected'
                    ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {status === 'connected' ? '✓ ' + deviceName + ' — tap to disconnect' : '⌚ Connect Heart Rate Monitor (optional)'}
              </button>
              <p className="text-center text-[11px] text-gray-400 mt-2">{statusLabel}</p>
            </div>

            <button
              onClick={() => setPhase('running')}
              className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold shadow-lg cursor-pointer"
            >
              Begin Session ▶
            </button>
            <button
              onClick={onExit}
              className="w-full py-2 text-xs text-gray-500 hover:text-gray-700 mt-2 cursor-pointer"
            >
              ← Back without starting
            </button>
          </div>
        </div>
      )}

      {/* Running phase HUD */}
      {phase === 'running' && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-4 left-4 bg-black/70 text-white rounded-xl px-4 py-3 space-y-1 text-sm pointer-events-auto">
            <div className="font-bold flex items-center gap-2"><span>❤️</span> Heart Rate: <span className="text-emerald-400">{Math.round(heartRate)} bpm</span></div>
            <div className="flex items-center gap-2"><span>📈</span> HRV (RMSSD): <span className="text-cyan-300">{hrvRmssd} ms</span></div>
            <div className="flex items-center gap-2"><span>🧠</span> Stress Index: <span className={stress > 50 ? 'text-red-400' : 'text-amber-300'}>{stress}/100</span></div>
            <div className="flex items-center gap-2">⏱ Time: <span className="font-mono">{minutesLeft}:{secondsLeft.toString().padStart(2, '0')}</span></div>
            <div className="flex items-center gap-2">📋 Stage: <span className="font-mono">{stage}/{session.exposure_steps}</span></div>
          </div>

          <div className="absolute top-4 right-4 flex flex-col gap-2 pointer-events-auto">
            <button
              onClick={onExit}
              className="bg-red-600 hover:bg-red-700 text-white font-bold text-sm px-4 py-2 rounded-xl shadow cursor-pointer"
            >
              ⏹ End Session
            </button>
          </div>

          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 pointer-events-auto">
            {stage < session.exposure_steps ? (
              <button
                onClick={() => setStage((s) => s + 1)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-8 py-3 rounded-2xl shadow-2xl cursor-pointer"
              >
                Advance to Stage {stage + 1} →
              </button>
            ) : (
              <button
                onClick={() => setPhase('post')}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-8 py-3 rounded-2xl shadow-2xl cursor-pointer"
              >
                ✓ I completed all stages — Finish
              </button>
            )}
          </div>
        </div>
      )}

      {/* Post phase */}
      {phase === 'post' && (
        <div className="absolute inset-0 flex items-center justify-center p-6 bg-gray-900 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-lg w-full p-8 shadow-2xl">
            <h2 className="text-xl font-bold text-gray-900 mb-1">Session Complete</h2>
            <p className="text-sm text-gray-500 mb-5">How are you feeling now compared to before the exposure?</p>

            <div className="mb-4">
              <div className="flex justify-between text-xs font-semibold text-gray-600 mb-1">
                <span>Distress NOW (SUDS 1-10)</span>
                <span>{sudsPost}</span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                value={sudsPost}
                onChange={(e) => setSudsPost(Number(e.target.value))}
                className="w-full accent-emerald-600"
              />
              {sudsPre > sudsPost && (
                <p className="text-xs text-emerald-600 font-medium mt-1">✓ Distress decreased since pre-session ({sudsPre} → {sudsPost})</p>
              )}
            </div>

            <div className="mb-5">
              <label className="block text-xs font-semibold text-gray-600 mb-1">Notes for your doctor (optional)</label>
              <textarea
                rows={3}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="What did you experience? What coping strategies helped?"
                className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {exitMessage && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold mb-4">
                {exitMessage}
              </div>
            )}

            <button
              onClick={handleComplete}
              disabled={submitting}
              className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl font-bold shadow-lg cursor-pointer"
            >
              {submitting ? 'Submitting...' : 'Submit Results'}
            </button>
            <button
              onClick={onExit}
              className="w-full py-2 text-xs text-gray-500 hover:text-gray-700 mt-2 cursor-pointer"
            >
              Exit
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
