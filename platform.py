import os
import pygame
import pygame.locals as pygame_locals

WHITE = (255, 255, 255)

SURFACE_SZ = 480   # Desired physical surface size, in pixels.


# Tick time
TICKS = 60
TICK_TIME = 1/TICKS

# Global physics
AIR_RESISTANCE = 3
JUMP_ACC = 50000
GRAVITY = 100000/TICKS

# player characteristics
PLAYER_HEIGHT, PLAYER_WIDTH = 60, 30
PLAYER_COLOR = (255, 0, 0)  # (Red, Green, Blue) 0 - 255
MOVE_ACC = 1000


class Wall(pygame.sprite.Sprite):
    """ Wall the player can run into. """

    def __init__(self, x, y, width, height, bouncy=False):
        """ Constructor for the wall that the player can run into. """
        # Call the parent's constructor
        super().__init__()

        # Make a blue wall, of the size specified in the parameters
        self.image = pygame.Surface([width, height])
        self.image.fill(WHITE)

        # Make our top-left corner the passed-in location.
        self.rect = self.image.get_rect()
        self.rect.y = SURFACE_SZ - y
        self.rect.x = x
        self.bouncy = bouncy


class Player(pygame.sprite.Sprite):

    def __init__(self, name='Alex', xpos=0, ypos=None, width=PLAYER_WIDTH,
                 height=PLAYER_HEIGHT, platforms=[]):
        super().__init__()

        # init image
        self._width = width
        self._height = height

        self._lowest_y = SURFACE_SZ - self._height

        # self.image = pygame.Surface([self._width, self._height])
        this_dir = os.path.dirname(__file__)
        image_file = os.path.join(this_dir, 'player.png')
        image = pygame.image.load(image_file).convert()
        self.image = pygame.transform.scale(image, (self._width, self._height))

        # self.image.convert_alpha()
        # self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect()

        if ypos is None:
            ypos = self._lowest_y
        self.ypos = ypos

        self.name = name
        self.mass = 1

        self._xvel = 0
        self._yvel = 0

        self._check_bounds()

        self._xacc = 0
        self._yacc = 0

        self._platforms = platforms
        self._grounded = False
        self.alive = True
        self.gravity = GRAVITY

    @property
    def xpos(self):
        return self.rect.x

    @xpos.setter
    def xpos(self, x):
        self.rect.x = x

    @property
    def ypos(self):
        return self.rect.y

    @ypos.setter
    def ypos(self, y):
        self.rect.y = y

    @property
    def platforms(self):
        return self._platforms

    def update(self):
        """Update acceleration, velocity, position"""

        # account for "air resistance"
        self._xacc += -self._xvel*AIR_RESISTANCE
        self._yacc += -self._yvel*AIR_RESISTANCE

        self.xpos += self._xvel*TICK_TIME + 0.5*self._xacc*TICK_TIME**2
        self.ypos += self._yvel*TICK_TIME + 0.5*self._yacc*TICK_TIME**2

        # only change velocity if no colision
        self._xvel += self._xacc*TICK_TIME
        self._yvel += self._yacc*TICK_TIME

        self._grounded = self._check_colision()
        self._check_bounds()
        self._floor_velocity()

        # reset forces on character
        self._yacc = self.gravity
        self._xacc = 0

    def _check_colision(self):
        block_hit_list = pygame.sprite.spritecollide(self, self.platforms, False)
        bottom = False
        for block in block_hit_list:

            tl = block.rect.collidepoint(self.rect.topleft)
            tm = block.rect.collidepoint(self.rect.midtop)
            tr = block.rect.collidepoint(self.rect.topright)

            bl = block.rect.collidepoint(self.rect.bottomleft)
            bm = block.rect.collidepoint(self.rect.midbottom)
            br = block.rect.collidepoint(self.rect.bottomright)
            if any((bl, bm, br)):
                bottom = True

            rm = block.rect.collidepoint(self.rect.midright)
            lm = block.rect.collidepoint(self.rect.midleft)

            # any mid intersection means that side is always in colision
            if rm:
                self.rect.right = block.rect.left
                self._xvel = 0
            elif lm:
                self.rect.left = block.rect.right
                self._xvel = 0
            elif tm:
                self.rect.top = block.rect.bottom
                self._yvel = 0
            elif bm:
                self.rect.bottom = block.rect.top
                self.set_yvel_bounce(block)

            # must be a corner, check which one
            elif br:
                if self._yvel > 0 and self._xvel > 0:
                    # double colision, determine which is greater
                    vert_dist = abs(self.rect.bottom - block.rect.top)
                    horz_dist = abs(self.rect.right - block.rect.left)
                    if vert_dist < horz_dist:
                        self.rect.bottom = block.rect.top
                        self.set_yvel_bounce(block)
                    else:
                        self.rect.right = block.rect.left
                        self._xvel = 0
                elif self._yvel > 0:
                    self.rect.bottom = block.rect.top
                    self._yvel = 0
                elif self._xvel > 0:
                    self.rect.right = block.rect.left
                    self._xvel = 0

            elif bl:
                if self._yvel > 0 and self._xvel < 0:
                    # double colision, determine which is greater
                    vert_dist = abs(self.rect.bottom - block.rect.top)
                    horz_dist = abs(self.rect.left - block.rect.right)
                    if vert_dist < horz_dist:
                        self.rect.bottom = block.rect.top
                    else:
                        self.rect.left = block.rect.right
                elif self._yvel > 0:
                    self.rect.bottom = block.rect.top
                    self.set_yvel_bounce(block)
                elif self._xvel < 0:
                    self.rect.left = block.rect.right
                    self._xvel = 0

            elif tr:
                if self._yvel < 0 and self._xvel > 0:
                    # double colision, determine which is greater
                    vert_dist = abs(self.rect.top - block.rect.bottom)
                    horz_dist = abs(self.rect.right - block.rect.left)
                    if vert_dist < horz_dist:
                        self.rect.top = block.rect.bottom
                        self._yvel = 0
                    else:
                        self.rect.right = block.rect.left
                        self._xvel = 0
                elif self._yvel > 0:
                    self.rect.top = block.rect.bottom
                    self._yvel = 0
                elif self._xvel < 0:
                    self.rect.right = block.rect.left
                    self._xvel = 0

            elif tl:
                if self._yvel < 0 and self._xvel < 0:
                    # double colision, determine which is greater
                    vert_dist = abs(self.rect.top - block.rect.bottom)
                    horz_dist = abs(self.rect.left - block.rect.right)
                    if vert_dist < horz_dist:
                        self.rect.top = block.rect.bottom
                        self._yvel = 0
                    else:
                        self.rect.left = block.rect.right
                        self._xvel = 0
                elif self._yvel < 0:
                    self.rect.top = block.rect.bottom
                    self._yvel = 0
                elif self._xvel < 0:
                    self.rect.left = block.rect.right
                    self._xvel = 0

        # any bottom collision
        return bottom

    def set_yvel_bounce(self, block):
        if block.bouncy:
            self._yvel = -block.bouncy
            # self.gravity = -GRAVITY
        else:
            self._yvel = 0

    def _check_bounds(self):
        # do not allow to fall through map
        if self.xpos < 0:
            self.xpos = 0
            self._xvel = 0

        if self.ypos > self._lowest_y:
            self.alive = False
        elif self.ypos < -200:
            self.alive = False
            # self.ypos = self._lowest_y
            # self._yvel = 0

    def _floor_velocity(self):
        if abs(self._xvel) < 10:
            self._xvel = 0
        if abs(self._yvel) < 10:
            self._yvel = 0

    def jump(self):
        """Implement jump, but only if on the 'ground' (i.e. xpos == 0) """
        if self._grounded:
            self._yacc = -JUMP_ACC

    def left(self):
        """Left movement acceleration"""
        # if self._grounded:
        self._xacc = -MOVE_ACC

    def right(self):
        """Right movement acceleration"""
        # if self._grounded:
        self._xacc = MOVE_ACC

    def __repr__(self):
        txt = [f'Player {self.name}']
        txt.append(f'Position     ({self.xpos}, {self.ypos})')
        txt.append(f'Velocity     ({self._xvel}, {self._yvel})')
        txt.append(f'Acceleration ({self._xacc}, {self._yacc})')
        return '\n'.join(txt)


def run():
    """ Set up the game and run the main game loop """
    pygame.init()      # Prepare the pygame module for use
    game_font = pygame.font.SysFont(pygame.font.get_default_font(), 80)
    pygame.key.set_repeat(1, 10)

    wallheight = 20
    platforms = []
    platforms.append(Wall(0, 100, 100, wallheight))
    platforms.append(Wall(150, 200, 100, wallheight, bouncy=500))
    platforms.append(Wall(400, 120, 100, wallheight))

    # Create surface of (width, height), and its window.
    screen = pygame.display.set_mode((SURFACE_SZ, SURFACE_SZ))

    # initialize player
    player = Player('Alex', platforms=platforms, xpos=0,
                    ypos=SURFACE_SZ-100-PLAYER_HEIGHT)

    # list of 'sprites.'
    # The list is managed by a class called 'Group.'
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    all_sprites.add(platforms)

    clock = pygame.time.Clock()

    game_running = True
    while game_running:

        for event in pygame.event.get():
            if event.type == pygame_locals.QUIT:
                print('quitting...')
                game_running = False

            keys = pygame.key.get_pressed()
            if keys[pygame_locals.K_w]:
                player.jump()
            if keys[pygame_locals.K_a]:
                player.left()
            if keys[pygame_locals.K_d]:
                player.right()
            if keys[pygame_locals.K_q]:
                game_running = False

        # We draw everything from scratch on each frame.
        # So first fill everything with the background color
        screen.fill((0, 0, 0))

        if not player.alive:
            text_surface = game_font.render('You died.', True,
                                            (255, 255, 255))
            text_rect = text_surface.get_rect()
            text_rect.left = 10
            text_rect.top = 0
            screen.blit(text_surface, text_rect)

        else:
            all_sprites.update()
            all_sprites.draw(screen)

        # # Now the surface is ready, tell pygame to display it!
        pygame.display.update()

        # Limit to TICKS frames per second
        clock.tick(TICKS)

    pygame.quit()     # Once we leave the loop, close the window.


if __name__ == '__main__':
    run()
