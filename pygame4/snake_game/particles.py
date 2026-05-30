"""
particles.py - Hệ thống particle hiệu ứng neon cho Cyberpunk Snake
"""

import pygame
import random
import math
from constants import *


class Particle:
    """Một hạt neon bay ra khi ăn mồi."""

    def __init__(self, x: float, y: float, color: tuple):
        angle  = random.uniform(0, math.tau)          # hướng ngẫu nhiên
        speed  = random.uniform(PARTICLE_SPEED_MIN, PARTICLE_SPEED_MAX)
        self.x  = x
        self.y  = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life     = PARTICLE_LIFETIME
        self.max_life = PARTICLE_LIFETIME
        self.size     = random.uniform(2, 5)
        self.color    = color
        # Một số hạt có màu trắng sáng để tăng cinematic feel
        if random.random() < 0.25:
            self.color = (255, 255, 255)

    # ── Cập nhật vật lý ──────────────────────────────────────────────────────
    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vx   *= 0.94          # ma sát không khí
        self.vy   *= 0.94
        self.vy   += 0.08          # trọng lực nhẹ
        self.life -= 1
        self.size *= 0.97          # co dần

    @property
    def alive(self) -> bool:
        return self.life > 0

    @property
    def alpha(self) -> int:
        """Độ mờ fade-out mượt."""
        return int(255 * (self.life / self.max_life) ** 1.5)

    # ── Vẽ hạt kèm glow nhỏ ─────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return
        a    = self.alpha
        r, g, b = self.color
        sz   = max(1, int(self.size))
        px, py = int(self.x), int(self.y)

        # Lớp glow mờ bên ngoài
        glow_sz = sz + 4
        glow_surf = pygame.Surface((glow_sz * 2, glow_sz * 2), pygame.SRCALPHA)
        ga = max(0, a // 4)
        pygame.draw.circle(
            glow_surf, (r, g, b, ga),
            (glow_sz, glow_sz), glow_sz
        )
        surface.blit(glow_surf, (px - glow_sz, py - glow_sz), special_flags=pygame.BLEND_ADD)

        # Nhân sáng trung tâm
        core_surf = pygame.Surface((sz * 2 + 2, sz * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(
            core_surf, (r, g, b, a),
            (sz + 1, sz + 1), sz
        )
        surface.blit(core_surf, (px - sz - 1, py - sz - 1), special_flags=pygame.BLEND_ADD)


class ParticleSystem:
    """Quản lý toàn bộ danh sách particle trong game."""

    def __init__(self):
        self._particles: list[Particle] = []

    # ── Thêm particle burst khi ăn mồi ───────────────────────────────────────
    def emit_food(self, cx: float, cy: float):
        """Phát PARTICLE_COUNT hạt xung quanh vị trí (cx, cy)."""
        colors = [NEON_YELLOW, NEON_CYAN, NEON_PINK, NEON_ORANGE, FOOD_CORE]
        for _ in range(PARTICLE_COUNT):
            color = random.choice(colors)
            self._particles.append(Particle(cx, cy, color))

    # ── Hiệu ứng va chạm: hạt đỏ ─────────────────────────────────────────────
    def emit_death(self, cx: float, cy: float):
        colors = [NEON_RED, NEON_ORANGE, (255, 80, 0)]
        for _ in range(PARTICLE_COUNT * 2):
            color = random.choice(colors)
            p = Particle(cx, cy, color)
            p.vx *= 1.8
            p.vy *= 1.8
            self._particles.append(p)

    # ── Cập nhật & dọn hạt hết sống ──────────────────────────────────────────
    def update(self):
        self._particles = [p for p in self._particles if p.alive]
        for p in self._particles:
            p.update()

    # ── Vẽ toàn bộ ────────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface):
        for p in self._particles:
            p.draw(surface)

    def clear(self):
        self._particles.clear()
