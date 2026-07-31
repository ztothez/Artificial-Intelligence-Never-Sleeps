"""Original procedural circuit-grid typography for the ZTTZ demo.

The glyphs in this module are hand-authored logical cell maps.  They are not
traced from, derived from, or converted from an existing typeface.  Pygame
primitives turn the maps into connected circuit traces at runtime.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

import pygame


Pattern = tuple[str, ...]
Color = tuple[int, int, int] | tuple[int, int, int, int]

GRID_ROWS = 7
GRID_COLS = 5
LOGICAL_HEIGHT = 9.0
ADVANCE_UNITS = 6.25


def _p(*rows: str) -> Pattern:
    if len(rows) != GRID_ROWS or any(len(row) != GRID_COLS for row in rows):
        raise ValueError("ZTTZ glyph patterns must be 5x7")
    return tuple(rows)


# Deliberately compact, squared construction.  Runtime connectors, node pads,
# small-cap scaling, and deterministic trace incisions supply the final style.
GLYPHS: dict[str, Pattern] = {
    "A": _p(".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": _p("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": _p(".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": _p("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": _p("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": _p("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": _p(".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": _p("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": _p("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": _p("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": _p("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": _p("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": _p("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": _p("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": _p(".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": _p("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": _p(".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": _p("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": _p(".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": _p("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": _p("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": _p("#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."),
    "W": _p("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": _p("#...#", ".#.#.", ".#.#.", "..#..", ".#.#.", ".#.#.", "#...#"),
    "Y": _p("#...#", ".#.#.", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": _p("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": _p(".###.", "#..##", "#.#.#", "#.#.#", "##..#", "#...#", ".###."),
    "1": _p("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": _p(".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": _p("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": _p("#...#", "#...#", "#...#", "#####", "....#", "....#", "....#"),
    "5": _p("#####", "#....", "#....", "####.", "....#", "....#", "####."),
    "6": _p(".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": _p("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": _p(".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": _p(".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    "#": _p(".#.#.", "#####", ".#.#.", ".#.#.", "#####", ".#.#.", ".#.#."),
    "$": _p("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": _p("##..#", "##.#.", "...#.", "..#..", ".#...", ".#.##", "#..##"),
    "&": _p(".##..", "#..#.", "#.#..", ".##..", "#.#.#", "#..#.", ".##.#"),
    "*": _p(".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "+": _p(".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "-": _p(".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "_": _p(".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "=": _p(".....", "#####", ".....", "#####", ".....", ".....", "....."),
    ".": _p(".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": _p(".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": _p(".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": _p(".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "/": _p("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "\\": _p("#....", ".#...", ".#...", "..#..", "...#.", "...#.", "....#"),
    ">": _p("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."),
    "<": _p("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"),
    "[": _p(".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": _p(".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    "(": _p("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": _p(".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "@": _p(".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".####"),
    "~": _p(".....", ".....", ".##.#", "#.##.", ".....", ".....", "....."),
    "!": _p("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": _p(".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": _p("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': _p(".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "|": _p("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "^": _p("..#..", ".#.#.", "#...#", ".....", ".....", ".....", "....."),
    "`": _p(".#...", "..#..", ".....", ".....", ".....", ".....", "....."),
    "✓": _p(".....", "....#", "...#.", "#.#..", ".#...", ".....", "....."),
}


@dataclass(frozen=True)
class _Style:
    stroke_ratio: float
    node_ratio: float
    incision_ratio: float


REGULAR = _Style(stroke_ratio=0.56, node_ratio=0.68, incision_ratio=0.14)
BOLD = _Style(stroke_ratio=0.70, node_ratio=0.82, incision_ratio=0.16)


class GridFont:
    """Small procedural type renderer with a font-like API."""

    def __init__(self, pixel_height: int, bold: bool = False) -> None:
        self.pixel_height = max(8, int(pixel_height))
        self.bold = bool(bold)
        self.style = BOLD if self.bold else REGULAR
        self.advance = max(5, int(round(self.pixel_height * ADVANCE_UNITS / LOGICAL_HEIGHT)))
        self._glyph_cache: dict[tuple[str, tuple[int, int, int, int]], pygame.Surface] = {}
        self._text_cache: OrderedDict[tuple[str, tuple[int, int, int, int]], pygame.Surface] = OrderedDict()

    @staticmethod
    def _rgba(color: Color) -> tuple[int, int, int, int]:
        if len(color) == 4:
            return tuple(int(v) for v in color)  # type: ignore[return-value]
        return int(color[0]), int(color[1]), int(color[2]), 255

    def get_height(self) -> int:
        return self.pixel_height

    def size(self, text: str) -> tuple[int, int]:
        return max(0, len(text) * self.advance), self.pixel_height

    def render(
        self,
        text: str,
        antialias: bool,
        color: Color,
        background: Color | None = None,
    ) -> pygame.Surface:
        del antialias  # Supersampling is deterministic and always enabled.
        rgba = self._rgba(color)
        key = (text, rgba)
        cached = self._text_cache.get(key)
        if cached is not None:
            self._text_cache.move_to_end(key)
            return cached.copy()

        width, height = self.size(text)
        surface = pygame.Surface((max(1, width), height), pygame.SRCALPHA)
        if background is not None:
            surface.fill(self._rgba(background))
        for index, char in enumerate(text):
            surface.blit(self._glyph(char, rgba), (index * self.advance, 0))

        self._text_cache[key] = surface
        if len(self._text_cache) > 2048:
            self._text_cache.popitem(last=False)
        return surface.copy()

    def _glyph(self, char: str, color: tuple[int, int, int, int]) -> pygame.Surface:
        key = (char, color)
        cached = self._glyph_cache.get(key)
        if cached is not None:
            return cached

        surface = self._render_glyph(char, color)
        self._glyph_cache[key] = surface
        return surface

    def _render_glyph(self, char: str, color: tuple[int, int, int, int]) -> pygame.Surface:
        if char == " ":
            return pygame.Surface((self.advance, self.pixel_height), pygame.SRCALPHA)
        if char == "█":
            surface = pygame.Surface((self.advance, self.pixel_height), pygame.SRCALPHA)
            pad = max(0, self.pixel_height // 32)
            pygame.draw.rect(surface, color, (pad, pad, self.advance - pad * 2, self.pixel_height - pad * 2))
            return surface
        if char == "░":
            return self._render_shade(color)

        is_small_cap = char.isalpha() and char.islower()
        pattern_char = char.upper() if is_small_cap else char
        pattern = GLYPHS.get(pattern_char, GLYPHS["?"])
        full = self._draw_pattern(pattern, pattern_char, color)
        if not is_small_cap:
            return full

        # Lowercase becomes engineered small caps: consistent language rhythm
        # without doubling the glyph-map surface area.
        target_h = max(6, int(round(self.pixel_height * 0.84)))
        target_w = max(4, int(round(self.advance * 0.88)))
        scaled = pygame.transform.smoothscale(full, (target_w, target_h))
        surface = pygame.Surface((self.advance, self.pixel_height), pygame.SRCALPHA)
        x = (self.advance - target_w) // 2
        y = self.pixel_height - target_h - max(0, self.pixel_height // 24)
        surface.blit(scaled, (x, y))
        return surface

    def _render_shade(self, color: tuple[int, int, int, int]) -> pygame.Surface:
        surface = pygame.Surface((self.advance, self.pixel_height), pygame.SRCALPHA)
        step = max(2, self.pixel_height // 7)
        radius = max(1, step // 4)
        muted = color[:3] + (max(24, color[3] // 2),)
        for y in range(step // 2, self.pixel_height, step):
            offset = 0 if (y // step) % 2 == 0 else step // 2
            for x in range(offset, self.advance, step):
                pygame.draw.rect(surface, muted, (x, y, radius, radius))
        return surface

    def _draw_pattern(
        self,
        pattern: Pattern,
        char: str,
        color: tuple[int, int, int, int],
    ) -> pygame.Surface:
        supersample = 3 if self.pixel_height < 18 else 2
        width = self.advance * supersample
        height = self.pixel_height * supersample
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        unit = height / LOGICAL_HEIGHT
        offset_x = unit * 0.82
        offset_y = unit * 1.02
        stroke = max(1, int(round(unit * self.style.stroke_ratio)))
        node = max(stroke, int(round(unit * self.style.node_ratio)))

        active = {
            (row, col)
            for row, line in enumerate(pattern)
            for col, value in enumerate(line)
            if value == "#"
        }
        points = {
            cell: (
                int(round(offset_x + cell[1] * unit)),
                int(round(offset_y + cell[0] * unit)),
            )
            for cell in active
        }
        edges: list[tuple[tuple[int, int], tuple[int, int]]] = []

        # Orthogonal traces.
        for row, col in sorted(active):
            for other in ((row, col + 1), (row + 1, col)):
                if other in active:
                    edges.append(((row, col), other))

        # Join isolated staircase cells to form clean engineered diagonals.
        for row, col in sorted(active):
            for dc in (-1, 1):
                other = (row + 1, col + dc)
                if other not in active:
                    continue
                bridge_a = (row, col + dc)
                bridge_b = (row + 1, col)
                if bridge_a not in active and bridge_b not in active:
                    edges.append(((row, col), other))

        for first, second in edges:
            pygame.draw.line(surface, color, points[first], points[second], stroke)
        for cell in sorted(active):
            x, y = points[cell]
            rect = pygame.Rect(x - node // 2, y - node // 2, node, node)
            pygame.draw.rect(surface, color, rect, border_radius=max(0, node // 5))

        # At title scale, one deterministic break makes each glyph read like a
        # routed signal path rather than a conventional filled display font.
        if self.pixel_height >= 58 and edges:
            first, second = edges[(ord(char[0]) * 17 + len(edges)) % len(edges)]
            x1, y1 = points[first]
            x2, y2 = points[second]
            mx, my = (x1 + x2) // 2, (y1 + y2) // 2
            gap = max(1, int(round(unit * self.style.incision_ratio)))
            if abs(x2 - x1) >= abs(y2 - y1):
                cut = pygame.Rect(mx - gap // 2, my - stroke, gap, stroke * 2 + 1)
            else:
                cut = pygame.Rect(mx - stroke, my - gap // 2, stroke * 2 + 1, gap)
            surface.fill((0, 0, 0, 0), cut)

        return pygame.transform.smoothscale(surface, (self.advance, self.pixel_height))
