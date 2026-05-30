"""
game_engine.py - Logic game Snake: rắn, mồi, va chạm, điểm số
Tách biệt hoàn toàn với rendering và input.
"""

import random
import os
import sys
from typing import Optional

# Đảm bảo import được module trong cùng thư mục khi chạy từ bất kỳ CWD nào
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from constants import *


class Snake:
    """Đối tượng rắn: vị trí, hướng, tăng trưởng."""

    # Hướng dưới dạng (dcol, drow)
    UP    = ( 0, -1)
    DOWN  = ( 0,  1)
    LEFT  = (-1,  0)
    RIGHT = ( 1,  0)

    def __init__(self):
        self.reset()

    def reset(self):
        # Bắt đầu ở trung tâm lưới, 3 đốt
        mid_col = GRID_COLS // 2
        mid_row = GRID_ROWS // 2
        self.body: list[tuple] = [
            (mid_col,     mid_row),
            (mid_col - 1, mid_row),
            (mid_col - 2, mid_row),
        ]
        self.direction  = self.RIGHT
        self._next_dir_queue = []
        self._grow       = 0          # số đốt cần thêm
        self.alive       = True

    # ── Input buffer ─────────────────────────────────────────────────────────
    def set_direction(self, new_dir: tuple):
        """Đặt hướng mới, sử dụng queue để nhận input nhanh, chặn quay 180°."""
        last_dir = self._next_dir_queue[-1] if self._next_dir_queue else self.direction
        opp = (-new_dir[0], -new_dir[1])
        if last_dir != opp and last_dir != new_dir:
            if len(self._next_dir_queue) < 3:
                self._next_dir_queue.append(new_dir)

    # ── Cập nhật một bước ───────────────────────────────────────────────────
    def step(self) -> tuple:
        """
        Di chuyển rắn một ô.
        Trả về vị trí ô đầu mới (head position).
        """
        if self._next_dir_queue:
            self.direction = self._next_dir_queue.pop(0)
            
        hc, hr = self.body[0]
        dc, dr = self.direction
        new_head = (hc + dc, hr + dr)

        self.body.insert(0, new_head)
        if self._grow > 0:
            self._grow -= 1          # giữ đuôi lại khi đang tăng
        else:
            self.body.pop()

        return new_head

    def grow(self, amount: int = 1):
        self._grow += amount

    # ── Kiểm tra va chạm ────────────────────────────────────────────────────
    def check_wall_collision(self) -> bool:
        hc, hr = self.body[0]
        return not (0 <= hc < GRID_COLS and 0 <= hr < GRID_ROWS)

    def check_self_collision(self) -> bool:
        head = self.body[0]
        return head in self.body[1:]

    @property
    def head(self) -> tuple:
        return self.body[0]


class GameEngine:
    """
    Engine lõi: quản lý Snake, mồi, điểm, tốc độ.
    Không liên quan đến pygame/render.
    """

    def __init__(self):
        self.snake          = Snake()
        self.food_pos: Optional[tuple] = None
        self.score          = 0

        # Top scores (leaderboard)
        self.top_scores: list[int] = self._load_high_scores()
        self.high_score: int = max(self.top_scores) if self.top_scores else 0

        self.speed_level    = 1             # cấp độ hiện tại
        self.is_new_record = False

        # Timer điều khiển tốc độ di chuyển
        self._move_timer     = 0.0         # tick tích lũy
        self._move_interval  = 1.0        # giây/bước (tính theo FPS)
        self._move_progress  = 0.0        # 0.0→1.0 giữa hai bước

        self._alive          = True
        self._spawned        = False       # mồi đã được tạo chưa

    # ── Reset game mới ───────────────────────────────────────────────────────
    def reset(self):
        self.snake.reset()
        self.score         = 0
        self.speed_level   = 1
        self.is_new_record  = False
        self._alive         = True
        self._move_timer    = 0.0
        self._move_progress  = 0.0
        self._update_interval()
        self.spawn_food()

    # ── Tính interval từ tốc độ ─────────────────────────────────────────────
    def _update_interval(self):
        speed = min(SNAKE_MAX_SPEED,
                    SNAKE_BASE_SPEED + (self.speed_level - 1) * SPEED_INCREMENT)
        self._move_interval = 1.0 / speed  # giây/bước

    # ── Tạo mồi tại ô ngẫu nhiên (không trùng thân rắn) ────────────────────
    def spawn_food(self):
        occupied = set(self.snake.body)
        free     = [(c, r) for c in range(GRID_COLS)
                    for r in range(GRID_ROWS) if (c, r) not in occupied]
        if free:
            self.food_pos = random.choice(free)

    # ── Cập nhật mỗi frame ──────────────────────────────────────────────────
    def update(self, dt: float) -> dict:
        """
        Cập nhật trạng thái game, trả về dict sự kiện:
        {
          "moved":   bool,  # rắn vừa bước
          "ate":     bool,  # rắn vừa ăn mồi
          "died":    bool,  # rắn vừa chết
          "leveled": bool,  # tốc độ vừa tăng
        }
        """
        events = {"moved": False, "ate": False, "died": False, "leveled": False}
        if not self._alive:
            return events

        self._move_timer    += dt
        self._move_progress  = min(1.0, self._move_timer / self._move_interval)

        if self._move_timer < self._move_interval:
            return events  # chưa đến lúc bước

        # ─ Thực hiện bước ───────────────────────────────────────────────────
        self._move_timer    -= self._move_interval
        self._move_progress  = 0.0
        events["moved"]      = True

        new_head = self.snake.step()

        # Va chạm
        if self.snake.check_wall_collision() or self.snake.check_self_collision():
            self._alive      = False
            self.snake.alive = False
            events["died"]   = True
            self._save_high_score()
            return events

        # Ăn mồi
        if new_head == self.food_pos:
            events["ate"]  = True
            bonus          = SCORE_SPEED_BONUS if self.speed_level > 3 else 0
            self.score    += SCORE_EAT + bonus
            self.snake.grow(1)

            # Cập nhật leaderboard/high score
            if self.score > self.high_score:
                self.high_score = self.score
                self.is_new_record = True

            # Tăng tốc mỗi 5 lần ăn
            old_level = self.speed_level
            self.speed_level = max(1, self.score // (SCORE_EAT * 5)) + 1
            if self.speed_level != old_level:
                events["leveled"] = True
                self._update_interval()

            self.spawn_food()

        return events

    # ── Lưu/tải leaderboard ───────────────────────────────────────────────
    def _load_high_scores(self) -> list[int]:
        """
        Tải top scores.
        - Dạng mới: mỗi dòng 1 số (int)
        - Dạng cũ: file chỉ chứa 1 số (best)
        """
        vals: list[int] = []
        try:
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                raw = f.read().strip()
                if not raw:
                    return []
                # if old format: single int
                if "\n" not in raw and raw.replace("-", "").isdigit():
                    v = int(raw)
                    if v >= 0:
                        return [v]
                # new format: lines
                for line in raw.splitlines():
                    t = line.strip()
                    if not t:
                        continue
                    if t.replace("-", "").isdigit():
                        iv = int(t)
                        if iv >= 0:
                            vals.append(iv)
        except FileNotFoundError:
            return []
        except Exception:
            return []

        vals = sorted(set(vals), reverse=True)[:LEADERBOARD_SIZE]
        return vals

    def _save_high_scores(self):
        try:
            # Ensure current best & list are consistent
            if self.score > self.high_score:
                self.high_score = self.score
            if self.score > 0 and self.score not in self.top_scores:
                self.top_scores.append(self.score)
            self.high_score = max(self.top_scores) if self.top_scores else 0
            self.top_scores = sorted(set(self.top_scores), reverse=True)[:LEADERBOARD_SIZE]

            # Save as one score per line
            with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(str(s) for s in self.top_scores))
        except Exception:
            pass

    # ── Thuộc tính tiện ích ─────────────────────────────────────────────────
    @property
    def alive(self) -> bool:
        return self._alive

    @property
    def move_progress(self) -> float:
        return self._move_progress

    # Backward compatibility (some code calls engine._save_high_score())
    def _save_high_score(self):
        self._save_high_scores()
