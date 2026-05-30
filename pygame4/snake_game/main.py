"""
main.py - Entry point của Cyberpunk Neon Snake
Tích hợp tất cả module: engine, renderer, particles, sound, camera.
"""

import pygame
import sys
import os
import math

# Đảm bảo chạy từ bất kỳ thư mục nào đều import được các module trong snake_game/
_this_dir = os.path.dirname(os.path.abspath(__file__))
if _this_dir not in sys.path:
    sys.path.insert(0, _this_dir)

from constants import *
from game_engine import GameEngine
from renderer   import Renderer
from particles  import ParticleSystem
from sound_manager import SoundManager
from camera     import CameraShake


# ── Lớp App chính ─────────────────────────────────────────────────────────────

class NeonSnakeApp:
    """
    Vòng lặp game chính.
    Điều phối: input → engine update → render → audio.
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT), pygame.NOFRAME
        )
        pygame.display.set_caption(TITLE)
        self.clock  = pygame.time.Clock()

        # Sub-systems
        self.engine    = GameEngine()
        self.renderer  = Renderer(self.screen)
        self.particles = ParticleSystem()
        self.sound     = SoundManager()
        self.camera    = CameraShake()

        # Trạng thái ứng dụng
        self.state          = STATE_MENU
        self._leaderboard_tick = 0
        self.prev_state     = None
        self.tick           = 0
        self._game_over_tick = 0

        # Transition
        self._trans_timer   = 0
        self._trans_from    = None
        self._trans_to      = None
        self._trans_phase   = 1.0    # 1.0 = fully open

        # Không cần màn đợi tải (high score/leaderboard load đã nằm trong GameEngine.__init__)

    # ── Transition helper ─────────────────────────────────────────────────────
    def _start_transition(self, target_state: str):
        self._trans_from  = self.state
        self._trans_to    = target_state
        self._trans_timer = 0
        self._trans_phase = 1.0
        self.state        = STATE_TRANSITION

    def _update_transition(self):
        self._trans_timer += 1
        half = TRANSITION_FRAMES // 2

        if self._trans_timer <= half:
            # Đóng màn
            self._trans_phase = 1.0 - self._trans_timer / half
        elif self._trans_timer == half + 1:
            # Chuyển state thực sự ở giữa
            self.state = self._trans_to
            if self._trans_to == STATE_PLAYING:
                self.engine.reset()
                self.particles.clear()
                self.camera._duration = 0
        else:
            # Mở màn
            t = (self._trans_timer - half) / half
            self._trans_phase = min(1.0, t)

        if self._trans_timer >= TRANSITION_FRAMES:
            # Kết thúc transition
            if self.state == STATE_TRANSITION:
                self.state = self._trans_to

    # ── Vòng lặp chính ────────────────────────────────────────────────────────
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0  # giây
            self.tick += 1

            self._handle_events()
            self._update(dt)
            self._draw()

            pygame.display.flip()

    # ── Xử lý sự kiện ────────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()

            if event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _on_key(self, key: int):
        S = self.state

        # Thoát toàn cục
        if key == pygame.K_ESCAPE:
            if S in (STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER):
                self._start_transition(STATE_MENU)
            elif S == STATE_MENU:
                self._quit()

        # Menu
        if S == STATE_MENU:
            if key == pygame.K_RETURN:
                self.sound.play("menu_select")
                self._start_transition(STATE_PLAYING)
            elif key == pygame.K_m:
                self.sound.toggle()
                self.sound.play("menu_blip")
            elif key == pygame.K_h:
                self.sound.play("menu_blip")
                self._start_transition(STATE_LEADERBOARD)

        # Đang chơi
        elif S == STATE_PLAYING:
            snake = self.engine.snake
            if key in (pygame.K_UP,    pygame.K_w): snake.set_direction(snake.UP)
            if key in (pygame.K_DOWN,  pygame.K_s): snake.set_direction(snake.DOWN)
            if key in (pygame.K_LEFT,  pygame.K_a): snake.set_direction(snake.LEFT)
            if key in (pygame.K_RIGHT, pygame.K_d): snake.set_direction(snake.RIGHT)
            if key == pygame.K_p:
                self.state = STATE_PAUSED
            if key == pygame.K_m:
                self.sound.toggle()

        # Tạm dừng
        elif S == STATE_PAUSED:
            if key == pygame.K_p:
                self.state = STATE_PLAYING

        # Game Over
        elif S == STATE_GAME_OVER:
            if key == pygame.K_RETURN:
                self.sound.play("menu_select")
                self._start_transition(STATE_PLAYING)

        # Leaderboard
        elif S == STATE_LEADERBOARD:
            if key == pygame.K_ESCAPE:
                self._start_transition(STATE_MENU)
            if key == pygame.K_RETURN:
                self._start_transition(STATE_MENU)

    # ── Cập nhật logic ────────────────────────────────────────────────────────
    def _update(self, dt: float):
        # Transition
        if self.state == STATE_TRANSITION:
            self._update_transition()
            return

        self.camera.update()
        self.particles.update()

        if self.state == STATE_PLAYING:
            events = self.engine.update(dt)
            self._handle_game_events(events)

        if self.state == STATE_GAME_OVER:
            self._game_over_tick += 1

    def _handle_game_events(self, events: dict):
        if events["moved"]:
            self.sound.play("move", volume=0.15)

        if events["ate"]:
            self.sound.play("eat", volume=0.8)
            # Spawn particles tại vị trí mồi
            if self.engine.food_pos:
                fc, fr = self.engine.food_pos
                # Vị trí pixel tâm ô cũ (trước khi tạo mồi mới)
                cx = PLAY_LEFT + fc * CELL_SIZE + CELL_SIZE // 2
                cy = PLAY_TOP  + fr * CELL_SIZE + CELL_SIZE // 2
            else:
                hc, hr = self.engine.snake.head
                cx = PLAY_LEFT + hc * CELL_SIZE + CELL_SIZE // 2
                cy = PLAY_TOP  + hr * CELL_SIZE + CELL_SIZE // 2
            self.particles.emit_food(cx, cy)

        if events["leveled"]:
            self.sound.play("level_up", volume=0.7)

        if events["died"]:
            self.sound.play("death", volume=0.9)
            # Camera shake mạnh
            self.camera.shake(SHAKE_INTENSITY, SHAKE_DURATION)
            # Particles đỏ tại đầu rắn
            hc, hr = self.engine.snake.head
            cx = PLAY_LEFT + hc * CELL_SIZE + CELL_SIZE // 2
            cy = PLAY_TOP  + hr * CELL_SIZE + CELL_SIZE // 2
            self.particles.emit_death(cx, cy)
            # Chuyển sang game over
            self._game_over_tick = 0
            self.state = STATE_GAME_OVER

    # ── Render ────────────────────────────────────────────────────────────────
    def _draw(self):
        S = self.state

        # Background và grid luôn vẽ
        if S in (STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER):
            self.renderer.draw_background()
        elif S == STATE_MENU:
            self.renderer.draw_background()
            self.renderer.draw_menu(self.tick, self.engine.high_score)
            return
        elif S == STATE_TRANSITION:
            # Render state dưới nền
            base = self._trans_to if self._trans_phase < 0.5 else self._trans_from
            self.renderer.draw_background()
            if base == STATE_PLAYING:
                self._draw_gameplay()
            elif base == STATE_MENU:
                self.renderer.draw_menu(self.tick, self.engine.high_score)
            self.renderer.draw_transition(self._trans_phase)
            return

        # Vẽ game
        if S in (STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER):
            self._draw_gameplay()

        if S == STATE_PAUSED:
            self.renderer.draw_pause()

        if S == STATE_GAME_OVER:
            self.renderer.draw_game_over(
                self.engine.score,
                self.engine.high_score,
                self.engine.is_new_record,
                self._game_over_tick
            )

        if S == STATE_LEADERBOARD:
            self.renderer.draw_leaderboard(
                self.tick,
                self.engine.top_scores,
            )

    def _draw_gameplay(self):
        """Vẽ đầy đủ cảnh chơi game."""
        offset = self.camera.offset

        # Mồi
        if self.engine.food_pos:
            fc, fr = self.engine.food_pos
            self.renderer.draw_food(fc, fr, offset)

        # Rắn
        self.renderer.draw_snake(
            self.engine.snake.body,
            self.engine.snake.direction,
            self.engine.move_progress,
            offset
        )

        # Particles (vẽ sau snake để nằm trên)
        self.particles.draw(self.screen)

        # HUD
        self.renderer.draw_hud(
            self.engine.score,
            self.engine.high_score,
            self.engine.speed_level,
            self.sound.enabled
        )

    # ── Thoát ────────────────────────────────────────────────────────────────
    def _quit(self):
        self.engine._save_high_score()
        pygame.quit()
        sys.exit(0)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = NeonSnakeApp()
    app.run()
