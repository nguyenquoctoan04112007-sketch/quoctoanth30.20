"""
sound_manager.py - Tổng hợp âm thanh bằng pygame (không cần file .mp3)
Tất cả âm thanh được sinh ra bằng sóng sin / noise.
"""

import pygame
import numpy as np
import math
from typing import Optional


class SoundManager:
    """Tổng hợp và phát âm thanh chuyên nghiệp dùng waveform."""

    SAMPLE_RATE = 44100
    BIT_DEPTH   = -16        # signed 16-bit

    def __init__(self):
        self._enabled = True
        try:
            pygame.mixer.init(
                frequency = self.SAMPLE_RATE,
                size      = self.BIT_DEPTH,
                channels  = 2,
                buffer    = 512
            )
            self._sounds: dict[str, pygame.mixer.Sound] = {}
            self._build_all()
        except Exception as e:
            print(f"[SoundManager] Không khởi tạo được mixer: {e}")
            self._enabled = False

    # ── Xây dựng tất cả sound ─────────────────────────────────────────────────
    def _build_all(self):
        self._sounds["eat"]        = self._synth_eat()
        self._sounds["move"]       = self._synth_move()
        self._sounds["death"]      = self._synth_death()
        self._sounds["menu_blip"]  = self._synth_blip(880, 0.07)
        self._sounds["menu_select"]= self._synth_select()
        self._sounds["level_up"]   = self._synth_level_up()

    # ── Tiện ích tạo sóng ─────────────────────────────────────────────────────
    def _make_sound(self, data: np.ndarray) -> pygame.mixer.Sound:
        """Chuyển array float [-1,1] → pygame.Sound stereo."""
        data = np.clip(data, -1.0, 1.0)
        pcm  = (data * 32767).astype(np.int16)
        stereo = np.column_stack([pcm, pcm])
        return pygame.sndarray.make_sound(stereo)

    def _sine(self, freq: float, duration: float, amp: float = 0.6) -> np.ndarray:
        n = int(self.SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n, endpoint=False)
        return amp * np.sin(2 * math.pi * freq * t)

    def _envelope(self, arr: np.ndarray,
                  attack=0.01, release=0.1) -> np.ndarray:
        """Attack-release envelope."""
        n = len(arr)
        a = int(attack  * self.SAMPLE_RATE)
        r = int(release * self.SAMPLE_RATE)
        env = np.ones(n)
        if a > 0: env[:a] = np.linspace(0, 1, a)
        if r > 0 and r < n:
            env[-r:] = np.linspace(1, 0, r)
        return arr * env

    # ── Âm thanh ─────────────────────────────────────────────────────────────

    def _synth_eat(self) -> pygame.mixer.Sound:
        """Âm thanh 'blip' tăng tông – cảm giác thu thập."""
        freqs = [440, 550, 660, 880]
        out   = np.zeros(int(self.SAMPLE_RATE * 0.22))
        seg   = len(out) // len(freqs)
        for i, f in enumerate(freqs):
            s = int(i * seg)
            e = s + seg
            t = np.linspace(0, seg / self.SAMPLE_RATE, seg)
            out[s:e] += 0.45 * np.sin(2 * math.pi * f * t)
        return self._make_sound(self._envelope(out, 0.005, 0.12))

    def _synth_move(self) -> pygame.mixer.Sound:
        """Tick nhỏ mỗi bước di chuyển."""
        n  = int(self.SAMPLE_RATE * 0.025)
        t  = np.linspace(0, 0.025, n)
        s  = 0.1 * np.sin(2 * math.pi * 200 * t)
        return self._make_sound(self._envelope(s, 0.002, 0.02))

    def _synth_death(self) -> pygame.mixer.Sound:
        """Tiếng vỡ neon – glitchy descending."""
        dur = 0.7
        n   = int(self.SAMPLE_RATE * dur)
        t   = np.linspace(0, dur, n)
        # Glide xuống từ 600 → 80 Hz
        freq = 600 * np.exp(-3 * t)
        s    = 0.5 * np.sin(2 * math.pi * np.cumsum(freq) / self.SAMPLE_RATE)
        # Thêm noise crackle
        noise = 0.15 * (np.random.rand(n) * 2 - 1)
        noise *= np.exp(-5 * t)
        return self._make_sound(self._envelope(s + noise, 0.005, 0.3))

    def _synth_blip(self, freq: float, dur: float) -> pygame.mixer.Sound:
        s = self._sine(freq, dur, 0.25)
        return self._make_sound(self._envelope(s, 0.003, 0.04))

    def _synth_select(self) -> pygame.mixer.Sound:
        """Tiếng chọn menu: hai âm nhanh."""
        s1 = self._sine(660, 0.06, 0.4)
        s2 = self._sine(990, 0.06, 0.4)
        gap = np.zeros(int(self.SAMPLE_RATE * 0.03))
        out = np.concatenate([s1, gap, s2])
        return self._make_sound(self._envelope(out, 0.005, 0.05))

    def _synth_level_up(self) -> pygame.mixer.Sound:
        """Fanfare nhỏ khi tăng tốc."""
        notes = [523, 659, 784, 1047]
        out   = []
        for f in notes:
            seg = self._sine(f, 0.08, 0.35)
            out.append(self._envelope(seg, 0.005, 0.04))
        return self._make_sound(np.concatenate(out))

    # ── API công khai ─────────────────────────────────────────────────────────
    def play(self, name: str, volume: float = 1.0):
        if not self._enabled:
            return
        sound = self._sounds.get(name)
        if sound:
            sound.set_volume(volume)
            sound.play()

    def toggle(self):
        self._enabled = not self._enabled

    @property
    def enabled(self) -> bool:
        return self._enabled
