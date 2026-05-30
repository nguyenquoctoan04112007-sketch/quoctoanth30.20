"""
camera.py - Camera shake effect khi va chạm
"""

import random
import math
from constants import *


class CameraShake:
    """Hiệu ứng rung camera khi rắn chết hoặc sự kiện đặc biệt."""

    def __init__(self):
        self._intensity = 0.0
        self._duration  = 0
        self._offset    = (0, 0)

    def shake(self, intensity: float = SHAKE_INTENSITY,
              duration: int = SHAKE_DURATION):
        """Kích hoạt shake với cường độ và thời gian cho trước."""
        self._intensity = intensity
        self._duration  = duration

    def update(self):
        """Cập nhật mỗi frame, giảm dần cường độ."""
        if self._duration <= 0:
            self._offset   = (0, 0)
            self._intensity = 0.0
            return

        self._duration  -= 1
        # Offset ngẫu nhiên, nhân với hàm giảm
        decay = self._intensity * (self._duration / SHAKE_DURATION)
        ox = int(random.uniform(-decay, decay))
        oy = int(random.uniform(-decay, decay))
        self._offset = (ox, oy)

        self._intensity *= SHAKE_DECAY

    @property
    def offset(self) -> tuple:
        return self._offset

    @property
    def active(self) -> bool:
        return self._duration > 0
