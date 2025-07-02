import pygame
import random
import sys
import math


# Инициализация Pygame
pygame.init()
# Размеры окна и блоков
WIDTH, HEIGHT = 600, 400
BLOCK_SIZE = 20  # более мелкая детализация
FPS = 10



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

screen = pygame.display.set_mode((WIDTH, HEIGHT))
grass_img = pygame.image.load("assets/images/grass.jpg").convert()
grass_img = pygame.transform.scale(grass_img, (WIDTH, HEIGHT))
daisy_img = pygame.image.load("assets/images/daisy.png").convert_alpha()
daisy_img = pygame.transform.scale(daisy_img, (20, 20))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

high_score = 0

def random_food():
    return (
        random.randint(0, (WIDTH - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE,
        random.randint(0, (HEIGHT - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
    )

# Единый фон с ромашками и пятнами
def draw_background():
    screen.blit(grass_img, (0, 0))
    # Ромашки (текстура)
    for _ in range(random.randint(10, 20)):
        cx = random.randint(20, WIDTH - 20)
        cy = random.randint(20, HEIGHT - 20)
        screen.blit(daisy_img, (cx - 10, cy - 10))


# Отрисовка объектов
def draw_snake_detailed(screen, snake, direction):
    if not snake:
        return
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
    # Голова — Т-образная, цвет тела
    t_len = BLOCK_SIZE * 1.8
    t_w = BLOCK_SIZE * 0.6
    t_end = (cx + t_len * math.cos(math.radians(angle)),
             cy + t_len * math.sin(math.radians(angle)))
    t_start = (cx, cy)
    pygame.draw.line(screen, (139, 69, 19), t_start, t_end, int(t_w))
    # "Крышка" T
    cap_w = BLOCK_SIZE * 1.2
    cap_offset = BLOCK_SIZE * 0.6
    cap_center = (cx + cap_offset * math.cos(math.radians(angle)),
                  cy + cap_offset * math.sin(math.radians(angle)))
    perp_angle = angle + 90
    cap1 = (cap_center[0] + cap_w/2 * math.cos(math.radians(perp_angle)),
            cap_center[1] + cap_w/2 * math.sin(math.radians(perp_angle)))
    cap2 = (cap_center[0] - cap_w/2 * math.cos(math.radians(perp_angle)),
            cap_center[1] - cap_w/2 * math.sin(math.radians(perp_angle)))
    pygame.draw.line(screen, (139, 69, 19), cap1, cap2, int(BLOCK_SIZE * 0.5))
    # Глаза
    eye_dist = BLOCK_SIZE * 0.25
    eye_offset = BLOCK_SIZE * 0.7
    ex1 = cx + eye_offset * math.cos(math.radians(angle)) + eye_dist * math.cos(math.radians(angle+90))
    ey1 = cy + eye_offset * math.sin(math.radians(angle)) + eye_dist * math.sin(math.radians(angle+90))
    ex2 = cx + eye_offset * math.cos(math.radians(angle)) - eye_dist * math.cos(math.radians(angle+90))
    ey2 = cy + eye_offset * math.sin(math.radians(angle)) - eye_dist * math.sin(math.radians(angle+90))
    pygame.draw.circle(screen, WHITE, (int(ex1), int(ey1)), 2)
    pygame.draw.circle(screen, WHITE, (int(ex2), int(ey2)), 2)
    # Язык
    tongue_len = BLOCK_SIZE * 0.8
    tx = cx + (t_len + tongue_len) * math.cos(math.radians(angle))
    ty = cy + (t_len + tongue_len) * math.sin(math.radians(angle))
    pygame.draw.line(screen, RED, t_end, (tx, ty), 2)
    # Туловище (всё кроме головы)
    for i, (x, y) in enumerate(snake[1:], 1):
        # Сужение для последних 30%
        scale = 1.0
        if i >= int(len(snake) * 0.7):
            # scale от 1.0 до 0.6
            scale = 0.6 + 0.4 * (len(snake) - i) / (len(snake) * 0.3)
        body_rect = pygame.Rect(
            int(x + (BLOCK_SIZE - BLOCK_SIZE * scale) / 2),
            int(y + (BLOCK_SIZE - BLOCK_SIZE * scale) / 2),
            int(BLOCK_SIZE * scale),
            int(BLOCK_SIZE * scale)
        )
        pygame.draw.rect(screen, (139, 69, 19), body_rect)
        c = (x + BLOCK_SIZE // 2, y + BLOCK_SIZE // 2)
        # Пятнышки
        random.seed(x*10000+y)
        for j in range(2):
            ox = int(BLOCK_SIZE*0.5 * (random.random()-0.5))
            oy = int(BLOCK_SIZE*0.3 * (random.random()-0.5))
            spot_rect = pygame.Rect(c[0]+ox-3, c[1]+oy-2, 6, 4)
            pygame.draw.ellipse(screen, WHITE, spot_rect.inflate(2, 2))
            pygame.draw.ellipse(screen, BLACK, spot_rect)
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
        pygame.draw.polygon(screen, (139, 69, 19), [tip, base1, base2])
        for j in range(2):
            ox = int(BLOCK_SIZE*0.15 * (random.random()-0.5))
            oy = int(BLOCK_SIZE*0.15 * (random.random()-0.5))
            spot_rect = pygame.Rect(tcx+ox-1, tcy+oy-1, 3, 2)
            pygame.draw.ellipse(screen, BLACK, spot_rect)

def draw_food(food):
    x, y = food
    center = (x + BLOCK_SIZE // 2, y + BLOCK_SIZE // 2)
    radius = BLOCK_SIZE // 2 - 2

    # Яблоко (красный круг)
    pygame.draw.circle(screen, RED, center, radius)

    # Отблеск (маленький белый круг)
    pygame.draw.circle(screen, WHITE, (center[0] - 4, center[1] - 4), 3)

    # Ветка (коричневая линия)
    pygame.draw.line(screen, (139, 69, 19), (center[0], center[1] - radius),
                     (center[0], center[1] - radius - 6), 2)

    # Листик (зелёный круг)
    pygame.draw.circle(screen, (0, 200, 0), (center[0] - 5, center[1] - radius - 6), 3)

# Отрисовка счёта во время игры
def draw_score(score):
    text = font.render(f"Счёт: {score}", True, WHITE)
    text_rect = text.get_rect(topleft=(10, 10))
    # Draw black outline
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        screen.blit(font.render(f"Счёт: {score}", True, BLACK), text_rect.move(dx, dy))
    screen.blit(text, text_rect)

# Отрисовка лучшего счёта в главном меню
def draw_best_score():
    if high_score > 0:
        small_font = pygame.font.SysFont(None, int(36 * 0.7))
        text = small_font.render(f"Лучший счёт: {high_score}", True, WHITE)
        text_rect = text.get_rect(topleft=(10, 10))
        # Draw black outline
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            screen.blit(small_font.render(f"Лучший счёт: {high_score}", True, BLACK), text_rect.move(dx, dy))
        screen.blit(text, text_rect)

# Логика меню
# Главное меню
def show_main_menu():
    global selected_difficulty
    menu_snake = [(100 - i * BLOCK_SIZE, 100) for i in range(6)]
    menu_food = random_food()
    menu_dir = (BLOCK_SIZE, 0)

    # Кнопки сложности — теперь столбик, высота 80% от "Запустить"
    button_width = 160
    button_height = 40
    y_offset = 30
    start_y = y_offset + 60
    launch_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, start_y, button_width, button_height)
    diff_label_gap = 22
    diff_buttons_gap = 10
    diff_button_height = int(button_height * 0.8)
    diff_button_width = button_width
    diff_label_y = start_y + button_height + diff_label_gap
    diff_buttons_start_y = diff_label_y + 30
    difficulty_button_rects = []
    for i in range(len(difficulty_buttons)):
        rect = pygame.Rect(
            WIDTH // 2 - diff_button_width // 2,
            diff_buttons_start_y + i * (diff_button_height + diff_buttons_gap),
            diff_button_width, diff_button_height
        )
        difficulty_button_rects.append(rect)

    while True:
        # Фон
        random.seed(42)
        draw_background()
        # Змейка и еда
        draw_snake_detailed(screen, menu_snake, menu_dir)
        if not launch_button_rect.collidepoint(menu_food):
            draw_food(menu_food)

        # Заголовок
        title_text = font.render("Добро пожаловать в змейку", True, WHITE)
        shadow_text = font.render("Добро пожаловать в змейку", True, BLACK)
        screen.blit(shadow_text, (WIDTH // 2 - title_text.get_width() // 2 - 1, y_offset - 2))
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, y_offset))

        # Кнопка "Запустить"
        pygame.draw.ellipse(screen, (60, 60, 60), launch_button_rect.inflate(4, 4))
        pygame.draw.ellipse(screen, GRAY, launch_button_rect)
        button_text = font.render("Запустить", True, WHITE)
        text_rect = button_text.get_rect(center=launch_button_rect.center)
        shadow = font.render("Запустить", True, (30, 30, 30))
        screen.blit(shadow, text_rect.move(1, 1))
        screen.blit(button_text, text_rect)

        # "Уровень сложности"
        diff_label = font.render("Уровень сложности", True, WHITE)
        screen.blit(diff_label, (WIDTH // 2 - diff_label.get_width() // 2, diff_label_y))

        # Кнопки сложности (столбик)
        for i, rect in enumerate(difficulty_button_rects):
            if i == selected_difficulty:
                pygame.draw.ellipse(screen, WHITE, rect.inflate(4, 4))
                pygame.draw.ellipse(screen, WHITE, rect)
                label = font.render(difficulty_buttons[i]["label"], True, GRAY)
                label_rect = label.get_rect(center=rect.center)
                screen.blit(label, label_rect)
            else:
                pygame.draw.ellipse(screen, (60, 60, 60), rect.inflate(4, 4))
                pygame.draw.ellipse(screen, GRAY, rect)
                label = font.render(difficulty_buttons[i]["label"], True, WHITE)
                label_rect = label.get_rect(center=rect.center)
                screen.blit(label, label_rect)

        draw_best_score()

        # Анимация змейки
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
        next_pos = ((menu_snake[0][0] + dx) % WIDTH, (menu_snake[0][1] + dy) % HEIGHT)
        if next_pos in menu_snake:
            if dx != 0:
                alt_pos = ((menu_snake[0][0]) % WIDTH, (menu_snake[0][1] - BLOCK_SIZE) % HEIGHT)
                if alt_pos not in menu_snake:
                    dx, dy = 0, -BLOCK_SIZE
                else:
                    alt_pos = ((menu_snake[0][0]) % WIDTH, (menu_snake[0][1] + BLOCK_SIZE) % HEIGHT)
                    if alt_pos not in menu_snake:
                        dx, dy = 0, BLOCK_SIZE
                    else:
                        dx, dy = menu_dir
            elif dy != 0:
                alt_pos = ((menu_snake[0][0] - BLOCK_SIZE) % WIDTH, (menu_snake[0][1]) % HEIGHT)
                if alt_pos not in menu_snake:
                    dx, dy = -BLOCK_SIZE, 0
                else:
                    alt_pos = ((menu_snake[0][0] + BLOCK_SIZE) % WIDTH, (menu_snake[0][1]) % HEIGHT)
                    if alt_pos not in menu_snake:
                        dx, dy = BLOCK_SIZE, 0
                    else:
                        dx, dy = menu_dir
        menu_dir = (dx, dy)
        head_x = (menu_snake[0][0] + menu_dir[0]) % WIDTH
        head_y = (menu_snake[0][1] + menu_dir[1]) % HEIGHT
        head = (head_x, head_y)
        if head not in menu_snake:
            menu_snake.insert(0, head)
        if head == menu_food:
            while True:
                new_food = random_food()
                if new_food not in menu_snake:
                    menu_food = new_food
                    break
        else:
            menu_snake.pop()

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if launch_button_rect.collidepoint(event.pos):
                    return
                for i, rect in enumerate(difficulty_button_rects):
                    if rect.collidepoint(event.pos):
                        selected_difficulty = i

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
def show_game_over(score):
    global high_score
    if score > high_score:
        high_score = score
    # Фон
    random.seed(42)
    draw_background()
    # Текст
    game_over_text = font.render("Конец игры", True, RED)
    score_text = font.render(f"Score: {score}", True, WHITE)
    high_score_text = font.render(f"Best: {high_score}", True, WHITE)
    screen.blit(game_over_text, (WIDTH // 2 - 80, HEIGHT // 2 - 60))
    screen.blit(score_text, (WIDTH // 2 - 60, HEIGHT // 2 - 20))
    screen.blit(high_score_text, (WIDTH // 2 - 60, HEIGHT // 2 + 10))

    # Анимированная змейка (как в меню, 2 сек) и кнопка "На главный экран"
    menu_snake = [(100 - i * BLOCK_SIZE, 100) for i in range(6)]
    menu_food = random_food()
    menu_dir = (BLOCK_SIZE, 0)
    menu_button_rect = pygame.Rect(WIDTH // 2 - 80, HEIGHT - 60, 160, 40)
    start_time = pygame.time.get_ticks()
    duration = 2000
    while True:
        random.seed(42)
        draw_background()
        screen.blit(game_over_text, (WIDTH // 2 - 80, HEIGHT // 2 - 60))
        screen.blit(score_text, (WIDTH // 2 - 60, HEIGHT // 2 - 20))
        screen.blit(high_score_text, (WIDTH // 2 - 60, HEIGHT // 2 + 10))
        draw_snake_detailed(screen, menu_snake, menu_dir)
        if not pygame.Rect(WIDTH // 2 - 80, HEIGHT // 2 + 60, 160, 40).collidepoint(menu_food):
            draw_food(menu_food)
        # Кнопка "На главный экран"
        pygame.draw.ellipse(screen, (60, 60, 60), menu_button_rect.inflate(4, 4))
        pygame.draw.ellipse(screen, GRAY, menu_button_rect)
        menu_text = font.render("На главный экран", True, WHITE)
        text_rect = menu_text.get_rect(center=menu_button_rect.center)
        shadow = font.render("На главный экран", True, (30, 30, 30))
        screen.blit(shadow, text_rect.move(1, 1))
        screen.blit(menu_text, text_rect)
        # Движение змейки
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
        next_pos = ((menu_snake[0][0] + dx) % WIDTH, (menu_snake[0][1] + dy) % HEIGHT)
        if next_pos in menu_snake:
            if dx != 0:
                alt_pos = ((menu_snake[0][0]) % WIDTH, (menu_snake[0][1] - BLOCK_SIZE) % HEIGHT)
                if alt_pos not in menu_snake:
                    dx, dy = 0, -BLOCK_SIZE
                else:
                    alt_pos = ((menu_snake[0][0]) % WIDTH, (menu_snake[0][1] + BLOCK_SIZE) % HEIGHT)
                    if alt_pos not in menu_snake:
                        dx, dy = 0, BLOCK_SIZE
                    else:
                        dx, dy = menu_dir
            elif dy != 0:
                alt_pos = ((menu_snake[0][0] - BLOCK_SIZE) % WIDTH, (menu_snake[0][1]) % HEIGHT)
                if alt_pos not in menu_snake:
                    dx, dy = -BLOCK_SIZE, 0
                else:
                    alt_pos = ((menu_snake[0][0] + BLOCK_SIZE) % WIDTH, (menu_snake[0][1]) % HEIGHT)
                    if alt_pos not in menu_snake:
                        dx, dy = BLOCK_SIZE, 0
                    else:
                        dx, dy = menu_dir
        menu_dir = (dx, dy)
        head_x = (menu_snake[0][0] + menu_dir[0]) % WIDTH
        head_y = (menu_snake[0][1] + menu_dir[1]) % HEIGHT
        head = (head_x, head_y)
        if head not in menu_snake:
            menu_snake.insert(0, head)
        if head == menu_food:
            menu_food = random_food()
        else:
            menu_snake.pop()
        pygame.display.flip()
        clock.tick(FPS)
        # События: кнопка "На главный экран"
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if menu_button_rect.collidepoint(event.pos):
                    return  # перейти в главное меню
        # Время анимации змейки — после 2 сек разрешить вернуться
        if pygame.time.get_ticks() - start_time > duration:
            # теперь разрешено кликать по кнопке (но мы её уже обработали выше)
            pass

# Движение
# Основной игровой цикл
def run_game():
    global FPS
    FPS = difficulty_buttons[selected_difficulty]["fps"]

    snake = [(100 - i * BLOCK_SIZE, 100) for i in range(6)]
    direction = (BLOCK_SIZE, 0)
    food = random_food()
    score = 0
    apples_eaten = 0
    big_food = None
    plus_one_pos = None
    plus_one_start_time = None
    plus_one_duration = 2000
    plus_three_pos = None
    plus_three_start_time = None
    poison = None
    minus_one_pos = None
    minus_one_start_time = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        direction = get_new_direction(direction)
        head_x = (snake[0][0] + direction[0]) % WIDTH
        head_y = (snake[0][1] + direction[1]) % HEIGHT
        head = (head_x, head_y)
        snake.insert(0, head)

        # Генерация кляксы (poison) вне змейки, еды и большого яблока
        if poison is None:
            while True:
                p = random_food()
                occupied = p in snake or p == food
                big_collide = False
                if big_food:
                    big_rect = pygame.Rect(*big_food, BLOCK_SIZE*2, BLOCK_SIZE*2)
                    p_rect = pygame.Rect(*p, BLOCK_SIZE, BLOCK_SIZE)
                    big_collide = p_rect.colliderect(big_rect)
                if not occupied and not big_collide:
                    poison = p
                    break

        # Обычное яблоко
        if head == food:
            score += 1
            apples_eaten += 1
            while True:
                food_candidate = random_food()
                if food_candidate not in snake:
                    food = food_candidate
                    break
            plus_one_pos = (head_x + BLOCK_SIZE // 2, head_y)
            plus_one_start_time = pygame.time.get_ticks()
            # Каждые 5 — большое яблоко
            if apples_eaten % 5 == 0 and big_food is None:
                while True:
                    candidate = random_food()
                    occupied_rects = [pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE) for x, y in snake]
                    big_rect = pygame.Rect(candidate[0], candidate[1], BLOCK_SIZE * 2, BLOCK_SIZE * 2)
                    if all(not r.colliderect(big_rect) for r in occupied_rects):
                        big_food = candidate
                        break
        # Клякса (poison)
        elif head == poison:
            score = max(0, score - 1)
            poison = None
            if len(snake) > 6:
                snake.pop()
            minus_one_pos = (head_x + BLOCK_SIZE // 2, head_y)
            minus_one_start_time = pygame.time.get_ticks()
            snake.pop()
        # Большое яблоко
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
        draw_snake_detailed(screen, snake, direction)
        draw_food(food)
        # Большое яблоко
        if big_food:
            x, y = big_food
            center = (x + BLOCK_SIZE // 2, y + BLOCK_SIZE // 2)
            big_radius = BLOCK_SIZE - 2
            pygame.draw.circle(screen, BLACK, center, big_radius + 1)
            pygame.draw.circle(screen, RED, center, big_radius)
            # Отблеск
            pygame.draw.circle(screen, WHITE, (center[0] - 10, center[1] - 10), 7)
            # Ветка
            pygame.draw.line(screen, (139, 69, 19), (center[0], center[1] - big_radius),
                             (center[0], center[1] - big_radius - 12), 3)
            # Листик
            pygame.draw.circle(screen, (0, 200, 0), (center[0] - 12, center[1] - big_radius - 10), 6)
        # Клякса (poison)
        if poison:
            pygame.draw.circle(screen, (255, 255, 0), (poison[0] + BLOCK_SIZE // 2, poison[1] + BLOCK_SIZE // 2), BLOCK_SIZE // 2 - 2)

        draw_score(score)
        # "+1"
        if plus_one_pos and plus_one_start_time:
            elapsed = pygame.time.get_ticks() - plus_one_start_time
            if elapsed < plus_one_duration:
                y_offset = int((elapsed / plus_one_duration) * 30)
                plus_one_text = font.render("+1", True, WHITE)
                plus_one_shadow = font.render("+1", True, BLACK)
                x = plus_one_pos[0] - plus_one_text.get_width() // 2
                y = plus_one_pos[1] - y_offset
                screen.blit(plus_one_shadow, (x + 1, y + 1))
                screen.blit(plus_one_text, (x, y))
            else:
                plus_one_pos = None
                plus_one_start_time = None
        # "+3"
        if plus_three_pos and plus_three_start_time:
            elapsed = pygame.time.get_ticks() - plus_three_start_time
            if elapsed < plus_one_duration:
                y_offset = int((elapsed / plus_one_duration) * 30)
                plus_three_text = font.render("+3", True, WHITE)
                plus_three_shadow = font.render("+3", True, BLACK)
                x = plus_three_pos[0] - plus_three_text.get_width() // 2
                y = plus_three_pos[1] - y_offset
                screen.blit(plus_three_shadow, (x + 1, y + 1))
                screen.blit(plus_three_text, (x, y))
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
                screen.blit(minus_one_shadow, (x + 1, y + 1))
                screen.blit(minus_one_text, (x, y))
            else:
                minus_one_pos = None
                minus_one_start_time = None

        pygame.display.flip()
        clock.tick(FPS)

# Главный цикл программы
while True:
    show_main_menu()
    run_game()