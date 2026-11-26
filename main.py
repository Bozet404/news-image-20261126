#!/usr/bin/env python3
"""news-image-20261126: one image summing up Thursday 26 November 2026.

Draws a newspaper front page (1024x1024 PNG) with Python's standard library
only: a hand-built 5x7 bitmap font, vector shapes, and a small PNG encoder.
No network, no files read, no timestamps: two runs write identical bytes.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# --- palette ---------------------------------------------------------------
NAVY = (10, 27, 51)
PANEL = (18, 41, 77)
PANEL_LT = (24, 54, 96)
WHITE = (245, 245, 240)
GOLD = (232, 180, 60)
MIST = (190, 205, 225)
RED = (220, 60, 60)
ORANGE = (240, 130, 40)
YELLOW = (240, 200, 60)
TEAL = (60, 200, 180)
BLUE = (80, 140, 240)
PURPLE = (170, 110, 230)
FLAME_Y = (255, 210, 80)
GREY = (150, 160, 175)

# --- 5x7 bitmap font, drawn by hand in this file ---------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    ":": (".....", ".##..", ".....", ".....", ".##..", ".....", "....."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = c[0]
                self.px[i + 1] = c[1]
                self.px[i + 2] = c[2]

    def line(self, x0, y0, x1, y1, c, width=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            half = width // 2
            self.fill_rect(x0 - half, y0 - half, width, width, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            dyy = yy - cy
            span = int((r * r - dyy * dyy) ** 0.5)
            self.fill_rect(cx - span, yy, span * 2 + 1, 1, c)

    def fill_polygon(self, pts, c):
        # scanline fill; pts = list of (x, y)
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[k]), y, int(xs[k + 1]) - int(xs[k]) + 1, 1, c)

    def text_width(self, s, scale):
        return len(s) * 6 * scale - scale

    def text(self, x, y, s, scale, c, align="left"):
        if align == "center":
            x -= self.text_width(s, scale) // 2
        elif align == "right":
            x -= self.text_width(s, scale)
        cx = x
        for ch in s:
            glyph = FONT.get(ch)
            if glyph is None:
                cx += 6 * scale
                continue
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(
                            cx + col * scale, y + row * scale, scale, scale, c
                        )
            cx += 6 * scale


# --- icons -----------------------------------------------------------------
def icon_flame(cv, x, y, s):
    # outer flame, then inner flame, over a small oil barrel
    cv.fill_polygon(
        [
            (x + s // 2, y),
            (x + s, y + s // 2),
            (x + int(s * 0.72), y + s),
            (x + int(s * 0.28), y + s),
            (x, y + s // 2),
        ],
        ORANGE,
    )
    cv.fill_polygon(
        [
            (x + s // 2, y + int(s * 0.34)),
            (x + int(s * 0.78), y + int(s * 0.66)),
            (x + int(s * 0.62), y + int(s * 0.92)),
            (x + int(s * 0.38), y + int(s * 0.92)),
            (x + int(s * 0.22), y + int(s * 0.66)),
        ],
        FLAME_Y,
    )


def icon_burst(cv, x, y, s):
    # explosion starburst: alternating long/short spikes
    import math

    cx, cy = x + s // 2, y + s // 2
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        r = s // 2 if i % 2 == 0 else s // 5
        pts.append((int(cx + r * math.cos(ang)), int(cy + r * math.sin(ang))))
    cv.fill_polygon(pts, YELLOW)
    cv.fill_circle(cx, cy, s // 6, ORANGE)


def icon_wall(cv, x, y, s):
    # a tall building split by a jagged crack, rubble at its base
    cv.fill_rect(x + int(s * 0.14), y + int(s * 0.06), int(s * 0.3), int(s * 0.66), (120, 125, 140))
    cv.fill_rect(x + int(s * 0.56), y + int(s * 0.06), int(s * 0.3), int(s * 0.66), (90, 95, 110))
    for wy in range(y + int(s * 0.14), y + int(s * 0.6), int(s * 0.16)):
        cv.fill_rect(x + int(s * 0.2), wy, 4, 5, GOLD)
        cv.fill_rect(x + int(s * 0.62), wy, 4, 5, GOLD)
    cv.line(x + int(s * 0.44), y + int(s * 0.06), x + int(s * 0.52), y + int(s * 0.3), NAVY, 3)
    cv.line(x + int(s * 0.52), y + int(s * 0.3), x + int(s * 0.46), y + int(s * 0.52), NAVY, 3)
    cv.line(x + int(s * 0.46), y + int(s * 0.52), x + int(s * 0.56), y + int(s * 0.72), NAVY, 3)
    cv.fill_polygon(
        [(x + int(s * 0.14), y + int(s * 0.72)), (x + int(s * 0.3), y + int(s * 0.72)), (x + int(s * 0.22), y + int(s * 0.86))],
        (120, 125, 140),
    )
    cv.fill_polygon(
        [(x + int(s * 0.56), y + int(s * 0.72)), (x + int(s * 0.72), y + int(s * 0.72)), (x + int(s * 0.64), y + int(s * 0.86))],
        (90, 95, 110),
    )
    cv.fill_polygon(
        [(x + int(s * 0.36), y + int(s * 0.78)), (x + int(s * 0.52), y + int(s * 0.78)), (x + int(s * 0.44), y + int(s * 0.92))],
        (150, 160, 175),
    )


def icon_chart(cv, x, y, s):
    cv.line(x, y + s, x, y + 4, WHITE, 3)
    cv.line(x, y + s, x + s, y + s, WHITE, 3)
    cv.line(x + 4, y + 8, x + int(s * 0.35), y + int(s * 0.4), RED, 4)
    cv.line(x + int(s * 0.35), y + int(s * 0.4), x + int(s * 0.62), y + int(s * 0.55), RED, 4)
    cv.line(x + int(s * 0.62), y + int(s * 0.55), x + s - 6, y + s - 6, RED, 4)
    cv.fill_polygon(
        [(x + s - 6, y + s - 6), (x + s - 18, y + s - 10), (x + s - 10, y + s - 18)],
        RED,
    )


def icon_rocket(cv, x, y, s):
    # body, nose, window, fins, flame
    cv.fill_polygon(
        [(x + s // 2, y), (x + int(s * 0.72), y + int(s * 0.3)), (x + int(s * 0.28), y + int(s * 0.3))],
        WHITE,
    )
    cv.fill_rect(x + int(s * 0.28), y + int(s * 0.3), int(s * 0.44), int(s * 0.45), WHITE)
    cv.fill_circle(x + s // 2, y + int(s * 0.45), s // 10, BLUE)
    cv.fill_polygon(
        [(x + int(s * 0.28), y + int(s * 0.6)), (x + int(s * 0.08), y + int(s * 0.85)), (x + int(s * 0.28), y + int(s * 0.78))],
        RED,
    )
    cv.fill_polygon(
        [(x + int(s * 0.72), y + int(s * 0.6)), (x + int(s * 0.92), y + int(s * 0.85)), (x + int(s * 0.72), y + int(s * 0.78))],
        RED,
    )
    cv.fill_polygon(
        [(x + int(s * 0.38), y + int(s * 0.78)), (x + int(s * 0.62), y + int(s * 0.78)), (x + s // 2, y + s)],
        ORANGE,
    )


def icon_ship(cv, x, y, s):
    cv.fill_polygon(
        [
            (x + int(s * 0.1), y + int(s * 0.45)),
            (x + int(s * 0.9), y + int(s * 0.45)),
            (x + int(s * 0.78), y + int(s * 0.72)),
            (x + int(s * 0.22), y + int(s * 0.72)),
        ],
        (200, 205, 215),
    )
    cv.fill_rect(x + int(s * 0.42), y + int(s * 0.18), int(s * 0.16), int(s * 0.27), (200, 205, 215))
    cv.line(x + int(s * 0.5), y + int(s * 0.18), x + int(s * 0.5), y, WHITE, 2)
    cv.line(x, y + int(s * 0.82), x + s, y + int(s * 0.82), BLUE, 3)
    cv.line(x + int(s * 0.1), y + int(s * 0.92), x + int(s * 0.9), y + int(s * 0.92), BLUE, 3)


# --- page ------------------------------------------------------------------
def draw_skyline(cv):
    base = 468
    heights = [52, 70, 44, 62, 80, 48, 66, 38, 74, 56, 68, 42, 60, 50]
    bw = 66
    x = 40
    for i, hgt in enumerate(heights):
        cv.fill_rect(x, base - hgt, bw - 6, hgt, PANEL_LT)
        for wy in range(base - hgt + 8, base - 6, 14):
            for wx in range(x + 8, x + bw - 14, 14):
                if (wx // 14 + wy // 14 + i) % 3 == 0:
                    cv.fill_rect(wx, wy, 5, 6, GOLD)
        x += bw
    # candle of remembrance at the right end
    cx = 952
    cv.fill_rect(cx, base - 46, 14, 46, WHITE)
    cv.fill_polygon(
        [(cx + 7, base - 66), (cx + 15, base - 50), (cx + 11, base - 44), (cx + 3, base - 44), (cx - 1, base - 50)],
        ORANGE,
    )
    cv.fill_polygon(
        [(cx + 7, base - 58), (cx + 12, base - 48), (cx + 2, base - 48)],
        FLAME_Y,
    )


def draw_tile(cv, x, y, w, h, bar, head1, head2, sub1, sub2, icon):
    cv.fill_rect(x, y, w, h, PANEL)
    cv.fill_rect(x, y, 8, h, bar)
    tx = x + 24
    if head2:
        cv.text(tx, y + 14, head1, 4, WHITE)
        cv.text(tx, y + 42, head2, 4, WHITE)
    else:
        cv.text(tx, y + 28, head1, 4, WHITE)
    icon(cv, x + 24, y + 84, 64)
    sx = x + 104
    cv.text(sx, y + 92, sub1, 3, MIST)
    cv.text(sx, y + 118, sub2, 3, MIST)


def build():
    cv = Canvas(W, H, NAVY)

    # masthead
    cv.text(W // 2, 28, "THE WORLD", 11, WHITE, align="center")
    cv.fill_rect(60, 118, W - 120, 4, GOLD)
    cv.text(W // 2, 130, "THURSDAY, 26 NOVEMBER 2026", 4, GOLD, align="center")
    cv.fill_rect(60, 168, W - 120, 3, GOLD)

    # lead story: Mumbai remembers 26/11, 18 years on
    cv.text(W // 2, 188, "INDIA", 3, GOLD, align="center")
    cv.text(W // 2, 216, "MUMBAI REMEMBERS", 6, WHITE, align="center")
    cv.text(W // 2, 264, "26/11 - 18 YEARS ON", 6, WHITE, align="center")
    cv.text(W // 2, 322, "INDIA MARKS CONSTITUTION DAY TOO", 3, MIST, align="center")
    cv.text(W // 2, 350, "77 YEARS SINCE 1949", 3, MIST, align="center")
    draw_skyline(cv)
    cv.fill_rect(60, 484, W - 120, 3, GOLD)

    # six stories, two columns by three rows
    tiles = [
        (ORANGE, "HOUTHIS HIT", "SAUDI REFINERY", "RAS TANURA HIT", "RIYADH TOWER TOO", icon_flame),
        (YELLOW, "UKRAINE HITS", "RUSSIAN REFINERIES", "LEAKED TOLL NEARS", "500,000 DEAD", icon_burst),
        (RED, "GAZA STRIKE", "KILLS HAMAS CHIEF", "CEASEFIRE UNDER", "STRAIN", icon_wall),
        (TEAL, "MARKETS TUMBLE", "", "NIKKEI -2.8%", "NASDAQ -2.4%", icon_chart),
        (BLUE, "FIRST PAKISTANI", "IN SPACE", "JOINS CHINA'S", "TIANGONG STATION", icon_rocket),
        (PURPLE, "TANKERS HIT", "BY MINES", "IN STRAIT OF", "HORMUZ", icon_ship),
    ]
    for i, t in enumerate(tiles):
        tx = 12 + (i % 2) * 504
        ty = 500 + (i // 2) * 166
        draw_tile(cv, tx, ty, 496, 156, *t)

    cv.text(W // 2, 1006, "THE WORLD - 26 NOVEMBER 2026", 2, MIST, align="center")
    return cv


# --- PNG writer ------------------------------------------------------------
def png_chunk(kind, data):
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def to_png(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3 : (y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + png_chunk(b"IEND", b"")
    )


def main():
    cv = build()
    data = to_png(cv)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
