import pygame
import random
import sys
import math
import heapq

# Инициализация Pygame
pygame.init()
pygame.mixer.init()
# Размеры окна и блоков
WIDTH, HEIGHT = 1920, 1080  # высокое разрешение окна
RENDER_W, RENDER_H = 1920, 1080  # внутреннее качество
BLOCK_SIZE = 32  # оптимально для высокого разрешения
FPS = 144  # суперплавность



difficulty_buttons = [
    {"label": "Начальный", "fps": 7},
    {"label": "Средний", "fps": 10},
    {"label": "Сложный", "fps": 13}
]
selected_difficulty = 1  # индекс по умолчанию: Средний

# Цвета
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED   = (255, 0, 0)
WHITE = (255, 255, 255)
GRAY  = (100, 100, 100)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
offscreen_surface = pygame.Surface((RENDER_W, RENDER_H), pygame.SRCALPHA)
grass_img = pygame.image.load("OldSnake/assets/images/grass.jpg").convert()
grass_img = pygame.transform.scale(grass_img, (RENDER_W, RENDER_H))
daisy_img = pygame.image.load("OldSnake/assets/images/daisy.png").convert_alpha()
daisy_img = pygame.transform.scale(daisy_img, (20, 20))
klyaksa_img_raw = pygame.image.load("OldSnake/assets/images/klyaksa.png").convert_alpha()
klyaksa_size = BLOCK_SIZE * 3
klyaksa_img = pygame.transform.scale(klyaksa_img_raw, (klyaksa_size, klyaksa_size))
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 36)

high_score = 0

# Фоновая музыка
pygame.mixer.music.load("OldSnake/assets/sounds/Music for Snake.mp3")
pygame.mixer.music.play(-1)

turnon_img = pygame.image.load("OldSnake/assets/images/turnon.png").convert_alpha()
turnoff_img = pygame.image.load("OldSnake/assets/images/turnoff.png").convert_alpha()
turnon_img = pygame.transform.scale(turnon_img, (54, 54))
turnoff_img = pygame.transform.scale(turnoff_img, (54, 54))
sound_on = True

start_img = pygame.image.load("OldSnake/assets/images/start_game.png").convert_alpha()
start_img = pygame.transform.smoothscale(start_img, (240, 60))

def random_food(forbidden=None):
    if forbidden is None:
        forbidden = set()
    while True:
        x = random.randint(0, (RENDER_W - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        y = random.randint(0, (RENDER_H - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        if (x, y) not in forbidden:
            return (x, y)
# Единый фон с ромашками и пятнами
def draw_background(target=None):
    if target is None:
        target = offscreen_surface
    target.blit(grass_img, (0, 0))
    # Ромашки (текстура)
    for _ in range(random.randint(10, 20)):
        cx = random.randint(20, RENDER_W - 20)
        cy = random.randint(20, RENDER_H - 20)
        target.blit(daisy_img, (cx - 10, cy - 10))


# Отрисовка объектов
def move_snake_ai(snake, food, direction):
    path = astar_path(snake[0], food, set(snake), RENDER_W, RENDER_H, BLOCK_SIZE)
    if path:
        next_head = path[0]
        dx = next_head[0] - snake[0][0]
        dy = next_head[1] - snake[0][1]
        return (dx, dy)
    else:
        for d in [(BLOCK_SIZE,0),(-BLOCK_SIZE,0),(0,BLOCK_SIZE),(0,-BLOCK_SIZE)]:
            nx = (snake[0][0]+d[0])%RENDER_W
            ny = (snake[0][1]+d[1])%RENDER_H
            if (nx,ny) not in snake:
                return d
        return direction

def draw_snake_detailed(target, snake, direction, thickness=None, eat_anim=0.0, tongue_anim=0.0):
    if not snake:
        return
    if thickness is None:
        thickness = [BLOCK_SIZE for _ in snake]
    # Тень змейки
    for i, (x, y) in enumerate(snake):
        w = thickness[i] if i < len(thickness) else BLOCK_SIZE
        shadow = pygame.Surface((w, w), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0,0,0,60), (2, 6, w-4, w//2))
        target.blit(shadow, (x, y+8))
    # Отражение змейки
    for i, (x, y) in enumerate(snake):
        w = thickness[i] if i < len(thickness) else BLOCK_SIZE
        reflect = pygame.Surface((w, w), pygame.SRCALPHA)
        pygame.draw.ellipse(reflect, (120,180,255,40), (0, 0, w, w//2))
        target.blit(reflect, (x, y+w//2+8))
    # Голова
    head = snake[0]
    hx, hy = head
    cx = hx + BLOCK_SIZE // 2
    cy = hy + BLOCK_SIZE // 2
    angle = 0
    if direction == (BLOCK_SIZE, 0):
        angle = 0
    elif direction == (0, BLOCK_SIZE):
        angle = 90
    elif direction == (-BLOCK_SIZE, 0):
        angle = 180
    elif direction == (0, -BLOCK_SIZE):
        angle = -90
    t_len = BLOCK_SIZE * 1.8
    t_w = BLOCK_SIZE * 0.6
    t_end = (cx + t_len * math.cos(math.radians(angle)),
             cy + t_len * math.sin(math.radians(angle)))
    t_start = (cx, cy)
    # --- анимация рта и языка ---
    mouth_open = int(BLOCK_SIZE * (0.18 + 0.22 * eat_anim))
    tongue_offset = int(10 * math.sin(tongue_anim * math.pi * 2))
    # Язык наружу
    tongue_len = BLOCK_SIZE * (0.7 + 0.5 * eat_anim)
    tongue_w = 2
    tongue_angle1 = angle - 15
    tongue_angle2 = angle + 15
    tip1 = (cx + tongue_len * math.cos(math.radians(tongue_angle1)),
            cy + tongue_len * math.sin(math.radians(tongue_angle1)))
    tip2 = (cx + tongue_len * math.cos(math.radians(tongue_angle2)),
            cy + tongue_len * math.sin(math.radians(tongue_angle2)))
    tongue_base = (cx + (BLOCK_SIZE//2 + mouth_open) * math.cos(math.radians(angle)),
                   cy + (BLOCK_SIZE//2 + mouth_open) * math.sin(math.radians(angle)))
    pygame.draw.line(target, RED, tongue_base, tip1, tongue_w)
    pygame.draw.line(target, RED, tongue_base, tip2, tongue_w)
    # Щёки
    cheek_w = int(BLOCK_SIZE * 0.7)
    cheek_h = int(BLOCK_SIZE * 0.45)
    offset = int(BLOCK_SIZE * 0.45)
    for sign in [-1, 1]:
        dx = math.cos(math.radians(angle + 90 * sign)) * offset
        dy = math.sin(math.radians(angle + 90 * sign)) * offset
        cheek_rect = pygame.Rect(cx + dx - cheek_w//2, cy + dy - cheek_h//2, cheek_w, cheek_h)
        pygame.draw.ellipse(target, (139, 69, 19), cheek_rect)
    # Центральная часть головы (эллипс)
    head_w = int(BLOCK_SIZE * 1.2 + mouth_open)
    head_h = int(BLOCK_SIZE * 0.8)
    head_rect = pygame.Rect(cx - head_w//2, cy - head_h//2, head_w, head_h)
    pygame.draw.ellipse(target, (139, 69, 19), head_rect)
    # Глаза
    eye_r = int(BLOCK_SIZE * 0.11)
    eye_offset = int(BLOCK_SIZE * 0.32)
    eye_y_offset = int(BLOCK_SIZE * -0.13)
    for sign in [-1, 1]:
        ex = cx + math.cos(math.radians(angle + 90 * sign)) * eye_offset
        ey = cy + math.sin(math.radians(angle + 90 * sign)) * eye_offset + eye_y_offset * math.cos(math.radians(angle))
        pygame.draw.circle(target, BLACK, (int(ex), int(ey)), eye_r)
    # Туловище
    t = pygame.time.get_ticks() / 400.0
    for i, (x, y) in enumerate(snake[1:], 1):
        scale = 1.0
        if thickness and i < len(thickness):
            scale = thickness[i] / BLOCK_SIZE
        elif len(snake) > 0 and i >= int(len(snake) * 0.7):
            denom = len(snake) * 0.3
            if denom == 0:
                denom = 1
            scale = 0.6 + 0.4 * (len(snake) - i) / denom
        body_rect = pygame.Rect(
            int(x + (BLOCK_SIZE - BLOCK_SIZE * scale) / 2),
            int(y + (BLOCK_SIZE - BLOCK_SIZE * scale) / 2),
            int(BLOCK_SIZE * scale),
            int(BLOCK_SIZE * scale)
        )
        pygame.draw.rect(target, (139, 69, 19), body_rect)
        c = (x + BLOCK_SIZE // 2, y + BLOCK_SIZE // 2)
        for j in range(2):
            phase = t - i * 0.25 + j * math.pi
            ox = int(BLOCK_SIZE*0.22 * math.sin(phase + j))
            oy = int(BLOCK_SIZE*0.13 * math.cos(phase + j))
            spot_rect = pygame.Rect(c[0]+ox-3, c[1]+oy-2, 6, 4)
            pygame.draw.ellipse(target, BLACK, spot_rect)
    # Хвост
    if len(snake) > 1:
        tail = snake[-1]
        tx_, ty_ = tail
        tcx = tx_ + BLOCK_SIZE // 2
        tcy = ty_ + BLOCK_SIZE // 2
        if len(snake) >= 2:
            px, py = snake[-2]
            dx = tcx - (px + BLOCK_SIZE // 2)
            dy = tcy - (py + BLOCK_SIZE // 2)
            norm = math.hypot(dx, dy)
            if norm == 0:
                norm = 1
            dx /= norm
            dy /= norm
        else:
            dx, dy = 1, 0
        tip = (tcx + dx * BLOCK_SIZE * 0.9, tcy + dy * BLOCK_SIZE * 0.9)
        base1 = (tcx - dx * BLOCK_SIZE * 0.4 + dy * BLOCK_SIZE * 0.4, tcy - dy * BLOCK_SIZE * 0.4 - dx * BLOCK_SIZE * 0.4)
        base2 = (tcx - dx * BLOCK_SIZE * 0.4 - dy * BLOCK_SIZE * 0.4, tcy - dy * BLOCK_SIZE * 0.4 + dx * BLOCK_SIZE * 0.4)
        pygame.draw.polygon(target, (139, 69, 19), [tip, base1, base2])
        for j in range(2):
            ox = int(BLOCK_SIZE*0.15 * (random.random()-0.5))
            oy = int(BLOCK_SIZE*0.15 * (random.random()-0.5))
            spot_rect = pygame.Rect(tcx+ox-1, tcy+oy-1, 3, 2)
            pygame.draw.ellipse(target, BLACK, spot_rect)
# Тень еды
def draw_food(food, target=None):
    if target is None:
        target = offscreen_surface
    x, y = food
    # Тень еды
    shadow = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0,0,0,70), (2, 6, BLOCK_SIZE-4, BLOCK_SIZE//2))
    target.blit(shadow, (x, y+8))
    # Отражение еды
    reflect = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
    pygame.draw.ellipse(reflect, (255,255,255,30), (0, 0, BLOCK_SIZE, BLOCK_SIZE//2))
    target.blit(reflect, (x, y+BLOCK_SIZE//2+8))

    center = (x + BLOCK_SIZE // 2, y + BLOCK_SIZE // 2)
    radius = BLOCK_SIZE // 2 - 2

    # Яблоко (красный круг)
    pygame.draw.circle(target, RED, center, radius)

    # Отблеск (маленький белый круг)
    pygame.draw.circle(target, WHITE, (center[0] - 4, center[1] - 4), 3)

    # Ветка (коричневая линия)
    pygame.draw.line(target, (139, 69, 19), (center[0], center[1] - radius),
                     (center[0], center[1] - radius - 6), 2)

    # Листик (зелёный круг)
    pygame.draw.circle(target, (0, 200, 0), (center[0] - 5, center[1] - radius - 6), 3)

# Отрисовка счёта во время игры
def draw_score(score, target=None):
    if target is None:
        target = offscreen_surface
    text = font.render(f"Счёт: {score}", True, WHITE)
    text_rect = text.get_rect(topleft=(10, 10))
    # Draw black outline
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        target.blit(font.render(f"Счёт: {score}", True, BLACK), text_rect.move(dx, dy))
    target.blit(text, text_rect)

# Отрисовка лучшего счёта в главном меню
def draw_best_score(target=None):
    if target is None:
        target = offscreen_surface
    if high_score > 0:
        small_font = pygame.font.SysFont("arial", int(36 * 0.7))
        text = small_font.render(f"Лучший счёт: {high_score}", True, WHITE)
        text_rect = text.get_rect(topleft=(10, 10))
        # Draw black outline
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            target.blit(small_font.render(f"Лучший счёт: {high_score}", True, BLACK), text_rect.move(dx, dy))
        target.blit(text, text_rect)

# Логика меню
# Главное меню 
def astar_path(start, goal, snake_body, grid_w, grid_h, block):
    def neighbors(pos):
        x, y = pos
        for dx, dy in [(-block,0),(block,0),(0,-block),(0,block)]:
            nx, ny = (x+dx)%grid_w, (y+dy)%grid_h
            if (nx, ny) not in snake_body:
                yield (nx, ny)
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: abs(start[0]-goal[0]) + abs(start[1]-goal[1])}
    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current != start:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        for neighbor in neighbors(current):
            tentative_g = g_score[current] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + abs(neighbor[0]-goal[0]) + abs(neighbor[1]-goal[1])
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []

def show_main_menu():
    global selected_difficulty
    global sound_on
    menu_snake = [(RENDER_W//2 - 3*BLOCK_SIZE + i*BLOCK_SIZE, RENDER_H//2) for i in range(6)]
    menu_food = random_food(set(menu_snake))
    menu_dir = (BLOCK_SIZE, 0)
    menu_thickness = [BLOCK_SIZE for _ in menu_snake]
    eat_anim = 0.0
    tongue_anim = 0.0
    eat_anim_timer = 0
    # --- интерфейс ---
    button_width = 240
    button_height = 60
    y_offset = 60
    start_y = y_offset + 120
    launch_button_rect = pygame.Rect(RENDER_W // 2 - button_width // 2, start_y, button_width, button_height)
    diff_label_gap = 32
    diff_buttons_gap = 16
    diff_button_height = int(button_height * 0.8)
    diff_button_width = button_width
    diff_label_y = start_y + button_height + diff_label_gap
    diff_buttons_start_y = diff_label_y + 40
    difficulty_button_rects = []
    for i in range(len(difficulty_buttons)):
        rect = pygame.Rect(
            RENDER_W // 2 - diff_button_width // 2,
            diff_buttons_start_y + i * (diff_button_height + diff_buttons_gap),
            diff_button_width, diff_button_height
        )
        difficulty_button_rects.append(rect)
    while True:
        random.seed(42)
        draw_background()
        draw_snake_detailed(offscreen_surface, menu_snake, menu_dir, menu_thickness, eat_anim, tongue_anim)
        if not launch_button_rect.collidepoint(menu_food):
            draw_food(menu_food, offscreen_surface)
        title_text = "Добро пожаловать в змейку"
        title_pos = (RENDER_W // 2 - font.size(title_text)[0] // 2, y_offset)
        draw_text_with_outline(title_text, font, WHITE, BLACK, title_pos, target=offscreen_surface)
        # --- Картинка-кнопка ---
        offscreen_surface.blit(start_img, launch_button_rect)
        # pygame.draw.ellipse(offscreen_surface, (60, 60, 60), launch_button_rect.inflate(6, 6))
        # pygame.draw.ellipse(offscreen_surface, GRAY, launch_button_rect)
        # button_text = "Запустить"
        # text_rect = font.render(button_text, True, WHITE).get_rect(center=launch_button_rect.center)
        # draw_text_with_outline(button_text, font, WHITE, BLACK, text_rect.topleft, target=offscreen_surface)
        diff_label = "Уровень сложности"
        diff_label_pos = (RENDER_W // 2 - font.size(diff_label)[0] // 2, diff_label_y)
        draw_text_with_outline(diff_label, font, WHITE, BLACK, diff_label_pos, target=offscreen_surface)
        for i, rect in enumerate(difficulty_button_rects):
            if i == selected_difficulty:
                pygame.draw.ellipse(offscreen_surface, WHITE, rect.inflate(6, 6))
                pygame.draw.ellipse(offscreen_surface, WHITE, rect)
                label = difficulty_buttons[i]["label"]
                label_rect = font.render(label, True, GRAY).get_rect(center=rect.center)
                offscreen_surface.blit(font.render(label, True, GRAY), label_rect)
            else:
                pygame.draw.ellipse(offscreen_surface, (60, 60, 60), rect.inflate(6, 6))
                pygame.draw.ellipse(offscreen_surface, GRAY, rect)
                label = difficulty_buttons[i]["label"]
                label_rect = font.render(label, True, WHITE).get_rect(center=rect.center)
                offscreen_surface.blit(font.render(label, True, WHITE), label_rect)
        draw_best_score(offscreen_surface)
        icon_size = 80
        icon_margin = 32
        icon_rect = pygame.Rect(RENDER_W - icon_size - icon_margin, RENDER_H - icon_size - icon_margin, icon_size, icon_size)
        if sound_on:
            offscreen_surface.blit(turnon_img, icon_rect)
        else:
            offscreen_surface.blit(turnoff_img, icon_rect)
        # --- интеллектуальное движение змейки ---
        menu_dir = move_snake_ai(menu_snake, menu_food, menu_dir)
        head_x = (menu_snake[0][0] + menu_dir[0]) % RENDER_W
        head_y = (menu_snake[0][1] + menu_dir[1]) % RENDER_H
        head = (head_x, head_y)
        if head not in menu_snake:
            menu_snake.insert(0, head)
            menu_thickness.insert(0, menu_thickness[0])
        if head == menu_food:
            menu_food = random_food(set(menu_snake))
            for i in range(min(6, len(menu_thickness))):
                menu_thickness[i] = int(BLOCK_SIZE * 1.35)
            eat_anim = 1.0
            eat_anim_timer = pygame.time.get_ticks()
        else:
            menu_snake.pop()
            menu_thickness.pop()
        # --- анимация утолщения и поедания ---
        for i in range(len(menu_thickness)):
            if menu_thickness[i] > BLOCK_SIZE:
                menu_thickness[i] -= 1
        if eat_anim > 0:
            elapsed = (pygame.time.get_ticks() - eat_anim_timer) / 400.0
            eat_anim = max(0.0, 1.0 - elapsed)
        tongue_anim = (pygame.time.get_ticks() % 1000) / 1000.0
        screen.blit(pygame.transform.smoothscale(offscreen_surface, (WIDTH, HEIGHT)), (0, 0))
        pygame.display.flip()
        offscreen_surface.fill((0, 0, 0, 0))
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                scaled_pos = (event.pos[0] * RENDER_W // WIDTH, event.pos[1] * RENDER_H // HEIGHT)
                if icon_rect.collidepoint(scaled_pos):
                    sound_on = not sound_on
                    if sound_on:
                        pygame.mixer.music.set_volume(1.0)
                    else:
                        pygame.mixer.music.set_volume(0.0)
                    break
                if launch_button_rect.collidepoint(scaled_pos):
                    return
                for i, rect in enumerate(difficulty_button_rects):
                    if rect.collidepoint(scaled_pos):
                        selected_difficulty = i
                        break

# Обработка ввода: WASD и стрелки
def get_new_direction(current_direction):
    keys = pygame.key.get_pressed()

    # Словарь возможных направлений: клавиша -> направление
    key_direction_map = {
        # Стрелки
        pygame.K_UP:    (0, -BLOCK_SIZE),
        pygame.K_DOWN:  (0, BLOCK_SIZE),
        pygame.K_LEFT:  (-BLOCK_SIZE, 0),
        pygame.K_RIGHT: (BLOCK_SIZE, 0),
        # WASD
        pygame.K_w: (0, -BLOCK_SIZE),
        pygame.K_s: (0, BLOCK_SIZE),
        pygame.K_a: (-BLOCK_SIZE, 0),
        pygame.K_d: (BLOCK_SIZE, 0),
    }

    for key, new_dir in key_direction_map.items():
        if keys[key]:
            # Запрещаем разворот на 180 градусов
            if (new_dir[0] != -current_direction[0] or
                new_dir[1] != -current_direction[1]):
                return new_dir

    return current_direction  # если ничего не нажато — продолжаем текущее направление

# Обработка столкновений
# Экран окончания игры (не главное меню)
class Firework:
    def __init__(self, x, y, color, angle, speed, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.angle = angle
        self.speed = speed
        self.lifetime = lifetime
        self.age = 0
    def update(self, dt):
        self.x += self.speed * math.cos(math.radians(self.angle)) * dt
        self.y += self.speed * math.sin(math.radians(self.angle)) * dt
        self.age += dt
    def draw(self, surface):
        if self.age < self.lifetime:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 4)

def show_game_over(score):
    global high_score
    global sound_on
    new_record = False
    if score > high_score:
        high_score = score
        new_record = True
    icon_size = 80
    icon_margin = 32
    icon_rect = pygame.Rect(RENDER_W - icon_size - icon_margin, RENDER_H - icon_size - icon_margin, icon_size, icon_size)
    menu_button_rect = pygame.Rect(RENDER_W // 2 - 120, RENDER_H - 120, 240, 60)
    start_time = pygame.time.get_ticks()
    duration = 2000
    allow_click = False
    menu_snake = [(RENDER_W//2 - 3*BLOCK_SIZE + i*BLOCK_SIZE, RENDER_H//2) for i in range(6)]
    menu_food = random_food(set(menu_snake))
    menu_dir = (BLOCK_SIZE, 0)
    menu_thickness = [BLOCK_SIZE for _ in menu_snake]
    eat_anim = 0.0
    tongue_anim = 0.0
    eat_anim_timer = 0
    fireworks = []
    last_firework_time = 0
    game_over_text = "Конец игры"
    score_text = f"Ваш счёт: {score}"
    high_score_text = f"Лучший счёт: {high_score}"
    # ...existing code...
    while True:
        dt = clock.get_time() / 1000.0
        random.seed(42)
        draw_background()
        draw_snake_detailed(offscreen_surface, menu_snake, menu_dir, menu_thickness, eat_anim, tongue_anim)
        if not menu_button_rect.collidepoint(menu_food):
            draw_food(menu_food, offscreen_surface)
        # --- динамические фейерверки ---
        now = pygame.time.get_ticks()
        if new_record and now - last_firework_time > 120:
            for _ in range(3):
                x = random.randint(40, RENDER_W-40)
                y = random.randint(40, RENDER_H-40)
                color = random.choice([(255,0,0),(0,255,0),(0,0,255),(255,255,0),(255,0,255),(0,255,255)])
                for i in range(8):
                    angle = i * 45 + random.randint(-10,10)
                    speed = random.uniform(120, 220)
                    fireworks.append(Firework(x, y, color, angle, speed, 0.7))
            last_firework_time = now
        for fw in list(fireworks):
            fw.update(dt)
            fw.draw(offscreen_surface)
            if fw.age > fw.lifetime:
                fireworks.remove(fw)
        # ...отрисовка текста и кнопок...
        draw_text_with_outline(game_over_text, font, RED, BLACK, (RENDER_W // 2 - 160, RENDER_H // 2 - 120), target=offscreen_surface)
        draw_text_with_outline(score_text, font, WHITE, BLACK, (RENDER_W // 2 - 120, RENDER_H // 2 - 40), target=offscreen_surface)
        draw_text_with_outline(high_score_text, font, WHITE, BLACK, (RENDER_W // 2 - 120, RENDER_H // 2 + 10), target=offscreen_surface)
        pygame.draw.ellipse(offscreen_surface, (60, 60, 60), menu_button_rect.inflate(6, 6))
        pygame.draw.ellipse(offscreen_surface, GRAY, menu_button_rect)
        menu_text = font.render("На главный экран", True, WHITE)
        text_rect = menu_text.get_rect(center=menu_button_rect.center)
        shadow = font.render("На главный экран", True, (30, 30, 30))
        offscreen_surface.blit(shadow, text_rect.move(1, 1))
        offscreen_surface.blit(menu_text, text_rect)
        # ...движение змейки...
        sx, sy = menu_snake[0]
        fx, fy = menu_food
        if sx != fx:
            dx = BLOCK_SIZE if fx > sx else -BLOCK_SIZE
            dy = 0
        elif sy != fy:
            dx = 0
            dy = BLOCK_SIZE if fy > sy else -BLOCK_SIZE
        else:
            dx, dy = menu_dir
        next_pos = ((menu_snake[0][0] + dx) % RENDER_W, (menu_snake[0][1] + dy) % RENDER_H)
        if next_pos in menu_snake:
            if dx != 0:
                alt_pos = ((menu_snake[0][0]) % RENDER_W, (menu_snake[0][1] - BLOCK_SIZE) % RENDER_H)
                if alt_pos not in menu_snake:
                    dx, dy = 0, -BLOCK_SIZE
                else:
                    alt_pos = ((menu_snake[0][0]) % RENDER_W, (menu_snake[0][1] + BLOCK_SIZE) % RENDER_H)
                    if alt_pos not in menu_snake:
                        dx, dy = 0, BLOCK_SIZE
                    else:
                        dx, dy = menu_dir
            elif dy != 0:
                alt_pos = ((menu_snake[0][0] - BLOCK_SIZE) % RENDER_W, (menu_snake[0][1]) % RENDER_H)
                if alt_pos not in menu_snake:
                    dx, dy = -BLOCK_SIZE, 0
                else:
                    alt_pos = ((menu_snake[0][0] + BLOCK_SIZE) % RENDER_W, (menu_snake[0][1]) % RENDER_H)
                    if alt_pos not in menu_snake:
                        dx, dy = BLOCK_SIZE, 0
                    else:
                        dx, dy = menu_dir
        menu_dir = (dx, dy)
        head_x = (menu_snake[0][0] + menu_dir[0]) % RENDER_W
        head_y = (menu_snake[0][1] + menu_dir[1]) % RENDER_H
        head = (head_x, head_y)
        if head not in menu_snake:
            menu_snake.insert(0, head)
        if head == menu_food:
            menu_food = random_food()
        else:
            menu_snake.pop()
        screen.blit(pygame.transform.smoothscale(offscreen_surface, (WIDTH, HEIGHT)), (0, 0))
        pygame.display.flip()
        offscreen_surface.fill((0, 0, 0, 0))
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and allow_click:
                scaled_pos = (event.pos[0] * RENDER_W // WIDTH, event.pos[1] * RENDER_H // HEIGHT)
                if icon_rect.collidepoint(scaled_pos):
                    sound_on = not sound_on
                    if sound_on:
                        pygame.mixer.music.set_volume(1.0)
                    else:
                        pygame.mixer.music.set_volume(0.0)
                if menu_button_rect.collidepoint(scaled_pos):
                    return  # перейти в главное меню
        if not allow_click and pygame.time.get_ticks() - start_time > duration:
            allow_click = True

# Движение
# Основной игровой цикл
def run_game():
    global FPS
    global high_score
    FPS = difficulty_buttons[selected_difficulty]["fps"]

    snake = [(RENDER_W//2 - i * BLOCK_SIZE, RENDER_H//2) for i in range(6)]
    direction = (BLOCK_SIZE, 0)
    food = random_food(set(snake))
    score = 0
    apples_eaten = 0
    big_food = None
    plus_one_pos = None
    plus_one_start_time = None
    plus_one_duration = 2000
    plus_three_pos = None
    plus_three_start_time = None
    minus_one_pos = None
    minus_one_start_time = None
    poison = None
    poison_timer = pygame.time.get_ticks()
    poison_interval = 6000  # 6 секунд

    try:
        print('START GAME')
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print('QUIT EVENT')
                    pygame.quit()
                    sys.exit()

            if not snake:
                print('CRASH: snake is empty')
                pygame.quit()
                sys.exit()

            direction = get_new_direction(direction)
            head_x = (snake[0][0] + direction[0]) % RENDER_W
            head_y = (snake[0][1] + direction[1]) % RENDER_H
            head = (head_x, head_y)
            snake.insert(0, head)

            now = pygame.time.get_ticks()
            forbidden_for_poison = set(snake)
            forbidden_for_poison.add(food)
            if big_food:
                for dx in [0, BLOCK_SIZE]:
                    for dy in [0, BLOCK_SIZE]:
                        forbidden_for_poison.add((big_food[0]+dx, big_food[1]+dy))
            if poison is None or now - poison_timer > poison_interval:
                all_cells = [(x*BLOCK_SIZE, y*BLOCK_SIZE) for x in range(RENDER_W//BLOCK_SIZE) for y in range(RENDER_H//BLOCK_SIZE)]
                free_cells = [cell for cell in all_cells if cell not in forbidden_for_poison]
                if free_cells:
                    poison = random.choice(free_cells)
                else:
                    poison = None
                poison_timer = now
            if head == food:
                score += 1
                apples_eaten += 1
                forbidden_for_food = set(snake)
                forbidden_for_food.add(poison)
                if big_food:
                    for dx in [0, BLOCK_SIZE]:
                        for dy in [0, BLOCK_SIZE]:
                            forbidden_for_food.add((big_food[0]+dx, big_food[1]+dy))
                food = random_food(forbidden_for_food)
                plus_one_pos = (head_x + BLOCK_SIZE // 2, head_y)
                plus_one_start_time = pygame.time.get_ticks()
                if apples_eaten % 5 == 0 and big_food is None:
                    forbidden_for_big = set(snake)
                    forbidden_for_big.add(poison)
                    forbidden_for_big.add(food)
                    forbidden_for_big.add(food)
                    while True:
                        candidate = random_food(forbidden_for_big)
                        occupied_rects = [pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE) for x, y in snake]
                        big_rect = pygame.Rect(candidate[0], candidate[1], BLOCK_SIZE * 2, BLOCK_SIZE * 2)
                        food_rect = pygame.Rect(food[0], food[1], BLOCK_SIZE, BLOCK_SIZE)
                        if all(not r.colliderect(big_rect) for r in occupied_rects) and not big_rect.colliderect(food_rect):
                            big_food = candidate
                            break
            elif head == poison:
                score = max(0, score - 1)
                poison = None
                if len(snake) > 6:
                    snake.pop()
                minus_one_pos = (head_x + BLOCK_SIZE // 2, head_y)
                minus_one_start_time = pygame.time.get_ticks()
                snake.pop()
            elif big_food:
                head_rect = pygame.Rect(head_x, head_y, BLOCK_SIZE, BLOCK_SIZE)
                big_rect = pygame.Rect(big_food[0], big_food[1], BLOCK_SIZE * 2, BLOCK_SIZE * 2)
                if head_rect.colliderect(big_rect):
                    score += 3
                    big_food = None
                    plus_three_pos = (head_x + BLOCK_SIZE // 2, head_y)
                    plus_three_start_time = pygame.time.get_ticks()
                else:
                    snake.pop()
            else:
                snake.pop()

            if head in snake[1:]:
                show_game_over(score)
                return
            random.seed(42)
            draw_background()
            draw_snake_detailed(offscreen_surface, snake, direction)
            draw_food(food, offscreen_surface)
            if big_food:
                x, y = big_food
                center = (x + BLOCK_SIZE // 2, y + BLOCK_SIZE // 2)
                big_radius = BLOCK_SIZE - 2
                pygame.draw.circle(offscreen_surface, BLACK, center, big_radius + 1)
                pygame.draw.circle(offscreen_surface, RED, center, big_radius)
                pygame.draw.circle(offscreen_surface, WHITE, (center[0] - 10, center[1] - 10), 7)
                pygame.draw.line(offscreen_surface, (139, 69, 19), (center[0], center[1] - big_radius),
                                 (center[0], center[1] - big_radius - 12), 3)
                pygame.draw.circle(offscreen_surface, (0, 200, 0), (center[0] - 12, center[1] - big_radius - 10), 6)
            if poison:
                offscreen_surface.blit(klyaksa_img, (poison[0] + BLOCK_SIZE // 2 - klyaksa_size // 2, poison[1] + BLOCK_SIZE // 2 - klyaksa_size // 2))

            draw_score(score, offscreen_surface)
            # "+1"
            if plus_one_pos and plus_one_start_time:
                elapsed = pygame.time.get_ticks() - plus_one_start_time
                if elapsed < plus_one_duration:
                    y_offset = int((elapsed / plus_one_duration) * 30)
                    plus_one_text = font.render("+1", True, (0,255,0))
                    plus_one_shadow = font.render("+1", True, BLACK)
                    x = plus_one_pos[0] - plus_one_text.get_width() // 2
                    y = plus_one_pos[1] - y_offset
                    offscreen_surface.blit(plus_one_shadow, (x + 1, y + 1))
                    offscreen_surface.blit(plus_one_text, (x, y))
                else:
                    plus_one_pos = None
                    plus_one_start_time = None
            # "+3"
            if plus_three_pos and plus_three_start_time:
                elapsed = pygame.time.get_ticks() - plus_three_start_time
                if elapsed < plus_one_duration:
                    y_offset = int((elapsed / plus_one_duration) * 30)
                    plus_three_text = font.render("+3", True, (0,255,0))
                    plus_three_shadow = font.render("+3", True, BLACK)
                    x = plus_three_pos[0] - plus_three_text.get_width() // 2
                    y = plus_three_pos[1] - y_offset
                    offscreen_surface.blit(plus_three_shadow, (x + 1, y + 1))
                    offscreen_surface.blit(plus_three_text, (x, y))
                else:
                    plus_three_pos = None
                    plus_three_start_time = None
            # "-1"
            if minus_one_pos and minus_one_start_time:
                elapsed = pygame.time.get_ticks() - minus_one_start_time
                if elapsed < plus_one_duration:
                    y_offset = int((elapsed / plus_one_duration) * 30)
                    minus_one_text = font.render("-1", True, (255, 0, 0))
                    minus_one_shadow = font.render("-1", True, BLACK)
                    x = minus_one_pos[0] - minus_one_text.get_width() // 2
                    y = minus_one_pos[1] - y_offset
                    offscreen_surface.blit(minus_one_shadow, (x + 1, y + 1))
                    offscreen_surface.blit(minus_one_text, (x, y))
                else:
                    minus_one_pos = None
                    minus_one_start_time = None

            pygame.display.flip()
            screen.blit(pygame.transform.smoothscale(offscreen_surface, (WIDTH, HEIGHT)), (0, 0))
            offscreen_surface.fill((0, 0, 0, 0))
            clock.tick(FPS)
    except Exception as e:
        print('CRASH:', e)
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit()

def draw_text_with_outline(text, font, color, outline_color, pos, outline_width=2, target=None):
    if target is None:
        target = offscreen_surface
    base = font.render(text, True, color)
    outline = font.render(text, True, outline_color)
    x, y = pos
    for dx in range(-outline_width, outline_width+1):
        for dy in range(-outline_width, outline_width+1):
            if dx != 0 or dy != 0:
                target.blit(outline, (x+dx, y+dy))
    target.blit(base, (x, y))

# Главный цикл программы
if __name__ == "__main__":
    while True:
        show_main_menu()
        run_game()