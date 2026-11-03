# 《山河织路》 — original procedural score for the 102 s demo film.
# Pure numpy synthesis: pads, noise beds, chimes, bells, rail clacks, launch.
# No samples, no external music. Same chord material as src/audio.js.
import numpy as np, wave, os

SR = 44100
DUR = 102.0
N = int(SR * DUR)
rng = np.random.default_rng(20261029)
L = np.zeros(N, np.float32)
R = np.zeros(N, np.float32)

def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)

def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)

def add(x, start, pan=0.0, gain=1.0):
    """x: mono float array; pan -1..1."""
    i = int(start * SR)
    if i >= N: return
    x = x[: N - i]
    gl = np.sqrt((1 - pan) / 2) * gain
    gr = np.sqrt((1 + pan) / 2) * gain
    L[i:i+len(x)] += x * gl
    R[i:i+len(x)] += x * gr

def env_ad(n, a, r, hold=1.0):
    e = np.ones(n, np.float32) * hold
    na = min(n, int(a * SR)); nr = min(n, int(r * SR))
    if na:
        u = np.linspace(0, 1, na, endpoint=False, dtype=np.float32)
        e[:na] *= smooth(u)
    if nr:
        u = np.linspace(0, 1, nr, endpoint=False, dtype=np.float32)
        e[-nr:] *= smooth(1 - u)
    return e

def pad(t0, t1, notes, level=0.06, a=2.6, r=2.6, sub=True):
    n = int((t1 - t0) * SR)
    if n <= 0: return
    t = np.arange(n, dtype=np.float32) / SR
    e = env_ad(n, a, r)
    outL = np.zeros(n, np.float32); outR = np.zeros(n, np.float32)
    for k, m in enumerate(notes):
        f = midi(m)
        for det, pan in ((-0.0011, -0.55), (0.0011, 0.55)):
            ph = rng.uniform(0, 6.283)
            w = (np.sin(2*np.pi*f*(1+det)*t + ph)
                 + 0.16*np.sin(2*np.pi*f*2*(1+det)*t + ph*0.7)
                 + 0.055*np.sin(2*np.pi*f*3*(1+det)*t + ph*1.3))
            lfo = 1 + 0.10*np.sin(2*np.pi*(0.055 + 0.008*k)*t + ph)
            x = (w * lfo * e).astype(np.float32)
            gl = np.sqrt((1-pan)/2); gr = np.sqrt((1+pan)/2)
            outL += x * gl; outR += x * gr
    if sub:
        f = midi(notes[0] - 12)
        x = (np.sin(2*np.pi*f*t) * e).astype(np.float32)
        outL += x * 0.6; outR += x * 0.6
    i = int(t0 * SR)
    n2 = min(n, N - i)
    L[i:i+n2] += outL[:n2] * level
    R[i:i+n2] += outR[:n2] * level

def noise_bed(t0, t1, lo, hi, level=0.03, brown=False, trem=0.0, pan=0.0):
    n = int((t1 - t0) * SR)
    if n <= 0: return
    x = rng.standard_normal(n).astype(np.float32)
    if brown:
        x = np.cumsum(x, dtype=np.float32)
        x /= (np.max(np.abs(x)) + 1e-9)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    if lo > 0:
        g = 1 / (1 + (lo / np.maximum(f, 1e-3)) ** 4)
    else:
        g = np.ones_like(f)
    if hi > 0:
        g *= 1 / (1 + (f / hi) ** 4)
    x = np.fft.irfft(X * g, n).astype(np.float32)
    x /= (np.sqrt(np.mean(x*x)) + 1e-9)
    t = np.arange(n, dtype=np.float32) / SR
    e = env_ad(n, 2.2, 2.2)
    if trem:
        e *= (0.75 + 0.25*np.sin(2*np.pi*trem*t + rng.uniform(0, 6.28)))
    add(x * e * level, t0, pan, 1)
    # decorrelated opposite channel
    y = np.roll(x, 137) * e * level
    add(y, t0, -pan if pan else 0.7, 1)

def chime(t, note, amp=0.045, dur=3.4, pan=0.0):
    n = int(dur * SR)
    tt = np.arange(n, dtype=np.float32) / SR
    f = midi(note)
    e = np.exp(-tt / 0.72) * (1 - np.exp(-tt * 90))
    x = (np.sin(2*np.pi*f*tt) * e
         + 0.38*np.sin(2*np.pi*f*2.01*tt) * np.exp(-tt/0.38)
         + 0.16*np.sin(2*np.pi*f*3.98*tt) * np.exp(-tt/0.22)).astype(np.float32)
    add(x * amp, t, pan, 1)

def bell(t, amp=0.05, pan=0.0):
    for k, f in enumerate((1180, 1480, 2640)):
        n = int(0.9 * SR)
        tt = np.arange(n, dtype=np.float32) / SR
        e = np.exp(-tt/(0.42 - k*0.09)) * (1 - np.exp(-tt*120))
        add((np.sin(2*np.pi*f*tt)*e*amp*(1 - k*0.25)).astype(np.float32), t + k*0.13, pan, 1)

def bird(t, base=2500):
    d = 0.16
    n = int(d * SR); tt = np.arange(n, dtype=np.float32) / SR
    f0 = base * rng.uniform(.85, 1.25); f1 = f0 * rng.uniform(.55, .8)
    ph = 2*np.pi*(f0*tt + (f1-f0)*tt*tt/(2*d))
    e = np.exp(-tt/0.055) * (1 - np.exp(-tt*180))
    add((np.sin(ph)*e*0.022).astype(np.float32), t, rng.uniform(-.7,.7), 1)

def horn(t, f=225, amp=0.022):
    n = int(0.45*SR); tt = np.arange(n, dtype=np.float32)/SR
    e = np.minimum(tt/0.03, 1) * np.minimum((0.45-tt)/0.12, 1)
    x = sum((1.0/(h**1.7))*np.sin(2*np.pi*f*h*tt) for h in range(1,6))
    add((x*e*amp).astype(np.float32), t, rng.uniform(-.5,.5), 1)

def clack(t, amp=0.035):
    for d, f in ((0.0, 1450), (0.16, 2100)):
        n = int(0.11*SR); tt = np.arange(n, dtype=np.float32)/SR
        x = rng.standard_normal(n).astype(np.float32)
        X = np.fft.rfft(x); ff = np.fft.rfftfreq(n, 1/SR)
        g = np.exp(-((ff - f)/(f*0.55))**2)
        x = np.fft.irfft(X*g, n).astype(np.float32)
        e = np.exp(-tt/0.028) * (1 - np.exp(-tt*900))
        add((x*e*amp).astype(np.float32), t+d, 0.15 if d else -0.15, 1)

def whoosh(t, amp=0.05, dur=1.7):
    n = int(dur*SR); x = rng.standard_normal(n).astype(np.float32)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1/SR)
    g = np.exp(-((np.log2(np.maximum(f,1)/900))/0.55)**2)
    x = np.fft.irfft(X*g, n).astype(np.float32)
    x /= (np.sqrt(np.mean(x*x))+1e-9)
    tt = np.arange(n,dtype=np.float32)/SR
    e = np.sin(np.pi*np.clip(tt/dur,0,1))**2
    add((x*e*amp).astype(np.float32), t, 0, 1)

def rocket(t0, t1):
    n = int((t1-t0)*SR); tt = np.arange(n, dtype=np.float32)/SR
    x = np.cumsum(rng.standard_normal(n).astype(np.float32))
    x /= (np.max(np.abs(x))+1e-9)
    X = np.fft.rfft(x); f = np.fft.rfftfreq(n,1/SR)
    g = 1/(1+(f/180)**2)
    x = np.fft.irfft(X*g,n).astype(np.float32)
    e = np.minimum(tt/1.6,1) * np.minimum(np.clip((t1-t0-tt)/3.0,0,1),1)
    e *= (1 + 0.12*np.sin(2*np.pi*3.1*tt))
    add((x*e*0.20).astype(np.float32), t0, 0, 1)
    # sub sweep
    fsw = 55*np.exp(-tt/9) + 27
    ph = 2*np.pi*np.cumsum(fsw)/SR
    add((np.sin(ph)*e*0.10).astype(np.float32), t0, 0, 1)
    # airy hiss
    y = rng.standard_normal(n).astype(np.float32)
    Y = np.fft.rfft(y); g2 = 1/(1+(3000/np.maximum(f,1))**4)
    y = np.fft.irfft(Y*g2,n).astype(np.float32)
    y /= (np.sqrt(np.mean(y*y))+1e-9)
    add((y*e*0.018).astype(np.float32), t0, 0, 1)

def pingpong(x, delay=0.34, fb=0.26, mix=0.22, taps=4):
    d = int(delay*SR)
    y = x.copy()
    for k in range(1, taps+1):
        if k*d >= len(x): break
        y[k*d:] += x[:-k*d] * (mix * (fb ** (k-1)))
    return y

# ---------------- arrangement ----------------
# pads: five eras + landing / prompt / launch / overview / end
pad(0.0, 6.4, [50, 57, 62, 66], 0.060, a=3.6, r=2.0)
pad(4.8, 19.6, [50, 57, 62, 66], 0.062)
pad(18.8, 33.6, [48, 55, 60, 64], 0.062)
pad(32.8, 47.6, [45, 52, 57, 60], 0.060)
pad(46.8, 61.6, [43, 50, 55, 59], 0.062)
pad(60.8, 75.5, [38, 45, 50, 53], 0.068)
pad(74.6, 79.2, [38, 45, 50, 53], 0.040, a=1.4, r=1.2)
pad(78.0, 90.6, [38, 45, 50, 53], 0.040, a=1.2, r=2.2)
pad(89.6, 96.6, [50, 57, 62, 66, 69], 0.058, a=2.4, r=2.2)
pad(95.8, 102.0, [50, 57, 62, 66], 0.045, a=2.0, r=4.0)

# beds
noise_bed(0.0, 6.4, 180, 900, 0.018, trem=0.09)
noise_bed(4.8, 19.4, 160, 1000, 0.030, trem=0.07)
noise_bed(19.0, 33.4, 260, 1100, 0.020, trem=0.05)
noise_bed(33.0, 47.4, 1200, 9000, 0.022, trem=0.13)
noise_bed(33.0, 47.4, 80, 260, 0.020, brown=True)
noise_bed(47.0, 61.4, 200, 1400, 0.028, trem=0.10)
noise_bed(47.0, 61.4, 70, 220, 0.020, brown=True)
noise_bed(61.0, 75.4, 4200, 12000, 0.007, trem=0.045)
noise_bed(61.0, 75.4, 60, 200, 0.018, brown=True)
noise_bed(89.6, 96.8, 300, 1800, 0.012, trem=0.05)

# whooshes on the four transitions
for t in (18.4, 32.4, 46.4, 60.4):
    whoosh(t, 0.040, 2.1)

# rural birds
for t in (6.6, 8.1, 10.3, 12.6, 14.9, 16.8, 18.0):
    bird(t, 2300 + rng.uniform(-300, 500))
# town bells + murmur accents
for t in (20.2, 26.1, 31.3):
    bell(t, 0.035, 0.35)
# city horns
for t in (35.4, 41.8):
    horn(t, 220 + rng.uniform(-15, 15), 0.016)
# rail clacks (two bogies)
for t in np.arange(48.0, 60.8, 0.86):
    clack(float(t), 0.030)

# pentatonic chimes
for t, n, p in [
    (7.0, 74, -0.4), (9.6, 78, 0.3), (12.4, 81, -0.2), (15.2, 83, 0.45), (17.6, 76, -0.35),
    (21.0, 72, 0.3), (24.0, 76, -0.3), (26.6, 79, 0.15), (29.4, 74, -0.4), (31.4, 81, 0.35),
    (35.6, 69, -0.35), (38.4, 72, 0.3), (41.6, 76, -0.2), (44.2, 74, 0.4),
    (49.2, 74, -0.3), (52.0, 78, 0.25), (54.6, 81, -0.4), (57.2, 83, 0.3), (59.6, 78, -0.15),
    (63.4, 62, -0.2), (66.2, 65, 0.3), (69.0, 69, -0.35), (72.0, 74, 0.2),
    (90.8, 74, -0.3), (92.6, 78, 0.25), (94.6, 81, -0.2), (95.8, 86, 0.3),
    (97.8, 83, -0.25), (100.0, 74, 0.1),
]:
    chime(t, n, 0.040 if t < 89 else 0.033, 3.2, p)

# launch
rocket(78.2, 90.0)
# end gong + soft bell
n = int(5.0*SR); tt = np.arange(n,dtype=np.float32)/SR
e = np.exp(-tt/1.9) * (1-np.exp(-tt*70))
gong = (np.sin(2*np.pi*55*tt) + .45*np.sin(2*np.pi*82.5*tt) + .22*np.sin(2*np.pi*110*tt))
add((gong*e*0.05).astype(np.float32), 96.2, 0, 1)
bell(97.0, 0.030, -0.2)
bell(99.6, 0.024, 0.25)

# space: gentle ping-pong on the musical bus
L = pingpong(L, 0.335, 0.24, 0.20, 4)
R = pingpong(R, 0.347, 0.24, 0.20, 4)

# master: soft clip, fades, normalize
m = np.maximum(np.abs(L), np.abs(R))
peak = float(np.max(m)) or 1.0
L = np.tanh(L / peak * 1.35) / np.tanh(1.35) * 0.9
R = np.tanh(R / peak * 1.35) / np.tanh(1.35) * 0.9
fade = np.ones(N, np.float32)
nf = int(0.8*SR)
fade[:nf] = np.linspace(0, 1, nf, dtype=np.float32) ** 2
nf2 = int(3.2*SR)
fade[-nf2:] = (np.linspace(1, 0, nf2, dtype=np.float32) ** 1.4)
L *= fade; R *= fade
p = max(float(np.max(np.abs(L))), float(np.max(np.abs(R))))
L /= p / 0.89; R /= p / 0.89

out = os.path.join(os.path.dirname(__file__), '..', 'production', 'score.wav')
out = os.path.abspath(out)
os.makedirs(os.path.dirname(out), exist_ok=True)
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    inter = np.empty(N*2, dtype=np.int16)
    inter[0::2] = np.clip(L, -1, 1) * 32767
    inter[1::2] = np.clip(R, -1, 1) * 32767
    w.writeframes(inter.tobytes())

rms = float(np.sqrt(np.mean((L.astype(np.float64)**2 + R.astype(np.float64)**2)/2)))
print('WROTE', out, 'peak', round(float(np.max(np.abs(L))),3), 'rms', round(rms,4), 'seconds', DUR)
for a, b in [(0,5),(5,19),(19,33),(33,47),(47,61),(61,75),(75,78),(78,90),(90,96),(96,102)]:
    i0, i1 = int(a*SR), int(b*SR)
    r = float(np.sqrt(np.mean((L[i0:i1].astype(np.float64)**2 + R[i0:i1].astype(np.float64)**2)/2)))
    print(f'  {a:>3}-{b:<3}s rms {r:.4f}')
