"""
constants.py - Tất cả hằng số và cấu hình của game
Cyberpunk Neon Snake - Indie Game Edition
"""

# ─── CỬA SỔ & HIỂN THỊ ────────────────────────────────────────────────────────
WINDOW_WIDTH   = 1280
WINDOW_HEIGHT  = 720
FPS            = 60
TITLE          = "NEON SERPENT  //  CYBERPUNK EDITION"

# ─── GRID ─────────────────────────────────────────────────────────────────────
CELL_SIZE       = 32          # pixel mỗi ô
GRID_COLS       = 25          # số cột trong vùng chơi
GRID_ROWS       = 18          # số hàng trong vùng chơi

# Vùng chơi được căn giữa màn hình
PLAY_LEFT   = (WINDOW_WIDTH  - GRID_COLS * CELL_SIZE) // 2
PLAY_TOP    = (WINDOW_HEIGHT - GRID_ROWS * CELL_SIZE) // 2
PLAY_WIDTH  = GRID_COLS * CELL_SIZE
PLAY_HEIGHT = GRID_ROWS * CELL_SIZE

# ─── TỐC ĐỘ RẮN ──────────────────────────────────────────────────────────────
SNAKE_BASE_SPEED  = 8   # ô/giây lúc đầu
SNAKE_MAX_SPEED   = 16  # ô/giây tối đa
SPEED_INCREMENT   = 0.5 # tăng mỗi 5 điểm

# ─── BẢNG MÀU CYBERPUNK NEON ─────────────────────────────────────────────────
BLACK        = (  0,   0,   0)
DEEP_BLACK   = (  5,   5,  15)
DARK_PURPLE  = ( 15,   5,  30)

# Neon chính
NEON_CYAN    = (  0, 255, 255)
NEON_PURPLE  = (180,   0, 255)
NEON_PINK    = (255,   0, 200)
NEON_BLUE    = (  0, 150, 255)
NEON_GREEN   = (  0, 255, 120)
NEON_YELLOW  = (255, 220,   0)
NEON_RED     = (255,  50,  50)
NEON_ORANGE  = (255, 140,   0)

# Màu mờ dùng cho glow/grid
DIM_CYAN     = (  0,  80,  80)
DIM_PURPLE   = ( 60,   0, 100)
DIM_BLUE     = (  0,  40,  80)

# Màu rắn (gradient đầu → đuôi)
SNAKE_HEAD   = NEON_CYAN
SNAKE_BODY   = NEON_PURPLE
SNAKE_TAIL   = (80, 0, 120)

# Màu mồi
FOOD_GLOW    = NEON_YELLOW
FOOD_CORE    = (255, 255, 200)

# UI
UI_BG        = (10, 5, 20, 180)     # RGBA
UI_BORDER    = NEON_PURPLE
UI_TEXT      = NEON_CYAN
UI_ACCENT    = NEON_PINK

# ─── PARTICLE ────────────────────────────────────────────────────────────────
PARTICLE_COUNT        = 40    # hạt khi ăn mồi
PARTICLE_LIFETIME     = 60    # frame
PARTICLE_SPEED_MIN    = 1.5
PARTICLE_SPEED_MAX    = 6.0

# ─── CAMERA SHAKE ────────────────────────────────────────────────────────────
SHAKE_INTENSITY  = 14   # pixel
SHAKE_DURATION   = 20   # frame
SHAKE_DECAY      = 0.85 # hệ số giảm mỗi frame

# ─── ANIMATION ───────────────────────────────────────────────────────────────
FOOD_PULSE_SPEED  = 0.08   # rad/frame
GRID_ANIM_SPEED   = 0.012  # rad/frame  (nhấp nháy grid)
GLOW_LAYERS       = 4      # số lớp glow
TRANSITION_FRAMES = 45     # frame hiệu ứng chuyển cảnh

# ─── ĐIỂM ─────────────────────────────────────────────────────────────────────
SCORE_EAT         = 10
SCORE_SPEED_BONUS = 5   # cộng thêm khi tốc độ cao

# ─── TRẠNG THÁI GAME ─────────────────────────────────────────────────────────
STATE_MENU       = "menu"
STATE_PLAYING    = "playing"
STATE_PAUSED     = "paused"
STATE_GAME_OVER  = "game_over"
STATE_TRANSITION = "transition"
STATE_LEADERBOARD = "leaderboard"

# ─── FILE ─────────────────────────────────────────────────────────────────────
# Dùng đường dẫn tuyệt đối để không phụ thuộc bạn chạy từ thư mục nào
import os as _os
HIGHSCORE_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "highscore.dat")

# Leaderboard
LEADERBOARD_SIZE = 10
