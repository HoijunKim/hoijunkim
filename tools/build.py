# -*- coding: utf-8 -*-
"""
Regenerate the profile artwork.

    python tools/build.py

Writes assets/hero.svg and assets/stack.svg. Deterministic (fixed seeds), so
re-running gives byte-identical output. Everything is self-contained, pure
SMIL/CSS animated SVG - no JavaScript, no external references - so it renders
and animates when GitHub serves it through its image proxy.

Tweak colors / text / waveforms here, then re-run and commit the assets.
"""
import math, random, io, os

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")

# ---- palette (shared) : cool blue instrument, one warm accent ----
C1, C2, C3, C4 = "#4d9fff", "#34c8f2", "#9d8cff", "#6f92cf"   # azure / cyan-blue / violet / steel(pose)
PT_C, AMBER = "#48b4ff", "#f2b45c"                             # blue / warm accent (actuator, INT8)
DIM, BRIGHT, LABEL, RED = "#6f8fc0", "#d8e8ff", "#4d6a99", "#ff6b6b"


# ============================ waveform generators ============================
def _path(pts):
    d = "M %.1f %.1f" % pts[0]
    for p in pts[1:]:
        d += " L %.1f %.1f" % p
    return d


def emg(center, half, bursts, seed, x0, x1, n, base_noise=1.6):
    r = random.Random(seed)
    pts = []
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        t = i / (n - 1)
        y = r.uniform(-base_noise, base_noise)
        for pos, width, amp, freq in bursts:
            env = math.exp(-((t - pos) ** 2) / (2 * width * width))
            y += env * half * amp * (math.sin(t * freq * 2 * math.pi + seed) + r.uniform(-0.35, 0.35))
        y = max(-half, min(half, y))
        pts.append((x, center - y))
    return _path(pts)


def pose(center, half, x0, x1, n):
    pts = []
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        t = i / (n - 1)
        y = (half * 0.62) * math.sin(t * 2.1 * 2 * math.pi + 0.4) + (half * 0.22) * math.sin(t * 4.7 * 2 * math.pi + 1.1)
        pts.append((x, center - y))
    return _path(pts)


def square(center, half, x0, x1, n, period=0.14):
    pts = []
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        t = i / (n - 1)
        y = half * 0.8 if (int(t / period) % 2 == 0) else -half * 0.8
        pts.append((x, center - y))
    return _path(pts)


def sine(center, half, freq, x0, x1, n):
    pts = []
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        t = i / (n - 1)
        y = half * 0.78 * math.sin(t * freq * 2 * math.pi) + half * 0.15 * math.sin(t * freq * 2.3 * 2 * math.pi + 1)
        pts.append((x, center - y))
    return _path(pts)


def staircase(center, half, steps, x0, x1, n):
    pts = []
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        t = i / (n - 1)
        phase = (t * 2.0) % 1.0
        lvl = math.floor(phase * steps) / (steps - 1)
        pts.append((x, center - (lvl * 2 - 1) * half * 0.85))
    return _path(pts)


# ============================== layout budget ===============================
# The README renders inside a ~780px column on GitHub, so an SVG is scaled by
# (780 / viewBox width). Anything below ~11px after that scale is unreadable.
# Both canvases are therefore sized close to the real column width instead of
# being drawn huge and shrunk - keep new text at >= 12px in design units.
HERO_W, HERO_H = 900, 360      # 2.5:1 - stays legible down to phone width
STACK_W, STACK_H = 900, 420


# ================================== hero ====================================
def build_hero():
    T = "5s"
    X0, X1 = 96, 700           # waveform span
    CH = [
        (emg(122, 18, [(0.16, 0.05, 0.9, 46), (0.54, 0.06, 1.0, 52), (0.83, 0.045, 0.8, 44)], 11, X0, X1, 260),
         122, C1, "CH1", "FDS", "0.51 mV", "p1"),
        (emg(172, 18, [(0.30, 0.055, 0.85, 40), (0.68, 0.05, 0.95, 48)], 23, X0, X1, 260),
         172, C2, "CH2", "EDC", "0.38 mV", "p2"),
        (emg(222, 18, [(0.44, 0.05, 0.9, 50), (0.90, 0.04, 0.7, 42)], 37, X0, X1, 260),
         222, C3, "CH3", "APB", "0.44 mV", "p3"),
        (pose(272, 18, X0, X1, 260), 272, C4, "CH4", "POSE", "23 fps", "p4"),
    ]
    SX, SY, SW, SH = 18, 86, 864, 256          # screen rect
    RAIL = 836                                  # decode rail centre
    s = io.StringIO(); W = s.write
    W('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
      'viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-labelledby="ti de" '
      'preserveAspectRatio="xMidYMid meet" '
      'font-family="ui-monospace, SFMono-Regular, Menlo, \'Courier New\', \'Malgun Gothic\', monospace">\n'
      % (HERO_W, HERO_H, HERO_W, HERO_H))
    W('<title id="ti">Hoijun Kim - biosignal and edge-AI researcher</title>\n')
    W('<desc id="de">A dark laboratory oscilloscope reading four looping biosignal channels - three '
      'forearm EMG channels (FDS, EDC, APB) and one video pose channel - with a sweeping scan bar and a '
      'prosthetic gripper that flexes in response, representing muscle signals decoded into motion.</desc>\n')
    W('<defs>\n')
    W('<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#080f1e"/>'
      '<stop offset="0.55" stop-color="#0b1526"/><stop offset="1" stop-color="#05080f"/></linearGradient>\n')
    W('<radialGradient id="crt" cx="0.5" cy="0.44" r="0.75"><stop offset="0" stop-color="#12345c" stop-opacity="0.35"/>'
      '<stop offset="0.7" stop-color="#080f1e" stop-opacity="0.05"/>'
      '<stop offset="1" stop-color="#03060f" stop-opacity="0.85"/></radialGradient>\n')
    W('<linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4da3ff" stop-opacity="0"/>'
      '<stop offset="0.78" stop-color="#4da3ff" stop-opacity="0.06"/>'
      '<stop offset="1" stop-color="#cfe4ff" stop-opacity="0.30"/></linearGradient>\n')
    W('<filter id="glow" x="-8%" y="-45%" width="116%" height="190%"><feGaussianBlur stdDeviation="1.1" result="b"/>'
      '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>\n')
    W('<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
      '<path d="M24 0H0V24" fill="none" stroke="#183a63" stroke-width="0.6" opacity="0.5"/></pattern>\n')
    W('<clipPath id="screen"><rect x="%d" y="%d" width="%d" height="%d" rx="6"/></clipPath>\n' % (SX, SY, SW, SH))
    W('<clipPath id="namewipe"><rect x="18" y="18" width="0" height="62">'
      f'<animate attributeName="width" values="0;500;500;500" keyTimes="0;0.34;0.94;1" dur="{T}" '
      'repeatCount="indefinite" calcMode="spline" keySplines="0.2 0.7 0.2 1;0 0 1 1;0 0 1 1"/></rect></clipPath>\n')
    W('</defs>\n')
    W('<rect x="0" y="0" width="%d" height="%d" rx="14" fill="#03060d"/>\n' % (HERO_W, HERO_H))
    W('<rect x="4" y="4" width="%d" height="%d" rx="11" fill="url(#bg)" stroke="#1c4066" stroke-width="1.2"/>\n'
      % (HERO_W - 8, HERO_H - 8))
    W('<g clip-path="url(#namewipe)">')
    W('<text x="26" y="49" font-size="30" font-weight="700" letter-spacing="0.5" fill="%s" filter="url(#glow)">'
      'Hoijun Kim</text>' % BRIGHT)
    W('<text x="27" y="71" font-size="12.5" letter-spacing="0.4" fill="%s">'
      'biosignal ML / edge-AI - decoding EMG into prosthetic motion</text>' % DIM)
    W('</g>\n')
    W('<text x="820" y="34" font-size="12.5" font-weight="700" letter-spacing="1.5" fill="%s">REC</text>' % RED)
    W('<circle cx="866" cy="29.5" r="4.5" fill="%s"><animate attributeName="opacity" '
      'values="1;1;0.12;0.12;1" keyTimes="0;0.45;0.5;0.55;1" dur="1.6s" repeatCount="indefinite"/></circle>\n' % RED)
    W('<g text-anchor="end">')
    W('<text x="874" y="56" font-size="12.5" letter-spacing="0.4" fill="%s">OpenVINO / Lunar Lake NPU</text>' % LABEL)
    W('<text x="874" y="74" font-size="12.5" letter-spacing="0.8" fill="%s">inference '
      '<tspan fill="%s" font-weight="700">LIVE</tspan></text>' % (LABEL, C2))
    W('</g>\n')
    W('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="#060e1d"/>\n' % (SX, SY, SW, SH))
    W('<g clip-path="url(#screen)">\n')
    W('  <rect x="%d" y="%d" width="%d" height="%d" fill="url(#grid)"/>\n' % (SX, SY, SW, SH))
    for d, cy, col, code, mus, val, pid in CH:
        W('  <line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#26497a" stroke-width="0.7" '
          'stroke-dasharray="2 5" opacity="0.6"/>\n' % (X0 - 6, cy, X1, cy))
    W('  <rect x="%d" y="0" width="%d" height="30" fill="#a9ccff" opacity="0.035">'
      '<animateTransform attributeName="transform" type="translate" values="0,%d;0,%d;0,%d" '
      'dur="7s" repeatCount="indefinite"/></rect>\n' % (SX, SW, SY - 6, SY + SH - 24, SY - 6))
    for d, cy, col, code, mus, val, pid in CH:
        W('  <path id="%s" d="%s" fill="none" stroke="%s" stroke-width="1.7" stroke-linejoin="round" '
          'stroke-linecap="round" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" filter="url(#glow)">'
          '<animate attributeName="stroke-dashoffset" values="1;0" dur="%s" repeatCount="indefinite" '
          'calcMode="linear"/></path>\n' % (pid, d, col, T))
        W('  <circle r="2.6" fill="#eaf3ff" filter="url(#glow)">'
          '<animateMotion dur="%s" repeatCount="indefinite" calcMode="linear" keyPoints="0;1" keyTimes="0;1">'
          '<mpath xlink:href="#%s"/></animateMotion></circle>\n' % (T, pid))
    W('  <g><rect x="-90" y="%d" width="90" height="%d" fill="url(#sweep)"/>'
      '<line x1="0" y1="%d" x2="0" y2="%d" stroke="#d3e6ff" stroke-width="1.1" opacity="0.55"/>'
      '<animateTransform attributeName="transform" type="translate" values="%d,0;%d,0" dur="%s" '
      'repeatCount="indefinite" calcMode="linear"/></g>\n' % (SY, SH, SY, SY + SH, X0 - 6, X1, T))
    W('</g>\n')
    W('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="url(#crt)" pointer-events="none"/>\n' % (SX, SY, SW, SH))
    W('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="none" stroke="#2a5688" stroke-width="1"/>\n' % (SX, SY, SW, SH))
    for d, cy, col, code, mus, val, pid in CH:
        W('<text x="26" y="%d" font-size="13" letter-spacing="0.4">'
          '<tspan font-weight="700" fill="%s">%s</tspan><tspan fill="%s"> %s</tspan></text>'
          % (cy + 4.5, col, code, LABEL, mus))
        W('<text x="782" y="%d" text-anchor="end" font-size="12.5" fill="%s">%s</text>\n' % (cy + 4.5, col, val))
    W('<text x="26" y="330" font-size="12" letter-spacing="0.4" fill="%s">'
      '20 mV/div   500 ms/div   fs 2 kHz   3x surface EMG + pose</text>\n' % LABEL)
    W('<line x1="790" y1="96" x2="790" y2="332" stroke="#1e4270" stroke-width="1" opacity="0.7"/>\n')
    W('<text x="%d" y="120" text-anchor="middle" font-size="11.5" letter-spacing="1" fill="%s">DECODE</text>\n' % (RAIL, LABEL))
    W('<text x="%d" y="137" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="0.5" fill="%s">-&gt; GRIP</text>\n' % (RAIL, AMBER))
    W('<g transform="translate(%d,208)" stroke-linecap="round">\n' % RAIL)
    W('  <line x1="0" y1="36" x2="0" y2="16" stroke="%s" stroke-width="5"/>\n' % DIM)
    W('  <rect x="-8" y="8" width="16" height="8" rx="4" fill="%s"/>\n' % DIM)
    W('  <circle cx="0" cy="12" r="3" fill="%s"/>\n' % AMBER)
    W('  <g transform="rotate(0 0 12)"><line x1="0" y1="12" x2="-13" y2="-14" stroke="%s" stroke-width="4.5"/>'
      '<line x1="-13" y1="-14" x2="-20" y2="-30" stroke="%s" stroke-width="4"/>'
      '<animateTransform attributeName="transform" type="rotate" values="0 0 12;0 0 12;26 0 12;26 0 12;0 0 12" '
      'keyTimes="0;0.42;0.56;0.82;1" dur="%s" repeatCount="indefinite" calcMode="spline" '
      'keySplines="0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1"/></g>\n' % (AMBER, AMBER, T))
    W('  <g transform="rotate(0 0 12)"><line x1="0" y1="12" x2="13" y2="-14" stroke="%s" stroke-width="4.5"/>'
      '<line x1="13" y1="-14" x2="20" y2="-30" stroke="%s" stroke-width="4"/>'
      '<animateTransform attributeName="transform" type="rotate" values="0 0 12;0 0 12;-26 0 12;-26 0 12;0 0 12" '
      'keyTimes="0;0.42;0.56;0.82;1" dur="%s" repeatCount="indefinite" calcMode="spline" '
      'keySplines="0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1;0.4 0 0.2 1"/></g>\n' % (AMBER, AMBER, T))
    W('</g>\n')
    W('<text x="%d" y="322" text-anchor="middle" font-size="11.5" letter-spacing="1" fill="%s">ACTUATOR</text>\n' % (RAIL, LABEL))
    W('</svg>\n')
    return s.getvalue()


# ================================== stack ===================================
def build_stack():
    T = "4.5s"
    WX0, WX1 = 316, 686        # sparkline x-range, inside the signal window
    CY = [92, 130, 168, 206, 244, 282, 320, 358]
    HALF = 11
    # probe, tech, note, color, sparkline, cy, usage-tag, is_main
    ROWS = [
        ("PY",  "Python",         "signal / ML",    C1,
         emg(CY[0], HALF, [(0.35, 0.08, 0.9, 22), (0.7, 0.07, 0.9, 22)], 7, WX0, WX1, 200, 1.0), CY[0], "primary", True),
        ("PT",  "PyTorch",        "deep learning",  PT_C,
         emg(CY[1], HALF, [(0.25, 0.06, 0.9, 34), (0.55, 0.05, 0.9, 34), (0.82, 0.05, 0.9, 34)], 15, WX0, WX1, 200, 1.0), CY[1], "daily", False),
        ("NP",  "NumPy / Pandas", "data frames",    C4,
         staircase(CY[2], HALF, 5, WX0, WX1, 200), CY[2], "daily", False),
        ("CV",  "OpenCV",         "video / pose",   C3,
         pose(CY[3], HALF, WX0, WX1, 200), CY[3], "daily", False),
        ("GO",  "Go",             "desktop / CLI",  C2,
         square(CY[4], HALF, WX0, WX1, 200), CY[4], "daily", False),
        ("TS",  "Svelte + TS",    "reactive UI",    C1,
         sine(CY[5], HALF, 3.0, WX0, WX1, 200), CY[5], "daily", False),
        ("AI",  "OpenVINO / NPU", "edge inference", AMBER,
         staircase(CY[6], HALF, 7, WX0, WX1, 200), CY[6], "exploring", False),
        ("WEB", "SCSS / Web",     "frontend",       C3,
         sine(CY[7], HALF, 2.2, WX0, WX1, 200), CY[7], "occasional", False),
    ]
    WIN = (298, 72, 406, 332)  # signal window x, y, w, h
    s = io.StringIO(); W = s.write
    W('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
      'viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-labelledby="ti de" '
      'preserveAspectRatio="xMidYMid meet" '
      'font-family="ui-monospace, SFMono-Regular, Menlo, \'Courier New\', \'Malgun Gothic\', monospace">\n'
      % (STACK_W, STACK_H, STACK_W, STACK_H))
    W('<title id="ti">Tech stack - probe bank</title>\n')
    W('<desc id="de">A probe bank listing the stack as oscilloscope channels - Python, PyTorch, '
      'NumPy and Pandas, OpenCV, Go, Svelte with TypeScript, OpenVINO on NPU, and SCSS - each with a mini '
      'signal that encodes its character (Go a square wave, OpenVINO an INT8 staircase, and so on) and a '
      'usage tag. Python is the main language.</desc>\n')
    W('<defs>')
    W('<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#080f1e"/>'
      '<stop offset="1" stop-color="#05080f"/></linearGradient>')
    W('<filter id="glow" x="-6%" y="-60%" width="112%" height="220%"><feGaussianBlur stdDeviation="1.15" result="b"/>'
      '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    W('<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
      '<path d="M24 0H0V24" fill="none" stroke="#183a63" stroke-width="0.6" opacity="0.4"/></pattern>')
    W('<clipPath id="scr"><rect x="%d" y="%d" width="%d" height="%d" rx="4"/></clipPath>' % WIN)
    W('</defs>\n')
    W('<rect x="0" y="0" width="%d" height="%d" rx="14" fill="#03060d"/>\n' % (STACK_W, STACK_H))
    W('<rect x="4" y="4" width="%d" height="%d" rx="11" fill="url(#bg)" stroke="#1c4066" stroke-width="1.2"/>\n'
      % (STACK_W - 8, STACK_H - 8))
    # header
    W('<text x="24" y="40" font-size="17" font-weight="700" letter-spacing="2" fill="%s">PROBE BANK</text>\n' % BRIGHT)
    W('<text x="162" y="40" font-size="12.5" letter-spacing="0.4" fill="%s">/ stack</text>\n' % DIM)
    W('<text x="800" y="40" text-anchor="end" font-size="11.5" letter-spacing="1" fill="%s">MAIN</text>' % LABEL)
    W('<text x="876" y="40" text-anchor="end" font-size="13" font-weight="700" letter-spacing="0.4" fill="%s">Python</text>\n' % AMBER)
    # column captions
    W('<text x="501" y="62" text-anchor="middle" font-size="10" letter-spacing="1.5" fill="%s">SIGNAL</text>' % LABEL)
    W('<text x="838" y="62" text-anchor="middle" font-size="10" letter-spacing="1.5" fill="%s">USAGE</text>\n' % LABEL)
    # signal window
    W('<rect x="%d" y="%d" width="%d" height="%d" rx="4" fill="#060e1d" stroke="#1e4270" stroke-width="0.8"/>\n' % WIN)
    W('<g clip-path="url(#scr)">')
    W('<rect x="%d" y="%d" width="%d" height="%d" fill="url(#grid)"/>' % WIN)
    for probe, tech, note, col, d, cy, cat, main in ROWS:
        W('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#26497a" stroke-width="0.6" stroke-dasharray="2 5" opacity="0.5"/>' % (WX0, cy, WX1, cy))
    for i, (probe, tech, note, col, d, cy, cat, main) in enumerate(ROWS):
        dly = "%.2fs" % (i * 0.18)
        W('<path d="%s" fill="none" stroke="%s" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" '
          'pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="1" filter="url(#glow)">'
          '<animate attributeName="stroke-dashoffset" values="1;0" dur="%s" begin="%s" repeatCount="indefinite" calcMode="linear"/></path>'
          % (d, col, T, dly))
    W('</g>\n')
    # rows: probe chip, tech + note on one line, usage tag (MAIN pill for the main language)
    for probe, tech, note, col, d, cy, cat, main in ROWS:
        W('<rect x="22" y="%d" width="34" height="20" rx="3" fill="#0b1d34" stroke="%s" stroke-width="0.9"/>' % (cy - 10, col))
        W('<text x="39" y="%d" text-anchor="middle" font-size="11" font-weight="700" fill="%s">%s</text>' % (cy + 4, col, probe))
        W('<text x="64" y="%d" font-size="13.5" font-weight="700" fill="%s">%s</text>' % (cy + 4.5, BRIGHT, tech))
        W('<text x="186" y="%d" font-size="12" letter-spacing="0.3" fill="%s">%s</text>' % (cy + 4.5, LABEL, note))
        if main:
            W('<rect x="816" y="%d" width="60" height="20" rx="10" fill="none" stroke="%s" stroke-width="1"/>' % (cy - 10, AMBER))
            W('<text x="846" y="%d" text-anchor="middle" font-size="10.5" font-weight="700" letter-spacing="1" fill="%s">MAIN</text>\n' % (cy + 4, AMBER))
        else:
            W('<text x="876" y="%d" text-anchor="end" font-size="12" letter-spacing="0.4" fill="%s">%s</text>\n' % (cy + 4.5, DIM, cat))
    W('</svg>\n')
    return s.getvalue()


def main():
    os.makedirs(ASSETS, exist_ok=True)
    for name, data in (("hero.svg", build_hero()), ("stack.svg", build_stack())):
        p = os.path.join(ASSETS, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(data)
        print("wrote", os.path.normpath(p), len(data), "bytes")


if __name__ == "__main__":
    main()
