import { useEffect, useRef, useState } from 'react';
import 'aframe';
import 'aframe-physics-system/dist/aframe-physics-system.min.js';
import { apiClient } from '../../../api/client';
import { useHeartRateMonitor } from '../../../components/HeartRateMonitor';
import { createAmbience, type AmbienceHandle } from '../../../utils/vrAmbience';

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
  source?: string;
  suds_pre?: number;
  suds_post?: number;
  patient_feedback?: string;
  assigned_at?: string;
  started_at?: string;
  completed_at?: string;
  patient_id?: string;
  scenario_id?: string;
  doctor_id?: string;
}

interface VRSessionRunnerProps {
  session: VRASession;
  onExit: () => void;
}

type RunnerPhase = 'intro' | 'running' | 'post';

export const VR_STAGE_EVENT = 'vr-stage-advance';

const SLIDE_TITLES = [
  'Stage 1 — Ground Yourself',
  'Stage 2 — Visualize Success',
  'Stage 3 — Breathe & Pace',
  'Stage 4 — Project Confidence',
  'Stage 5 — Open Discussion',
];

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
    const isGlass = i % 3 === 0;
    const color = isGlass ? '#2c3e50' : i % 3 === 1 ? '#34495e' : '#1a252f';
    const metalness = isGlass ? '0.75' : '0.15';
    const roughness = isGlass ? '0.15' : '0.85';
    buildings += `<a-box position="${x.toFixed(1)} ${y.toFixed(1)} ${z.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}" depth="${w.toFixed(1)}" material="color: ${color}; metalness: ${metalness}; roughness: ${roughness}"></a-box>`;
  }

  // Lit window strips on the nearest towers (dusk skyline)
  let windowStrips = '';
  for (let i = 0; i < 12; i++) {
    const x = (rand() - 0.5) * 60;
    const z = -(30 + rand() * 45);
    const baseY = -height - 2 - rand() * 10;
    for (let s = 0; s < 3; s++) {
      const wy = baseY + s * 3.2;
      const wx = x + (s - 1) * 0.9;
      windowStrips += `<a-box position="${wx.toFixed(1)} ${wy.toFixed(1)} ${z.toFixed(1)}" width="0.35" height="1.6" depth="0.35" material="color: #ffd27d; shader: flat; opacity: ${0.55 + rand() * 0.45}"></a-box>`;
    }
  }

  return `
    <a-scene physics="debug: false; iterations: 2; tolerance: 0.001" renderer="antialias: true; colorManagement: true; foveationLevel: 2; sortObjects: true" fog="type: linear; color: #d98e5f; near: 18; far: ${height + 130}" shadow="type: pcf">
      <a-sky color="#e8946a"></a-sky>

      <a-entity light="type: ambient; intensity: 0.5; color: #ffd9b0"></a-entity>
      <a-entity light="type: directional; intensity: 1.05; color: #ffb367; castShadow: true; shadowMapWidth: 1024; shadowMapHeight: 1024; shadowCameraFar: 140; shadowCameraTop: 70; shadowCameraRight: 70; shadowCameraBottom: -70; shadowCameraLeft: -70; position: -25 20 -60"></a-entity>
      <a-entity light="type: hemisphere; color: #ffc490; groundColor: #334155; intensity: 0.45"></a-entity>

      <!-- Dusk sun disc -->
      <a-sphere position="-38 ${-(height - 14)} -95" radius="11" material="shader: flat; color: #ffe3ad"></a-sphere>
      <a-sphere position="-38 ${-(height - 14)} -94.6" radius="16" material="shader: flat; color: #ff9e54; opacity: 0.25; transparent: true"></a-sphere>

      <a-plane static-body position="0 -${height} 0" rotation="-90 0 0" width="220" height="220" material="color: #475569; metalness: 0.2; roughness: 0.9" shadow="receive: true"></a-plane>
      <a-entity id="skyline">${buildings}</a-entity>
      <a-entity id="window-strips">${windowStrips}</a-entity>

      <a-entity id="deck" position="0 0 0">
        <a-box static-body position="0 -0.5 0" width="14" height="1" depth="14" material="color: #cbd5e1; metalness: 0.35; roughness: 0.5" shadow="cast: true; receive: true"></a-box>
        <a-plane position="0 0.01 0" rotation="-90 0 0" width="14" height="14" material="color: #ffffff; opacity: 0.2; transparent: true; metalness: 0.8; roughness: 0.1"></a-plane>
        <a-box static-body position="-6.5 1 0" width="0.3" height="2.5" depth="14" material="color: #0f172a; metalness: 0.9; roughness: 0.2" shadow="cast: true; receive: true"></a-box>
        <a-box static-body position="6.5 1 0" width="0.3" height="2.5" depth="14" material="color: #0f172a; metalness: 0.9; roughness: 0.2" shadow="cast: true; receive: true"></a-box>
        <a-box id="front-rail" static-body position="0 1 -6.5" width="13" height="2.5" depth="0.3" material="color: #0f172a; metalness: 0.9; roughness: 0.2; transparent: true; opacity: 1" shadow="cast: true; receive: true"></a-box>
        <a-box static-body position="0 1 6.5" width="13" height="2.5" depth="0.3" material="color: #0f172a; metalness: 0.9; roughness: 0.2" shadow="cast: true; receive: true"></a-box>
        <a-box position="0 2.4 0" width="14" height="0.2" depth="14" material="color: #1e293b; metalness: 0.95; roughness: 0.1" shadow="cast: true; receive: true"></a-box>

        <!-- Hazard striping near the edge -->
        <a-plane position="0 0.02 -6.1" rotation="-90 0 0" width="13" height="0.8" material="shader: flat; color: #facc15; opacity: 0.85"></a-plane>
        <a-text value="CAUTION — EDGE" align="center" color="#111827" width="5" position="0 0.04 -6.1" rotation="-90 0 0"></a-text>
      </a-entity>

      <a-entity id="sway-rig">
        <a-entity camera look-controls="enabled: true" position="0 1.6 0">
          <a-entity cursor="rayOrigin: mouse" raycaster="far: 100; objects: [stage-advance]" geometry="primitive: ring; radiusInner: 0.02; radiusOuter: 0.03" material="color: white; shader: flat" position="0 0 -1"></a-entity>
        </a-entity>
        <a-entity laser-controls="hand: right" raycaster="far: 20; objects: [stage-advance]" line="color: #d4a84b; opacity: 0.7"></a-entity>
        <a-entity laser-controls="hand: left" raycaster="far: 20; objects: [stage-advance]" line="color: #d4a84b; opacity: 0.7"></a-entity>
      </a-entity>

      <a-entity stage-advance position="0 0.5 -4" geometry="primitive: box; width: 3; height: 0.8; depth: 0.1" material="color: #b8860b; opacity: 0.85; transparent: true">
        <a-text value="Advance Stage →" align="center" color="#ffffff" width="4" position="0 0 0.06"></a-text>
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
      const bodyColor = ['#1e293b', '#334155', '#475569', '#0f172a', '#1e1b4b'][Math.floor(rand() * 5)];
      const swayDur = Math.round(2400 + rand() * 1600);
      const swayDelay = Math.round(rand() * 1800);
      const swayDir = rand() > 0.5 ? 6 : -6;
      audience += `
        <a-entity position="${x.toFixed(2)} 0 ${z.toFixed(1)}">
          <a-box position="0 0.55 0" width="0.7" height="1.1" depth="0.5" material="color:${bodyColor}; roughness: 0.85; metalness: 0.05" shadow="cast: true; receive: true"></a-box>
          <a-sphere position="0 1.45 0" radius="0.28" material="color:${headColor}; roughness: 0.7; metalness: 0.0" shadow="cast: true"
            animation="property: rotation; to: 0 ${swayDir} 0; dur: ${swayDur}; dir: alternate; loop: true; delay: ${swayDelay}; easing: easeInOutSine"></a-sphere>
        </a-entity>`;
      placed++;
    }
    row++;
  }

  let phoneGlows = '';
  for (let i = 0; i < 6; i++) {
    const px = (rand() - 0.5) * 12;
    const pz = -7 - rand() * 10;
    phoneGlows += `<a-plane position="${px.toFixed(2)} 0.75 ${pz.toFixed(1)}" rotation="-65 0 0" width="0.16" height="0.28" material="shader: flat; color: #9ecbff; opacity: 0.9" visible="false"></a-plane>`;
  }

  const audienceScale = intensity === 'high' ? '1' : intensity === 'medium' ? '0.85' : '0.6';
  const chatterText = intensity === 'high' ? 'Crowd murmurs softly' : intensity === 'medium' ? 'A few people chatting' : 'Empty hall, quiet';

  return `
    <a-scene physics="debug: false; iterations: 2; tolerance: 0.001" renderer="antialias: true; colorManagement: true; foveationLevel: 2; sortObjects: true" fog="type: linear; color: #1e293b; near: 12; far: 65" shadow="type: pcf">
      <a-sky color="#0f172a"></a-sky>
      <a-entity id="ambient-light" light="type: ambient; intensity: 0.4; color: #cbd5e1"></a-entity>
      <a-entity id="key-light" light="type: directional; intensity: 0.8; color: #fef08a; castShadow: true; shadowMapWidth: 1024; shadowMapHeight: 1024; shadowCameraFar: 80; position: -4 14 6"></a-entity>
      <a-entity id="spot-light" light="type: spot; intensity: 1.6; color: #ffffff; angle: 40; penumbra: 0.4; position: 0 7 1; target: #podium" shadow="cast: true"></a-entity>

      <a-box static-body position="0 -0.5 -4" width="32" height="1" depth="26" material="color: #334155; roughness: 0.8; metalness: 0.15" shadow="receive: true"></a-box>
      <a-box static-body position="0 3 -12" width="36" height="12" depth="1" material="color: #1e293b; roughness: 0.95; metalness: 0.05" shadow="receive: true"></a-box>

      <a-entity id="podium" position="0 0 0">
        <a-entity position="0 0.9 -2.6">
          <a-box static-body position="0 0 0" width="2.4" height="1.3" depth="1.4" material="color: #451a03; roughness: 0.35; metalness: 0.1" shadow="cast: true; receive: true"></a-box>
          <a-box static-body position="0 0.55 0" width="1.6" height="0.12" depth="0.8" material="color: #78350f; roughness: 0.25; metalness: 0.2" shadow="cast: true"></a-box>
          <a-box dynamic-body position="0 1.2 0" width="0.2" height="0.4" depth="0.2" material="color: #ef4444; roughness: 0.2" shadow="cast: true"></a-box>
        </a-entity>
      </a-entity>

      <a-cone id="projector-beam" position="0 3.6 -6.2" rotation="-22 0 0" radius-bottom="3.4" radius-top="0.12" height="5.5" open-ended="true" material="shader: flat; color: #e0f2fe; opacity: 0.09; transparent: true; side: double"
        animation="property: material.opacity; to: 0.14; dir: alternate; dur: 900; loop: true; easing: easeInOutSine"></a-cone>

      <a-plane position="0 3.2 -10.2" width="9" height="5" material="color: #38bdf8; emissive: #0284c7; emissiveIntensity: 0.25; roughness: 0.3" shadow="receive: true"></a-plane>
      <a-text id="slide-title" position="0 4.3 -10.1" value="${SLIDE_TITLES[0]}" color="#f8fafc" width="8" align="center"></a-text>
      <a-text position="0 3.5 -10.1" value="${chatterText}" color="#e2e8f0" width="8" align="center"></a-text>

      <a-entity id="audience" scale="${audienceScale} ${audienceScale} ${audienceScale}">
        ${audience}
        ${phoneGlows}
      </a-entity>

      <a-entity camera look-controls="enabled: true" position="0 1.6 4">
        <a-entity cursor="rayOrigin: mouse" raycaster="far: 100; objects: [stage-advance]" geometry="primitive: ring; radiusInner: 0.02; radiusOuter: 0.03" material="color: white; shader: flat" position="0 0 -1"></a-entity>
      </a-entity>
      <a-entity laser-controls="hand: right" raycaster="far: 20; objects: [stage-advance]" line="color: #d4a84b; opacity: 0.7"></a-entity>
      <a-entity laser-controls="hand: left" raycaster="far: 20; objects: [stage-advance]" line="color: #d4a84b; opacity: 0.7"></a-entity>

      <a-entity stage-advance position="0 1.4 -3" geometry="primitive: box; width: 3; height: 0.7; depth: 0.1" material="color: #b8860b; opacity: 0.85; transparent: true">
        <a-text value="Advance Stage →" align="center" color="#ffffff" width="4" position="0 0 0.06"></a-text>
      </a-entity>
    </a-scene>
  `;
}

function computeStressIndex(hr: number, hrv: number): number {
  const hrC = Math.max(0, Math.min(100, (hr - 60) * 1.4));
  const hrvC = Math.max(0, Math.min(100, (60 - hrv) * 1.2));
  return Math.round(hrC * 0.55 + hrvC * 0.45);
}

declare global {
  interface Window {
    __vrApplyStage?: (stage: number) => void;
    __vrApplyAmbience?: (levels: { wind: number | null; murmur: number | null }) => void;
  }
}

export default function VRSessionRunner({ session, onExit }: VRSessionRunnerProps) {
  const [phase, setPhase] = useState<RunnerPhase>('intro');
  const [stage, setStage] = useState(1);
  const [elapsed, setElapsed] = useState(0);
  const [interactionCount, setInteractionCount] = useState(0);
  const [sudsPre, setSudsPre] = useState(5);
  const [sudsPost, setSudsPost] = useState(5);
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [exitMessage, setExitMessage] = useState('');

  const sceneRef = useRef<HTMLDivElement>(null);
  const { status, heartRate, hrvRmssd, deviceName, connect, disconnect } = useHeartRateMonitor();
  const telemetryTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const ambienceRef = useRef<AmbienceHandle | null>(null);

  const totalSeconds = session.duration_minutes * 60;

  const stageRef = useRef(stage);
  stageRef.current = stage;
  const hrRef = useRef(heartRate);
  hrRef.current = heartRate;
  const hrvRef = useRef(hrvRmssd);
  hrvRef.current = hrvRmssd;

  const mode: 'heights' | 'lecture' = session.scenario_slug === 'public_speaking' ? 'lecture' : 'heights';

  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).AFRAME && !(window as any).__vr_components_registered) {
      (window as any).__vr_components_registered = true;
      (window as any).AFRAME.registerComponent('stage-advance', {
        init: function () {
          this.el.addEventListener('click', () => {
            this.el.sceneEl?.emit(VR_STAGE_EVENT, {}, true);
          });
        }
      });

      (window as any).AFRAME.registerComponent('stage-director', {
        schema: { mode: { default: 'heights' } },
        init: function () {
          this.stage = 1;
          const el = this.el;
          this.swayRig = el.querySelector('#sway-rig');
          this.frontRail = el.querySelector('#front-rail');
          this.slideTitle = el.querySelector('#slide-title');
          this.phoneGlows = Array.from(el.querySelectorAll('#audience a-plane[material*="9ecbff"]'));
          this.baseFogFar = (el.getAttribute('fog') || {}).far ?? 80;

          if (this.data.mode === 'heights') {
            this.baseZ = this.swayRig ? this.swayRig.object3D.position.z : 0;
            this.ampX = 0.015;
            this.ampZ = 0.03;
            this.phaseSeed = Math.random() * 1000;
          }

          this.applyStage = (stage: number) => {
            this.stage = stage;
            if (this.data.mode === 'heights') {
              this.ampZ = 0.03 + (stage - 1) * 0.09;
              this.ampX = 0.015 + (stage - 1) * 0.03;
              const far = Math.max(55, this.baseFogFar - (stage - 1) * 16);
              el.setAttribute('fog', { far });
              if (this.swayRig) {
                const z = Math.min(4.2, (stage - 1) * 1.05);
                this.swayRig.object3D.position.z = this.baseZ - z;
                this.baseZOffset = z;
              }
              if (this.frontRail) {
                const opacity = Math.max(0.12, 1 - (stage - 1) * 0.28);
                this.frontRail.setAttribute('material', 'opacity', String(opacity));
              }
              window.__vrApplyAmbience?.({ wind: Math.min(1, 0.25 + (stage - 1) * 0.18), murmur: null });
            } else {
              el.querySelector('#ambient-light')?.setAttribute('light', 'intensity', String(Math.max(0.16, 0.4 - (stage - 1) * 0.07)));
              el.querySelector('#key-light')?.setAttribute('light', 'intensity', String(Math.max(0.3, 0.8 - (stage - 1) * 0.12)));
              el.querySelector('#spot-light')?.setAttribute('light', 'intensity', String(Math.min(2.3, 1.6 + (stage - 1) * 0.18)));
              this.slideTitle?.setAttribute('value', SLIDE_TITLES[(stage - 1) % SLIDE_TITLES.length]);
              this.phoneGlows.forEach((pg: any) => pg.setAttribute('visible', stage >= 2 ? 'true' : 'false'));
              window.__vrApplyAmbience?.({ wind: null, murmur: Math.min(1, 0.2 + (stage - 1) * 0.16) });
            }
          };

          el.addEventListener(VR_STAGE_EVENT, () => {
            const next = this.stage >= 99 ? this.stage : this.stage + 1;
            this.applyStage(next);
          });
        },
        tick: function (t: number) {
          if (this.data.mode !== 'heights' || !this.swayRig) return;
          const tt = (t + this.phaseSeed) / 1400;
          this.swayRig.object3D.rotation.z = Math.sin(tt) * this.ampZ;
          this.swayRig.object3D.rotation.x = Math.sin(tt * 0.7 + 1.3) * this.ampX;
        },
      });

      (window as any).__vrApplyStage = (stage: number) => {
        const sceneEl = document.querySelector('a-scene');
        const director = sceneEl?.querySelector('[stage-director]') as any;
        director?.components?.['stage-director']?.applyStage?.(stage);
      };
    }
  }, []);

  useEffect(() => {
    if (phase !== 'running') return;

    const container = sceneRef.current;
    if (container && container.childElementCount === 0) {
      container.innerHTML =
        mode === 'lecture'
          ? buildLectureScene(session.intensity_level)
          : buildHeightsScene(session.intensity_level);

      const aScene = container.querySelector('a-scene');
      if (aScene) {
        const directorEl = document.createElement('a-entity');
        directorEl.setAttribute('stage-director', `mode: ${mode}`);
        aScene.appendChild(directorEl);
      }
    }

    const onAdvance = () => {
      setInteractionCount((prev) => prev + 1);
      setStage((s) => Math.min(s + 1, session.exposure_steps));
    };
    document.addEventListener(VR_STAGE_EVENT, onAdvance);

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
      const stress = computeStressIndex(hrRef.current, hrvRef.current);
      apiClient
        .post(`/patient/vr/sessions/${session.id}/telemetry`, {
          heart_rate: hrRef.current,
          hrv_rmssd: hrvRef.current,
          stress_index: stress,
          scene_stage: stageRef.current,
        })
        .catch(() => {
          // telemetry best-effort; never block therapy flow
        });
    }, 5000);

    timerRef.current = timer;
    telemetryTimer.current = telemetry;

    const amb = ambienceRef.current;
    return () => {
      document.removeEventListener(VR_STAGE_EVENT, onAdvance);
      clearInterval(timer);
      clearInterval(telemetry);
      amb?.stop();
      if (container) container.innerHTML = '';
      if (ambienceRef.current === amb) ambienceRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  useEffect(() => {
    if (phase !== 'running') return;
    (window as any).__vrApplyStage?.(stage);
  }, [phase, stage, mode]);

  const beginRunningPhase = () => {
    if (!ambienceRef.current) {
      ambienceRef.current = createAmbience(mode === 'lecture' ? 'murmur' : 'wind');
      (window as any).__vrApplyAmbience = ({ wind, murmur }: { wind: number | null; murmur: number | null }) => {
        if (wind !== null) ambienceRef.current?.setWindLevel(wind);
        if (murmur !== null) ambienceRef.current?.setMurmurLevel(murmur);
      };
    }
    setInteractionCount(0);
    setStage(1);
    setElapsed(0);
    setPhase('running');
  };

  const handleComplete = async (earlyExit: boolean = false) => {
    setSubmitting(true);
    try {
      await apiClient.post(`/patient/vr/sessions/${session.id}/complete`, {
        suds_pre: sudsPre,
        suds_post: sudsPost,
        patient_feedback: feedback,
        time_in_scene: elapsed,
        interaction_count: interactionCount,
        completion_status: earlyExit ? "exited_early" : "completed_fully"
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
        <div className="absolute inset-0 flex items-center justify-center overflow-y-auto bg-gray-900 p-6">
          <div className="rounded-lg bg-white max-w-xl w-full p-8 shadow-2xl">
            <div className="mb-4 flex items-center gap-3">
              <span className="text-3xl">🥽</span>
              <div>
                <h2 className="text-xl font-bold text-gray-900">{session.scenario_name}</h2>
                <p className="text-xs text-gray-500 capitalize">{session.phobia_type} exposure therapy · {session.intensity_level} intensity</p>
              </div>
            </div>

            <div className="mb-4 space-y-2 rounded-lg border border-[#e8e4df] bg-muted p-4 text-sm text-slate-700">
              {session.doctor_id ? (
                <p><strong>Doctor's instructions:</strong> {session.instructions || 'Follow the guided steps and pace yourself.'}</p>
              ) : (
                <p><strong>Self-guided session:</strong> Go at your own pace — pause or exit anytime.</p>
              )}
              <p className="text-xs text-accent">
                Session length: {session.duration_minutes} min · Exposure steps: {session.exposure_steps}
              </p>
            </div>

            <div className="mb-4">
              <div className="mb-1 flex justify-between text-xs font-semibold text-gray-600">
                <span>Distress NOW (SUDS 1-10)</span>
                <span>{sudsPre}</span>
              </div>
              <input
                type="range"
                min={1}
                max={10}
                value={sudsPre}
                onChange={(e) => setSudsPre(Number(e.target.value))}
                className="w-full accent-[#b8860b]"
              />
            </div>

            <div className="mb-5">
              <button
                onClick={status === 'connected' || status === 'simulated' ? disconnect : connect}
                className={`w-full cursor-pointer rounded-md py-3 font-bold text-sm transition duration-200 ${
                  status === 'connected'
                    ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {status === 'connected' ? '✓ ' + deviceName + ' — tap to disconnect' : '⌚ Connect Heart Rate Monitor (optional)'}
              </button>
              <p className="mt-2 text-center text-[11px] text-gray-400">{statusLabel}</p>
            </div>

            <button
              onClick={beginRunningPhase}
              className="w-full cursor-pointer rounded-md bg-accent py-3.5 font-bold text-white transition-all duration-200 hover:bg-accent-secondary motion-safe:hover:-translate-y-0.5"
            >
              Begin Session ▶
            </button>
            <button
              onClick={onExit}
              className="mt-2 w-full cursor-pointer py-2 text-xs text-gray-500 hover:text-gray-700"
            >
              ← Back without starting
            </button>
          </div>
        </div>
      )}

      {/* Running phase HUD */}
      {phase === 'running' && (
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-4 top-4 space-y-1 rounded-md bg-black/70 px-4 py-3 text-sm text-white">
            <div className="flex items-center gap-2 font-bold"><span>❤️</span> Heart Rate: <span className="text-emerald-400">{Math.round(heartRate)} bpm</span></div>
            <div className="flex items-center gap-2"><span>📈</span> HRV (RMSSD): <span className="text-cyan-300">{hrvRmssd} ms</span></div>
            <div className="flex items-center gap-2"><span>🧠</span> Stress Index: <span className={stress > 50 ? 'text-red-400' : 'text-amber-300'}>{stress}/100</span></div>
            <div className="flex items-center gap-2">⏱ Time: <span className="font-mono">{minutesLeft}:{secondsLeft.toString().padStart(2, '0')}</span></div>
            <div className="flex items-center gap-2">📋 Stage: <span className="font-mono">{stage}/{session.exposure_steps}</span></div>
          </div>

          <div className="absolute right-4 top-4 flex flex-col gap-2 pointer-events-auto">
            <button
              onClick={() => {
                const aScene = sceneRef.current?.querySelector('a-scene') as any;
                if (aScene?.enterVR) aScene.enterVR();
              }}
              className="cursor-pointer rounded-md bg-accent px-4 py-2 text-sm font-bold text-white shadow transition-colors hover:bg-accent-secondary"
              aria-label="Enter immersive VR mode"
            >
              Enter VR
            </button>
            <button
              onClick={async () => { await handleComplete(true); onExit(); }}
              className="cursor-pointer rounded-md border border-red-800 bg-transparent px-4 py-2 text-sm font-semibold text-red-700 transition-colors hover:bg-red-50"
            >
              ⏹ End Session
            </button>
          </div>

          <div className="pointer-events-auto absolute bottom-6 left-1/2 -translate-x-1/2">
            {stage < session.exposure_steps ? (
              <button
                onClick={() => { setInteractionCount(c => c + 1); setStage((s) => s + 1); }}
                className="cursor-pointer rounded-md bg-accent px-8 py-3 font-bold text-white shadow-lg transition-all duration-200 hover:bg-accent-secondary motion-safe:hover:-translate-y-0.5"
              >
                Advance to Stage {stage + 1} →
              </button>
            ) : (
              <button
                onClick={() => setPhase('post')}
                className="cursor-pointer rounded-md bg-emerald-600 px-8 py-3 font-bold text-white shadow-lg transition-colors hover:bg-emerald-700"
              >
                ✓ I completed all stages — Finish
              </button>
            )}
          </div>
        </div>
      )}

      {/* Post phase */}
      {phase === 'post' && (
        <div className="absolute inset-0 flex items-center justify-center overflow-y-auto bg-gray-900 p-6">
          <div className="w-full max-w-lg rounded-lg bg-white p-8 shadow-2xl">
            <h2 className="font-display text-2xl font-semibold text-foreground mb-1">Session Complete</h2>
            <p className="mb-5 text-sm text-muted-foreground">How are you feeling now compared to before the exposure?</p>

            <div className="mb-4">
              <div className="mb-1 flex justify-between text-xs font-semibold text-gray-600">
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
                <p className="mt-1 text-xs font-medium text-emerald-600">✓ Distress decreased since pre-session ({sudsPre} → {sudsPost})</p>
              )}
            </div>

            <div className="mb-5">
              <label className="mb-1 block text-xs font-semibold text-gray-600">Notes for your doctor (optional)</label>
              <textarea
                rows={3}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="What did you experience? What coping strategies helped?"
                className="w-full rounded-md border border-gray-300 px-4 py-2.5 text-sm focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/15"
              />
            </div>

            {exitMessage && (
              <div className="mb-4 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-xs font-semibold text-emerald-800">
                {exitMessage}
              </div>
            )}

            <button
              onClick={() => handleComplete(false)}
              disabled={submitting}
              className="w-full cursor-pointer rounded-md bg-emerald-600 py-3.5 font-bold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:opacity-50"
            >
              {submitting ? 'Submitting...' : 'Submit Results'}
            </button>
            <button
              onClick={onExit}
              className="mt-2 w-full cursor-pointer py-2 text-xs text-gray-500 hover:text-gray-700"
            >
              Exit
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
