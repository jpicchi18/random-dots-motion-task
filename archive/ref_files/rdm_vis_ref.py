
import pygame, sys

pygame.init()

monitor = pygame.display.Info()
screen = pygame.display.set_mode((monitor.current_w, monitor.current_h))
pygame.display.set_caption('RDM Task')

# Set our color constants
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)

# Specified field position
screen_center = pygame.Rect((0,0),(monitor.current_w, monitor.current_h)).center


class Field():
    def __init__(self, shape, pos, radius):
        self.shape = shape
        self.pos = pos
        self.image = pygame.Surface([radius * 2, radius * 2]).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.radius = radius
    def get_fieldsurface(self):
        return self.image
    def get_fieldrect(self):
        return self.rect
    def draw(self):
        if self.shape == 'circle':
            pygame.draw.circle(screen, BLACK, self.rect.center, self.radius)
        elif self.shape == 'square':
            pygame.draw.rect(screen, BLACK, self.rect)

class Dot(pygame.sprite.Sprite):
    # This code gets executed as soon as we create a new instance
    def __init__(self, color, radius, speed, field):
        pygame.sprite.Sprite.__init__(self)
        self.color = color
        self.radius = radius
        # x = dist from left of screen ; y = dist from top of screen
        # 3rd param = width ; 4th param = height
        self.image = pygame.Surface([radius * 2, radius * 2]).convert_alpha()
        self.rect = self.image.get_rect()
        self.speed = [speed, speed]
        self.field = field

    # Update our game state by moving and bouncing if needed
    def update(self):
        self.rect = self.rect.move(self.speed)
        if self.rect.right >= screen.get_width() or self.rect.left <= 0:
            self.speed[0] = -self.speed[0]
        if self.rect.top <= 0 or self.rect.bottom >= screen.get_height():
            self.speed[1] = -self.speed[1]

    # Draw our Dot to the screen
    def draw(self):
        pygame.draw.circle(screen, self.color, self.rect.center, self.radius)


dots_field = Field('circle', screen_center, 300)
# exp_dots = Dot(WHITE, 30, 30, dots_field
dots_arr = pygame.sprite.Group()
for i in range(10):
    dots_arr.add(Dot((255,255,i*20), 30, (i*10), dots_field))



# Task loop
while True:

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Update game state
    for dot in dots_arr.sprites():
        dot.update()
    # exp_dots.update()
    # Draw screen
    screen.fill(GRAY)
    dots_field.draw()
    # exp_dots.draw()
    for dot in dots_arr.sprites():
        dot.draw()
    pygame.display.update()
