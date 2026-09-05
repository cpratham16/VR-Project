export type AmbienceMode = 'wind' | 'murmur';

export interface AmbienceHandle {
  setWindLevel: (level01: number) => void;
  setMurmurLevel: (level01: number) => void;
  stop: () => void;
}

function makeNoiseBuffer(ctx: AudioContext, seconds = 2): AudioBuffer {
  const buffer = ctx.createBuffer(1, ctx.sampleRate * seconds, ctx.sampleRate);
  const data = buffer.getChannelData(0);
  let lastOut = 0;
  for (let i = 0; i < data.length; i++) {
    const white = Math.random() * 2 - 1;
    lastOut = (lastOut + 0.02 * white) / 1.02;
    data[i] = lastOut * 3.5;
  }
  return buffer;
}

export function createAmbience(mode: AmbienceMode): AmbienceHandle {
  const ctx = new AudioContext();
  const master = ctx.createGain();
  master.gain.value = 0;
  master.connect(ctx.destination);

  const noise = ctx.createBufferSource();
  noise.buffer = makeNoiseBuffer(ctx);
  noise.loop = true;

  if (mode === 'wind') {
    const lp = ctx.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 480;
    lp.Q.value = 0.7;
    noise.connect(lp).connect(master);
  } else {
    const bp = ctx.createBiquadFilter();
    bp.type = 'bandpass';
    bp.frequency.value = 260;
    bp.Q.value = 0.9;
    const tremolo = ctx.createGain();
    const lfo = ctx.createOscillator();
    const lfoGain = ctx.createGain();
    lfo.frequency.value = 2.6;
    lfoGain.gain.value = 0.35;
    lfo.connect(lfoGain).connect(tremolo.gain);
    noise.connect(bp).connect(tremolo).connect(master);
    lfo.start();
    void lfoGain;
  }

  noise.start();

  const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

  return {
    setWindLevel(level01: number) {
      if (mode !== 'wind') return;
      master.gain.setTargetAtTime(clamp01(level01) * 0.5, ctx.currentTime, 0.6);
    },
    setMurmurLevel(level01: number) {
      if (mode !== 'murmur') return;
      master.gain.setTargetAtTime(clamp01(level01) * 0.45, ctx.currentTime, 0.6);
    },
    stop() {
      try {
        master.gain.setTargetAtTime(0, ctx.currentTime, 0.15);
        setTimeout(() => void ctx.close(), 250);
      } catch {
        /* already closed */
      }
    },
  };
}
