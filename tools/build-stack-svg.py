#!/usr/bin/env python3
"""Erzeugt assets/stack-dark.svg und assets/stack-light.svg.

Stack aendern -> GROUPS unten anpassen -> Skript laufen lassen:
    python tools/build-stack-svg.py
"""
import os

# (Kategorie, [(Name, Markenfarbe), ...])
GROUPS = [
    ("Backend & Data", [
        ("C#",          "#9B4F96"),
        (".NET",        "#512BD4"),
        ("SQL Server",  "#CC2927"),
        ("T-SQL",       "#CC2927"),
        ("PHP",         "#777BB4"),
        ("REST APIs",   "#4C8EDA"),
    ]),
    ("Frontend", [
        ("HTML",        "#E34F26"),
        ("CSS",         "#1572B6"),
        ("JavaScript",  "#F7DF1E"),
    ]),
    ("Tools & Workflow", [
        ("Visual Studio", "#8661C5"),
        ("VS Code",       "#0098FF"),
        ("Git",           "#F05032"),
        ("Postman",       "#FF6C37"),
        ("Copilot",       "#8B949E"),
    ]),
    ("Currently Learning", [
        ("TypeScript",  "#3178C6"),
        ("React",       "#61DAFB"),
        ("Docker",      "#2496ED"),
        ("Vue.js",      "#4FC08D"),
    ]),
]

W          = 900
MARGIN     = 28
FS         = 13.5      # Chip-Schriftgroesse
CHAR_W     = FS * 0.60 # Monospace-Zeichenbreite
PAD_X      = 13
DOT_R      = 3.6
DOT_GAP    = 9
CHIP_H     = 30
CHIP_GAP   = 9
ROW_GAP    = 9
LABEL_FS   = 11
LABEL_H    = 26
GROUP_GAP  = 20

MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

THEMES = {
    "dark":  dict(bg="#0D1117", bg2="#161B22", card="#161B22", stroke="#2A3139",
                  label="#6E7681", text="#C9D1D9", grid="#1F2630"),
    "light": dict(bg="#FFFFFF", bg2="#F4F7FA", card="#F6F8FA", stroke="#D0D7DE",
                  label="#6E7781", text="#1F2328", grid="#E1E7EE"),
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chip_width(name):
    return PAD_X + DOT_R * 2 + DOT_GAP + len(name) * CHAR_W + PAD_X


def layout():
    """Berechnet Positionen und die Gesamthoehe."""
    inner = W - 2 * MARGIN
    out, y = [], MARGIN + 4
    for gi, (label, items) in enumerate(GROUPS):
        if gi:
            y += GROUP_GAP
        out.append(("label", MARGIN, y + LABEL_FS, label))
        y += LABEL_H
        x = MARGIN
        for name, color in items:
            cw = chip_width(name)
            if x > MARGIN and x + cw > MARGIN + inner:
                x = MARGIN
                y += CHIP_H + ROW_GAP
            out.append(("chip", x, y, (name, color, cw)))
            x += cw + CHIP_GAP
        y += CHIP_H
    return out, y + MARGIN


def render(theme_name):
    t = THEMES[theme_name]
    items, height = layout()
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
             f'width="{W}" height="{height}" role="img" aria-label="Tech Stack">')
    p.append('<defs>'
             f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
             f'<stop offset="0%" stop-color="{t["bg"]}"/>'
             f'<stop offset="100%" stop-color="{t["bg2"]}"/></linearGradient>'
             f'<pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">'
             f'<path d="M30 0 L0 0 0 30" fill="none" stroke="{t["grid"]}" stroke-width="1"/>'
             f'</pattern></defs>')
    p.append(f'<rect width="{W}" height="{height}" rx="14" fill="url(#bg)"/>')
    p.append(f'<rect width="{W}" height="{height}" rx="14" fill="url(#grid)" opacity="0.5"/>')

    for kind, x, y, data in items:
        if kind == "label":
            p.append(f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="{LABEL_FS}" '
                     f'font-weight="700" fill="{t["label"]}" letter-spacing="1.6" '
                     f'textLength="{len(data) * LABEL_FS * 0.68:.0f}" lengthAdjust="spacingAndGlyphs">'
                     f'{esc(data.upper())}</text>')
        else:
            name, color, cw = data
            tw = len(name) * CHAR_W
            p.append(f'<g><rect x="{x:.1f}" y="{y:.1f}" width="{cw:.1f}" height="{CHIP_H}" rx="{CHIP_H/2:.1f}" '
                     f'fill="{t["card"]}" stroke="{t["stroke"]}" stroke-width="1"/>'
                     f'<circle cx="{x + PAD_X + DOT_R:.1f}" cy="{y + CHIP_H/2:.1f}" r="{DOT_R}" fill="{color}"/>'
                     f'<text x="{x + PAD_X + DOT_R*2 + DOT_GAP:.1f}" y="{y + CHIP_H/2 + FS*0.36:.1f}" '
                     f'font-family="{MONO}" font-size="{FS}" fill="{t["text"]}" '
                     f'textLength="{tw:.1f}" lengthAdjust="spacingAndGlyphs">{esc(name)}</text></g>')
    p.append('</svg>')
    return "\n".join(p)


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.makedirs(os.path.join(root, "assets"), exist_ok=True)
    for name in ("dark", "light"):
        path = os.path.join(root, "assets", f"stack-{name}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(render(name))
        print(f"geschrieben: assets/stack-{name}.svg")
