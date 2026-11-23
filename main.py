#!/usr/bin/env python3
"""The World Today - 23 November 2026 in one image.

A Python 3 program (standard library only) that draws a newspaper
front page summing up the world news of Monday 23 November 2026 and
writes it as a deterministic PNG to /output/entry.png (or to
$MAKEFUN_OUTPUT_DIR/entry.png when that variable is set).

Everything is drawn by this file: a hand-rolled PNG encoder, a tiny
5x7 bitmap font defined below, and simple raster shapes.  No clocks,
no randomness, no network, no input files - two runs always produce
byte-identical output.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- canvas

PAPER = (247, 242, 231)
INK = (18, 18, 20)
RED = (178, 34, 30)
BLUE = (24, 62, 120)
SEA = (38, 96, 143)
SKY = (168, 205, 232)
GOLD = (198, 148, 32)
GREY = (92, 92, 96)
LIGHT = (232, 224, 205)
WHITE = (255, 255, 255)
ORANGE = (232, 116, 32)
GREEN = (28, 110, 62)

PX = bytearray(W * H * 3)


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        PX[i] = c[0]
        PX[i + 1] = c[1]
        PX[i + 2] = c[2]


def rect(x, y, w, h, c):
    for yy in range(y, y + h):
        base = yy * W * 3
        for xx in range(x, x + w):
            if 0 <= xx < W and 0 <= yy < H:
                i = base + xx * 3
                PX[i] = c[0]
                PX[i + 1] = c[1]
                PX[i + 2] = c[2]


def frame(x, y, w, h, c, t=3):
    rect(x, y, w, t, c)
    rect(x, y + h - t, w, t, c)
    rect(x, y, t, h, c)
    rect(x + w - t, y, t, h, c)


def disc(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                put(xx, yy, c)


def ring(cx, cy, r, c, t=3):
    for yy in range(cy - r - t, cy + r + t + 1):
        for xx in range(cx - r - t, cx + r + t + 1):
            d2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
            if (r - t) * (r - t) <= d2 <= (r + t) * (r + t):
                put(xx, yy, c)


def line(x0, y0, x1, y1, c, t=2):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    r = max(1, t // 2)
    for s in range(steps + 1):
        x = x0 + (x1 - x0) * s // steps
        y = y0 + (y1 - y0) * s // steps
        disc(x, y, r, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    lo_y = max(0, min(y0, y1, y2))
    hi_y = min(H - 1, max(y0, y1, y2))
    for yy in range(lo_y, hi_y + 1):
        xs = []
        for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                   ((x1, y1), (x2, y2)),
                                   ((x2, y2), (x0, y0))):
            if ay == by:
                continue
            if (ay <= yy < by) or (by <= yy < ay):
                xs.append(ax + (bx - ax) * (yy - ay) // (by - ay))
        if len(xs) >= 2:
            for xx in range(min(xs), max(xs) + 1):
                put(xx, yy, c)


# ---------------------------------------------------------------- font
# A 5x7 bitmap font.  Each glyph is seven rows of five bits.

FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
}


def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, c, bold=False):
    s = s.upper()
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    rect(x + col * scale, y + row * scale, scale, scale, c)
                    if bold and scale > 2:
                        rect(x + col * scale + 1, y + row * scale,
                             scale, scale, c)
        x += 6 * scale
    return x


def text_c(cx, y, s, scale, c, bold=False):
    return draw_text(cx - text_w(s, scale) // 2, y, s, scale, c, bold)


def wrap(s, scale, max_w):
    words = s.upper().split()
    lines = []
    cur = ""
    for wd in words:
        trial = wd if not cur else cur + " " + wd
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def block(x, y, s, scale, c, max_w, leading=10, bold=False):
    for ln in wrap(s, scale, max_w):
        draw_text(x, y, ln, scale, c, bold)
        y += 7 * scale + leading
    return y


# ---------------------------------------------------------------- scenes

def draw_lead_scene(x, y, w, h):
    """Sea drones closing on a warship at a Libyan port, at dawn."""
    rect(x, y, w, h, SKY)
    rect(x + 30, y + 22, 84, 16, WHITE)
    rect(x + 52, y + 12, 44, 16, WHITE)
    rect(x + 236, y + 18, 70, 14, WHITE)
    sea_y = y + h * 55 // 100
    rect(x, sea_y, w, h - (sea_y - y), SEA)
    for i in range(9):
        wx = x + 18 + i * 52
        line(wx, sea_y + 26 + (i % 3) * 22, wx + 30, sea_y + 26 + (i % 3) * 22,
             WHITE, 2)
    # harbour crane on the left shore
    line(x + 14, sea_y, x + 14, sea_y - 118, INK, 5)
    line(x + 14, sea_y - 118, x + 104, sea_y - 118, INK, 5)
    line(x + 88, sea_y - 118, x + 88, sea_y - 88, INK, 3)
    rect(x + 78, sea_y - 88, 20, 16, GOLD)
    # the corvette: hull, deck, bridge, mast, gun
    hx = x + 56
    hy = sea_y - 6
    tri(hx - 26, hy, hx + 6, hy + 34, hx + 6, hy, (52, 56, 64))
    rect(hx, hy - 4, 252, 30, (52, 56, 64))
    tri(hx + 252, hy - 4, hx + 252, hy + 26, hx + 220, hy + 26, (52, 56, 64))
    rect(hx + 44, hy - 34, 110, 30, (88, 94, 104))
    rect(hx + 72, hy - 62, 54, 28, (88, 94, 104))
    line(hx + 98, hy - 62, hx + 98, hy - 100, INK, 4)
    line(hx + 98, hy - 100, hx + 138, hy - 86, INK, 3)
    rect(hx + 164, hy - 26, 46, 8, INK)
    for i in range(5):
        disc(hx + 62 + i * 30, hy + 10, 5, WHITE)
    rect(hx + 14, hy - 20, 22, 16, RED)
    # explosion where a drone has hit, aft of the bridge
    ex, ey = hx + 204, hy - 44
    disc(ex, ey, 24, ORANGE)
    disc(ex, ey, 15, (246, 190, 60))
    disc(ex, ey, 7, WHITE)
    for dx, dy in ((-32, -20), (30, -26), (38, 6), (-28, 16), (4, -38)):
        line(ex, ey, ex + dx, ey + dy, ORANGE, 5)
    for i in range(6):
        disc(ex - 22 + i * 10, ey - 56 - (i % 2) * 14, 10 + (i % 3) * 3,
             (96, 96, 100))
    # three sea drones with wakes, heading for the ship
    for (dx, dy) in ((30, 52), (128, 30), (216, 62)):
        bx, by = x + dx, y + h - dy
        tri(bx, by, bx + 46, by + 10, bx, by + 20, INK)
        rect(bx - 4, by + 4, 30, 12, INK)
        line(bx - 44, by + 16, bx - 6, by + 12, WHITE, 3)
        line(bx - 44, by + 4, bx - 6, by + 8, WHITE, 3)
        disc(bx + 30, by + 10, 4, RED)


def draw_globe(x, y, r):
    disc(x, y, r, (64, 132, 190))
    ring(x, y, r, INK, 3)
    disc(x - r // 3, y - r // 4, r // 4, GREEN)
    disc(x + r // 4, y + r // 5, r // 3, GREEN)
    disc(x + r // 6, y - r // 2, r // 5, GREEN)
    line(x - r, y, x + r, y, (30, 80, 130), 2)
    line(x, y - r, x, y + r, (30, 80, 130), 2)


def draw_chart(x, y, w, h):
    rect(x, y, w, h, (24, 26, 34))
    pts = [(0, 18), (52, 26), (104, 20), (156, 44), (208, 66), (260, 96)]
    for i in range(len(pts) - 1):
        line(x + pts[i][0], y + pts[i][1], x + pts[i + 1][0],
             y + pts[i + 1][1], RED, 5)
        disc(x + pts[i][0], y + pts[i][1], 5, WHITE)
    disc(x + pts[-1][0], y + pts[-1][1], 6, RED)
    for gx in range(0, w, 52):
        line(x + gx, y + 6, x + gx, y + h - 6, (60, 64, 74), 1)


# ---------------------------------------------------------------- page

def panel(x, y, w, h, tag, tag_c, head, body):
    frame(x, y, w, h, INK, 3)
    rect(x, y, w, 34, tag_c)
    draw_text(x + 12, y + 7, tag, 3, WHITE, bold=True)
    yy = block(x + 12, y + 46, head, 4, INK, w - 24, 6, bold=True)
    rect(x + 12, yy + 1, w - 24, 3, tag_c)
    block(x + 12, yy + 13, body, 2, (40, 40, 44), w - 24, 6)


def build():
    rect(0, 0, W, H, PAPER)
    frame(14, 14, W - 28, H - 28, INK, 4)

    # masthead
    text_c(W // 2, 36, "THE WORLD TODAY", 9, INK, bold=True)
    rect(48, 112, W - 96, 6, RED)
    text_c(W // 2, 130, "MONDAY 23 NOVEMBER 2026", 5, RED, bold=True)
    text_c(W // 2, 172, "THE DAY'S WORLD NEWS IN ONE IMAGE", 3, GREY)

    # lead story
    rect(48, 206, W - 96, 4, INK)
    draw_text(48, 218, "UKRAINE WAR REACHES THE MEDITERRANEAN", 3, RED, bold=True)
    draw_text(48, 252, "SEA DRONES SINK", 6, INK, bold=True)
    draw_text(48, 302, "RUSSIAN WARSHIP", 6, INK, bold=True)
    block(48, 360,
          "ZELENSKY SAYS 7 UKRAINIAN SEA DRONES SANK THE CORVETTE "
          "MERKURY AT BENGHAZI PORT IN LIBYA AND HIT A SECOND SHIP. "
          "THE UN URGES A PROBE AS THE WAR SPILLS INTO THE MED.",
          2, (40, 40, 44), 520, 6)
    draw_lead_scene(600, 252, 376, 200)
    frame(600, 252, 376, 200, INK, 3)
    draw_text(600, 460, "BENGHAZI PORT, LIBYA", 2, GREY)

    # four secondary stories, two by two
    panel(48, 492, 452, 186, "CLIMATE - ANTALYA", RED,
          "COP31 COLLAPSES, NO DEAL",
          "EU AND 130 NATIONS REJECT A TEXT THAT OMITS FOSSIL "
          "FUELS. TALKS END AFTER RECORD OVERTIME.")
    panel(524, 492, 452, 186, "WAR - DYMER, UKRAINE", BLUE,
          "STRIKE KILLS 11 NEAR KYIV",
          "RUSSIAN DRONE LEVELS A BLOCK OF FLATS. RESCUERS PULL "
          "A BOY, 7, ALIVE FROM THE RUBBLE.")
    panel(48, 690, 452, 186, "MARKETS - TOKYO / NY", GOLD,
          "AI SELL-OFF RATTLES MARKETS",
          "NIKKEI -5.1% AND S&P 500 -3.7% AS TECH SHARES SLIDE. "
          "GOLD JUMPS AS INVESTORS SEEK SAFETY.")
    panel(524, 690, 452, 186, "U.S. - WASHINGTON", GREEN,
          "DEMOCRATS WIN HOUSE MAJORITY",
          "BIGGEST MAJORITY SINCE 1992. AT LEAST 258 SEATS AFTER "
          "A NORTH CAROLINA RECOUNT.")

    # bottom ticker
    rect(48, 888, W - 96, 108, INK)
    draw_text(64, 898, "ALSO TODAY", 3, GOLD, bold=True)
    block(64, 928,
          "SUDAN: DRONES HIT HOMES AND A U.N. BUILDING IN KHARTOUM  -  "
          "INDONESIA: CANDY FACTORY FIRE IN BANTEN KILLS 24  -  "
          "IRAN: TRUMP WARNS U.S. STRIKES MAY RESUME AFTER NEW YEAR  -  "
          "SPORT: ALCARAZ WINS HIS FIRST ATP FINALS TITLE",
          2, WHITE, W - 128, 4)

    return PX


# ---------------------------------------------------------------- png out

def png_bytes():
    raw = bytearray()
    row = W * 3
    for yy in range(H):
        raw.append(0)
        raw += PX[yy * row:(yy + 1) * row]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    build()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(png_bytes())


if __name__ == "__main__":
    main()
