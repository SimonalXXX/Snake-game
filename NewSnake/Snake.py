import pygame
import sys
import math
import random

# Настройки
WIDTH, HEIGHT = 960, 540  # окно в 2 раза меньше
RENDER_W, RENDER_H = 1920, 1080  # внутреннее качество
FPS = 144
SNAKE_INIT_LENGTH = 25  # увеличено в 5 раз
SNAKE_RADIUS = 12 * 1.5  # уменьшено в 2 раза относительно предыдущего значения
SNAKE_SPEED = 320  # пикселей в секунду
APPLE_RADIUS = SNAKE_RADIUS * 2  # уменьшено в 2 раза

class Apple:
    def __init__(self, radius, snake_segments):
        self.radius = radius
        self.position = self.random_position(snake_segments)
        # Вероятности для значений яблока
        values = [1,2,3,4,5,6,7,8,9,10]
        weights = [0.182,0.164,0.145,0.127,0.109,0.091,0.073,0.055,0.036,0.018]
        self.value = random.choices(values, weights=weights)[0]

    def random_position(self, snake_segments):
        margin = self.radius * 3
        while True:
            x = random.randint(margin, RENDER_W - margin)
            y = random.randint(margin, RENDER_H - margin)
            pos = (x, y)
            # Проверяем, не попадает ли яблоко под змею
            collision = False
            for seg in snake_segments:
                if math.hypot(seg[0] - x, seg[1] - y) < self.radius * 2:
                    collision = True
                    break
            if not collision:
                return pos

    def draw(self, surface, font):
        pygame.draw.circle(surface, (255, 0, 0), (int(self.position[0]), int(self.position[1])), self.radius)
        # Подбор размера шрифта под радиус яблока
        value_font_size = max(18, int(self.radius * 1.2))
        value_font = pygame.font.SysFont('arial', value_font_size, bold=True)
        value_text = value_font.render(f'+{self.value}', True, (255,255,255))
        text_rect = value_text.get_rect(center=(int(self.position[0]), int(self.position[1])))
        surface.blit(value_text, text_rect)

class Snake:
    def __init__(self, x, y, length, radius, speed):
        self.radius = radius
        self.speed = speed
        self.segments = []
        self.base_length = length
        self.direction = (1, 0)
        for i in range(length):
            self.segments.append((x - i * radius * 2, y))
        self.target_length = length
        self.red_waves = []  # список волн: (текущий_индекс, длина_волны)

    def set_direction_towards(self, target):
        head_x, head_y = self.segments[0]
        dx = target[0] - head_x
        dy = target[1] - head_y
        length = math.hypot(dx, dy)
        if length > 0:
            self.direction = (dx / length, dy / length)

    def update(self, dt):
        dx = self.direction[0] * self.speed * dt
        dy = self.direction[1] * self.speed * dt
        head_x, head_y = self.segments[0]
        new_head = (head_x + dx, head_y + dy)
        # Корректная телепортация головы
        new_head = (new_head[0] % RENDER_W, new_head[1] % RENDER_H)
        self.segments = [new_head] + self.segments
        if len(self.segments) > self.target_length:
            self.segments = self.segments[:self.target_length]
        for i in range(1, len(self.segments)):
            prev_x, prev_y = self.segments[i-1]
            x, y = self.segments[i]
            dist = math.hypot(prev_x - x, prev_y - y)
            if dist > self.radius * 2:
                angle = math.atan2(prev_y - y, prev_x - x)
                x = prev_x - math.cos(angle) * self.radius * 2
                y = prev_y - math.sin(angle) * self.radius * 2
                # Корректная телепортация сегментов
                x = x % RENDER_W
                y = y % RENDER_H
                self.segments[i] = (x, y)
        # Обновление красных волн
        for i in range(len(self.red_waves)):
            self.red_waves[i] = (self.red_waves[i][0] + 1, self.red_waves[i][1])
        # Удаляем волны, которые полностью ушли за хвост
        self.red_waves = [w for w in self.red_waves if w[0] < len(self.segments)]

    def add_red_wave(self, length=15):
        self.red_waves.append((0, length))

    def check_death(self):
        head = self.segments[0]
        head_int = (round(head[0]), round(head[1]))
        for seg in self.segments[2:]:
            seg_int = (round(seg[0]), round(seg[1]))
            if head_int == seg_int:
                return True
        return False

    def grow_tail(self, n):
        # Просто увеличиваем целевую длину
        self.target_length += n

    def reset(self):
        self.segments = []
        for i in range(self.base_length):
            self.segments.append((WIDTH // 2 - i * self.radius * 2, HEIGHT // 2))
        self.target_length = self.base_length
        self.direction = (1, 0)

    def head_collides_with(self, pos, radius):
        hx, hy = self.segments[0]
        return math.hypot(hx - pos[0], hy - pos[1]) < self.radius + radius

    def draw(self, surface):
        t = pygame.time.get_ticks() / 1000.0
        n = len(self.segments)
        for i, pos in enumerate(self.segments):
            is_red = False
            for wave_start, wave_len in self.red_waves:
                if wave_start <= i < wave_start + wave_len:
                    is_red = True
                    break
            if is_red:
                color = (255, 0, 0)
            else:
                hue = ((i / n) + t * 0.15) % 1.0
                color = hsv_to_rgb(hue, 1, 1)
            pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), int(self.radius))


# HSV to RGB helper
# h,s,v in [0,1], returns (r,g,b) in 0-255
def hsv_to_rgb(h, s, v):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r*255), int(g*255), int(b*255))


def main():
    print('STARTGAME')
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    offscreen_surface = pygame.Surface((RENDER_W, RENDER_H))
    pygame.display.set_caption('Snake 144Hz')
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('arial', 36)
    big_font = pygame.font.SysFont('arial', 120, bold=True)
    snake = Snake(RENDER_W // 2, RENDER_H // 2, SNAKE_INIT_LENGTH, SNAKE_RADIUS, SNAKE_SPEED)
    apple = Apple(APPLE_RADIUS, snake.segments)
    score = 0
    game_over = False
    while True:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print('CLOSED GAME')
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r or event.key == pygame.K_K:
                    print('STARTGAME')
                    snake = Snake(RENDER_W // 2, RENDER_H // 2, SNAKE_INIT_LENGTH, SNAKE_RADIUS, SNAKE_SPEED)
                    apple = Apple(APPLE_RADIUS, snake.segments)
                    score = 0
                    game_over = False
        if not game_over:
            # Движение к мышке
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Переводим координаты мыши в пространство offscreen_surface
            mouse_x = mouse_x * RENDER_W / WIDTH
            mouse_y = mouse_y * RENDER_H / HEIGHT
            snake.set_direction_towards((mouse_x, mouse_y))
            snake.update(dt)
            if snake.head_collides_with(apple.position, apple.radius):
                snake.grow_tail(apple.value * 5)
                score += apple.value
                apple = Apple(APPLE_RADIUS, snake.segments)
                snake.add_red_wave(15)
        offscreen_surface.fill((20, 20, 20))
        apple.draw(offscreen_surface, font)
        snake.draw(offscreen_surface)
        score_text = font.render(f'Счет: {score}', True, (255, 255, 255))
        offscreen_surface.blit(score_text, (20, 20))
        if game_over:
            over_text = big_font.render('ТЫ УМЕР', True, (255, 0, 0))
            over_rect = over_text.get_rect(center=(RENDER_W//2, RENDER_H//2))
            offscreen_surface.blit(over_text, over_rect)
            info_text = font.render('Нажмите R или К для рестарта', True, (255,255,255))
            info_rect = info_text.get_rect(center=(RENDER_W//2, RENDER_H//2+100))
            offscreen_surface.blit(info_text, info_rect)
        scaled = pygame.transform.smoothscale(offscreen_surface, (WIDTH, HEIGHT))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

if __name__ == '__main__':
    main()
