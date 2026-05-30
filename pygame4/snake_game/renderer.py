"""
renderer.py - Toàn bộ logic vẽ: background, grid, snake, food, HUD, menu
Phong cách Cyberpunk Neon với glow và hiệu ứng cinematic.
"""

import pygame
import math
import random
import os
import sys
from typing import Optional

# Đảm bảo import được module trong cùng thư mục khi chạy từ bất kỳ CWD nào
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from constants import *


# ── Tiện ích vẽ glow ──────────────────────────────────────────────────────────

def _lerp_color(c1: tuple, c2: tuple, t: float) -> tuple:
    """Nội suy tuyến tính giữa hai màu."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_glow_circle(surf: pygame.Surface, color: tuple,
                     cx: int, cy: int, radius: int, layers: int = GLOW_LAYERS):
    """Vẽ hình tròn có nhiều lớp glow mờ dần ra ngoài."""
    for i in range(layers, 0, -1):
        r   = radius + i * 6
        a   = max(0, int(60 - i * 12))
        s   = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, a), (r, r), r)
        surf.blit(s, (cx - r, cy - r), special_flags=pygame.BLEND_ADD)


def draw_glow_rect(surf: pygame.Surface, color: tuple,
                   rect: pygame.Rect, radius: int = 6, layers: int = 3):
    """Vẽ hình chữ nhật bo góc có glow."""
    for i in range(layers, 0, -1):
        exp = i * 5
        s   = pygame.Surface((rect.w + exp * 2, rect.h + exp * 2), pygame.SRCALPHA)
        a   = max(0, int(55 - i * 15))
        pygame.draw.rect(
            s, (*color, a),
            pygame.Rect(0, 0, rect.w + exp * 2, rect.h + exp * 2),
            border_radius=radius + exp
        )
        surf.blit(s, (rect.x - exp, rect.y - exp), special_flags=pygame.BLEND_ADD)
    pygame.draw.rect(surf, color, rect, border_radius=radius)


def draw_outlined_rect(surf: pygame.Surface, fill: tuple, border: tuple,
                       rect: pygame.Rect, border_w: int = 2, radius: int = 6):
    pygame.draw.rect(surf, fill,   rect, border_radius=radius)
    pygame.draw.rect(surf, border, rect, border_w, border_radius=radius)


# ── Lớp Renderer chính ────────────────────────────────────────────────────────

class Renderer:
    """
    Xử lý toàn bộ việc vẽ game.
    Nhận trạng thái từ GameEngine và render lên surface.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen  = screen
        self.W       = WINDOW_WIDTH
        self.H       = WINDOW_HEIGHT

        # Surfaces tái dụng
        self._bg_surf  = pygame.Surface((self.W, self.H))
        self._hud_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self._overlay  = pygame.Surface((self.W, self.H), pygame.SRCALPHA)

        # Fonts
        pygame.font.init()
        self._load_fonts()

        # Grid animation phase
        self._grid_phase = 0.0
        self._food_phase = 0.0

        # Pre-build background grid (static part)
        self._grid_cache: Optional[pygame.Surface] = None

    # ── Font loader ─────────────────────────────────────────────────────────
    def _load_fonts(self):
        """Tải font hệ thống, fallback về mặc định nếu cần."""
        candidates = ["Consolas", "Courier New", "monospace", None]
        self._font_huge  = self._try_font(candidates, 92)
        self._font_large = self._try_font(candidates, 52)
        self._font_mid   = self._try_font(candidates, 34)
        self._font_small = self._try_font(candidates, 22)
        self._font_tiny  = self._try_font(candidates, 16)

    def _try_font(self, names: list, size: int) -> pygame.font.Font:
        for name in names:
            try:
                if name:
                    f = pygame.font.SysFont(name, size, bold=True)
                else:
                    f = pygame.font.Font(None, size)
                return f
            except Exception:
                continue
        return pygame.font.Font(None, size)

    # ── Text helper ─────────────────────────────────────────────────────────
    def _text(self, surf: pygame.Surface, text: str, font: pygame.font.Font,
              color: tuple, cx: int, cy: int,
              glow_color: Optional[tuple] = None, anchor: str = "center"):
        """Vẽ text với optional glow shadow."""
        if glow_color:
            for dx, dy in [(-2,-2),(2,-2),(-2,2),(2,2),(0,-3),(0,3),(-3,0),(3,0)]:
                s = font.render(text, True, glow_color)
                r = s.get_rect()
                setattr(r, anchor, (cx + dx, cy + dy))
                surf.blit(s, r)
        s = font.render(text, True, color)
        r = s.get_rect()
        setattr(r, anchor, (cx, cy))
        surf.blit(s, r)

    # ── Background & Grid ────────────────────────────────────────────────────
    def draw_background(self):
        """Vẽ nền tối có gradient và grid động."""
        self._grid_phase += GRID_ANIM_SPEED

        # Gradient tím đậm → đen
        for y in range(self.H):
            t   = y / self.H
            col = _lerp_color(DARK_PURPLE, DEEP_BLACK, t)
            pygame.draw.line(self._bg_surf, col, (0, y), (self.W, y))
        self.screen.blit(self._bg_surf, (0, 0))

        # Vẽ grid nhỏ ngoài vùng chơi (ambient)
        self._draw_ambient_grid()
        # Vẽ grid chính bên trong vùng chơi
        self._draw_play_grid()

    def _draw_ambient_grid(self):
        """Grid mờ toàn màn hình (background decoration)."""
        step  = 40
        pulse = int(20 + 10 * math.sin(self._grid_phase * 0.7))
        col   = (*DIM_PURPLE, pulse)
        h_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for x in range(0, self.W, step):
            pygame.draw.line(h_surf, col, (x, 0), (x, self.H))
        for y in range(0, self.H, step):
            pygame.draw.line(h_surf, col, (0, y), (self.W, y))
        self.screen.blit(h_surf, (0, 0))

    def _draw_play_grid(self):
        """Grid bên trong vùng chơi sáng hơn, có pulse."""
        pulse_a = int(35 + 20 * math.sin(self._grid_phase))
        col     = (*DIM_CYAN, pulse_a)
        g_surf  = pygame.Surface((PLAY_WIDTH + 2, PLAY_HEIGHT + 2), pygame.SRCALPHA)

        for col_i in range(GRID_COLS + 1):
            x = col_i * CELL_SIZE
            pygame.draw.line(g_surf, col, (x, 0), (x, PLAY_HEIGHT))
        for row_i in range(GRID_ROWS + 1):
            y = row_i * CELL_SIZE
            pygame.draw.line(g_surf, col, (0, y), (PLAY_WIDTH, y))

        self.screen.blit(g_surf, (PLAY_LEFT - 1, PLAY_TOP - 1))

        # Viền vùng chơi
        border_rect = pygame.Rect(PLAY_LEFT - 2, PLAY_TOP - 2,
                                  PLAY_WIDTH + 4, PLAY_HEIGHT + 4)
        pulse_b = int(180 + 75 * math.sin(self._grid_phase * 1.3))
        pygame.draw.rect(self.screen, (*NEON_PURPLE, pulse_b),
                         border_rect, 2)
        # Glow nhẹ cho viền
        draw_glow_rect(self.screen, NEON_PURPLE, border_rect, radius=0, layers=2)

    # ── Vẽ rắn ──────────────────────────────────────────────────────────────
    def draw_snake(self, snake_body: list[tuple], direction: tuple,
                   move_progress: float, offset: tuple = (0, 0)):
        """
        Vẽ toàn bộ thân rắn với gradient màu và animation mượt.
        snake_body: danh sách (grid_col, grid_row)
        move_progress: 0.0 → 1.0 (interpolation giữa 2 ô)
        offset: camera shake offset
        """
        n = len(snake_body)
        if n == 0:
            return

        ox, oy = offset

        for i, (gc, gr) in enumerate(snake_body):
            # Nội suy vị trí mượt cho đầu rắn
            if i == 0 and n > 1:
                px = PLAY_LEFT + gc * CELL_SIZE + ox
                py = PLAY_TOP  + gr * CELL_SIZE + oy
                # Smooth move: interpolate từ đoạn trước
                prev_gc, prev_gr = snake_body[1]
                dx = (gc - prev_gc) * CELL_SIZE * (1 - move_progress) * (-1) if False else 0
                dy = 0
                # Thực ra ta interpolate head từ prev position
                px = int(PLAY_LEFT + (prev_gc + (gc - prev_gc) * move_progress) * CELL_SIZE) + ox
                py = int(PLAY_TOP  + (prev_gr + (gr - prev_gr) * move_progress) * CELL_SIZE) + oy
            else:
                px = PLAY_LEFT + gc * CELL_SIZE + ox
                py = PLAY_TOP  + gr * CELL_SIZE + oy

            # Gradient màu đầu → đuôi
            t      = i / max(n - 1, 1)
            color  = _lerp_color(SNAKE_HEAD, SNAKE_TAIL, t)
            margin = 3 if i > 0 else 2
            rect   = pygame.Rect(px + margin, py + margin,
                                 CELL_SIZE - margin * 2, CELL_SIZE - margin * 2)

            # Glow cho đầu và vài đốt đầu
            if i == 0:
                draw_glow_rect(self.screen, SNAKE_HEAD, rect, radius=6, layers=3)
            elif i < 5:
                gl = _lerp_color(SNAKE_HEAD, SNAKE_BODY, i / 5)
                draw_glow_rect(self.screen, gl, rect, radius=5, layers=1)

            # Thân đốt bo góc
            pygame.draw.rect(self.screen, color, rect, border_radius=6)
            # Highlight sáng phía trên
            hl_rect = pygame.Rect(rect.x + 3, rect.y + 2, rect.w - 6, 4)
            hl_col  = _lerp_color(color, (255, 255, 255), 0.4)
            pygame.draw.rect(self.screen, hl_col, hl_rect, border_radius=2)

        # Vẽ mắt đầu rắn
        if n >= 1:
            hgc, hgr = snake_body[0]
            if n > 1:
                hpx = int(PLAY_LEFT + (snake_body[1][0] + (hgc - snake_body[1][0]) * move_progress) * CELL_SIZE) + ox
                hpy = int(PLAY_TOP  + (snake_body[1][1] + (hgr - snake_body[1][1]) * move_progress) * CELL_SIZE) + oy
            else:
                hpx = PLAY_LEFT + hgc * CELL_SIZE + ox
                hpy = PLAY_TOP  + hgr * CELL_SIZE + oy
            self._draw_snake_eyes(hpx, hpy, direction)

    def _draw_snake_eyes(self, hpx: int, hpy: int, direction: tuple):
        """Vẽ mắt rắn với con ngươi nhìn theo hướng di chuyển."""
        dx, dy = direction
        # Tâm đầu rắn
        cx = hpx + CELL_SIZE // 2
        cy = hpy + CELL_SIZE // 2

        # Hai mắt vuông góc với hướng đi
        if dx != 0:   # đi ngang
            eye_positions = [(cx + dx * 4, cy - 6), (cx + dx * 4, cy + 6)]
        else:          # đi dọc
            eye_positions = [(cx - 6, cy + dy * 4), (cx + 6, cy + dy * 4)]

        for ex, ey in eye_positions:
            # Tròng trắng
            pygame.draw.circle(self.screen, (220, 255, 255), (ex, ey), 4)
            # Con ngươi tím
            pupil_x = ex + dx * 1
            pupil_y = ey + dy * 1
            pygame.draw.circle(self.screen, NEON_PURPLE, (pupil_x, pupil_y), 2)
            # Phản chiếu nhỏ
            pygame.draw.circle(self.screen, (255, 255, 255),
                                (pupil_x - 1, pupil_y - 1), 1)

    # ── Vẽ mồi ──────────────────────────────────────────────────────────────
    def draw_food(self, gc: int, gr: int, offset: tuple = (0, 0)):
        """Vẽ mồi dạng viên neon pulse."""
        self._food_phase += FOOD_PULSE_SPEED
        ox, oy = offset
        cx = PLAY_LEFT + gc * CELL_SIZE + CELL_SIZE // 2 + ox
        cy = PLAY_TOP  + gr * CELL_SIZE + CELL_SIZE // 2 + oy

        pulse = 0.7 + 0.3 * math.sin(self._food_phase)
        r     = int((CELL_SIZE // 2 - 5) * pulse)

        # Glow nhiều lớp
        draw_glow_circle(self.screen, FOOD_GLOW, cx, cy, r + 4, layers=5)

        # Vòng ngoài xoay
        angle = self._food_phase * 2
        for i in range(6):
            a   = angle + i * math.tau / 6
            sx  = int(cx + math.cos(a) * (r + 3))
            sy  = int(cy + math.sin(a) * (r + 3))
            pygame.draw.circle(self.screen, NEON_ORANGE, (sx, sy), 2)

        # Nhân sáng
        pygame.draw.circle(self.screen, FOOD_GLOW,  (cx, cy), r)
        pygame.draw.circle(self.screen, FOOD_CORE,  (cx, cy), max(1, r - 4))
        # Điểm trắng trung tâm
        pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), max(1, r - 8))

    # ── HUD ─────────────────────────────────────────────────────────────────
    def draw_hud(self, score: int, high_score: int,
                 speed_level: int, sound_on: bool):
        """Vẽ thanh HUD phía trên và dưới vùng chơi."""
        self._hud_surf.fill((0, 0, 0, 0))

        # --- Thanh điểm trên -----------------------------------------------
        bar_rect = pygame.Rect(PLAY_LEFT, 10, PLAY_WIDTH, 44)
        hud_bg   = pygame.Surface((bar_rect.w, bar_rect.h), pygame.SRCALPHA)
        hud_bg.fill((10, 5, 30, 180))
        self._hud_surf.blit(hud_bg, bar_rect)
        pygame.draw.rect(self._hud_surf, NEON_PURPLE, bar_rect, 1)

        # Score
        self._text(self._hud_surf, f"SCORE  {score:06d}",
                   self._font_mid, NEON_CYAN,
                   PLAY_LEFT + 10, 32, NEON_BLUE, anchor="midleft")

        # High score
        self._text(self._hud_surf, f"BEST  {high_score:06d}",
                   self._font_mid, NEON_PINK,
                   PLAY_LEFT + PLAY_WIDTH // 2, 32,
                   (120, 0, 80), anchor="center")

        # Speed indicator
        speed_txt = f"SPD  {speed_level}"
        self._text(self._hud_surf, speed_txt,
                   self._font_mid, NEON_GREEN,
                   PLAY_LEFT + PLAY_WIDTH - 10, 32,
                   (0, 60, 30), anchor="midright")

        # --- Thanh dưới (sound toggle) ----------------------------------------
        bot_y    = PLAY_TOP + PLAY_HEIGHT + 8
        sound_lbl = "♪ ON" if sound_on else "♪ OFF"
        sound_col = NEON_GREEN if sound_on else NEON_RED
        self._text(self._hud_surf, f"[M] {sound_lbl}  [P] PAUSE  [ESC] MENU",
                   self._font_tiny, sound_col,
                   PLAY_LEFT + PLAY_WIDTH // 2, bot_y + 10,
                   anchor="center")

        self.screen.blit(self._hud_surf, (0, 0))

    # ── Menu ─────────────────────────────────────────────────────────────────
    def draw_menu(self, tick: int, high_score: int):
        """Màn hình menu đẹp với scanlines và logo neon."""
        # Scanlines overlay
        sc_surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        for y in range(0, self.H, 3):
            pygame.draw.line(sc_surf, (0, 0, 0, 30), (0, y), (self.W, y))
        self.screen.blit(sc_surf, (0, 0))

        phase = tick * 0.018

        # ── Logo ────────────────────────────────────────────────────────────
        logo_y = int(self.H * 0.22 + math.sin(phase) * 8)
        # Shadow
        self._text(self.screen, "NEON", self._font_huge,
                   (*NEON_PURPLE, 255), self.W // 2 - 2, logo_y + 4,
                   glow_color=DIM_PURPLE)
        self._text(self.screen, "NEON", self._font_huge,
                   NEON_CYAN, self.W // 2, logo_y, glow_color=NEON_BLUE)

        self._text(self.screen, "SERPENT", self._font_large,
                   NEON_PINK,
                   self.W // 2, logo_y + 80, glow_color=(80, 0, 50))

        # Subtitle
        self._text(self.screen, "//  CYBERPUNK  EDITION  //",
                   self._font_tiny, (*NEON_PURPLE, 200),
                   self.W // 2, logo_y + 130)

        # ── Divider ─────────────────────────────────────────────────────────
        div_y = logo_y + 155
        div_a = int(150 + 105 * math.sin(phase * 1.5))
        pygame.draw.line(self.screen, (*NEON_CYAN, div_a),
                         (self.W // 2 - 220, div_y), (self.W // 2 + 220, div_y), 1)

        # ── Menu items ──────────────────────────────────────────────────────
        items = [
            ("[ENTER]  START GAME",   NEON_CYAN),
            ("[H]      HIGH SCORES",  NEON_PURPLE),
            ("[M]      TOGGLE SOUND", NEON_GREEN),
            ("[ESC]    QUIT",         NEON_RED),
        ]
        start_y = div_y + 55
        for idx, (label, col) in enumerate(items):
            iy     = start_y + idx * 50
            blink  = (math.sin(phase * 3 + idx) > 0.2) if idx == 0 else True
            if blink:
                self._text(self.screen, label, self._font_small,
                           col, self.W // 2, iy, glow_color=_lerp_color(col, BLACK, 0.6))

        # ── High score ───────────────────────────────────────────────────────
        hs_y = start_y + len(items) * 50 + 30
        self._text(self.screen, f"BEST SCORE  :  {high_score:06d}",
                   self._font_small, NEON_YELLOW,
                   self.W // 2, hs_y, glow_color=(80, 60, 0))

        # ── Decorative corners ───────────────────────────────────────────────
        self._draw_corner_decorations(phase)

    def _draw_corner_decorations(self, phase: float):
        """Góc trang trí cyberpunk."""
        a   = int(100 + 80 * math.sin(phase))
        col = (*NEON_CYAN, a)
        L   = 40
        for (x0, y0, xs, ys) in [
            (20, 20,  1,  1), (self.W - 20, 20, -1,  1),
            (20, self.H - 20, 1, -1), (self.W - 20, self.H - 20, -1, -1)
        ]:
            s = pygame.Surface((L + 4, L + 4), pygame.SRCALPHA)
            pygame.draw.line(s, col, (2, 2), (2 + L * (xs > 0), 2), 2)
            pygame.draw.line(s, col, (2, 2), (2, 2 + L * (ys > 0)), 2)
            bx = x0 - (L + 2) if xs < 0 else x0 - 2
            by = y0 - (L + 2) if ys < 0 else y0 - 2
            self.screen.blit(s, (bx, by))

    # ── Pause overlay ────────────────────────────────────────────────────────
    def draw_pause(self):
        ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((5, 0, 20, 160))
        self.screen.blit(ov, (0, 0))
        self._text(self.screen, "PAUSED", self._font_large,
                   NEON_CYAN, self.W // 2, self.H // 2 - 30,
                   glow_color=NEON_BLUE)
        self._text(self.screen, "[P] RESUME   [ESC] MENU",
                   self._font_small, NEON_PURPLE,
                   self.W // 2, self.H // 2 + 40)

    # ── Leaderboard ──────────────────────────────────────────────────────────
    def draw_leaderboard(self, tick: int, top_scores: list[int]):
        """Vẽ bảng xếp hạng top N."""
        self.screen.fill((0, 0, 0))  # fallback

        # Nền
        self.draw_background()

        # Overlay panel
        panel_w, panel_h = int(self.W * 0.72), int(self.H * 0.68)
        panel_x, panel_y = (self.W - panel_w) // 2, (self.H - panel_h) // 2

        ov = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        ov.fill((10, 5, 30, 210))
        self.screen.blit(ov, (panel_x, panel_y))

        border_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, NEON_PURPLE, border_rect, 2, border_radius=18)
        draw_glow_rect(self.screen, NEON_PURPLE, border_rect, radius=0, layers=3)

        # Title
        phase = tick * 0.04
        pulse = int(120 + 80 * math.sin(phase))
        self._text(
            self.screen,
            "HIGH  SCORES",
            self._font_large,
            NEON_CYAN,
            self.W // 2,
            panel_y + 70,
            glow_color=(*NEON_PURPLE, min(255, pulse)),
        )

        # Header row
        self._text(
            self.screen,
            "RANK   SCORE",
            self._font_small,
            NEON_PINK,
            self.W // 2,
            panel_y + 120,
            glow_color=(80, 0, 50),
        )

        # List
        y0 = panel_y + 165
        if not top_scores:
            self._text(
                self.screen,
                "NO SCORES YET",
                self._font_mid,
                NEON_YELLOW,
                self.W // 2,
                y0 + 50,
                glow_color=(80, 60, 0),
            )
        else:
            for i, s in enumerate(top_scores[:LEADERBOARD_SIZE], start=1):
                col = NEON_CYAN if i == 1 else NEON_PURPLE if i <= 3 else NEON_PINK
                blink = (i == 1 and math.sin(phase * 5) > 0)
                if blink:
                    col = _lerp_color(col, (255, 255, 255), 0.35)

                row = f"{i:>2}    {s:06d}"
                self._text(
                    self.screen,
                    row,
                    self._font_small,
                    col,
                    self.W // 2,
                    y0 + (i - 1) * 40,
                    glow_color=_lerp_color(col, BLACK, 0.6),
                )

        # Footer hint
        self._text(
            self.screen,
            "[ESC]  BACK  |  [ENTER]  BACK",
            self._font_tiny,
            NEON_GREEN,
            self.W // 2,
            panel_y + panel_h - 40,
            anchor="center",
        )

    # ── Game Over overlay ────────────────────────────────────────────────────
    def draw_game_over(self, score: int, high_score: int,
                       is_new_record: bool, tick: int):
        phase = tick * 0.04
        ov    = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((20, 0, 5, 200))
        self.screen.blit(ov, (0, 0))

        # Title
        title_col = NEON_RED if not is_new_record else NEON_YELLOW
        self._text(self.screen, "GAME  OVER", self._font_large,
                   title_col, self.W // 2, self.H // 2 - 100,
                   glow_color=_lerp_color(title_col, BLACK, 0.5))

        if is_new_record:
            blink = math.sin(phase * 5) > 0
            if blink:
                self._text(self.screen, "✦  NEW HIGH SCORE  ✦",
                           self._font_mid, NEON_YELLOW,
                           self.W // 2, self.H // 2 - 40)

        self._text(self.screen, f"SCORE  :  {score:06d}",
                   self._font_mid, NEON_CYAN,
                   self.W // 2, self.H // 2 + 20)
        self._text(self.screen, f"BEST   :  {high_score:06d}",
                   self._font_mid, NEON_PINK,
                   self.W // 2, self.H // 2 + 60)

        self._text(self.screen, "[ENTER] PLAY AGAIN   [ESC] MENU",
                   self._font_small, NEON_PURPLE,
                   self.W // 2, self.H // 2 + 120)

    # ── Transition ───────────────────────────────────────────────────────────
    def draw_transition(self, progress: float):
        """
        Hiệu ứng chuyển cảnh: màn che đen mở ra hoặc đóng lại.
        progress: 0.0 = đóng hoàn toàn, 1.0 = mở hoàn toàn
        """
        a = int((1.0 - progress) * 255)
        if a <= 0:
            return
        ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((0, 0, 10, a))
        # Thêm neon scanline khi đang chuyển
        if a > 100:
            line_a = min(255, a)
            for y in range(0, self.H, 8):
                t  = y / self.H
                hue = (*_lerp_color(NEON_CYAN, NEON_PURPLE, t), line_a // 6)
                pygame.draw.line(ov, hue, (0, y), (self.W, y))
        self.screen.blit(ov, (0, 0))
