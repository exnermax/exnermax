#!/usr/bin/env python3
"""Erzeugt die vier Banner-SVGs mit animiertem Netzwerk.

    python tools/build-banner-svg.py

Schreibt assets/banner-{dark,light}.svg und assets/banner-mobile-{dark,light}.svg.

Das Netzwerk bewegt sich wirklich: jeder Knoten laeuft eine geschlossene
Lissajous-Bahn um seine Ruheposition, die Kanten werden aus denselben Bahnen
berechnet und laufen deshalb immer synchron mit. Zusaetzlich wandern
Datenpakete ueber die Kanten.

Die Bahnen haben ganzzahlige Frequenzen und eine gemeinsame Dauer, dadurch
ist der Zyklus nahtlos: der letzte Keyframe ist identisch mit dem ersten.
"""
import math, os

CYCLE   = 24          # Sekunden fuer einen kompletten Netzwerk-Zyklus
SAMPLES = 48          # Keyframes pro Bahn
TYPE_DUR = 12         # Sekunden fuer den Typing-Zyklus

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

THEMES = {
    "dark": dict(bg0="#0D1117", bg1="#111722", bg2="#161B22", grid="#1F2630",
                 name="#E6EDF3", rule="#21262D", sub="#8B949E", foot="#6E7681",
                 dot="#30363D", edge="#30394A", accent="#58A6FF",
                 violet="#A371F7", green="#7EE787", glow=0.18),
    "light": dict(bg0="#FFFFFF", bg1="#FBFCFD", bg2="#F4F7FA", grid="#E1E7EE",
                  name="#1F2328", rule="#D8DEE4", sub="#59636E", foot="#6E7781",
                  dot="#C4CCD6", edge="#A9B4C0", accent="#0969DA",
                  violet="#8250DF", green="#1A7F37", glow=0.10),
}

# Knoten: (x, y, farbrolle, amplitude_x, amplitude_y, freq_x, freq_y, phase)
# freq sind ganze Zahlen -> die Bahn schliesst sich exakt nach CYCLE Sekunden.
NODES_WIDE = [
    (690,  62, "accent", 11,  8, 1, 2, 0.00),
    (760,  44, "violet",  9, 12, 2, 1, 0.35),
    (822,  78, "accent", 13,  9, 1, 1, 0.70),
    (734, 110, "green",  10, 11, 2, 2, 1.10),
    (806, 148, "accent", 12,  8, 1, 2, 1.55),
]
NODES_NARROW = [
    (356, 208, "accent",  7, 5, 1, 2, 0.00),
    (400, 190, "violet",  6, 8, 2, 1, 0.35),
    (444, 214, "accent",  8, 6, 1, 1, 0.70),
    (392, 232, "green",   7, 7, 2, 2, 1.10),
]
EDGES_WIDE   = [(0,1),(1,2),(0,3),(3,2),(3,1),(3,4),(4,2)]
EDGES_NARROW = [(0,1),(1,2),(0,3),(3,2),(3,1)]

# Datenpakete: (kanten-index, startzeit 0..1, anteil der Fahrt am Zyklus)
PACKETS_WIDE   = [(0, 0.02, 0.22), (3, 0.28, 0.22), (5, 0.54, 0.22), (6, 0.78, 0.22)]
PACKETS_NARROW = [(0, 0.05, 0.26), (3, 0.40, 0.26), (1, 0.72, 0.26)]


def node_pos(n, t):
    """Position von Knoten n zum Zeitpunkt t (0..1 = ein Zyklus)."""
    x, y, _, ax, ay, fx, fy, ph = n
    return (x + ax * math.sin(2 * math.pi * (fx * t + ph)),
            y + ay * math.sin(2 * math.pi * (fy * t + ph * 1.7)))


def vals(seq):
    return ";".join(f"{v:.1f}" for v in seq)


def anim(attr, seq, dur):
    return f'<animate attributeName="{attr}" values="{vals(seq)}" dur="{dur}s" repeatCount="indefinite"/>'


def network(nodes, edges, packets, t):
    """Erzeugt Kanten, Knoten und Pakete als SVG-Fragmente."""
    ts = [i / SAMPLES for i in range(SAMPLES + 1)]   # letzter == erster -> nahtlos
    track = [[node_pos(n, u) for u in ts] for n in nodes]
    out = []

    # Kanten zuerst, damit die Knoten darueber liegen
    out.append(f'<g stroke="{t["edge"]}" stroke-width="1.2" stroke-linecap="round" opacity="0.9">')
    for a, b in edges:
        out.append('<line>'
                   + anim("x1", [p[0] for p in track[a]], CYCLE)
                   + anim("y1", [p[1] for p in track[a]], CYCLE)
                   + anim("x2", [p[0] for p in track[b]], CYCLE)
                   + anim("y2", [p[1] for p in track[b]], CYCLE)
                   + '</line>')
    out.append('</g>')

    # Datenpakete entlang der Kanten
    for ei, start, span in packets:
        a, b = edges[ei]
        px, py, op = [], [], []
        for i, u in enumerate(ts):
            rel = (u - start) % 1.0
            if rel < span:
                s = rel / span
                fade = min(1.0, min(s, 1 - s) * 6)
            else:
                s, fade = 0.0, 0.0
            ax_, ay_ = track[a][i]
            bx_, by_ = track[b][i]
            px.append(ax_ + (bx_ - ax_) * s)
            py.append(ay_ + (by_ - ay_) * s)
            op.append(fade)
        ops = ";".join(f"{v:.2f}" for v in op)
        # Aura + Kern, damit das Paket auf dem skalierten Banner sichtbar bleibt
        for radius, fade in ((7.5, 0.28), (3.4, 1.0)):
            out.append(f'<circle r="{radius}" fill="{t["accent"]}" opacity="0">'
                       + anim("cx", px, CYCLE) + anim("cy", py, CYCLE)
                       + f'<animate attributeName="opacity" '
                         f'values="{";".join(f"{v*fade:.2f}" for v in op)}" '
                         f'dur="{CYCLE}s" repeatCount="indefinite"/></circle>')

    # Knoten
    for n, tr in zip(nodes, track):
        col = t[n[2]]
        pulse = 2.4 + 1.6 * abs(math.sin(n[7] * 3))
        out.append(f'<circle r="4.5" fill="{col}">'
                   + anim("cx", [p[0] for p in tr], CYCLE)
                   + anim("cy", [p[1] for p in tr], CYCLE)
                   + f'<animate attributeName="opacity" values="0.4;1;0.4" dur="{pulse:.1f}s" repeatCount="indefinite"/>'
                   + '</circle>')
    return "\n  ".join(out)


PHRASES = ["Backend & ERP Developer", "C# · .NET · SQL · PHP", "Internal tools & automation"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def typing(x0, base_y, clip_y, clip_h, size, t):
    """Getippte Zeile, die durch PHRASES rotiert, mit mitwanderndem Cursor."""
    n = len(PHRASES)
    widths = [len(p) * size * 0.60 for p in PHRASES]
    clips, texts = [], []
    cur_kt, cur_x = [0.0], [x0]

    for i, (p, w) in enumerate(zip(PHRASES, widths)):
        a, b = i / n, (i + 1) / n
        kt = [0.0, a, a + 0.10, b - 0.05, b, 1.0]
        vv = [0.0, 0.0, w, w, 0.0, 0.0]
        k2, v2 = [], []
        for k, v in zip(kt, vv):
            if k2 and abs(k - k2[-1]) < 1e-9:
                k2[-1], v2[-1] = k, v
            else:
                k2.append(k); v2.append(v)
        clips.append(
            f'<clipPath id="c{i}"><rect x="{x0}" y="{clip_y}" height="{clip_h}" width="0">'
            f'<animate attributeName="width" values="{";".join(f"{v:.1f}" for v in v2)}" '
            f'keyTimes="{";".join(f"{k:.4f}" for k in k2)}" dur="{TYPE_DUR}s" repeatCount="indefinite"/>'
            f'</rect></clipPath>')
        texts.append(
            f'<g clip-path="url(#c{i})"><text x="{x0}" y="{base_y}" font-family="{MONO}" '
            f'font-size="{size}" fill="{t["sub"]}" textLength="{w:.1f}" '
            f'lengthAdjust="spacingAndGlyphs">{esc(p)}</text></g>')
        cur_kt += [a, a + 0.10, b - 0.05, b]
        cur_x  += [x0, x0 + w, x0 + w, x0]

    cur_kt.append(1.0); cur_x.append(x0)
    k3, x3 = [], []
    for k, v in zip(cur_kt, cur_x):
        if k3 and abs(k - k3[-1]) < 1e-9:
            k3[-1], x3[-1] = k, v
        else:
            k3.append(k); x3.append(v)

    cursor = (f'<rect y="{clip_y + 2}" width="{max(2, size/7):.1f}" height="{clip_h - 4}" '
              f'fill="{t["accent"]}" x="{x0}">'
              f'<animate attributeName="x" values="{";".join(f"{v:.1f}" for v in x3)}" '
              f'keyTimes="{";".join(f"{k:.4f}" for k in k3)}" dur="{TYPE_DUR}s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values="1;1;0;0;1;1" '
              f'keyTimes="0;0.48;0.5;0.98;1;1" dur="1.1s" repeatCount="indefinite"/></rect>')
    return "\n  ".join(clips), "\n  ".join(texts) + "\n  " + cursor


def render(theme, wide=True):
    t = THEMES[theme]
    if wide:
        W, H, pad = 900, 220, 56
        name_size, name_len, name_y = 46, 286, 86
        rule_y, type_size = 102, 17
        clip_y, clip_h, base_y = 132, 26, 151
        foot_y, foot_size, grid = 184, 12.5, 30
        glow = (740, 72, 240, 150)
        nodes, edges, packets = NODES_WIDE, EDGES_WIDE, PACKETS_WIDE
        foot = [("Germany", 72, "foot"), ("exnermax.de", 120, "foot"), ("open to work", 128, "green")]
    else:
        W, H, pad = 480, 250, 32
        name_size, name_len, name_y = 40, 248, 86
        rule_y, type_size = 104, 14
        clip_y, clip_h, base_y = 138, 22, 155
        foot_y, foot_size, grid = 196, 11.5, 24
        glow = (400, 56, 150, 110)
        nodes, edges, packets = NODES_NARROW, EDGES_NARROW, PACKETS_NARROW
        foot = [("Germany", 60, "foot"), ("open to work", 90, "green")]

    clips, typed = typing(pad, base_y, clip_y, clip_h, type_size, t)

    fg, x = [], pad
    for label, width, role in foot:
        fg.append(f'<text x="{x:.0f}" y="{foot_y}" fill="{t[role]}" textLength="{width}" '
                  f'lengthAdjust="spacingAndGlyphs">{esc(label)}</text>')
        x += width
        if (label, width, role) != foot[-1]:
            fg.append(f'<circle cx="{x + 14:.0f}" cy="{foot_y - 4}" r="2" fill="{t["dot"]}"/>')
            x += 28

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Max Exner — Backend and ERP Developer, Germany">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{t['bg0']}"/><stop offset="55%" stop-color="{t['bg1']}"/><stop offset="100%" stop-color="{t['bg2']}"/>
    </linearGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{t['accent']}" stop-opacity="0"/>
      <stop offset="50%" stop-color="{t['accent']}" stop-opacity="1"/>
      <stop offset="100%" stop-color="{t['violet']}" stop-opacity="0"/>
      <animate attributeName="x1" values="-1;0;-1" dur="6s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="0;2;0" dur="6s" repeatCount="indefinite"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{t['accent']}" stop-opacity="{t['glow']}"/><stop offset="100%" stop-color="{t['accent']}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="{grid}" height="{grid}" patternUnits="userSpaceOnUse">
      <path d="M{grid} 0 L0 0 0 {grid}" fill="none" stroke="{t['grid']}" stroke-width="1"/>
    </pattern>
  {clips}
  </defs>

  <rect width="{W}" height="{H}" rx="14" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#grid)" opacity="0.5"/>
  <ellipse cx="{glow[0]}" cy="{glow[1]}" rx="{glow[2]}" ry="{glow[3]}" fill="url(#glow)"/>

  {network(nodes, edges, packets, t)}

  <text x="{pad}" y="{name_y}" font-family="{SANS}" font-size="{name_size}" font-weight="700" fill="{t['name']}" letter-spacing="1.2" textLength="{name_len}" lengthAdjust="spacingAndGlyphs">MAX EXNER</text>
  <rect x="{pad}" y="{rule_y}" width="{name_len}" height="2.5" rx="1.25" fill="{t['rule']}"/>
  <rect x="{pad}" y="{rule_y}" width="{name_len}" height="2.5" rx="1.25" fill="url(#rule)"/>

  {typed}

  <g font-family="{MONO}" font-size="{foot_size}">
  {chr(10).join("  " + l for l in fg)}
  </g>
</svg>'''


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.makedirs(os.path.join(root, "assets"), exist_ok=True)
    for theme in ("dark", "light"):
        for wide, suffix in ((True, ""), (False, "-mobile")):
            path = os.path.join(root, "assets", f"banner{suffix}-{theme}.svg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(render(theme, wide))
            print(f"geschrieben: assets/banner{suffix}-{theme}.svg")
