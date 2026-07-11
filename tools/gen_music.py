#!/usr/bin/env python
"""AURIGA - generatore delle 8 tracce musicali originali (contratto, sez. 7).

Sintesi interamente in numpy + stdlib. Nessun campione esterno: tutto originale.
Mood di riferimento: Honkai Star Rail (armonie maj7/add9/sus, arpeggi delicati,
piano emotivo, pad caldi, campanelli FM, produzione pulita).

Output: WAV 22050 Hz 16-bit STEREO in auriga/assets/music/ (ffmpeg assente).
Loop senza click: la coda (riverbero/delay) oltre il punto di loop viene
ripiegata con crossfade sull'attacco della traccia (tranne victory).

Uso:  .venv/bin/python tools/gen_music.py [nomi_traccia...]
"""
import math
import os
import sys
import wave

import numpy as np

SR = 22050
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "music")
RNG = np.random.default_rng(20260709)

# ---------------------------------------------------------------- utilita' --

def midi2f(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


def fftconv(x, h):
    """Convoluzione veloce via FFT, output troncato alla lunghezza di x."""
    n = len(x) + len(h) - 1
    N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(h, N), N)[: len(x)]


def onepole_lp(x, fc, sr=SR):
    """Passa-basso one-pole: y[n] = a*x[n] + (1-a)*y[n-1], via IR troncata."""
    a = 1.0 - math.exp(-2.0 * math.pi * fc / sr)
    n = max(4, int(math.log(1e-5) / math.log(1.0 - a)))
    k = np.arange(n)
    h = a * (1.0 - a) ** k
    return fftconv(x, h)


def env_adsr(n, sr, a, d, s, r, gate_n=None):
    """Inviluppo ADSR di n campioni; il release parte a gate_n (default n-r)."""
    if gate_n is None:
        gate_n = n - int(r * sr)
    gate_n = max(1, min(gate_n, n))
    e = np.zeros(n)
    na, nd = max(1, int(a * sr)), max(1, int(d * sr))
    seg = min(na, gate_n)
    e[:seg] = np.linspace(0.0, 1.0, seg, endpoint=False)
    if gate_n > na:
        seg = min(nd, gate_n - na)
        e[na:na + seg] = np.linspace(1.0, s, seg, endpoint=False)
        e[na + seg:gate_n] = s
    nr = n - gate_n
    if nr > 0:
        e[gate_n:] = e[gate_n - 1] * np.linspace(1.0, 0.0, nr) ** 1.5
    return e

# -------------------------------------------------------------- strumenti --
# Ogni synth(freq, dur, vel, sr) -> array mono float.


def sy_piano(f, dur, vel, sr=SR):
    """Piano-like: armoniche smorzate esponenzialmente + rumore d'attacco."""
    ring = min(dur + 1.4, 4.5)
    n = int(ring * sr)
    t = np.arange(n) / sr
    x = np.zeros(n)
    rate = (f / 261.6) ** 0.45          # le note acute decadono prima
    for h in range(1, 9):
        fh = f * h * math.sqrt(1.0 + 3.2e-4 * h * h)   # inarmonicita'
        if fh > 0.45 * sr:
            break
        x += (np.exp(-t * (0.9 + 0.55 * h) * rate) / h ** 1.55
              * np.sin(2 * np.pi * fh * t + 0.37 * h * h))
    na = int(0.010 * sr)                                # colpo del martelletto
    th = RNG.uniform(-1, 1, na) * np.linspace(1, 0, na) ** 2
    x[:na] += onepole_lp(th, 3000, sr) * 0.5
    ar = max(2, int(0.002 * sr))
    x[:ar] *= np.linspace(0, 1, ar)
    gn = int(dur * sr)                                  # rilascio dopo la nota
    if gn < n:
        x[gn:] *= np.linspace(1, 0, n - gn) ** 1.3
    return 0.5 * vel * x


def make_pad(attack=0.45, release=1.0, fc=1000, detunes=(-6.0, 0.0, 5.0),
             sub=0.0, shimmer=0.0):
    """Pad caldo: saw detunate in additiva, gia' filtrate con risposta one-pole."""
    def synth(f, dur, vel, sr=SR):
        n = int((dur + release) * sr)
        t = np.arange(n) / sr
        x = np.zeros(n)
        for c in detunes:
            fd = f * 2.0 ** (c / 1200.0)
            K = max(1, min(int(0.45 * sr / fd), int(6.0 * fc / fd) + 1))
            ks = np.arange(1, K + 1, dtype=float)
            amp = (1.0 / ks) / np.sqrt(1.0 + (ks * fd / fc) ** 2)  # saw + LP one-pole
            ph = RNG.uniform(0, 2 * np.pi, K)
            x += (np.sin(2 * np.pi * fd * np.outer(ks, t) + ph[:, None])
                  * amp[:, None]).sum(0)
        x /= len(detunes)
        if sub > 0:
            x += sub * np.sin(2 * np.pi * f * 0.5 * t)
        if shimmer > 0:                                  # 12ma sopra, lenta
            x += shimmer * np.sin(2 * np.pi * f * 3.0 * t) * np.minimum(t / 2.0, 1.0)
        e = env_adsr(n, sr, attack, 0.1, 1.0, release, gate_n=int(dur * sr))
        return 0.42 * vel * x * e
    return synth


def make_bell(ratio=3.0, index=1.1, decay=2.4):
    """Campanella FM: portante + modulante con indice che decade."""
    def synth(f, dur, vel, sr=SR):
        ring = min(dur + 2.2, 5.0)
        n = int(ring * sr)
        t = np.arange(n) / sr
        mod = index * np.exp(-t * 1.7) * np.sin(2 * np.pi * f * ratio * t)
        x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * decay * (f / 880.0) ** 0.3)
        x += 0.18 * np.sin(2 * np.pi * f * 4.16 * t) * np.exp(-t * 6.0)
        ar = max(2, int(0.0015 * sr))
        x[:ar] *= np.linspace(0, 1, ar)
        gn = int(dur * sr)
        if gn < n:
            x[gn:] *= np.linspace(1, 0, n - gn) ** 1.2
        return 0.5 * vel * x
    return synth


def sy_bass(f, dur, vel, sr=SR):
    """Basso sinusoidale morbido con un filo di 2a/3a armonica."""
    n = int((dur + 0.10) * sr)
    t = np.arange(n) / sr
    x = (np.sin(2 * np.pi * f * t)
         + 0.30 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3.0)
         + 0.10 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 5.0))
    e = env_adsr(n, sr, 0.008, 0.05, 0.9, 0.08, gate_n=int(dur * sr))
    return 0.62 * vel * x * e


def make_lead(fc=3200, detunes=(-7.0, 6.0), attack=0.012, release=0.14):
    """Riff synth: due saw detunate, brillanti, inviluppo rapido."""
    pad = make_pad(attack=attack, release=release, fc=fc, detunes=detunes)
    def synth(f, dur, vel, sr=SR):
        x = pad(f, dur, vel, sr)
        return 1.25 * x
    return synth


def sy_kick(f, dur, vel, sr=SR):
    n = int(0.30 * sr)
    t = np.arange(n) / sr
    freq = 42.0 + 130.0 * np.exp(-t * 30.0)
    x = np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-t * 13.0)
    nc = int(0.003 * sr)
    x[:nc] += RNG.uniform(-1, 1, nc) * 0.5 * np.linspace(1, 0, nc)
    return 0.95 * vel * x


def sy_hat(f, dur, vel, sr=SR):
    n = int(max(dur, 0.05) * sr)
    t = np.arange(n) / sr
    nz = RNG.uniform(-1, 1, n)
    nz = nz - onepole_lp(nz, 5200, sr)                 # passa-alto
    rate = 70.0 if dur <= 0.06 else 16.0               # chiuso / aperto
    return 0.5 * vel * nz * np.exp(-t * rate)


def sy_snare(f, dur, vel, sr=SR):
    n = int(0.20 * sr)
    t = np.arange(n) / sr
    nz = RNG.uniform(-1, 1, n)
    body = onepole_lp(nz, 5500, sr) - onepole_lp(nz, 500, sr)
    x = body * np.exp(-t * 22.0) + 0.6 * np.sin(2 * np.pi * 182 * t) * np.exp(-t * 34.0)
    return 0.8 * vel * x

# ----------------------------------------------------------------- effetti --

def tape_delay(x, sr, time_s, fb=0.35, mix=0.25, damp=2600, echoes=6):
    """Delay 'a nastro': echi via somma esplicita, ogni giro ri-filtrato in LP."""
    D = int(time_s * sr)
    wet = np.zeros_like(x)
    cur = x.copy()
    for k in range(1, echoes + 1):
        cur = onepole_lp(cur, damp, sr) * fb
        if D * k >= len(x) or np.max(np.abs(cur)) < 1e-4:
            break
        wet[D * k:] += cur[: len(x) - D * k]
    return x + mix * wet


def _comb(x, D, g):
    n = len(x)
    y = np.zeros(n)
    for s in range(0, n, D):
        e = min(s + D, n)
        seg = x[s:e].copy()
        if s >= D:
            seg += g * y[s - D:s - D + (e - s)]
        y[s:e] = seg
    return y


def _allpass(x, D, g):
    n = len(x)
    y = np.zeros(n)
    xd = np.concatenate([np.zeros(D), x])[:n]
    for s in range(0, n, D):
        e = min(s + D, n)
        y[s:e] = -g * x[s:e] + xd[s:e]
        if s >= D:
            y[s:e] += g * y[s - D:s - D + (e - s)]
    return y


def reverb(st, sr, g=0.78, wet=0.25, damp=4200, predelay=0.02):
    """Riverbero leggero alla Schroeder: 4 comb + 2 allpass, stereo spread."""
    out = st.copy()
    combs = [778, 808, 745, 711]
    for ch in range(2):
        x = onepole_lp(st[ch], damp, sr)
        pd = int(predelay * sr)
        x = np.concatenate([np.zeros(pd), x])[: len(x)]
        w = np.zeros_like(x)
        for i, D in enumerate(combs):
            w += _comb(x, D + ch * 13 + i * 2, g)
        w /= len(combs)
        w = _allpass(w, 113 + ch * 5, 0.5)
        w = _allpass(w, 279 + ch * 7, 0.5)
        out[ch] += wet * w
    return out


def soft_limit(x, t=0.80, cap=0.95):
    """Soft limiter: trasparente sotto t, tanh fra t e cap (peak < cap)."""
    y = x.copy()
    m = np.abs(x) > t
    y[m] = np.sign(x[m]) * (t + (cap - t) * np.tanh((np.abs(x[m]) - t) / (cap - t)))
    return y

# -------------------------------------------------------------- sequencer --

def render_bus(events, synth, total_n, spb, sr=SR):
    """events: (beat, dur_beat, midi, vel, pan) -> stereo (2, total_n)."""
    L = np.zeros(total_n)
    R = np.zeros(total_n)
    for beat, durb, midi, vel, pan in events:
        x = synth(midi2f(midi), max(durb * spb, 0.02), vel, sr)
        i0 = int(beat * spb * sr)
        i1 = min(i0 + len(x), total_n)
        if i1 <= i0:
            continue
        seg = x[: i1 - i0]
        L[i0:i1] += seg * math.cos(pan * math.pi / 2)
        R[i0:i1] += seg * math.sin(pan * math.pi / 2)
    return np.stack([L, R])


class Bus:
    def __init__(self, synth, gain=1.0, rev=True, delay=None, pan=0.5):
        self.synth, self.gain, self.rev, self.delay, self.pan = synth, gain, rev, delay, pan
        self.ev = []

    def n(self, beat, dur, midi, vel=1.0, pan=None):
        self.ev.append((beat, dur, midi, vel, self.pan if pan is None else pan))

    def chord(self, beat, dur, midis, vel=1.0, spread=0.0, pan=None):
        for i, m in enumerate(midis):
            self.n(beat + i * spread, dur - i * spread, m, vel, pan)


def mixdown(buses, bpm, beats, tail=3.0, wet=0.25, rev_g=0.78, rev_damp=4200,
            loop=True, rms_target=0.16, sr=SR):
    spb = 60.0 / bpm
    loop_n = int(round(beats * spb * sr))
    total_n = loop_n + int(tail * sr)
    dry = np.zeros((2, total_n))
    send = np.zeros((2, total_n))
    for b in buses:
        st = render_bus(b.ev, b.synth, total_n, spb, sr) * b.gain
        if b.delay:
            tds, fb, mx = b.delay
            for ch in range(2):
                st[ch] = tape_delay(st[ch], sr, tds * spb, fb, mx)
        (send if b.rev else dry).__iadd__(st)
    mix = dry + reverb(send, sr, g=rev_g, wet=wet, damp=rev_damp)
    mix -= mix.mean(axis=1, keepdims=True)
    if loop:                                   # ripiega la coda sull'attacco
        k = total_n - loop_n
        w = 0.5 * (1 + np.cos(np.linspace(0, np.pi, k)))   # 1 -> 0
        out = mix[:, :loop_n].copy()
        out[:, :k] += mix[:, loop_n:] * w
    else:
        out = mix
        k = int(1.2 * sr)
        out[:, -k:] *= np.linspace(1, 0, k) ** 1.5
        a = int(0.004 * sr)
        out[:, :a] *= np.linspace(0, 1, a)
    for _ in range(4):                          # normalizza RMS + limiter
        r = math.sqrt(float(np.mean(out ** 2)))
        out *= rms_target / max(r, 1e-9)
        out = soft_limit(out)
        r = math.sqrt(float(np.mean(out ** 2)))
        if abs(20 * math.log10(r) - 20 * math.log10(rms_target)) < 0.8:
            break
    return out

# ------------------------------------------------------- scale / accordi ---
# midi: C4=60. Voci scritte a mano per ogni brano.

def A(*args):  # scorciatoia per liste di accordi
    return list(args)

# ============================================================== 1. TITLE ===
# 68 BPM, Am - F - C - G lento: piano emotivo + pad caldo + basso, meraviglia.

def compose_title():
    bpm, bars = 68, 20
    beats = bars * 4
    piano = Bus(sy_piano, gain=1.00, delay=(0.75, 0.32, 0.20))
    pad = Bus(make_pad(attack=0.8, release=1.6, fc=900, sub=0.12), gain=0.55)
    bell = Bus(make_bell(ratio=3.0, index=0.9), gain=0.42, delay=(1.5, 0.35, 0.30))
    bass = Bus(sy_bass, gain=0.80, rev=False)

    prog = [  # (root_midi, voicing pad)
        (45, A(57, 60, 64, 71)),   # Am(add9)
        (41, A(53, 57, 60, 64)),   # Fmaj7
        (48, A(55, 60, 64, 71)),   # Cmaj7
        (43, A(55, 59, 62, 69)),   # G(add9)
    ]
    order = [0, 1, 2, 3] * 4 + [1, 3, 0, 3]           # 16 + coda F G Am G
    for bar, ci in enumerate(order):
        root, voic = prog[ci]
        t = bar * 4
        pad.chord(t, 4.2, voic, vel=1.0, spread=0.02)
        bass.n(t, 3.6, root, 0.95)
        if bar % 2 == 1:
            bass.n(t + 2, 1.8, root + 7, 0.55)

    mel = [  # (beat, dur, midi, vel)  frase A (b0-7) + A' (b8-15)
        (0, 2, 76, .95), (2, 1, 72, .8), (3, 1, 74, .85),
        (4, 3, 76, .9), (7, 1, 69, .7),
        (8, 1, 67, .7), (9, 1, 72, .8), (10, 2, 76, .9),
        (12, 3, 74, .9), (15, 1, 71, .7),
        (16, 2, 69, .85), (18, 1, 72, .8), (19, 1, 76, .85),
        (20, 2, 77, .95), (22, 1, 76, .85), (23, 1, 74, .8),
        (24, 3, 76, .9), (27, 1, 67, .65),
        (28, 2, 69, .8), (30, 2, 71, .85),
        (32, 1, 76, .8), (33, 2, 81, 1.0), (35, 1, 79, .9),
        (36, 2, 77, .95), (38, 1, 76, .85), (39, 1, 72, .8),
        (40, 1, 76, .85), (41, 2, 79, .95), (43, 1, 76, .85),
        (44, 3, 74, .9), (47, 1, 76, .8),
        (48, 2, 72, .85), (50, 1, 71, .8), (51, 1, 69, .75),
        (52, 1, 69, .7), (53, 1, 72, .8), (54, 2, 76, .9),
        (56, 2, 74, .85), (58, 1, 72, .8), (59, 1, 71, .75),
        (60, 3, 71, .8), (63, 1, 74, .8),
    ]
    for b, d, m, v in mel:
        piano.n(b, d, m, v)
        if b >= 32:                                    # 2a strofa: campanelli
            bell.n(b, d, m + 12, v * 0.45)
    coda = [(64, 2, 72, .85), (66, 1, 69, .7), (67, 1, 65, .65),
            (68, 4, 67, .8), (72, 4, 69, .85), (76, 2, 71, .8), (78, 2, 74, .85)]
    for b, d, m, v in coda:
        piano.n(b, d, m, v)
    return dict(bpm=bpm, beats=beats, buses=[piano, pad, bell, bass],
                wet=0.28, rev_g=0.80, rms=0.150, hf=False)

# ============================================================ 2. EXPLORE ===
# 100 BPM, curioso: arpeggi di piano delicati su maj7, melodia rada.

def compose_explore():
    bpm, bars = 100, 30
    beats = bars * 4
    arp = Bus(sy_piano, gain=0.80, delay=(0.75, 0.34, 0.24))
    pad = Bus(make_pad(attack=1.0, release=1.4, fc=800), gain=0.40)
    lead = Bus(make_bell(ratio=3.0, index=0.8), gain=0.55, delay=(1.5, 0.3, 0.28))
    bass = Bus(sy_bass, gain=0.72, rev=False)

    prog = [
        (36, A(60, 64, 67, 71)),   # Cmaj7
        (33, A(57, 60, 64, 67)),   # Am7
        (41, A(53, 57, 60, 64)),   # Fmaj7
        (43, A(55, 59, 62, 67)),   # G
    ]
    pattern = [0, 1, 2, 3, 4, 3, 2, 1]                 # su e giu', 8i
    for bar in range(bars):
        root, voic = prog[bar % 4]
        notes = voic + [voic[0] + 12]
        t = bar * 4
        for i, pi in enumerate(pattern):
            v = 0.62 if i % 2 else 0.80
            if bar < 2:
                v *= 0.7                              # intro in punta di dita
            arp.n(t + i * 0.5, 0.55, notes[pi], v, pan=0.38 + 0.24 * (i % 2))
        if bar % 2 == 0:
            pad.chord(t, 8.3, voic, vel=0.9, spread=0.03)
        bass.n(t, 3.5, root, 0.9)
    mel = [  # entra alla battuta 8, curiosa, con salti
        (32, 2, 76, .8), (34, 2, 79, .85),
        (36, 3, 81, .9), (39, 1, 79, .8),
        (40, 2, 76, .8), (42, 2, 74, .75),
        (44, 4, 74, .7),
        (48, 2, 72, .75), (50, 2, 76, .8),
        (52, 2, 79, .85), (54, 1, 81, .85), (55, 1, 83, .9),
        (56, 4, 79, .85),
        (64, 2, 84, .85), (66, 2, 81, .8),
        (68, 3, 79, .85), (71, 1, 76, .75),
        (72, 2, 79, .8), (74, 2, 76, .75),
        (76, 4, 74, .75),
        (80, 2, 72, .75), (82, 1, 74, .75), (83, 1, 76, .8),
        (84, 2, 79, .85), (86, 2, 74, .75),
        (88, 4, 72, .8),
    ]
    for b, d, m, v in mel:
        lead.n(b, d, m, v)
    return dict(bpm=bpm, beats=beats, buses=[arp, pad, lead, bass],
                wet=0.22, rev_g=0.78, rms=0.150, hf=False)

# ============================================================== 3. HYDRO ===
# 84 BPM, Re maggiore sognante: campanelli FM morbidi, pad verde, arpa-piano.

def compose_hydro():
    bpm, bars = 84, 26
    beats = bars * 4
    bell = Bus(make_bell(ratio=3.0, index=1.0, decay=2.0), gain=0.62,
               delay=(1.5, 0.38, 0.32))
    pad = Bus(make_pad(attack=1.2, release=1.8, fc=750, shimmer=0.06), gain=0.48)
    arp = Bus(sy_piano, gain=0.55, delay=(0.75, 0.3, 0.18))
    bass = Bus(sy_bass, gain=0.70, rev=False)

    prog = [
        (38, A(62, 66, 69, 73)),   # Dmaj7
        (43, A(55, 59, 62, 66)),   # Gmaj7
        (35, A(59, 62, 66, 69)),   # Bm7
        (33, A(57, 61, 64, 71)),   # A(add9)
    ]
    for bar in range(bars):
        root, voic = prog[bar % 4]
        t = bar * 4
        if bar % 2 == 0:
            pad.chord(t, 8.4, voic, vel=1.0, spread=0.04)
        bass.n(t, 3.6, root, 0.85)
        if bar >= 2:                                   # arpa discreta, 8i radi
            for i, pi in enumerate([0, 2, 3, 2]):
                arp.n(t + i, 1.0, voic[pi] + 12, 0.42, pan=0.35 + 0.3 * (i % 2))
    mel = [  # frase di 8 battute x2 (entra a b2), pentatonica di Re
        (8, 2, 81, .9), (10, 2, 78, .8),
        (12, 3, 76, .85), (15, 1, 74, .7),
        (16, 2, 78, .8), (18, 1, 81, .85), (19, 1, 83, .9),
        (20, 4, 81, .9),
        (24, 2, 78, .8), (26, 2, 76, .75),
        (28, 3, 74, .8), (31, 1, 76, .7),
        (32, 2, 78, .8), (34, 2, 76, .75),
        (36, 4, 74, .8),
        (40, 2, 81, .85), (42, 2, 78, .8),
        (44, 3, 76, .8), (47, 1, 74, .7),
        (48, 2, 78, .8), (50, 1, 81, .85), (51, 1, 83, .85),
        (52, 4, 85, .9),
        (56, 2, 83, .85), (58, 2, 81, .8),
        (60, 3, 78, .8), (63, 1, 76, .7),
        (64, 2, 74, .75), (66, 2, 78, .8),
        (68, 4, 74, .8),
        (76, 2, 69, .6), (78, 2, 73, .6),              # coda bassa, sospesa
        (80, 4, 74, .7), (84, 4, 78, .55), (88, 4, 74, .5),
        (96, 4, 74, .45), (100, 4, 81, .4),
    ]
    for b, d, m, v in mel:
        bell.n(b, d, m, v)
    return dict(bpm=bpm, beats=beats, buses=[bell, pad, arp, bass],
                wet=0.32, rev_g=0.82, rms=0.145, hf=False)

# ============================================================== 4. RUINS ===
# 56 BPM, Mi minore modale: corale sintetico lento, drone, riverbero fondo.

def compose_ruins():
    bpm, bars = 56, 18
    beats = bars * 4
    choir = Bus(make_pad(attack=1.6, release=2.2, fc=650,
                         detunes=(-12.0, -5.0, 0.0, 6.0, 12.0)), gain=0.55)
    voice = Bus(make_pad(attack=0.9, release=1.6, fc=900,
                         detunes=(-4.0, 4.0)), gain=0.50)
    glint = Bus(make_bell(ratio=3.53, index=1.4, decay=1.6), gain=0.30,
                delay=(2.0, 0.42, 0.4))
    drone = Bus(sy_bass, gain=0.62, rev=False)

    prog = [
        A(52, 59, 64, 66),    # Em(add9)
        A(48, 55, 59, 64),    # Cmaj7
        A(45, 52, 59, 64),    # Asus2
        A(47, 54, 59, 64),    # Bsus4
    ]
    order = [0, 0, 1, 1, 2, 2, 3, 3] * 2 + [0, 0]
    for bar, ci in enumerate(order):
        t = bar * 4
        if bar % 2 == 0:
            choir.chord(t, 8.6, prog[ci], vel=1.0, spread=0.08)
    drone.n(0, beats + 1, 40, 0.9)                    # E2, tutto il brano
    drone.n(0, beats + 1, 28, 0.4)                    # E1 sotto pelle
    mel = [  # voce corale solista, lunga e modale
        (8, 6, 64, .8), (14, 2, 66, .7),
        (16, 6, 67, .85), (22, 2, 64, .7),
        (24, 8, 71, .85),
        (32, 4, 67, .8), (36, 4, 66, .75),
        (40, 6, 64, .8), (46, 2, 62, .7),
        (48, 8, 60, .8),
        (56, 6, 66, .8), (62, 2, 59, .7),
        (64, 8, 64, .85),
    ]
    for b, d, m, v in mel:
        voice.n(b, d, m, v)
    for b, m, v in [(6, 88, .5), (20, 83, .45), (30, 90, .5), (44, 86, .4),
                    (54, 88, .45), (62, 91, .5), (68, 83, .4)]:
        glint.n(b, 1.5, m, v, pan=0.3 + 0.4 * RNG.random())
    return dict(bpm=bpm, beats=beats, buses=[choir, voice, glint, drone],
                wet=0.5, rev_g=0.86, rev_damp=3600, rms=0.140, hf=False)

# ============================================================== 5. BATTLE ==
# 126 BPM, La minore: quattro-sul-pavimento, riff di saw, stab, basso in 8i.

def compose_battle():
    bpm, bars = 126, 32
    beats = bars * 4
    lead = Bus(make_lead(fc=3400), gain=0.62, delay=(0.75, 0.3, 0.18))
    stab = Bus(make_pad(attack=0.006, release=0.22, fc=1800), gain=0.5)
    bass = Bus(sy_bass, gain=0.85, rev=False)
    kick = Bus(sy_kick, gain=0.9, rev=False)
    hat = Bus(sy_hat, gain=0.55, rev=False)
    snare = Bus(sy_snare, gain=0.6)

    MIN, MAJ = [0, 3, 7, 3, 0, -2, 0], [0, 4, 7, 4, 0, -1, 0]
    secA = [(69, MIN), (69, MIN), (65, MAJ), (65, MAJ),
            (67, MAJ), (67, MAJ), (64, MIN), (64, MIN)]
    chordsA = [A(57, 60, 64), A(53, 57, 60), A(55, 59, 62), A(52, 55, 59)]
    riff_beats = [0, .5, 1, 1.5, 2, 2.5, 3]

    def riff_bar(bus, t, root, iv, vel, oct_=0):
        for i, off in enumerate(iv):
            d = 1.0 if i == len(iv) - 1 else 0.48
            bus.n(t + riff_beats[i], d, root + off + oct_, vel * (1 - 0.12 * (i % 2)))

    def bass_bar(t, root):
        for i, off in enumerate([0, 0, 0, 0, 12, 0, 10, 12]):
            bass.n(t + i * 0.5, 0.42, root + off, 0.95 if i in (0, 4) else 0.75)

    def drums_bar(t, fill=False, lite=False):
        for b in range(4):
            kick.n(t + b, 0.2, 0, 1.0 if b in (0, 2) else 0.85)
        if not lite:
            snare.n(t + 1, 0.2, 0, 0.9)
            snare.n(t + 3, 0.2, 0, 0.9)
        for i in range(8):
            hat.n(t + i * 0.5, 0.05 if i % 2 == 0 else 0.11, 0,
                  0.5 if i % 2 == 0 else 0.8, pan=0.62)
        if fill:
            for i in range(4):
                snare.n(t + 3 + i * 0.25, 0.1, 0, 0.55 + 0.12 * i)

    bassroots = {69: 45, 65: 41, 67: 43, 64: 40, 62: 38, 57: 45}
    bar = 0
    for i in range(4):                                  # intro: si accende
        root, iv = secA[i * 2]
        t = bar * 4
        riff_bar(lead, t, root, iv, 0.5 + 0.1 * i)
        bass_bar(t, bassroots[root])
        drums_bar(t, lite=(i < 2), fill=(i == 3))
        bar += 1
    for i in range(8):                                  # sezione A: riff pieno
        root, iv = secA[i]
        t = bar * 4
        riff_bar(lead, t, root, iv, 0.9)
        stab.chord(t, 0.6, chordsA[i // 2], 0.9)
        stab.chord(t + 1.5, 0.5, chordsA[i // 2], 0.7)
        stab.chord(t + 3.0, 0.5, chordsA[i // 2], 0.8)
        bass_bar(t, bassroots[root])
        drums_bar(t, fill=(i in (3, 7)))
        bar += 1
    secB = [(A(53, 57, 60), 41), (A(55, 59, 62), 43), (A(57, 60, 64), 45),
            (A(52, 55, 59), 40), (A(53, 57, 60), 41), (A(55, 59, 62), 43),
            (A(52, 56, 59), 40), (A(52, 56, 59), 40)]   # ...E maggiore: tensione
    melB = [
        (0, 2, 69, .9), (2, 1, 72, .85), (3, 1, 74, .9),
        (4, 3, 76, 1.0), (7, 1, 74, .85),
        (8, 2, 72, .9), (10, 1, 71, .85), (11, 1, 69, .8),
        (12, 4, 71, .9),
        (16, 1, 69, .85), (17, 1, 72, .9), (18, 2, 77, 1.0),
        (20, 2, 76, .95), (22, 1, 74, .85), (23, 1, 71, .8),
        (24, 2, 68, .95), (26, 2, 71, .9),
        (28, 4, 68, .95),
    ]
    tB = bar * 4
    for i, (ch, rt) in enumerate(secB):                 # sezione B: anthem
        t = tB + i * 4
        stab.chord(t, 0.6, ch, 0.9)
        stab.chord(t + 1.5, 0.5, ch, 0.75)
        stab.chord(t + 2.5, 0.5, ch, 0.7)
        bass_bar(t, rt)
        drums_bar(t, fill=(i in (3, 7)))
    for b, d, m, v in melB:
        lead.n(tB + b, d, m, v)
        lead.n(tB + b, d, m + 12, v * 0.5)
    bar += 8
    for i in range(8):                                  # A': riff ottava sopra
        root, iv = secA[i]
        t = bar * 4
        riff_bar(lead, t, root, iv, 0.85)
        riff_bar(lead, t, root, iv, 0.45, oct_=12)
        stab.chord(t, 0.6, chordsA[i // 2], 0.9)
        stab.chord(t + 1.5, 0.5, chordsA[i // 2], 0.7)
        bass_bar(t, bassroots[root])
        drums_bar(t, fill=(i in (3, 7)))
        bar += 1
    turn = [(A(53, 57, 60), 41), (A(55, 59, 62), 43),
            (A(52, 56, 59), 40), (A(52, 56, 59), 40)]   # F G E E -> loop in Am
    for i, (ch, rt) in enumerate(turn):
        t = (bar + i) * 4
        stab.chord(t, 0.7, ch, 0.95)
        stab.chord(t + 2, 0.6, ch, 0.8)
        bass_bar(t, rt)
        drums_bar(t, fill=(i == 3))
        lead.n(t, 4, ch[-1] + 12, 0.7)
    return dict(bpm=bpm, beats=beats, buses=[lead, stab, bass, kick, hat, snare],
                wet=0.14, rev_g=0.74, rms=0.200, hf=True)

# ================================================================ 6. BOSS ==
# 120 BPM, Re minore con seconda bemolle: basso insistente in 8i, epico-teso.

def compose_boss():
    bpm, bars = 120, 32
    beats = bars * 4
    bass = Bus(sy_bass, gain=0.95, rev=False)
    lead = Bus(make_lead(fc=3000, detunes=(-9.0, 8.0)), gain=0.58,
               delay=(0.5, 0.28, 0.16))
    choir = Bus(make_pad(attack=0.7, release=1.4, fc=700,
                         detunes=(-11.0, -4.0, 0.0, 5.0, 11.0)), gain=0.5)
    kick = Bus(sy_kick, gain=0.95, rev=False)
    hat = Bus(sy_hat, gain=0.5, rev=False)
    snare = Bus(sy_snare, gain=0.62)

    def bass_bars(t, root, tense=True):
        pa = [0, 0, 0, 0, 0, 0, 1, 1] if tense else [0, 0, 0, 0, 0, 0, 0, 0]
        pb = [0, 0, 0, 0, -2, 0, 1, 0]
        for i, off in enumerate(pa):
            bass.n(t + i * 0.5, 0.42, root + off, 0.95 if i % 4 == 0 else 0.78)
        for i, off in enumerate(pb):
            bass.n(t + 4 + i * 0.5, 0.42, root + off, 0.95 if i % 4 == 0 else 0.78)

    def drums_bars(t, heavy=True, fill=False):
        for tb in (t, t + 4):
            for b in (0, 1.75, 2.5):
                kick.n(tb + b, 0.2, 0, 1.0 if b == 0 else 0.8)
            snare.n(tb + 1, 0.2, 0, 0.85)
            snare.n(tb + 3, 0.2, 0, 0.9)
            step = 0.5 if not heavy else 0.25
            i = 0.0
            while i < 4:
                hat.n(tb + i, 0.05, 0, 0.42 + 0.28 * (int(i * 4) % 2), pan=0.6)
                i += step
        if fill:
            for i in range(6):
                snare.n(t + 6.5 + i * 0.25, 0.1, 0, 0.5 + 0.09 * i)

    Dm, Bb, Gm, Amaj, Eb = A(62, 65, 69), A(58, 62, 65), A(55, 58, 62), \
        A(57, 61, 64), A(58, 63, 67)
    for i in range(2):                                  # intro 4 bar: basso+kick
        t = i * 8
        bass_bars(t, 38)
        drums_bars(t, heavy=False, fill=(i == 1))
        choir.chord(t, 8.4, A(62, 65, 69), 0.55 + 0.2 * i, spread=0.05)
    secA = [(38, Dm), (38, Dm), (34, Bb), (33, Amaj)]   # radici: D D Bb A
    melA = [(0, 3, 74, .95), (3, 1, 72, .85),
            (4, 2, 75, 1.0), (6, 2, 74, .9),
            (8, 3, 77, .95), (11, 1, 74, .85),
            (12, 2, 76, .95), (14, 2, 73, .9)]
    for rep in range(2):                                # sezione A x2
        t0 = 16 + rep * 16
        for i, (rt, ch) in enumerate(secA):
            t = t0 + i * 4
            if i % 2 == 0:
                bass_bars(t, rt, tense=(ch is Dm))
                drums_bars(t, fill=(i == 2))
                choir.chord(t, 8.4, ch, 0.8, spread=0.05)
        for b, d, m, v in melA:
            lead.n(t0 + b, d, m + (12 if rep else 0), v)
            if rep:
                lead.n(t0 + b, d, m, v * 0.5)
    secB = [(31, Gm), (27, Eb), (38, Dm), (33, Amaj)]   # G Eb D A
    melB = [(0, 2, 70, .9), (2, 2, 74, .95),
            (4, 3, 75, 1.0), (7, 1, 74, .9),
            (8, 2, 74, .95), (10, 2, 72, .9),
            (12, 2, 73, .95), (14, 2, 76, 1.0)]
    for rep in range(2):                                # sezione B (epica) x2
        t0 = 48 + rep * 16
        for i, (rt, ch) in enumerate(secB):
            t = t0 + i * 4
            if i % 2 == 0:
                bass_bars(t, rt)
                drums_bars(t, fill=(i == 2 and rep == 1))
                choir.chord(t, 8.4, [n + 12 for n in ch], 0.85, spread=0.05)
                choir.chord(t, 8.4, ch, 0.6, spread=0.05)
        for b, d, m, v in melB:
            lead.n(t0 + b, d, m, v)
    for i in range(4):                                  # coda: Eb Eb A A -> Dm
        t = (28 + i) * 4
        rt, ch = (27, Eb) if i < 2 else (33, Amaj)
        if i % 2 == 0:
            bass_bars(t, rt)
            drums_bars(t, fill=(i == 2))
            choir.chord(t, 8.4, ch, 0.85, spread=0.05)
    lead.n(112, 4, 75, .9)
    lead.n(116, 4, 74, .85)
    lead.n(120, 4, 73, .9)
    lead.n(124, 4, 76, .95)
    return dict(bpm=bpm, beats=beats, buses=[bass, lead, choir, kick, hat, snare],
                wet=0.16, rev_g=0.76, rms=0.200, hf=True)

# ============================================================= 7. VICTORY ==
# ~8 s, 132 BPM: jingle luminoso in Do maggiore, niente loop.

def compose_victory():
    bpm = 132
    beats = 10
    piano = Bus(sy_piano, gain=0.95)
    bell = Bus(make_bell(ratio=3.0, index=0.9), gain=0.6, delay=(0.75, 0.3, 0.25))
    pad = Bus(make_pad(attack=0.05, release=2.2, fc=1100), gain=0.5)
    bass = Bus(sy_bass, gain=0.8, rev=False)
    fanfare = [(0, .5, 67, .85), (.5, .5, 72, .9), (1, .5, 76, .95),
               (1.5, 1.5, 79, 1.0), (3, 1, 81, .95), (4, .75, 79, .9),
               (4.75, .25, 77, .8), (5, 4, 84, 1.0)]
    for b, d, m, v in fanfare:
        piano.n(b, d, m, v)
        bell.n(b, d, m + 12, v * 0.5)
    pad.chord(0, 1.4, A(60, 64, 67), .8)
    pad.chord(1.5, 1.4, A(60, 65, 69), .85)            # F/C
    pad.chord(3, 1.9, A(59, 62, 67), .85)              # G
    pad.chord(5, 4.5, A(60, 64, 67, 72), 1.0, spread=0.04)
    bass.n(0, 1.4, 36, .9)
    bass.n(1.5, 1.4, 41, .9)
    bass.n(3, 1.9, 43, .9)
    bass.n(5, 4.5, 36, 1.0)
    return dict(bpm=bpm, beats=beats, buses=[piano, bell, pad, bass],
                wet=0.3, rev_g=0.8, rms=0.170, hf=False, loop=False, tail=2.5)

# ============================================================== 8. ENDING ==
# 68 BPM, tema del titolo ripreso in DO MAGGIORE: commosso, risolutivo.

def compose_ending():
    bpm, bars = 68, 20
    beats = bars * 4
    piano = Bus(sy_piano, gain=1.0, delay=(0.75, 0.32, 0.2))
    pad = Bus(make_pad(attack=0.9, release=1.8, fc=950, sub=0.12, shimmer=0.05),
              gain=0.58)
    bell = Bus(make_bell(ratio=3.0, index=0.85), gain=0.45, delay=(1.5, 0.34, 0.3))
    bass = Bus(sy_bass, gain=0.78, rev=False)

    prog = [
        (48, A(55, 60, 64, 71)),   # Cmaj7
        (43, A(55, 59, 62, 69)),   # G(add9)
        (45, A(57, 60, 64, 71)),   # Am(add9)
        (41, A(53, 57, 60, 64)),   # Fmaj7
    ]
    order = [0, 1, 2, 3] * 4 + [3, 1, 0, 0]            # coda F G C C
    for bar, ci in enumerate(order):
        root, voic = prog[ci]
        t = bar * 4
        pad.chord(t, 4.2, voic, vel=1.0, spread=0.03)
        bass.n(t, 3.6, root, 0.9)
        if bar % 2 == 1:
            bass.n(t + 2, 1.8, root + 7, 0.5)
    # Tema del titolo (stesso profilo melodico) riarmonizzato in maggiore.
    mel = [
        (0, 2, 76, .9), (2, 1, 74, .8), (3, 1, 76, .85),
        (4, 3, 79, .95), (7, 1, 74, .8),
        (8, 2, 76, .85), (10, 1, 72, .8), (11, 1, 74, .8),
        (12, 3, 76, .9), (15, 1, 72, .75),
        (16, 2, 79, .95), (18, 1, 76, .85), (19, 1, 74, .8),
        (20, 2, 74, .85), (22, 2, 71, .8),
        (24, 2, 72, .85), (26, 1, 71, .8), (27, 1, 69, .75),
        (28, 2, 69, .8), (30, 1, 71, .8), (31, 1, 74, .85),
        (32, 2, 76, .9), (34, 1, 79, .95), (35, 1, 81, 1.0),
        (36, 3, 79, .95), (39, 1, 74, .85),
        (40, 2, 81, .95), (42, 1, 79, .9), (43, 1, 76, .85),
        (44, 3, 76, .9), (47, 1, 72, .8),
        (48, 2, 84, 1.0), (50, 1, 83, .9), (51, 1, 81, .9),
        (52, 2, 79, .9), (54, 2, 76, .85),
        (56, 2, 74, .85), (58, 1, 76, .85), (59, 1, 79, .9),
        (60, 4, 76, .9),
    ]
    for b, d, m, v in mel:
        piano.n(b, d, m, v)
        if b >= 32:
            bell.n(b, d, m + 12, v * 0.45)
    coda = [(64, 2, 72, .85), (66, 2, 74, .85), (68, 2, 74, .85),
            (70, 2, 71, .8), (72, 4, 72, .9), (76, 4, 76, .8)]
    for b, d, m, v in coda:
        piano.n(b, d, m, v)
    bell.n(72, 6, 84, .5)
    bell.n(76, 4, 88, .4)
    return dict(bpm=bpm, beats=beats, buses=[piano, pad, bell, bass],
                wet=0.3, rev_g=0.82, rms=0.150, hf=False)

# ------------------------------------------------------------------- main --

TRACKS = {
    "title": compose_title,
    "explore": compose_explore,
    "hydro": compose_hydro,
    "ruins": compose_ruins,
    "battle": compose_battle,
    "boss": compose_boss,
    "victory": compose_victory,
    "ending": compose_ending,
}


def write_wav(path, st, sr=SR):
    data = np.clip(st, -1.0, 1.0)
    pcm = (data.T * 32767.0).astype("<i2")             # (n, 2) interleave
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def metrics(st, sr=SR):
    peak = float(np.max(np.abs(st)))
    rms = math.sqrt(float(np.mean(st ** 2)))
    mono = st.mean(0)
    spec = np.abs(np.fft.rfft(mono)) ** 2
    freqs = np.fft.rfftfreq(len(mono), 1 / sr)
    hf = float(spec[freqs > 2000].sum() / max(spec.sum(), 1e-12))
    return peak, 20 * math.log10(max(rms, 1e-9)), hf


def main(names):
    os.makedirs(OUT_DIR, exist_ok=True)
    report = []
    for name in names:
        spec = TRACKS[name]()
        print(f"[{name}] compongo e sintetizzo...", flush=True)
        st = mixdown(spec["buses"], spec["bpm"], spec["beats"],
                     tail=spec.get("tail", 3.0), wet=spec["wet"],
                     rev_g=spec["rev_g"], rev_damp=spec.get("rev_damp", 4200),
                     loop=spec.get("loop", True), rms_target=spec["rms"])
        path = os.path.join(OUT_DIR, f"{name}.wav")
        write_wav(path, st)
        pk, rms_db, hf = metrics(st)
        dur = st.shape[1] / SR
        ok = (pk < 0.95 and -20.0 <= rms_db <= -12.0
              and (hf >= 0.02 if spec["hf"] else True))
        report.append((name, dur, pk, rms_db, hf, ok))
        print(f"[{name}] {dur:6.1f}s  peak={pk:.3f}  RMS={rms_db:6.1f} dBFS  "
              f"HF>2k={hf * 100:5.2f}%  {'PASS' if ok else 'FAIL'}", flush=True)
    print("\n=== REPORT ===")
    for name, dur, pk, rms_db, hf, ok in report:
        print(f"{name:8s} dur={dur:6.1f}s peak={pk:.3f} rms={rms_db:6.1f}dBFS "
              f"hf2k={hf * 100:5.2f}% {'PASS' if ok else 'FAIL'}")
    if not all(r[-1] for r in report):
        sys.exit(1)


if __name__ == "__main__":
    args = sys.argv[1:] or list(TRACKS)
    bad = [a for a in args if a not in TRACKS]
    if bad:
        sys.exit(f"tracce sconosciute: {bad}")
    main(args)
