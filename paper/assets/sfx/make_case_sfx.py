"""Case-file board SFX for paper-factory (typewriter / corkboard / stamp / string / camera).
Pure numpy, no downloads. 48 kHz / 16-bit mono WAV, fades >= 5 ms, no clicks.

This folder is a different project from ud-style/sfx-pack, so instead of a cross-project
import this script carries a small self-contained copy of that pack's house-style helpers
(fade, normalize_peak, fft_filter, lowpass/highpass/resonant_bp, pink_noise, tv_filter,
write_wav-style RIFF writer) plus one addition, brown_noise() (same FFT-shaping technique as
pink_noise, just 1/f instead of 1/sqrt(f)). Same techniques, same deterministic-seed style as
make_sfx.py / sfx_paper.py / sfx_extra.py. Run: python make_case_sfx.py (from this folder).
"""
import os, math, struct
import numpy as np

SR = 48000
OUT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(20260928)


# ---------- shared helpers (house style, see ud-style/sfx-pack/make_sfx.py) ----------
def db(x):
    return 10 ** (x / 20.0)


def fade(x, ms_in=5, ms_out=5):
    x = x.copy()
    a = int(SR * ms_in / 1000)
    b = int(SR * ms_out / 1000)
    ramp_in = np.sin(np.linspace(0, np.pi / 2, a)) ** 2
    ramp_out = np.cos(np.linspace(0, np.pi / 2, b)) ** 2
    if x.ndim == 1:
        x[:a] *= ramp_in
        x[-b:] *= ramp_out
    else:
        x[:a] *= ramp_in[:, None]
        x[-b:] *= ramp_out[:, None]
    return x


def normalize_peak(x, peak_db):
    p = np.max(np.abs(x))
    return x / p * db(peak_db)


def finalize(x, peak_db, fade_in_ms=5.0, fade_out_ms=5.0):
    """fade THEN normalize_peak so an edge ramp can never pull the loudest sample below
    the declared peak: final max(|x|) always equals peak_db exactly (sfx_extra.py style)."""
    x = fade(x, fade_in_ms, fade_out_ms)
    return normalize_peak(x, peak_db)


def fft_filter(x, gain_fn):
    """Zero-phase static filter: gain_fn(freqs_hz) -> linear gain."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(X * gain_fn(f), n)


def lowpass(fc, order=2):
    return lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * order))


def highpass(fc, order=2):
    return lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-6)) ** (2 * order))


def resonant_bp(fc, q):
    def g(f):
        f = np.maximum(f, 1e-6)
        return 1 / np.sqrt(1 + (q * (f / fc - fc / f)) ** 2)
    return g


def pink_noise(n):
    w = rng.standard_normal(n)
    W = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    W = W / np.sqrt(f)
    x = np.fft.irfft(W, n)
    return x / np.max(np.abs(x))


def brown_noise(n):
    """Not in make_sfx.py: same FFT-shaping technique as pink_noise, 1/f amplitude
    (-6 dB/oct, i.e. integrated white noise) for a duller, punchier "crunch" texture."""
    w = rng.standard_normal(n)
    W = np.fft.rfft(w)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    W = W / f
    x = np.fft.irfft(W, n)
    return x / np.max(np.abs(x))


def tv_filter(x, mask_fn, frame=2048, hop=512):
    """Time-varying zero-phase filter via STFT overlap-add (Hann, COLA at hop=frame/4).
    mask_fn(t_sec, freqs_hz) -> gain array."""
    n = len(x)
    win = np.hanning(frame + 1)[:-1]
    pad = frame
    xp = np.concatenate([np.zeros(pad), x, np.zeros(pad + frame)])
    out = np.zeros_like(xp)
    freqs = np.fft.rfftfreq(frame, 1 / SR)
    for start in range(0, len(xp) - frame, hop):
        seg = xp[start:start + frame] * win
        t = (start + frame / 2 - pad) / SR
        S = np.fft.rfft(seg) * mask_fn(t, freqs)
        out[start:start + frame] += np.fft.irfft(S, frame) * win
    return out[pad:pad + n] / 1.5


def write_wav16(path, data, sr=SR):
    """data: float array shape (n,) or (n, ch) in -1..1. 16-bit PCM mono/interleaved."""
    if data.ndim == 1:
        data = data[:, None]
    n, ch = data.shape
    data = np.clip(data, -1.0, 1.0)
    ints = np.round(data * (2 ** 15 - 1)).astype("<i2")
    raw = ints.tobytes()
    byte_rate = sr * ch * 2
    with open(path, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + len(raw)))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<IHHIIHH", 16, 1, ch, sr, byte_rate, ch * 2, 16))
        f.write(b"data")
        f.write(struct.pack("<I", len(raw)))
        f.write(raw)


# ---------- 1. typekey (~70 ms) - single mechanical typewriter key strike ----------
def typekey():
    """Sharp transient: high-passed noise burst (type-bar clack) + short 1.2-2 kHz
    metallic ping (two slightly detuned partials)."""
    dur = 0.070
    n = int(round(SR * dur))
    t = np.arange(n) / SR

    imp = rng.standard_normal(n) * np.exp(-t / 0.0015)
    burst = fft_filter(imp, highpass(1400, 2))
    burst = burst / np.max(np.abs(burst)) * np.exp(-t / 0.010)

    ping = (np.sin(2 * np.pi * 1500 * t) + 0.55 * np.sin(2 * np.pi * 1960 * t + 0.7)) * np.exp(-t / 0.014)
    ping = ping / np.max(np.abs(ping))

    x = 0.75 * burst + 0.55 * ping
    x = fft_filter(x, highpass(500, 2))   # small hard hit, no low rumble
    return finalize(x, -10.0, 5, 15)


# ---------- 2. pinpush (~120 ms) - pin pushed into corkboard ----------
def pinpush():
    """Soft thump: 140->80 Hz sine burst, soft attack. Tiny crunch: short
    band-limited brown-noise burst (cork-fibre texture)."""
    dur = 0.120
    n = int(round(SR * dur))
    t = np.arange(n) / SR

    f_inst = 140.0 - 60.0 * np.clip(t / 0.05, 0.0, 1.0)   # 140 -> 80 Hz over 50 ms
    phase = 2 * np.pi * np.cumsum(f_inst) / SR
    thump = np.sin(phase) * (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.045)
    thump = thump / np.max(np.abs(thump))

    crunch = brown_noise(n) * np.exp(-t / 0.018)
    crunch = fft_filter(crunch, lambda f: highpass(600, 2)(f) * lowpass(4500, 2)(f))
    crunch = crunch / np.max(np.abs(crunch))

    x = 0.85 * thump + 0.40 * crunch
    return finalize(x, -10.0, 5, 20)


# ---------- 3. stampslam (~260 ms) - rubber stamp slam on paper ----------
def stampslam():
    """Heavier thud: 60 Hz decaying sine + low-passed noise body, plus a short
    band-passed paper-slap transient."""
    dur = 0.260
    n = int(round(SR * dur))
    t = np.arange(n) / SR

    thud = np.sin(2 * np.pi * 60 * t) * (1 - np.exp(-t / 0.003)) * np.exp(-t / 0.085)
    thud = thud / np.max(np.abs(thud))

    body = fft_filter(rng.standard_normal(n), lowpass(200, 3)) * np.exp(-t / 0.07)
    body = body / np.max(np.abs(body))

    slap = fft_filter(rng.standard_normal(n), resonant_bp(2600, 1.5)) * np.exp(-t / 0.007)
    slap = slap / np.max(np.abs(slap))

    x = 0.80 * thud + 0.35 * body + 0.55 * slap
    x = fft_filter(x, highpass(35, 2))
    return finalize(x, -6.0, 5, 40)


# ---------- 4. stringzip (~350 ms) - red string pulled taut between pins ----------
def stringzip():
    """Filtered noise sweep 600 -> 2400 Hz (rise/fall amplitude envelope) with a
    soft decaying 220 Hz pluck crossfaded in at the end."""
    dur = 0.350
    n = int(round(SR * dur))
    t = np.arange(n) / SR
    sweep_dur = 0.26

    noise = pink_noise(n)

    def mask(tt, f):
        p = min(max(tt / sweep_dur, 0.0), 1.0)
        fc = 600.0 * (2400.0 / 600.0) ** p     # exponential 600 -> 2400 Hz
        return resonant_bp(fc, 3.5)(f)

    sweep = tv_filter(noise, mask)
    sweep = sweep / np.max(np.abs(sweep))
    sweep_env = np.where(t <= sweep_dur, np.sin(np.pi * np.clip(t / sweep_dur, 0, 1)) ** 0.6, 0.0)

    t0 = 0.24
    on = t >= t0
    tl = np.where(on, t - t0, 0.0)
    pluck = np.where(on, np.sin(2 * np.pi * 220 * tl), 0.0) * np.where(on, (1 - np.exp(-tl / 0.003)) * np.exp(-tl / 0.045), 0.0)
    pluck = pluck / np.max(np.abs(pluck))

    x = 0.75 * (sweep * sweep_env) + 0.60 * pluck
    x = fft_filter(x, highpass(80, 2))
    return finalize(x, -12.0, 5, 30)


# ---------- 5. shutter (~180 ms) - camera shutter click with flash ----------
def shutter():
    """Two noise-transient clicks 60 ms apart + a faint high 5 kHz tick trailing
    the second click (flash mechanism whine)."""
    dur = 0.180
    n = int(round(SR * dur))
    t = np.arange(n) / SR

    def click(t0, fc, q, amp, tau_pre=0.0015, tau_post=0.007):
        on = t >= t0
        tl = np.where(on, t - t0, 0.0)
        imp = rng.standard_normal(n) * np.where(on, np.exp(-tl / tau_pre), 0.0)
        burst = fft_filter(imp, resonant_bp(fc, q))
        burst = burst * np.where(on, np.exp(-tl / tau_post), 0.0)
        p = np.max(np.abs(burst))
        return (burst / p if p > 0 else burst) * amp

    c1 = click(0.000, 3600, 2.5, 1.00, tau_post=0.007)
    c2 = click(0.060, 4400, 3.0, 0.85, tau_post=0.006)

    t0h = 0.063
    on = t >= t0h
    tl = np.where(on, t - t0h, 0.0)
    hi = np.where(on, np.sin(2 * np.pi * 5000 * tl), 0.0) * np.where(on, np.exp(-tl / 0.030), 0.0)
    hi = hi / np.max(np.abs(hi)) * 0.20

    x = c1 + c2 + hi
    x = fft_filter(x, highpass(1500, 2))
    return finalize(x, -10.0, 5, 20)


if __name__ == "__main__":
    jobs = [
        ("typekey.wav", typekey),
        ("pinpush.wav", pinpush),
        ("stampslam.wav", stampslam),
        ("stringzip.wav", stringzip),
        ("shutter.wav", shutter),
    ]
    for name, fn in jobs:
        x = fn()
        write_wav16(os.path.join(OUT, name), x)
        print(f"{name:14s} {len(x) / SR * 1000:7.1f} ms  peak {20 * math.log10(np.max(np.abs(x))):6.2f} dBFS  ch={1 if x.ndim == 1 else x.shape[1]}")
