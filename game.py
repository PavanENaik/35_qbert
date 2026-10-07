import random
import pygame

WIDTH, HEIGHT, CUBE_W, CUBE_H = 720, 560, 72, 42
SIDE = 21
ROWS, TARGET = 7, 2
HOP_TIME, HOP_HEIGHT = 0.28, 26

CELLS = {(r, c) for r in range(ROWS) for c in range(r + 1)}

DEFAULT_PALETTE = [
    (90, 160, 220),
    (190, 120, 70),
    (100, 210, 140)
]

KEY_HOPS = {
    pygame.K_LEFT: (-1, -1),
    pygame.K_UP: (-1, 0),
    pygame.K_DOWN: (1, 0),
    pygame.K_RIGHT: (1, 1)
}


# TASK 2: Different cube colors for each level
def cube_palette(level):
    """Return a different 3-color palette for each level."""

    palettes = [
        [
            (90, 160, 220),
            (190, 120, 70),
            (100, 210, 140)
        ],
        [
            (120, 100, 220),
            (220, 100, 150),
            (100, 220, 190)
        ],
        [
            (220, 130, 80),
            (230, 180, 70),
            (120, 210, 100)
        ],
        [
            (80, 180, 220),
            (150, 100, 220),
            (240, 100, 100)
        ]
    ]

    return palettes[(level - 1) % len(palettes)]


# TASK 3:
# This function is implemented as a Game method below.
# It gives a 50-point bonus when a cube reaches its target.
# TASK 4: Bonus life every 1000 points
def bonus_life_threshold():
    """Return the score required for a bonus life."""
    return 1000


# TASK 1: Fixed pyramid projection
def cube_center(row, col):
    return pygame.Vector2(
        WIDTH / 2 + (col - row / 2) * CUBE_W,
        90 + row * CUBE_H
    )


def neighbors(row, col):
    return [
        (row - 1, col - 1),
        (row - 1, col),
        (row + 1, col),
        (row + 1, col + 1)
    ]


def shade(color, factor):
    return tuple(int(v * factor) for v in color)


class Hopper:
    def __init__(self, cell):
        self.cell, self.target, self.t, self.fall = cell, None, 0.0, None

    @property
    def busy(self):
        return self.target is not None or self.fall is not None

    def start(self, target):
        self.target, self.t = target, 0.0

    def update(self, dt):
        """Advance the hop; return the landing cell when a hop finishes."""

        if self.fall is not None:
            self.fall += 420 * dt
            return None

        if self.target is None:
            return None

        self.t += dt / HOP_TIME

        if self.t < 1:
            return None

        self.cell, self.target = self.target, None

        if self.cell not in CELLS:
            self.fall = 0.0
            return None

        return self.cell

    def pos(self):
        if self.target is None:
            base = cube_center(*self.cell)

            if self.fall is not None:
                base.y += self.fall

            return base

        start = cube_center(*self.cell)
        end = cube_center(*self.target)

        point = start.lerp(end, self.t)
        point.y -= HOP_HEIGHT * 4 * self.t * (1 - self.t)

        return point


class Game:
    def __init__(self):
        self.font = pygame.font.Font(None, 26)
        self.level, self.score, self.lives = 1, 0, 3
        self.reset()

    def reset(self, full=True):
        if full:
            self.level, self.score, self.lives = 1, 0, 3
            self.bonus_awarded = 0

        self.stages = {cell: 0 for cell in CELLS}
        self.state = "play"

        self.respawn()

    def respawn(self):
        self.player = Hopper((0, 0))
        self.coily, self.balls = None, []
        self.coily_timer, self.ball_timer, self.enemy_hop = 3.0, 2.0, 0.0

    # TASK 3: Called when a cube reaches its target stage
    def on_cube_completed(self, cell):
        # Give an additional 50 point bonus
        self.score += 50

    def paint(self, cell):
        if cell not in self.stages or self.stages[cell] >= TARGET:
            return

        self.stages[cell] += 1

        # Normal painting score
        self.score += 25

        # Call completion function only when target is reached
        if self.stages[cell] == TARGET:
            self.on_cube_completed(cell)

    def hop(self, key):
        if self.state != "play" or self.player.busy:
            return

        delta = KEY_HOPS[key]

        candidate = (
            self.player.cell[0] + delta[0],
            self.player.cell[1] + delta[1]
        )

        self.player.start(candidate)

    def move_enemies(self):
        if self.coily and not self.coily.busy:
            options = [
                n for n in neighbors(*self.coily.cell)
                if n in CELLS
            ]

            goal = cube_center(*self.player.cell)

            self.coily.start(
                min(
                    options,
                    key=lambda n: cube_center(*n).distance_squared_to(goal)
                )
            )

        for ball in self.balls:
            if not ball.busy:
                ball.start(
                    (
                        ball.cell[0] + 1,
                        ball.cell[1] + random.randint(0, 1)
                    )
                )

    def lose_life(self):
        self.lives -= 1

        if self.lives <= 0:
            self.state = "lose"
        else:
            self.respawn()

    def update(self, dt):
        if self.state != "play":
            return

        landed = self.player.update(dt)

        if landed:
            self.paint(landed)

        # TASK 4: Award bonus life every 1000 points
        threshold = bonus_life_threshold()

        if threshold and self.score // threshold > self.bonus_awarded:
            self.bonus_awarded = self.score // threshold
            self.lives += 1

        # Player falls off pyramid
        if self.player.fall is not None and self.player.fall > 260:
            self.lose_life()
            return

        # Create Coily
        self.coily_timer -= dt

        if self.coily is None and self.coily_timer <= 0:
            self.coily = Hopper((0, 0))

        # Create red balls
        self.ball_timer -= dt

        if self.ball_timer <= 0:
            self.balls.append(Hopper((0, 0)))
            self.ball_timer = 5.0

        # Move enemies
        self.enemy_hop -= dt

        if self.enemy_hop <= 0:
            self.enemy_hop = 0.35
            self.move_enemies()

        enemies = ([self.coily] if self.coily else []) + self.balls

        for enemy in enemies:
            enemy.update(dt)

        self.balls = [
            b for b in self.balls
            if b.fall is None or b.fall < 260
        ]

        # Enemy collision
        if self.player.target is None and self.player.fall is None:
            for enemy in enemies:
                if (
                    enemy.fall is None
                    and enemy.pos().distance_to(self.player.pos()) < 26
                ):
                    self.lose_life()
                    return

        # Level completed
        if all(stage >= TARGET for stage in self.stages.values()):
            self.score += 500
            self.state = "win"

    def draw_cube(self, screen, cell, colors):
        cx, cy = cube_center(*cell)

        top = [
            (cx, cy - CUBE_H / 2),
            (cx + CUBE_W / 2, cy),
            (cx, cy + CUBE_H / 2),
            (cx - CUBE_W / 2, cy)
        ]

        color = colors[self.stages[cell]]

        left = [
            top[3],
            top[2],
            (cx, cy + CUBE_H / 2 + SIDE),
            (cx - CUBE_W / 2, cy + SIDE)
        ]

        right = [
            top[1],
            top[2],
            (cx, cy + CUBE_H / 2 + SIDE),
            (cx + CUBE_W / 2, cy + SIDE)
        ]

        pygame.draw.polygon(
            screen,
            shade(colors[0], 0.45),
            left
        )

        pygame.draw.polygon(
            screen,
            shade(colors[0], 0.30),
            right
        )

        pygame.draw.polygon(
            screen,
            color,
            top
        )

        pygame.draw.polygon(
            screen,
            (240, 240, 240),
            top,
            1
        )

    def draw(self, screen):
        screen.fill((18, 20, 38))

        colors = cube_palette(self.level) or DEFAULT_PALETTE

        for cell in sorted(CELLS):
            self.draw_cube(screen, cell, colors)

        # Red balls
        for enemy in self.balls:
            pygame.draw.circle(
                screen,
                (230, 60, 60),
                enemy.pos() - (0, 12),
                9
            )

        # Coily
        if self.coily:
            pos = self.coily.pos() - (0, 14)

            pygame.draw.circle(
                screen,
                (170, 80, 220),
                pos,
                11
            )

            pygame.draw.circle(
                screen,
                (255, 255, 255),
                pos + (0, -2),
                3
            )

        # Player
        pos = self.player.pos() - (0, 14)

        pygame.draw.circle(
            screen,
            (250, 150, 40),
            pos,
            13
        )

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            pos + (-5, -3),
            3
        )

        pygame.draw.circle(
            screen,
            (255, 255, 255),
            pos + (5, -3),
            3
        )

        pygame.draw.circle(
            screen,
            (250, 90, 40),
            pos + (0, 6),
            5
        )

        # HUD
        hud = self.font.render(
            f"Score {self.score}  Lives {self.lives}  "
            f"Level {self.level}  R = reset",
            True,
            (240, 240, 240)
        )

        screen.blit(hud, (10, 8))

        # Game state message
        if self.state != "play":
            text = (
                "LEVEL CLEAR! Press Space"
                if self.state == "win"
                else "GAME OVER - Press R"
            )

            label = self.font.render(
                text,
                True,
                (255, 255, 120)
            )

            screen.blit(
                label,
                label.get_rect(
                    center=(WIDTH // 2, HEIGHT - 40)
                )
            )


def main():
    pygame.init()

    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT)
    )

    pygame.display.set_caption("Q*bert")

    clock = pygame.time.Clock()

    game = Game()

    running = True

    while running:
        dt = min(
            clock.tick(60) / 1000,
            0.05
        )

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:

                if event.key in KEY_HOPS:
                    game.hop(event.key)

                elif event.key == pygame.K_r:
                    game.reset()

                elif (
                    event.key == pygame.K_SPACE
                    and game.state == "win"
                ):
                    game.level += 1
                    game.reset(full=False)

        game.update(dt)
        game.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()