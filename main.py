
import pygame
import random
import math
import os
import json

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1280, 720
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ARKANOID: HELLBREAK EDITION")

clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (10, 10, 15)
RED = (255, 50, 50)
DARK_RED = (120, 0, 0)
ORANGE = (255, 120, 0)
YELLOW = (255, 200, 0)

font = pygame.font.SysFont("Consolas", 28, bold=True)
small_font = pygame.font.SysFont("Consolas", 20, bold=True)
big_font = pygame.font.SysFont("Consolas", 72, bold=True)
title_font = pygame.font.SysFont("Consolas", 96, bold=True)

SAVE_FILE = "highscore.json"

def load_sound(path):
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except:
            return None
    return None

hit_sound = load_sound("hit.wav")
brick_sound = load_sound("brick.wav")
lose_sound = load_sound("lose.wav")
click_sound = load_sound("click.wav")

def play_music(path):
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
        except:
            pass

def load_highscore():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f).get("highscore", 0)
        except:
            return 0
    return 0

def save_highscore(score):
    with open(SAVE_FILE, "w") as f:
        json.dump({"highscore": score}, f)

highscore = load_highscore()

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.life = random.randint(20, 40)
        self.size = random.randint(3, 7)
        self.speed_x = random.uniform(-4, 4)
        self.speed_y = random.uniform(-4, 4)

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        self.size *= 0.95

    def draw(self, surface):
        if self.life > 0 and self.size > 0:
            pygame.draw.circle(
                surface,
                self.color,
                (int(self.x), int(self.y)),
                max(1, int(self.size))
            )

class Button:
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        color = RED if hovered else DARK_RED

        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, WHITE, self.rect, 3, border_radius=12)

        txt = font.render(self.text, True, WHITE)

        surface.blit(
            txt,
            (
                self.rect.centerx - txt.get_width() // 2,
                self.rect.centery - txt.get_height() // 2
            )
        )

    def clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    if click_sound:
                        click_sound.play()
                    return True
        return False

class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.rect = pygame.Rect(WIDTH // 2, HEIGHT // 2, 18, 18)
        self.speed_x = random.choice([-6, 6])
        self.speed_y = -6

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

        if self.rect.left <= 0:
            self.rect.left = 0
            self.speed_x *= -1

        if self.rect.right >= WIDTH:
            self.rect.right = WIDTH
            self.speed_x *= -1

        if self.rect.top <= 0:
            self.rect.top = 0
            self.speed_y *= -1

    def draw(self, surface):
        pygame.draw.ellipse(surface, WHITE, self.rect)

class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - 80, HEIGHT - 60, 160, 20)

    def move(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= 12

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += 12

        mouse_x = pygame.mouse.get_pos()[0]
        self.rect.centerx += (mouse_x - self.rect.centerx) * 0.15

        if self.rect.left < 0:
            self.rect.left = 0

        if self.rect.right > WIDTH:
            self.rect.right = WIDTH

    def draw(self, surface):
        glow = pygame.Rect(
            self.rect.x - 8,
            self.rect.y - 8,
            self.rect.width + 16,
            self.rect.height + 16
        )

        pygame.draw.rect(surface, DARK_RED, glow, border_radius=16)
        pygame.draw.rect(surface, RED, self.rect, border_radius=12)

class Bonus:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.speed = 4
        self.type = random.choice(["expand", "score", "multiball"])

    def move(self):
        self.rect.y += self.speed

    def draw(self, surface):
        color = YELLOW

        if self.type == "expand":
            color = ORANGE

        if self.type == "multiball":
            color = RED

        pygame.draw.rect(surface, color, self.rect, border_radius=8)

def create_level(level):
    bricks = []

    rows = min(8, 3 + level)
    cols = 12

    for row in range(rows):
        for col in range(cols):

            hp = random.choice([1, 1, 2, 2, 3])

            brick = {
                "rect": pygame.Rect(
                    col * 96 + 55,
                    row * 40 + 80,
                    85,
                    28
                ),
                "hp": hp,
                "color": (
                    min(255, 120 + hp * 40),
                    random.randint(20, 70),
                    random.randint(20, 60)
                )
            }

            bricks.append(brick)

    return bricks

def reset_game():
    global paddle, balls, particles, bonuses
    global score, lives, level, bricks
    global shake, flash, trail

    paddle = Paddle()
    balls = [Ball()]
    particles = []
    bonuses = []
    trail = []

    score = 0
    lives = 3
    level = 1

    bricks = create_level(level)

    shake = 0
    flash = 0

reset_game()

menu = True
paused = False
game_over = False
victory = False
running = True

play_music("menu.mp3")

start_button = Button("START GAME", WIDTH // 2 - 160, 320, 320, 80)
quit_button = Button("EXIT", WIDTH // 2 - 160, 430, 320, 80)
resume_button = Button("RESUME", WIDTH // 2 - 160, 320, 320, 80)
menu_button = Button("MAIN MENU", WIDTH // 2 - 160, 430, 320, 80)

while running:

    clock.tick(FPS)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if menu:

            if start_button.clicked(event):
                menu = False
                game_over = False
                victory = False
                reset_game()
                play_music("87.mp3")

            if quit_button.clicked(event):
                running = False

        elif paused:

            if resume_button.clicked(event):
                paused = False

            if menu_button.clicked(event):
                paused = False
                menu = True
                play_music("menu.mp3")

        else:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    paused = True

                if event.key == pygame.K_r:
                    if game_over or victory:
                        reset_game()
                        game_over = False
                        victory = False

    if not menu and not paused and not game_over and not victory:

        paddle.move()

        for ball in balls[:]:

            ball.move()

            trail.append((ball.rect.centerx, ball.rect.centery))

            if len(trail) > 20:
                trail.pop(0)

            if ball.rect.colliderect(paddle.rect):

                if ball.speed_y > 0:

                    if hit_sound:
                        hit_sound.play()

                    offset = (
                        ball.rect.centerx - paddle.rect.centerx
                    ) / (paddle.rect.width // 2)

                    ball.speed_x = int(offset * 10)

                    if ball.speed_x == 0:
                        ball.speed_x = random.choice([-4, 4])

                    ball.speed_y *= -1

                    shake = 5

            for brick in bricks[:]:

                if ball.rect.colliderect(brick["rect"]):

                    if brick_sound:
                        brick_sound.play()

                    ball.speed_y *= -1

                    brick["hp"] -= 1

                    shake = 10
                    flash = 4

                    for _ in range(15):
                        particles.append(
                            Particle(
                                brick["rect"].centerx,
                                brick["rect"].centery,
                                brick["color"]
                            )
                        )

                    if brick["hp"] <= 0:

                        score += 10

                        if random.randint(1, 100) <= 20:
                            bonuses.append(
                                Bonus(
                                    brick["rect"].centerx,
                                    brick["rect"].centery
                                )
                            )

                        bricks.remove(brick)

                    break

            if ball.rect.top > HEIGHT:

                if ball in balls:
                    balls.remove(ball)

        if len(balls) == 0:

            if lose_sound:
                lose_sound.play()

            lives -= 1

            if lives <= 0:

                game_over = True

                if score > highscore:
                    highscore = score
                    save_highscore(highscore)

            else:
                balls.append(Ball())

        for bonus in bonuses[:]:

            bonus.move()

            if bonus.rect.colliderect(paddle.rect):

                if bonus.type == "expand":

                    paddle.rect.width += 40

                    if paddle.rect.width > 320:
                        paddle.rect.width = 320

                elif bonus.type == "score":
                    score += 100

                elif bonus.type == "multiball":

                    for _ in range(2):

                        new_ball = Ball()

                        new_ball.rect.center = bonus.rect.center

                        new_ball.speed_x = random.choice([-7, -5, 5, 7])

                        balls.append(new_ball)

                bonuses.remove(bonus)

            elif bonus.rect.top > HEIGHT:
                bonuses.remove(bonus)

        for particle in particles[:]:

            particle.update()

            if particle.life <= 0:
                particles.remove(particle)

        if len(bricks) == 0:

            level += 1

            if level > 6:

                victory = True

                if score > highscore:
                    highscore = score
                    save_highscore(highscore)

            else:

                bricks = create_level(level)

                balls = [Ball()]

    offset_x = random.randint(-shake, shake) if shake > 0 else 0
    offset_y = random.randint(-shake, shake) if shake > 0 else 0

    if shake > 0:
        shake -= 1

    screen.fill(BLACK)

    for y in range(0, HEIGHT, 40):

        pulse = math.sin(pygame.time.get_ticks() * 0.002 + y * 0.02)

        color = (
            20 + int(pulse * 20),
            0,
            0
        )

        pygame.draw.rect(screen, color, (0, y, WIDTH, 40))

    if menu:

        pulse = abs(math.sin(pygame.time.get_ticks() * 0.003))

        title_color = (
            255,
            50 + int(pulse * 120),
            50 + int(pulse * 120)
        )

        title = title_font.render("HELLBREAK", True, title_color)

        screen.blit(
            title,
            (
                WIDTH // 2 - title.get_width() // 2,
                130
            )
        )

        subtitle = font.render(
            "ARKANOID DELUXE EDITION",
            True,
            WHITE
        )

        screen.blit(
            subtitle,
            (
                WIDTH // 2 - subtitle.get_width() // 2,
                250
            )
        )

        hs_text = font.render(
            f"HIGH SCORE: {highscore}",
            True,
            ORANGE
        )

        screen.blit(
            hs_text,
            (
                WIDTH // 2 - hs_text.get_width() // 2,
                580
            )
        )

        start_button.draw(screen)
        quit_button.draw(screen)

    else:

        for i, pos in enumerate(trail):

            alpha = i / len(trail)

            size = int(14 * alpha)

            pygame.draw.circle(
                screen,
                (255, 80, 80),
                pos,
                max(2, size)
            )

        for brick in bricks:

            pygame.draw.rect(
                screen,
                brick["color"],
                brick["rect"],
                border_radius=8
            )

            pygame.draw.rect(
                screen,
                WHITE,
                brick["rect"],
                2,
                border_radius=8
            )

            hp_text = small_font.render(
                str(brick["hp"]),
                True,
                WHITE
            )

            screen.blit(
                hp_text,
                (
                    brick["rect"].centerx - hp_text.get_width() // 2,
                    brick["rect"].centery - hp_text.get_height() // 2
                )
            )

        for particle in particles:
            particle.draw(screen)

        for bonus in bonuses:
            bonus.draw(screen)

        for ball in balls:
            ball.draw(screen)

        paddle.draw(screen)

        ui = font.render(
            f"SCORE: {score}   LIVES: {lives}   LEVEL: {level}",
            True,
            WHITE
        )

        screen.blit(ui, (20, 20))

        hs = font.render(
            f"HIGH SCORE: {highscore}",
            True,
            ORANGE
        )

        screen.blit(hs, (900, 20))

        pause_hint = small_font.render(
            "ESC = PAUSE",
            True,
            WHITE
        )

        screen.blit(pause_hint, (20, 60))

        if paused:

            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)

            screen.blit(overlay, (0, 0))

            txt = big_font.render("PAUSED", True, RED)

            screen.blit(
                txt,
                (
                    WIDTH // 2 - txt.get_width() // 2,
                    200
                )
            )

            resume_button.draw(screen)
            menu_button.draw(screen)

        if game_over:

            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)

            screen.blit(overlay, (0, 0))

            txt = big_font.render("GAME OVER", True, RED)

            screen.blit(
                txt,
                (
                    WIDTH // 2 - txt.get_width() // 2,
                    220
                )
            )

            restart = font.render(
                "PRESS R TO RESTART",
                True,
                WHITE
            )

            screen.blit(
                restart,
                (
                    WIDTH // 2 - restart.get_width() // 2,
                    340
                )
            )

        if victory:

            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)

            screen.blit(overlay, (0, 0))

            txt = big_font.render("YOU WIN", True, ORANGE)

            screen.blit(
                txt,
                (
                    WIDTH // 2 - txt.get_width() // 2,
                    220
                )
            )

            restart = font.render(
                "PRESS R TO PLAY AGAIN",
                True,
                WHITE
            )

            screen.blit(
                restart,
                (
                    WIDTH // 2 - restart.get_width() // 2,
                    340
                )
            )

    if flash > 0:

        flash_surface = pygame.Surface((WIDTH, HEIGHT))
        flash_surface.set_alpha(40)
        flash_surface.fill(RED)

        screen.blit(flash_surface, (0, 0))

        flash -= 1

    temp = screen.copy()

    screen.fill(BLACK)

    screen.blit(temp, (offset_x, offset_y))

    pygame.display.flip()

pygame.quit()
