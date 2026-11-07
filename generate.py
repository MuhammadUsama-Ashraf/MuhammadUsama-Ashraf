#!/usr/bin/env python3
"""Builds the animated ASCII-terminal profile SVGs. Edit the data below, then run: python generate.py
Needs Pillow (pip install pillow) and internet access (it downloads your GitHub avatar)."""
import io, os, random, re, urllib.request
from PIL import Image, ImageDraw, ImageOps

OUT = os.path.dirname(os.path.abspath(__file__))
NAME = "Muhammad Usama"
HANDLE = "MuhammadUsama-Ashraf"
USER_ID = "171089131"
AVATAR = f"https://avatars.githubusercontent.com/u/{USER_ID}?v=4&s=288"
MONO = "Consolas,'SF Mono',Menlo,'DejaVu Sans Mono','Courier New',monospace"
STACK = ["JavaScript", "TypeScript", "React", "Next.js", "Node.js", "Flutter",
         "Dart", "PostgreSQL", "Tailwind", "Three.js", "Laravel", "Python"]
# Numbers from the GitHub API on 2026-11-06. They are static: update them by hand.
COMMITS, PRS, MERGED, REPOS, CONTRIB = 1696, 167, 150, 74, 26
LANGS = [("JavaScript", 49.5), ("HTML", 16.6), ("TypeScript", 13.7), ("Dart", 7.0), ("CSS", 6.3), ("PL/pgSQL", 2.1)]

DARK = dict(bg="#0b0d13", panel="#141826", line="#262b3d", hi="#ffe3c7", fg="#ff7a1a", dim="#8a90a2",
            faint="#3a3f52", glow=True, crt=.18, rain=.10)
OR, RED, PUR, GRN, BLU = "#ff7a1a", "#e2383f", "#c77dff", "#2fd48a", "#4aa3ff"
LIGHT = dict(bg="#ffffff", panel="#fafafa", line="#d4d4d4", hi="#000000", fg="#1a1a1a", dim="#5c5c5c",
             faint="#b5b5b5", glow=False, crt=.025, rain=.08)
CARD = DARK  # the stat cards and badge are dark terminals in both themes

# Name in the "ANSI Shadow" figlet style (only the letters we need).
FIG = {
    "M": ["███╗   ███╗", "████╗ ████║", "██╔████╔██║", "██║╚██╔╝██║", "██║ ╚═╝ ██║", "╚═╝     ╚═╝"],
    "U": ["██╗   ██╗", "██║   ██║", "██║   ██║", "██║   ██║", "╚██████╔╝", " ╚═════╝ "],
    "H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "D": ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
    "S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
}


def figlet(word):
    return ["".join(FIG[c][r] for c in word.upper()) for r in range(6)]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>{body}</svg>\n')


def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(text)
    print(f"wrote {name} ({len(text) // 1024} KB)")


def defs(t, w, h, extra=""):
    glow = ('<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.2" result="b"/>'
            '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    return (f'<defs>{glow}<pattern id="crt" width="4" height="3" patternUnits="userSpaceOnUse">'
            f'<rect width="4" height="1" fill="#000" opacity="{t["crt"]}"/></pattern>'
            f'<clipPath id="frame"><rect width="{w}" height="{h}" rx="10"/></clipPath>{extra}</defs>')


def G(t):
    return ' filter="url(#glow)"' if t["glow"] else ""


def text(x, y, s, fs, fill, extra=""):
    return f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{fs}" fill="{fill}" xml:space="preserve"{extra}>{esc(s)}</text>'


# ---------- your GitHub avatar as ASCII art ----------
def ascii_avatar(cols=64, rows=32, invert=False):
    src = Image.open(io.BytesIO(urllib.request.urlopen(AVATAR).read())).convert("RGB").resize((288, 288))
    im, key = src.copy(), (255, 0, 255)
    # shortcut: removes a plain, light background only; a busy photo background would show up as characters
    for c in [(0, 0), (287, 0), (0, 144), (287, 144), (0, 200), (287, 200), (144, 0)]:
        if im.getpixel(c) != key:
            ImageDraw.floodfill(im, c, key, thresh=48)
    mask = im.resize((cols, rows), Image.BOX)
    g = ImageOps.autocontrast(src.convert("L"), cutoff=1).resize((cols, rows), Image.LANCZOS)
    ramp = " .:-=+*#%@"
    out = []
    for y in range(rows):
        row = ""
        for x in range(cols):
            r, gg, b = mask.getpixel((x, y))
            v = g.getpixel((x, y)) / 255
            row += " " if (r > 180 and b > 180 and gg < 140) else ramp[min(9, int((v if invert else 1 - v) * 10))]
        out.append(row)
    return out


def ascii_rows(lines, x, y, width, fs, lh, fill, begin=None, step=0.045):
    out = ""
    for i, row in enumerate(lines):
        hidden = "" if begin is None else ' opacity="0"'
        reveal = "" if begin is None else f'<set attributeName="opacity" to="1" begin="{begin + i * step:.2f}s"/>'
        out += (f'<text x="{x}" y="{y + i * lh:.1f}" font-family="{MONO}" font-size="{fs}" fill="{fill}" textLength="{width}" '
                f'lengthAdjust="spacingAndGlyphs" xml:space="preserve"{hidden}>{esc(row)}{reveal}</text>')
    return out


# ---------- typing: a discrete-step clip reveal, taller than the text so no font gets clipped ----------
def typed(uid, x, y, spans, fs, begin, cps, c, cursor="hide"):
    n = sum(len(s) for s, _ in spans)
    cw = fs * 0.6
    dur = max(n / cps, .2)  # very short SMIL durations stall every animation in the file in Chrome
    xs = ";".join(f"{x + i * cw:.1f}" for i in range(n + 1))
    ws = ";".join(f"{i * cw + 6:.1f}" for i in range(n + 1))
    kt = ";".join(f"{i / n:.4f}" for i in range(n + 1))
    a = f'calcMode="discrete" keyTimes="{kt}" dur="{dur:.2f}s" begin="{begin:.2f}s" fill="freeze"'
    tsp = "".join(f'<tspan fill="{col}">{esc(s)}</tspan>' for s, col in spans)
    out = (f'<clipPath id="{uid}"><rect x="{x - 6}" y="{y - fs * 1.7:.1f}" height="{fs * 2.6:.1f}" width="0">'
           f'<animate attributeName="width" values="{ws}" {a}/></rect></clipPath>'
           f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{fs}" textLength="{n * cw:.1f}" '
           f'lengthAdjust="spacingAndGlyphs" xml:space="preserve" clip-path="url(#{uid})">{tsp}</text>')
    if cursor:
        end = (f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" begin="{begin + dur:.2f}s" repeatCount="indefinite"/>'
               if cursor == "blink" else f'<set attributeName="opacity" to="0" begin="{begin + dur + 0.1:.2f}s"/>')
        out += (f'<rect x="{x}" y="{y - fs * 0.85:.1f}" width="{fs * 0.55:.1f}" height="{fs * 1.05:.1f}" fill="{c}" opacity="0">'
                f'<animate attributeName="x" values="{xs}" {a}/><set attributeName="opacity" to="1" begin="{begin:.2f}s"/>{end}</rect>')
    return out, begin + dur


def wipe(uid, x, top, h, cols, cw, begin, cps):
    dur = cols / cps
    ws = ";".join(f"{i * cw + 4:.1f}" for i in range(cols + 1))
    kt = ";".join(f"{i / cols:.4f}" for i in range(cols + 1))
    return (f'<clipPath id="{uid}"><rect x="{x - 4}" y="{top:.1f}" height="{h:.1f}" width="0"><animate attributeName="width" values="{ws}" '
            f'keyTimes="{kt}" calcMode="discrete" dur="{dur:.2f}s" begin="{begin:.2f}s" fill="freeze"/></rect></clipPath>')


def flicker_in(inner, begin):
    return (f'<g opacity="0"><animate attributeName="opacity" values="0;1;.2;1" keyTimes="0;.3;.6;1" calcMode="discrete" '
            f'dur=".3s" begin="{begin:.2f}s" fill="freeze"/>{inner}</g>')


def rain(t, W, H, cols=22):
    r = random.Random(11)
    chars = "01{}[]=+*#$%;:/|"
    out = f'<g opacity="{t["rain"]}">'
    for i in range(cols):
        x = 20 + i * (W - 40) / cols + r.uniform(-8, 8)
        n, d = r.randint(8, 16), r.uniform(9, 18)
        col = "".join(f'<tspan x="{x:.0f}" dy="18">{esc(r.choice(chars))}</tspan>' for _ in range(n))
        out += (f'<text y="0" font-family="{MONO}" font-size="14" fill="{t["fg"]}">{col}'
                f'<animateTransform attributeName="transform" type="translate" from="0 {-n * 18}" to="0 {H}" dur="{d:.1f}s" '
                f'begin="{-r.uniform(0, d):.1f}s" repeatCount="indefinite"/></text>')
    return out + "</g>"


def crt_overlay(t, W, H):
    band = (f'<linearGradient id="band" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["fg"]}" stop-opacity="0"/>'
            f'<stop offset=".85" stop-color="{t["fg"]}" stop-opacity="{.08 if t["glow"] else .05}"/><stop offset="1" stop-color="{t["fg"]}" stop-opacity="0"/></linearGradient>')
    return band, (f'<g clip-path="url(#frame)"><rect width="{W}" height="{H}" fill="url(#crt)"/>'
                  f'<g><animateTransform attributeName="transform" type="translate" from="0 -90" to="0 {H + 20}" dur="3.5s" begin="3s" repeatCount="indefinite"/>'
                  f'<rect y="-200" width="{W}" height="80" fill="url(#band)"/></g></g>')


# ---------- banner ----------
def banner(t, avatar):
    W, H = 1280, 740
    band, overlay = crt_overlay(t, W, H)
    vig = ('<radialGradient id="vig" cx=".5" cy=".5" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/>'
           '<stop offset="1" stop-color="#000" stop-opacity=".55"/></radialGradient>') if t["glow"] else ""
    b = (f'<rect width="{W}" height="{H}" rx="10" fill="{t["bg"]}"/>'
         f'<g clip-path="url(#frame)">{rain(t, W, H)}</g>')

    # prompt line
    b += f'<rect x="40" y="28" width="1200" height="44" rx="4" fill="{t["panel"]}" stroke="{t["line"]}"/>'
    prompt = [("usama@github", t["hi"]), (":", t["dim"]), ("~", t["fg"]), ("$ ", t["dim"])]
    plen = sum(len(s) for s, _ in prompt)
    b += (f'<text x="60" y="56" font-family="{MONO}" font-size="18" textLength="{plen * 10.8:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
          + "".join(f'<tspan fill="{c}">{s}</tspan>' for s, c in prompt) + '</text>')
    b += typed("tTerm", 60 + plen * 10.8, 56, [("cat README.md", t["fg"])], 18, 0.3, 16, t["fg"], "blink")[0]
    b += text(1220, 56, "tty1  80x24", 13, t["dim"], ' text-anchor="end"')

    # name in ASCII block letters, wiped in column by column
    words = [figlet(w) for w in NAME.split()]
    cw = 640 / max(len(w[0]) for w in words)
    fs, lh = cw / 0.6, cw / 0.6 * 1.05
    y, nm, begin = 118.0, "", 1.0
    for k, rows in enumerate(words):
        cols = len(rows[0])
        nm += wipe(f"wName{k}", 60, y - fs, lh * 6 + 6, cols, cw, begin, 60)
        nm += f'<g clip-path="url(#wName{k})">' + ascii_rows(rows, 60, y, round(cols * cw, 1), round(fs, 2), lh, t["hi"]) + "</g>"
        y, begin = y + lh * 6 + 22, begin + cols / 60 + 0.1
    b += (f'<g{G(t)}><animateTransform attributeName="transform" type="translate" values="0 0;0 0;5 0;-4 0;0 0" '
          f'keyTimes="0;.9;.92;.94;1" dur="6s" begin="4s" repeatCount="indefinite"/>{nm}</g>')

    # stack, as [ tokens ]
    x, y = 60, 352
    for i, s in enumerate(STACK):
        w = (len(s) + 4) * 8.4
        if x + w > 700:
            x, y = 60, y + 30
        tok = (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="14" xml:space="preserve">'
               f'<tspan fill="{t["dim"]}">[ </tspan><tspan fill="{t["fg"]}">{esc(s)}</tspan><tspan fill="{t["dim"]}"> ]</tspan></text>')
        b += flicker_in(tok, 3.3 + i * 0.07)
        x += w + 4

    # stats line
    b += f'<rect x="60" y="398" width="640" height="40" rx="4" fill="{t["panel"]}" stroke="{t["line"]}"/>'
    D, HI, F = t["dim"], t["hi"], t["faint"]
    stats = [("commits ", D), (f"{COMMITS:,}", HI), ("  |  ", F), ("PRs ", D), (str(PRS), HI), ("  |  ", F),
             ("repos ", D), (str(REPOS), HI), ("  |  ", F), ("contributed to ", D), (str(CONTRIB), HI)]
    b += typed("tStats", 78, 424, stats, 14, 4.0, 70, t["fg"])[0]

    # code card typing buildDreams()
    T, K, S = t["fg"], t["hi"], t["dim"]
    code = [(0, [("const ", K), ("buildDreams", T), (" = () => {", T)]),
            (2, [("const ", K), ("stack", T), (" = [", T), ("'React'", S), (", ", T), ("'Flutter'", S), (", ", T), ("'Node'", S), ("];", T)]),
            (2, [("while ", K), ("(alive) {", T)]),
            (4, [("code", K), ("(); ", T), ("learn", K), ("(); ", T), ("ship", K), ("();", T)]),
            (2, [("}", T)]),
            (2, [("return ", K), ("<Future made=", T), ('"with love"', S), (" />", T)]),
            (0, [("};", T)])]
    b += (f'<rect x="60" y="456" width="640" height="250" rx="4" fill="{t["panel"]}" stroke="{t["line"]}"/>'
          + text(78, 480, "-- buildDreams.jsx " + "-" * 44, 13, t["dim"]))
    tl = 4.9
    for n, (ind, spans) in enumerate(code):
        yy = 516 + n * 25
        b += text(78, yy, f"{n + 1:>2}", 14, t["faint"])
        part, tl = typed(f"tCode{n}", 112 + ind * 10.2, yy, spans, 17, tl, 42, t["fg"], "blink" if n == len(code) - 1 else "hide")
        b += part
        tl += 0.06

    # ASCII avatar, printed row by row behind a scan line
    acw = 368.0 / 64
    afs = round(acw / 0.6, 2)
    b += (f'<rect x="812" y="96" width="424" height="424" rx="4" fill="{t["panel"]}" stroke="{t["line"]}"/>'
          + text(830, 120, "$ ascii ./avatar.png", 13, t["dim"])
          + f'<g{G(t)}><animate attributeName="opacity" values="1;.55;1;1" keyTimes="0;.01;.02;1" dur="5s" begin="3s" repeatCount="indefinite"/>'
          + ascii_rows(avatar, 840, 146, 368, afs, afs * 1.2, t["fg"], begin=0.6) + "</g>"
          + f'<rect x="814" y="134" width="420" height="2" fill="{t["hi"]}" opacity="0"{G(t)}><set attributeName="opacity" to=".9" begin=".6s"/>'
          f'<animate attributeName="y" from="134" to="{146 + 32 * afs * 1.2:.0f}" begin=".6s" dur="{32 * 0.045:.2f}s" fill="freeze"/>'
          f'<set attributeName="opacity" to="0" begin="{0.6 + 32 * 0.045 + 0.1:.2f}s"/></rect>')

    # sign
    sign = (f'<rect x="812" y="540" width="424" height="166" rx="4" fill="none" stroke="{t["fg"]}" stroke-width="1.5"/>'
            f'<rect x="819" y="547" width="410" height="152" rx="2" fill="none" stroke="{t["fg"]}" stroke-width="1"/>'
            + text(1024, 610, "KEEP CODING", 32, t["hi"], ' text-anchor="middle" font-weight="700" letter-spacing="4"')
            + text(1024, 666, "KEEP GROWING", 32, t["hi"], ' text-anchor="middle" font-weight="700" letter-spacing="4"'))
    b += (f'<g opacity="0"{G(t)}><animate attributeName="opacity" values="0;1;.15;1;.35;1" keyTimes="0;.2;.35;.5;.7;1" calcMode="discrete" begin="3s" dur="1.2s" fill="freeze"/>'
          '<animate attributeName="opacity" values="1;.35;1;.6;1;1" keyTimes="0;.02;.04;.06;.08;1" dur="7s" begin="5s" repeatCount="indefinite"/>'
          + sign + '</g>')

    b += overlay + (f'<rect width="{W}" height="{H}" rx="10" fill="url(#vig)"/>' if vig else "")
    b += f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="10" fill="none" stroke="{t["line"]}" stroke-width="1.5"/>'
    return svg(W, H, defs(t, W, H, band + vig) + b, f"{NAME}, animated ASCII terminal banner")


# ---------- swinging ID badge ----------
def lanyard(avatar):
    t, W, H, px = CARD, 520, 700, 260
    r = random.Random(3)
    barcode = "".join(r.choice("▌│█║▌│") for _ in range(26))
    strap_text = ("MUHAMMAD USAMA // " * 4).strip()
    extra = ('<linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f8fafc"/><stop offset=".5" stop-color="#94a3b8"/><stop offset="1" stop-color="#e2e8f0"/></linearGradient>'
             '<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffe3c7" stop-opacity="0"/>'
             '<stop offset=".5" stop-color="#ffe3c7" stop-opacity=".18"/><stop offset="1" stop-color="#ffe3c7" stop-opacity="0"/></linearGradient>'
             f'<path id="strapL" d="M{px - 84} -10 L{px - 8} 252"/><path id="strapR" d="M{px + 84} -10 L{px + 8} 252"/>'
             f'<clipPath id="cardClip"><rect x="{px - 140}" y="290" width="280" height="392" rx="10"/></clipPath>')
    strap = (f'<path d="M{px - 98} -10 L{px - 70} -10 L{px + 2} 252 L{px - 18} 252 Z" fill="{t["panel"]}" stroke="{t["line"]}"/>'
             f'<path d="M{px + 70} -10 L{px + 98} -10 L{px + 18} 252 L{px - 2} 252 Z" fill="{t["bg"]}" stroke="{t["line"]}"/>'
             + "".join(f'<text font-family="{MONO}" font-size="9" font-weight="700" letter-spacing="1.5" fill="{t["fg"]}" dy="3">'
                       f'<textPath href="#{p}">{strap_text}</textPath></text>' for p in ("strapL", "strapR")) +
             f'<rect x="{px - 14}" y="246" width="28" height="22" rx="5" fill="url(#metal)"/>'
             f'<circle cx="{px}" cy="278" r="10" fill="none" stroke="url(#metal)" stroke-width="4"/>'
             f'<rect x="{px - 6}" y="284" width="12" height="14" rx="3" fill="url(#metal)"/>')
    acw = 220 / 64
    card = (f'<rect x="{px - 140}" y="290" width="280" height="392" rx="10" fill="{t["bg"]}" stroke="{t["fg"]}" stroke-width="1.5"/>'
            f'<rect x="{px - 24}" y="302" width="48" height="8" rx="4" fill="#000" stroke="{t["line"]}"/>'
            + text(px, 330, "ACCESS CARD // DEV", 11, t["dim"], ' text-anchor="middle" letter-spacing="3"')
            + f'<path d="M{px - 120} 340 H{px + 120}" stroke="{t["line"]}"/>'
            + '<g filter="url(#glow)">' + ascii_rows(avatar, px - 110, 356, 220, round(acw / 0.6, 2), acw / 0.6 * 1.2, t["fg"]) + "</g>"
            + text(px, 606, NAME.upper(), 20, t["hi"], ' text-anchor="middle" font-weight="700" filter="url(#glow)"')
            + text(px, 627, "@" + HANDLE, 12, t["fg"], ' text-anchor="middle"')
            + f'<text x="{px - 100}" y="657" font-family="{MONO}" font-size="22" fill="{t["hi"]}" textLength="200" lengthAdjust="spacingAndGlyphs">{barcode}</text>'
            + text(px, 674, f"ID {USER_ID}", 10, t["dim"], ' text-anchor="middle" letter-spacing="3"')
            + '<g clip-path="url(#cardClip)"><rect x="-120" y="270" width="110" height="430" fill="url(#shine)" transform="skewX(-18)">'
            '<animate attributeName="x" values="-120;-120;620" keyTimes="0;.55;1" dur="4.5s" repeatCount="indefinite"/></rect>'
            f'<rect x="{px - 140}" y="290" width="280" height="392" fill="url(#crt)"/></g>')
    spline = lambda n: ";".join([".45 0 .55 1"] * n)
    body = ('<g transform="translate(0 -700)">'
            '<animateTransform attributeName="transform" type="translate" values="0 -700;0 18;0 -6;0 0" keyTimes="0;.6;.82;1" '
            'dur="1.1s" begin=".2s" fill="freeze" calcMode="spline" keySplines=".5 0 .9 .6;.2 .6 .4 1;.4 0 .6 1"/>'
            '<g><animateTransform attributeName="transform" type="rotate" '
            f'values="{";".join(f"{a} {px} 0" for a in (0, 13, -10, 7, -4.5, 2.5, -1, 0))}" dur="3.4s" begin="1.1s" fill="freeze" '
            f'calcMode="spline" keySplines="{spline(7)}"/>'
            f'<animateTransform attributeName="transform" type="rotate" values="{";".join(f"{a} {px} 0" for a in (0, 1.8, 0, -1.8, 0))}" '
            f'dur="4s" begin="4.5s" repeatCount="indefinite" calcMode="spline" keySplines="{spline(4)}"/>'
            + strap + card + '</g></g>')
    return svg(W, H, defs(t, W, H, extra) + body, f"{NAME} ID badge")


# ---------- terminal stat cards (local files, so no third-party card service can break) ----------
def card_frame(w, h, title, cmd, inner):
    t = CARD
    band, overlay = crt_overlay(t, w, h)
    head = (f'<rect width="{w}" height="{h}" rx="10" fill="{t["bg"]}"/>'
            + text(20, 30, f"[ {title} ]", 15, t["hi"], ' font-weight="700" filter="url(#glow)"')
            + f'<path d="M20 42 H{w - 20}" stroke="{t["line"]}"/>'
            + typed("tCmd", 20, 66, [("$ ", t["dim"]), (cmd, t["fg"])], 14, 0.2, 50, t["fg"])[0])
    return svg(w, h, defs(t, w, h, band) + head + inner + overlay
               + f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="10" fill="none" stroke="{t["dim"]}" stroke-width="1.5"/>', title)


def stats():
    t = CARD
    pct = MERGED / PRS
    bar = "█" * round(pct * 10) + "░" * (10 - round(pct * 10))
    rows = [("commits", f"{COMMITS:,}"), ("pull requests", str(PRS)), ("merged prs", str(MERGED)),
            ("repositories", str(REPOS)), ("contributed to", str(CONTRIB))]
    inner, tl = "", 1.1
    for i, (k, v) in enumerate(rows):
        part, tl = typed(f"tRow{i}", 30, 94 + i * 22, [(f" {k} ".ljust(22, "."), t["dim"]), (" " + v, t["hi"])], 14, tl, 90, t["fg"])
        inner += part
    inner += typed("tRate", 30, 94 + 5 * 22, [(" merge rate ".ljust(22, "."), t["dim"]), (f" [{bar}] ", t["fg"]), (f"{round(pct * 100)}%", t["hi"])],
                   14, tl, 90, t["fg"], "blink")[0]
    return card_frame(495, 230, "GitHub Stats", f"gh stats --user {HANDLE}", inner)


def langs():
    t = CARD
    inner, tl = "", 0.9
    for i, (n, p) in enumerate(LANGS):
        blocks = max(1, round(24 * p / 100))
        spans = [(f" {n}".ljust(13), t["fg"]), ("█" * blocks, t["hi"]), ("░" * (24 - blocks), t["faint"]), (f" {p:>4}%", t["dim"])]
        part, tl = typed(f"tLang{i}", 30, 94 + i * 22, spans, 14, tl, 110, t["fg"], "blink" if i == len(LANGS) - 1 else "hide")
        inner += part
    return card_frame(495, 230, "Most Used Languages", "langs --top 6", inner)


def trophies():
    t = CARD
    # Rank letters follow github-profile-trophy style thresholds, roughly.
    cells = [("Commits", f"{COMMITS:,}", "S"), ("Pull Requests", str(PRS), "AAA"), ("Merged PRs", str(MERGED), "AAA"),
             ("Repositories", str(REPOS), "SSS"), ("Contributed To", str(CONTRIB), "AA"), ("Languages", "12+", "S")]
    cup = ["  ___  ", " (   ) ", "  \\_/  ", "  _|_  "]
    inner = ""
    for i, (k, v, rank) in enumerate(cells):
        x = 20 + i * 136
        cx = x + 63
        cell = (f'<rect x="{x}" y="84" width="126" height="132" rx="4" fill="{t["panel"]}" stroke="{t["line"]}"/>'
                + "".join(text(cx, 104 + j * 12, row, 12, t["fg"], ' text-anchor="middle"') for j, row in enumerate(cup))
                + text(cx, 164, f"[ {rank} ]", 16, t["hi"], ' text-anchor="middle" font-weight="700" filter="url(#glow)"')
                + text(cx, 186, k, 12, t["fg"], ' text-anchor="middle"')
                + text(cx, 204, v, 12, t["dim"], ' text-anchor="middle"'))
        inner += flicker_in(cell, 1.0 + i * 0.15)
    return card_frame(846, 232, "Trophies", "trophies --list", inner)


# ---------- sections in Meghamittal0920's layout, drawn as ASCII ----------
def section(W, H, inner, title, extra=""):
    t = DARK
    band, overlay = crt_overlay(t, W, H)
    ex = (band + '<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#262b3d"/></pattern>'
          f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{OR}"/><stop offset=".5" stop-color="{t["line"]}"/>'
          f'<stop offset="1" stop-color="{BLU}"/></linearGradient>'
          f'<linearGradient id="ul" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{OR}"/><stop offset="1" stop-color="{BLU}"/></linearGradient>'
          f'<radialGradient id="warm" cx=".12" cy=".15" r=".6"><stop offset="0" stop-color="{OR}" stop-opacity=".14"/>'
          f'<stop offset="1" stop-color="{OR}" stop-opacity="0"/></radialGradient>' + extra)
    return svg(W, H, defs(t, W, H, ex) + f'<rect width="{W}" height="{H}" rx="10" fill="{t["bg"]}"/>'
               f'<g clip-path="url(#frame)"><rect width="{W}" height="{H}" fill="url(#dots)"/><rect width="{W}" height="{H}" fill="url(#warm)"/></g>'
               + inner + overlay
               + f'<rect x=".75" y=".75" width="{W - 1.5}" height="{H - 1.5}" rx="10" fill="none" stroke="url(#edge)" stroke-width="1.5"/>', title)


def label(x, y, s, col=OR):
    return text(x, y, s, 13, col, ' font-weight="700" letter-spacing="3"')


def show(inner, begin):
    return f'<g opacity="0"><set attributeName="opacity" to="1" begin="{begin:.2f}s"/>{inner}</g>'


def window(x, y, w, h, title):
    t = DARK
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{t["panel"]}" stroke="{t["line"]}"/>'
            f'<circle cx="{x + 22}" cy="{y + 22}" r="6" fill="{RED}"/><circle cx="{x + 42}" cy="{y + 22}" r="6" fill="#f5b83d"/>'
            f'<circle cx="{x + 62}" cy="{y + 22}" r="6" fill="{GRN}"/>'
            + text(x + w / 2, y + 27, title, 12, t["dim"], ' text-anchor="middle"') + f'<path d="M{x} {y + 42} H{x + w}" stroke="{t["line"]}"/>')


def hero(av):
    t, W, H = DARK, 1280, 560
    b = (text(52, 64, "usama@github", 15, GRN, ' textLength="108" lengthAdjust="spacingAndGlyphs"')
         + text(160, 64, ":~$ ", 15, t["dim"], ' textLength="36" lengthAdjust="spacingAndGlyphs"'))
    b += typed("tSum", 196, 64, [("summon ", t["hi"]), ("--profile", t["dim"])], 15, .3, 18, OR, "blink")[0]
    b += show(text(52, 140, "Hi, I'm", 24, t["hi"], ' font-weight="700"'), 1.2)
    words = [figlet(w) for w in NAME.split()]
    cw = 600 / max(len(w[0]) for w in words)
    fs, lh = cw / .6, cw / .6 * 1.05
    y, nm, begin = 190.0, "", 1.5
    for k, rows in enumerate(words):
        cols = len(rows[0])
        nm += wipe(f"wHero{k}", 52, y - fs, lh * 6 + 6, cols, cw, begin, 70)
        nm += f'<g clip-path="url(#wHero{k})">' + ascii_rows(rows, 52, y, round(cols * cw, 1), round(fs, 2), lh, OR) + "</g>"
        y, begin = y + lh * 6 + 16, begin + cols / 70 + .1
    b += f'<g filter="url(#glow)">{nm}</g>'
    b += (f'<rect x="52" y="384" width="0" height="3" rx="1.5" fill="url(#ul)"><animate attributeName="width" from="0" to="150" '
          f'begin="{begin:.1f}s" dur=".6s" fill="freeze"/></rect>')
    tiles = [("REPOS", str(REPOS)), ("COMMITS", f"{COMMITS:,}"), ("PULL REQS", str(PRS)), ("CONTRIB TO", str(CONTRIB))]
    for i, (k, v) in enumerate(tiles):
        x = 52 + i * 142
        tile = (f'<rect x="{x}" y="412" width="128" height="58" rx="8" fill="{t["panel"]}" stroke="{t["line"]}"/>'
                + text(x + 14, 440, v, 22, OR, ' font-weight="700"') + text(x + 14, 459, k, 10, t["dim"], ' letter-spacing="2"'))
        b += flicker_in(tile, 3.0 + i * .12)
    b += text(52, 516, "MOTTO  ·", 12, t["dim"], ' letter-spacing="2"')
    b += typed("tMotto", 136, 516, [("keep coding, keep growing.", OR)], 12, 3.8, 24, OR, "blink")[0]

    # right: an ASCII "video" of your avatar
    x0, y0, fw, fh = 700, 52, 524, 424
    b += f'<rect x="{x0}" y="{y0}" width="{fw}" height="{fh}" rx="6" fill="{t["panel"]}" opacity=".55"/>'
    for (x, y, dx, dy) in [(x0, y0, 1, 1), (x0 + fw, y0, -1, 1), (x0, y0 + fh, 1, -1), (x0 + fw, y0 + fh, -1, -1)]:
        b += f'<path d="M{x} {y + dy * 26} V{y} H{x + dx * 26}" fill="none" stroke="{OR}" stroke-width="2"/>'
    afs, alh, aw = 9.0, 10.8, 346
    b += (f'<g filter="url(#glow)">' + ascii_rows(av, x0 + (fw - aw) / 2, 82, aw, afs, alh, OR, begin=.6, step=.04) + "</g>"
          f'<rect x="{x0 + 4}" y="70" width="{fw - 8}" height="2" fill="{t["hi"]}" opacity="0"><set attributeName="opacity" to=".8" begin=".6s"/>'
          f'<animate attributeName="y" from="70" to="{82 + 32 * alh:.0f}" begin=".6s" dur="{32 * .04:.2f}s" fill="freeze"/>'
          f'<set attributeName="opacity" to="0" begin="{.6 + 32 * .04 + .1:.2f}s"/></rect>')
    b += (text(x0 + 22, 450, "* USAMA.ASCII", 12, t["hi"], ' font-weight="700" letter-spacing="2"')
          + text(x0 + fw - 22, 450, "GITHUB · 24FPS · LOOP", 11, t["dim"], ' text-anchor="end" letter-spacing="2"')
          + f'<rect x="{x0 + 22}" y="460" width="{fw - 44}" height="2" fill="{t["line"]}"/>'
          f'<rect x="{x0 + 22}" y="460" width="0" height="2" fill="url(#ul)"><animate attributeName="width" values="0;{fw - 44}" dur="8s" repeatCount="indefinite"/></rect>')
    return section(W, H, b, f"Hi, I'm {NAME}")


def build():
    t, W, H = DARK, 1280, 520
    D, F, HI = t["dim"], t["fg"], t["hi"]
    b = window(32, 36, 540, 448, "~/projects")
    lines = [[("$ ", D), ("tree ~/projects -L 1", HI)], [("~/projects", F)],
             [("├── ", D), ("mobility-platform/", F), ("   flutter · node", D)],
             [("├── ", D), ("creator-platform/ ", F), ("   react · ts", D)],
             [("├── ", D), ("3d-warehouse/     ", F), ("   three.js · r3f", D)],
             [("├── ", D), ("storefront/       ", F), ("   next.js · webgl", D)],
             [("├── ", D), ("job-portal/       ", F), ("   react · ts", D)],
             [("└── ", D), ("motion-slides/    ", F), ("   remotion", D)],
             None, [("6 directories, ", D), (f"{COMMITS:,} commits", HI)], [("$ ", D)]]
    tl = .4
    for i, spans in enumerate(lines):
        if spans:
            part, tl = typed(f"tTree{i}", 56, 112 + i * 32, spans, 15, tl, 60 if i == 0 else 140, OR,
                             "blink" if i == len(lines) - 1 else "hide")
            b += part
            tl += .08
    x = 630
    b += label(x, 74, "// WHAT I BUILD") + text(x, 120, "Ideas in, apps out", 32, HI, ' font-weight="700"')
    items = [("[ ]", "Mobile apps", "Rider and driver apps, admin panels: Flutter, Dart", OR),
             ("</>", "Web platforms", "Dashboards, storefronts, portals: React, Next.js, Node", BLU),
             ("{*}", "3D and motion", "WebGL scenes and programmatic video: Three.js, Remotion", PUR)]
    for i, (ic, h, d, col) in enumerate(items):
        y = 166 + i * 76
        it = (f'<rect x="{x}" y="{y}" width="46" height="46" rx="8" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-opacity=".5"/>'
              + text(x + 23, y + 29, ic, 15, col, ' text-anchor="middle" font-weight="700"')
              + text(x + 64, y + 19, h, 18, HI, ' font-weight="700"') + text(x + 64, y + 40, d, 13, D))
        b += flicker_in(it, 1.0 + i * .25)
    b += flicker_in(f'<rect x="{x}" y="404" width="612" height="72" rx="10" fill="{OR}" fill-opacity=".06" stroke="{OR}" stroke-opacity=".35"/>'
                    f'<rect x="{x}" y="404" width="4" height="72" rx="2" fill="{OR}"/>'
                    + text(x + 22, 436, '"keep coding, keep growing."', 17, HI, ' font-weight="700"')
                    + text(x + 22, 460, f"{REPOS} REPOS  ·  {COMMITS:,} COMMITS  ·  {PRS} PRS", 11, D, ' letter-spacing="2"'), 2.0)
    return section(W, H, b, "What I build")


def stack():
    t, W, H = DARK, 1280, 340
    brand = {"JavaScript": ("JS", "#f7df1e"), "TypeScript": ("TS", "#3178c6"), "React": ("Re", "#61dafb"), "Next.js": ("Nx", "#e6e8ee"),
             "Node.js": ("No", "#5fa04e"), "Flutter": ("Fl", "#47c5fb"), "Dart": ("Dt", "#2bb7f6"), "PostgreSQL": ("Pg", "#6b8cff"),
             "Tailwind": ("Tw", "#38bdf8"), "Three.js": ("3D", "#cfd3dc"), "Laravel": ("Lv", "#ff2d20"), "Python": ("Py", "#ffd43b")}
    beam = (f'<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{OR}" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="{OR}" stop-opacity=".16"/><stop offset="1" stop-color="{OR}" stop-opacity="0"/></linearGradient>')
    b = (label(52, 62, "// TECH ARSENAL") + text(52, 106, "Tools I build with", 32, t["hi"], ' font-weight="700"')
         + text(1228, 62, f"{len(STACK)} TOOLS LOADED", 11, t["dim"], ' text-anchor="end" letter-spacing="3"'))
    for i, s in enumerate(STACK):
        code, col = brand.get(s, (s[:2], OR))
        x, y = 52 + (i % 6) * 196, 146 + (i // 6) * 84
        tile = (f'<rect x="{x}" y="{y}" width="184" height="64" rx="10" fill="{col}" fill-opacity=".07" stroke="{col}" stroke-opacity=".45"/>'
                f'<rect x="{x + 14}" y="{y + 16}" width="34" height="32" rx="6" fill="{col}" fill-opacity=".16"/>'
                + text(x + 31, y + 37, code, 14, col, ' text-anchor="middle" font-weight="700"')
                + text(x + 62, y + 38, s, 15, t["hi"]))
        b += flicker_in(tile, .5 + i * .07)
    b += ('<g clip-path="url(#frame)"><rect x="-300" y="120" width="220" height="200" fill="url(#beam)" transform="skewX(-20)">'
          '<animate attributeName="x" values="-300;1500;1500" keyTimes="0;.6;1" dur="6s" begin="1.5s" repeatCount="indefinite"/></rect></g>')
    return section(W, H, b, "Tech stack", beam)


# Shown in connect.svg. Add more as (name, handle, colour), e.g. ("LinkedIn", "in/your-id", BLU).
LINKS = [("GitHub", "@" + HANDLE, OR)]


def connect():
    t, W, H = DARK, 1280, 400
    D, HI = t["dim"], t["hi"]
    b = window(32, 36, 600, 328, "network")
    part, tl = typed("tPing", 56, 112, [("$ ", D), ("ping usama", HI)], 15, .4, 14, OR)
    b += part
    out = [[("PING github.com/" + HANDLE + ": 56 data bytes", D)]]
    out += [[("64 bytes from ", D), ("@" + HANDLE, OR), (f": seq={i} time=0.{4 + i}2 ms", D)] for i in range(3)]
    out += [[("--- usama ping statistics ---", D)], [("3 packets sent, 3 received, ", D), ("0% packet loss", GRN)]]
    for i, spans in enumerate(out):
        line = (f'<text x="56" y="{146 + i * 30}" font-family="{MONO}" font-size="13" xml:space="preserve">'
                + "".join(f'<tspan fill="{c}">{esc(s)}</tspan>' for s, c in spans) + "</text>")
        b += show(line, tl + .3 + i * .45)
    x = 680
    b += label(x, 84, "// LET'S CONNECT") + text(x, 130, "Let's build something", 32, HI, ' font-weight="700"')
    for i, (name, handle, col) in enumerate(LINKS):
        y = 166 + i * 92
        card = (f'<rect x="{x}" y="{y}" width="548" height="76" rx="10" fill="{t["panel"]}" stroke="{col}" stroke-opacity=".45"/>'
                f'<rect x="{x + 16}" y="{y + 16}" width="44" height="44" rx="8" fill="{col}" fill-opacity=".14"/>'
                + text(x + 38, y + 44, name[:2].upper(), 15, col, ' text-anchor="middle" font-weight="700"')
                + text(x + 76, y + 34, name, 17, HI, ' font-weight="700"') + text(x + 76, y + 56, handle, 12, D)
                + text(x + 524, y + 46, "->", 16, col, ' text-anchor="end" font-weight="700"'))
        b += flicker_in(card, 1.0 + i * .2)
    return section(W, H, b, "Let's connect")


def dashboard(av):
    t, W, H = DARK, 1280, 620
    # the swinging badge, nested with its ids prefixed so they can't clash with this file's ids
    badge = lanyard(av)
    badge = badge[badge.index(">", badge.index("<svg")) + 1:badge.rindex("</svg>")]
    badge = re.sub(r"<title>.*?</title>", "", badge).replace('id="', 'id="L').replace("url(#", "url(#L").replace('href="#', 'href="#L')
    b = f'<svg x="0" y="0" width="460" height="620" viewBox="0 0 520 700">{badge}</svg>'
    x0 = 470
    b += (label(x0, 70, "// DEV DASHBOARD") + text(x0, 112, "Stats from the field", 32, t["hi"], ' font-weight="700"')
          + f'<rect x="1088" y="54" width="160" height="26" rx="13" fill="{GRN}" fill-opacity=".1" stroke="{GRN}" stroke-opacity=".5"/>'
          f'<circle cx="1104" cy="67" r="4" fill="{GRN}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>'
          + text(1116, 71, "ACTIVE · GITHUB", 11, GRN, ' font-weight="700" letter-spacing="2"'))
    tiles = [("REPOS", str(REPOS), OR), ("COMMITS", f"{COMMITS:,}", "#f5b83d"), ("PULL REQS", str(PRS), BLU), ("CONTRIB TO", str(CONTRIB), GRN)]
    for i, (k, v, col) in enumerate(tiles):
        x = x0 + i * 196
        b += flicker_in(f'<rect x="{x}" y="140" width="182" height="96" rx="10" fill="{t["panel"]}" stroke="{t["line"]}"/>'
                        f'<rect x="{x + 18}" y="156" width="24" height="3" rx="1.5" fill="{col}"/>'
                        + text(x + 18, 198, v, 30, t["hi"], ' font-weight="700"') + text(x + 18, 220, k, 10, t["dim"], ' letter-spacing="2"'),
                        .8 + i * .12)
    # top languages
    b += (f'<rect x="{x0}" y="260" width="470" height="320" rx="10" fill="{t["panel"]}" stroke="{t["line"]}"/>'
          + text(x0 + 22, 292, "TOP LANGUAGES · %", 11, t["dim"], ' letter-spacing="2"'))
    top = LANGS[0][1]
    for i, (n, p) in enumerate(LANGS):
        y = 330 + i * 38
        b += (text(x0 + 22, y, n, 13, t["hi"]) + f'<rect x="{x0 + 130}" y="{y - 10}" width="250" height="10" rx="5" fill="{t["line"]}"/>'
              f'<rect x="{x0 + 130}" y="{y - 10}" width="0" height="10" rx="5" fill="url(#ul)"><animate attributeName="width" from="0" '
              f'to="{250 * p / top:.0f}" begin="{1.4 + i * .12:.2f}s" dur=".8s" fill="freeze"/></rect>'
              + text(x0 + 448, y, f"{p}%", 12, t["dim"], ' text-anchor="end"'))
    b += text(x0 + 22, 560, "share of code in public repos", 10, t["faint"])
    # stack focus
    x1 = 956
    b += (f'<rect x="{x1}" y="260" width="292" height="320" rx="10" fill="{t["panel"]}" stroke="{t["line"]}"/>'
          + text(x1 + 22, 292, "STACK FOCUS", 11, t["dim"], ' letter-spacing="2"'))
    for i, (k, v, col) in enumerate([("MOBILE", "Flutter · Dart", OR), ("WEB", "React · Next.js · Node", BLU),
                                     ("3D / MOTION", "Three.js · Remotion", PUR), ("DATA", "PostgreSQL · Laravel", GRN)]):
        y = 334 + i * 60
        b += flicker_in(f'<circle cx="{x1 + 27}" cy="{y - 4}" r="4" fill="{col}"/>' + text(x1 + 40, y, k, 11, col, ' font-weight="700" letter-spacing="2"')
                        + text(x1 + 40, y + 22, v, 13, t["hi"]), 2.0 + i * .15)
    return section(W, H, b, f"{NAME} ID badge and GitHub dashboard")


if __name__ == "__main__":
    av = ascii_avatar()
    av_dark = ascii_avatar(invert=True)  # dense characters on bright pixels reads right on dark backgrounds
    write("banner.svg", banner(DARK, av_dark))
    write("banner-light.svg", banner(LIGHT, av))
    write("hero.svg", hero(av_dark))
    write("build.svg", build())
    write("stack.svg", stack())
    write("lanyard.svg", lanyard(av_dark))
    write("stats.svg", stats())
    write("langs.svg", langs())
    write("trophies.svg", trophies())
    write("connect.svg", connect())
    write("dashboard.svg", dashboard(av_dark))
