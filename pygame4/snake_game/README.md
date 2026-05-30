## NEON SERPENT — Cyberpunk Snake Game

Một game Snake hoàn chỉnh phong cách Cyberpunk Indie với:
- Giao diện neon tím xanh cinematic
- Background grid động có pulse
- Rắn có animation mượt + mắt nhìn theo hướng
- Hiệu ứng glow nhiều lớp
- Particle burst khi ăn mồi
- Camera shake khi va chạm
- Âm thanh tổng hợp (không cần file .mp3)
- Menu đẹp với logo neon
- HUD score / high score / speed
- Hiệu ứng chuyển cảnh
- FPS 60 ổn định

### Cài đặt
```
pip install pygame numpy
```

### Chạy
```
python main.py
```

### Điều khiển
- **Mũi tên / WASD**: Di chuyển
- **P**: Tạm dừng
- **M**: Tắt/bật âm thanh
- **Enter**: Bắt đầu / Chơi lại
- **ESC**: Về menu / Thoát

### Cấu trúc file
```
snake_game/
├── main.py          ← Entry point, vòng lặp chính
├── constants.py     ← Tất cả hằng số, màu sắc, cấu hình
├── game_engine.py   ← Logic Snake, điểm, tốc độ
├── renderer.py      ← Toàn bộ vẽ: background, snake, food, HUD, menu
├── particles.py     ← Hệ thống particle neon
├── sound_manager.py ← Tổng hợp âm thanh bằng waveform
├── camera.py        ← Camera shake effect
└── README.md
```
