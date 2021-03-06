from math import sin, cos, degrees
from os import path, environ
from random import choice, randrange, randint
from sys import exit

import pygame as pg

import gfx
import helper_functions
import player
import snd
from chroma import BLACK, WHITE
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, FONT_SIZE

# Macros
SCREEN_CENTER = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)


class Stars(pg.sprite.Sprite):
    MAX_STARS = 100
    color = (0, 0, 0)

    def __init__(self):
        self.stars = []
        for i in range(self.MAX_STARS):
            star = [randrange(0, gfx.screen.get_width() - 1),
                    randrange(0, gfx.screen.get_height() - 1),
                    choice([1, 2, 3])]
            self.stars.append(star)

    def render(self):
        for star in self.stars:
            star[1] += star[2]
            if star[1] >= gfx.screen.get_height():
                star[1] = 0
                star[0] = randrange(0, SCREEN_WIDTH)
                star[2] = choice([1, 2, 3])

            if star[2] == 1:
                self.color = (100, 100, 100)
            elif star[2] == 2:
                self.color = (190, 190, 190)
            elif star[2] == 3:
                self.color = (255, 255, 255)

            gfx.screen.fill(self.color, (star[0], star[1], star[2], star[2]))


class Bullet(pg.sprite.Sprite):
    def __init__(self, x, y, image):
        pg.sprite.Sprite.__init__(self)

        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.size = (self.rect.x, self.rect.y)
        self.dx = 0
        self.dy = 0

    def update(self):
        x, y = self.rect.center
        x += self.dx
        y += self.dy
        self.rect.center = x, y

        if y <= 0:
            self.kill()

    def on_hit(self):
        s = gfx.screen.blit(gfx.img_hit, (self.rect.centerx - gfx.img_hit.get_width() / 2, self.rect.y))
        pg.display.update(s)


class PowerUp(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.images = []
        self.images.append(gfx.load_image("POWERUP/powerup_a.png"))
        self.images.append(gfx.load_image("POWERUP/powerup_b.png"))
        self.images.append(gfx.load_image("POWERUP/powerup_c.png"))
        self.next_anim_frame = 0
        self.index = 0
        self.image = self.images[self.index]
        self.rect = pg.Rect(0, 0, 40, 40)
        self.rect.x = randrange(40, SCREEN_WIDTH - 40)
        self.rect.y = 1

    def update(self):
        self.next_anim_frame += 1
        if self.next_anim_frame >= 10:
            self.index += 1
            self.next_anim_frame = 0
            if self.index >= len(self.images):
                self.index = 0

            self.image = self.images[self.index]

        self.rect.y += 2

    def on_pickup(self):
        snd.load_sound("powerup.wav")
        self.kill()


class EnemyFighter(pg.sprite.Sprite):
    image = None
    HEALTH = 2
    BULLETS_MAX = 1
    allBullets = pg.sprite.Group()
    spawn_areas = [50, 100, 200, 300, 400, 500, 600, 700, 750]

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.image = gfx.img_fighter
        self.rect = self.image.get_rect()
        self.rect.x = choice(self.spawn_areas)
        self.rect.y = 0
        self.dx = 0
        self.dy = 3
        self.spawn_time = pg.time.get_ticks()
        self.bullets = pg.sprite.Group()
        self.has_shot = False
        self.is_hit = False
        self.change = 0
        self.angle = 0

    def movement(self):
        if self.rect.bottom > 300:
            self.dy = 2

        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.kill()

        if self.has_shot:
            self.dy = 4
            if self.rect.centerx > SCREEN_WIDTH / 2:
                self.change += .1
            else:
                self.change -= .1

        self.rect.x += self.dx + self.change
        self.rect.y += self.dy

        self.angle += degrees(self.change) / 180

    def update(self):
        if self.is_hit:
            self.image = gfx.img_fighter_hit
            pg.display.update(self.rect)
            self.is_hit = False
        else:
            self.image = gfx.img_fighter

        if self.rect.y >= SCREEN_HEIGHT:
            self.kill()
        else:
            self.movement()

        if self.HEALTH <= 0:
            self.die()

        for bullet in self.allBullets:
            bullet.image = choice([gfx.img_enemy_shot_a, gfx.img_enemy_shot_b])

        self.image = pg.transform.rotate(self.image, self.angle)

    def shoot(self, target):
        for bullet in range(self.BULLETS_MAX):
            new_bullet = Bullet(self.rect.centerx, self.rect.bottom, gfx.img_enemy_shot_a)
            new_bullet.dx = 5 * cos(helper_functions.calc_angle(self, target))
            new_bullet.dy = 5 * sin(helper_functions.calc_angle(self, target))
            self.allBullets.add(new_bullet)
            snd.load_sound("enemy_shoot.wav")
        self.has_shot = True

    def die(self):
        snd.load_sound("explode.wav")
        self.image = gfx.img_explosion
        s = gfx.screen.blit(self.image, (self.rect.x - 40, self.rect.y - 40))
        pg.display.update(s)
        self.kill()


class EnemyFrigate(pg.sprite.Sprite):
    image = None
    HEALTH = 50
    MAX_SHOTS = 3

    allBullets = pg.sprite.Group()

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.spawn_delay = 0
        self.image = gfx.img_frigate
        self.rect = self.image.get_rect()
        self.size = self.image.get_size()
        self.rect.x = 0
        self.rect.right = 0
        self.rect.bottom = 0
        self.dx = 1
        self.dy = 0
        self.is_hit = False

    def update(self):
        if self.is_hit:
            self.image = gfx.img_frigate_hit
            self.is_hit = False
            if self.HEALTH <= 0:
                self.die()
        else:
            self.image = gfx.img_frigate

        self.rect.x += self.dx

    def shoot(self):
        missile = Bullet(self.rect.centerx, self.rect.bottom, gfx.img_missile)
        missile.image = pg.transform.rotate(missile.image, 180)
        missile.dy = 4
        self.allBullets.add(missile)

    def die(self):
        snd.load_sound("explode.wav")
        self.image = gfx.img_explosion_final
        self.image = pg.transform.scale(self.image, (300, 300))
        s = gfx.screen.blit(self.image, (self.rect.x - 50, self.rect.y - 120))
        pg.display.update(s)
        self.kill()


class EnemyCruiser(pg.sprite.Sprite):
    image = None
    HEALTH = 1000
    allBullets = pg.sprite.Group()

    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.image = gfx.img_cruiser
        self.rect = self.image.get_rect()
        self.size = self.image.get_size()
        self.rect.x = (SCREEN_WIDTH / 2) - (self.size[0] / 2)
        self.center = (self.rect.x + 100, self.rect.y + 270)
        self.rect.bottom = 0
        self.dx = 0
        self.dy = 1
        self.is_hit = False
        self.charging = False
        self.firing = False
        self.has_shot = False
        self.next_shot = 0
        self.charge = 0
        self.duration = 0
        self.beamtime = 0
        self.new_pos = "middle_to_left"

    def update(self):
        if self.is_hit:
            self.image = gfx.img_cruiser_hit
            self.is_hit = False
            if self.HEALTH < 0:
                self.die()
        else:
            self.image = gfx.img_cruiser

        if not (self.charging or self.firing) and self.rect.bottom == SCREEN_HEIGHT / 2:
            self.dy = 0
            self.charge = 0
            self.duration = 0
            self.next_shot += 1
            if self.next_shot >= 250:
                self.charging = True
                self.next_shot = 0

        if self.charging:
            self.has_shot = False
            self.firing = False
            self.charge += 1
            snd.load_sound("charging.wav")
            if self.charge >= 150:
                self.firing = True

        if self.firing:
            self.charging = False
            self.image = gfx.img_cruiser_firing
            self.beamtime += 1
            if self.beamtime >= 5:
                self.duration += 1
                self.fire_beam()
                self.beamtime = 0
                if self.duration >= 20:
                    self.image = gfx.img_cruiser
                    self.has_shot = True
                    self.firing = False

        if self.has_shot and not self.firing:
            # Move to new position based on last location
            if self.new_pos == "middle_to_left":
                if self.rect.left > 100:
                    self.dx = -1
                else:
                    self.dx = 0
                    self.new_pos = "left_to_middle"
                    self.has_shot = False

                if self.HEALTH < 500 and self.rect.centerx % 10 == 0:
                    self.fire_shots()

            elif self.new_pos == "left_to_middle":
                if self.rect.centerx < SCREEN_CENTER[0]:
                    self.dx = 1

                else:
                    self.dx = 0
                    self.new_pos = "middle_to_right"
                    self.has_shot = False

                if self.HEALTH < 500 and self.rect.centerx % 10 == 0:
                    self.fire_shots()

            elif self.new_pos == "middle_to_right":
                if self.rect.right < SCREEN_WIDTH - 100:
                    self.dx = 1

                else:
                    self.dx = 0
                    self.new_pos = "right_to_middle"
                    self.has_shot = False

                if self.HEALTH < 500 and self.rect.centerx % 10 == 0:
                    self.fire_shots()

            elif self.new_pos == "right_to_middle":
                if self.rect.centerx > SCREEN_CENTER[0]:
                    self.dx = -1

                else:
                    self.dx = 0
                    self.new_pos = "middle_to_left"
                    self.has_shot = False

                if self.HEALTH < 500 and self.rect.centerx % 10 == 0:
                    self.fire_shots()

        if self.rect.left > 0 and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.dx
            self.rect.y += self.dy
        elif self.HEALTH < self.HEALTH / 2:
            self.dx *= 2

    def fire_beam(self):

        beam = Bullet(self.rect.centerx, self.rect.bottom - 60, gfx.img_beam)
        beam.dy = 8
        self.allBullets.add(beam)
        snd.load_sound("firing_beam.wav")
        s = gfx.screen.blit(gfx.img_beam_arc,
                            (self.rect.centerx - (gfx.img_beam_arc.get_width() / 2), self.rect.bottom - 100))
        pg.display.update(s)
        self.has_shot = True

    def fire_shots(self):
        shot_left = Bullet(self.rect.left, self.rect.y + 100, gfx.img_enemy_shot_a)
        shot_right = Bullet(self.rect.right, self.rect.y + 100, gfx.img_enemy_shot_a)
        shot_left.dx = -1 * helper_functions.randomize(1)
        shot_left.dy = 5
        shot_right.dx = 1 * helper_functions.randomize(1)
        shot_right.dy = 5
        self.allBullets.add(shot_left, shot_right)

    def die(self):
        for i in range(9):
            pg.display.update(
                    gfx.explosion(self.center[0] + randrange(-100, 100, 20), self.center[1] + randrange(-100, 100, 20)))
            snd.load_sound("explode.wav")
        self.image = pg.transform.scale2x(gfx.load_image("explosion_last.png"))
        snd.load_sound("blow_up.wav")
        pg.display.update()
        snd.play_song("saturns_folly.ogg")
        self.kill()

    def health_bar(self, surf):
        pg.draw.rect(surf, (255, 0, 0), [SCREEN_WIDTH - 50, 40, 20, 500])
        pg.draw.rect(surf, (0, 0, 0), [SCREEN_WIDTH - 50, 40, 20, 500 - int(self.HEALTH / 2)])
        pg.draw.rect(surf, WHITE, [SCREEN_WIDTH - 50, 40, 20, 500], 5)


class GameControl:
    clock = 0
    MAX_ENEMIES = 5
    ENEMIES_KILLED = 0
    KILL_COUNT = 0
    SCORE = 0

    def __init__(self):
        self.screen = gfx.screen
        self._is_fullscreen = False
        self.font = None
        self._is_running = True
        self.started = True
        self.boss_defeated = False
        self.start_time = 0
        self.gametime = 0
        self.FPS = 60
        self.player = player.Player()
        self.powerups = pg.sprite.Group()
        self.drop_chance = 5
        self.player_lives = 3
        self.dead_timer = 0
        self.player_bullets = self.player.allBullets
        self.fighters = pg.sprite.Group()
        self.frigates = pg.sprite.Group()
        self.cruiser = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        self.enemy_bullets = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group()
        self.star_speed = 1
        self.counter = 0
        self.ticker = 0
        self.spawn_timer = 0
        self.stars = None

    def on_init(self):
        environ["SDL_VIDEO_CENTERED"] = "1"
        pg.mixer.pre_init(44100, -16, 4, 512)
        pg.init()
        pg.display.init()
        pg.mixer.init()
        pg.font.init()

        self.font = pg.font.Font(path.join("fonts", "spacebit.ttf"), FONT_SIZE)
        self.clock = pg.time.Clock()

        self.stars = Stars()

    def on_event(self):
        for e in pg.event.get():
            if e.type == pg.QUIT:
                pg.quit()
                exit()
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    self._is_running = False
                if e.key == pg.K_F1:
                    if not self._is_fullscreen:
                        pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pg.FULLSCREEN)
                        self._is_fullscreen = True
                    elif self._is_fullscreen:
                        pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                        self._is_fullscreen = False

        pressed = pg.key.get_pressed()
        if not self.player.dead:
            if pressed[pg.K_LEFT]:
                self.player.move_left()
            if pressed[pg.K_RIGHT]:
                self.player.move_right()
            if pressed[pg.K_UP]:
                self.player.move_up()
            if pressed[pg.K_DOWN]:
                self.player.move_down()
            if pressed[pg.K_UP] and pressed[pg.K_LEFT]:
                self.player.move_upleft()
            if pressed[pg.K_UP] and pressed[pg.K_RIGHT]:
                self.player.move_upright()
            if pressed[pg.K_DOWN] and pressed[pg.K_LEFT]:
                self.player.move_downleft()
            if pressed[pg.K_DOWN] and pressed[pg.K_RIGHT]:
                self.player.move_downright()
            if pressed[pg.K_SPACE]:
                self.player.shoot()

    def update_loop(self):
        # self.gametime = round(time() - self.start_time)
        self.ticker += 1
        if self.ticker == self.FPS:
            self.gametime += 1
            self.ticker = 0

        self.all_sprites.add(self.player_bullets)
        self.all_sprites.add(self.enemy_bullets)
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.enemies)
        self.all_sprites.add(self.powerups)

        if self.player_lives <= 0:
            self._is_running = False

        if self._is_running and self.gametime > 10:
            if not self.boss_defeated and not self.player.dead:
                if len(self.cruiser) < 1 and self.KILL_COUNT >= 99:
                    snd.play_song("deadly_opposition.ogg")
                    big_enemy = EnemyCruiser()
                    self.cruiser.add(big_enemy)
                    self.enemies.add(self.cruiser)

                if len(self.fighters) < self.MAX_ENEMIES:
                    if len(self.cruiser) == 0:
                        self.spawn_timer += 1
                        if self.spawn_timer >= 20:
                            little_enemy = EnemyFighter()
                            self.fighters.add(little_enemy)
                            self.enemies.add(self.fighters)
                            self.spawn_timer = 0

                        if len(self.frigates) < 1:
                            frigate = EnemyFrigate()
                            frigate.rect.y = choice([50, 100, 150, 200, 250, 300])
                            frigate.rect.right = 0
                            self.frigates.add(frigate)
                            self.enemies.add(self.frigates)

            if self.ENEMIES_KILLED > 25:
                self.MAX_ENEMIES += 1
                self.ENEMIES_KILLED = 0

            for fighter in self.fighters:
                if not self.player.dead or self.player.arrive or self.player.respawn or self.player.invulnerable:
                    if not fighter.has_shot:
                        if abs(self.player.rect.y - fighter.rect.bottom <= 300) and abs(
                                                self.player.rect.centerx - fighter.rect.centerx <= 500) and fighter.rect.y <= 900:
                            fighter.shoot(self.player)
                            self.enemy_bullets.add(fighter.allBullets)

            for frigate in self.frigates:
                if frigate.rect.left >= SCREEN_WIDTH:
                    frigate.kill()
                if frigate.rect.centerx == self.player.rect.centerx:
                    frigate.shoot()
                self.enemy_bullets.add(frigate.allBullets)

            for cruiser in self.cruiser:
                print(cruiser.HEALTH)
                if cruiser.HEALTH < 1:
                    print("DEAD")
                    self.boss_defeated = True
                    cruiser.die()
                if self.player.dead:
                    cruiser.allBullets.empty()
                # if cruiser.rect.bottom <= self.player.rect.bottom:
                #     new_bullet = Bullet(cruiser.rect.centerx, cruiser.rect.y, gfx.img_enemy_shot_a)
                #     if self.player.rect.centerx < cruiser.rect.centerx:
                #         new_bullet.dx = -10
                #         cruiser.allBullets.add(new_bullet)
                #     elif self.player.rect.centerx > cruiser.rect.centerx:
                #         new_bullet.dx = 10
                #         cruiser.allBullets.add(new_bullet)
                self.enemy_bullets.add(cruiser.allBullets)

            if not self.player.invulnerable:
                for enemy in self.enemies:
                    if pg.sprite.collide_mask(self.player, enemy):
                        enemy.HEALTH -= 10
                        self.player.die()
                        self.player_lives -= 1

                for bullet in self.enemy_bullets:
                    if not self.player.dead and self.player.rect.colliderect(bullet.rect):
                        self.player.die()
                        bullet.kill()
                        self.player_lives -= 1

            for bullet in self.player_bullets:
                for enemy in self.enemies:
                    if enemy.HEALTH > 0 and enemy.rect.y >= 10 and pg.sprite.collide_mask(bullet, enemy):
                        bullet.on_hit()
                        snd.load_sound("hit.wav")
                        enemy.is_hit = True
                        enemy.HEALTH -= 1
                        if self.player.power_level <= 2:
                            bullet.kill()
                        if enemy.HEALTH <= 0:
                            self.ENEMIES_KILLED += 1
                            self.KILL_COUNT += 1
                            pwr_up = PowerUp()
                            pwr_up.rect = enemy.rect
                            if randint(1, 20) == self.drop_chance:
                                self.powerups.add(pwr_up)

            for beam in EnemyCruiser.allBullets:
                for fighter in self.fighters:
                    if pg.sprite.collide_mask(beam, fighter):
                        fighter.die()
                for frigate in self.frigates:
                    if pg.sprite.collide_mask(beam, frigate):
                        frigate.die()

            for powerup in self.powerups:
                if pg.sprite.collide_mask(powerup, self.player):
                    powerup.on_pickup()
                    self.player.power_level += 1

            for sprite in self.all_sprites:
                if 0 > sprite.rect.x > SCREEN_WIDTH:
                    sprite.kill()
                    self.all_sprites.remove(sprite)
                if 0 > sprite.rect.y > SCREEN_HEIGHT:
                    sprite.kill()
                    self.all_sprites.remove(sprite)

        # Mimic the apperance of hyper drive
        if self.player.arrive:
            self.star_speed = 10
        else:
            self.counter += 1
            if self.star_speed > 2 and self.counter >= 10:
                self.star_speed -= 1
                self.counter = 0
            else:
                pass

        # Player ship leaves after boss defeated
        if self.boss_defeated:
            self.enemy_bullets.empty()
            self.star_speed = 5
            self.player.dx = 0
            self.player.move_up()
            if self.player.rect.bottom <= 0:
                self._is_running = False

        self.all_sprites.update()
        self.clock.tick(self.FPS)

    def on_render(self):

        # Background rendering
        self.screen.blit(gfx.img_background, (0, 0))
        for _ in range(self.star_speed):
            self.stars.render()

        # Display game info
        score = self.font.render("ENEMIES KILLED: " + str(self.KILL_COUNT), True, WHITE)
        lives = [(SCREEN_WIDTH - (gfx.img_life.get_width() + 10),
                  SCREEN_HEIGHT - gfx.img_life.get_height() - 20),
                 (SCREEN_WIDTH - (gfx.img_life.get_width() + 10) * 2,
                  SCREEN_HEIGHT - gfx.img_life.get_height() - 20), (
                     SCREEN_WIDTH - (gfx.img_life.get_width() + 10) * 3,
                     SCREEN_HEIGHT - gfx.img_life.get_height() - 20)]
        for i in range(self.player_lives):
            self.screen.blit(gfx.img_life, lives[i])

        for boss in self.cruiser:
            boss.health_bar(self.screen)

        self.screen.blit(score, (20, SCREEN_HEIGHT - 50))

        if self.boss_defeated and self.player.rect.y < 100:
            i = 1 + i
            self.screen.fill((0,0,0,i))

        # Render each sprite
        self.all_sprites.draw(gfx.screen)

        # Draw screen (with scanline)
        helper_functions.scanlines()
        pg.display.flip()

    def on_cleanup(self):
        pg.quit()
        quit()
        exit()

    def stars(self):
        max = 100
        color = (0, 0, 0)

        stars = []
        for i in range(max):
            star = [randrange(0, SCREEN_WIDTH - 1),
                    randrange(0, SCREEN_WIDTH - 1),
                    choice([1, 2, 3])]
            stars.append(star)

        for star in stars:
            star[1] += star[2]
            if star[1] >= SCREEN_HEIGHT:
                star[1] = 0
                star[0] = randrange(0, SCREEN_WIDTH)
                star[2] = choice([1, 2, 3])

            if star[2] == 1:
                color = (100, 100, 100)
            elif star[2] == 2:
                color = (190, 190, 190)
            elif star[2] == 3:
                color = (255, 255, 255)

            self.screen.fill(color, (star[0], star[1], star[2], star[2]))

    def title_screen(self):
        scroll = 0
        anim = 0
        ship_image = None

        while True:
            title_a = gfx.img_title_a
            title_b = gfx.img_title_b
            title_size = title_a.get_size()
            steps = int(title_size[0] / 2)
            for i in range(steps + 75):
                self.screen.blit(gfx.img_title_background, (0, 0))
                self.screen.blit(gfx.img_title_stars, (0, 100))
                self.screen.blit(title_a, (10 - title_size[0] + i * 2, 300))
                self.screen.blit(title_b, (10 + SCREEN_WIDTH - i * 2, 300))
                pg.display.flip()
            snd.load_sound("blow_up.wav")
            for i in range(100):
                pg.display.update(self.screen.fill(WHITE))
            self.screen.blit(gfx.img_title_background, (0, 0))
            snd.play_song("title_song.ogg")
            break

        while True:

            if scroll <= SCREEN_WIDTH:
                scroll += .5
            else:
                scroll = 0

            self.screen.blit(gfx.img_title_stars, (scroll, 100))
            self.screen.blit(gfx.img_title_stars, (-SCREEN_WIDTH + scroll, 100))
            self.screen.blit(gfx.img_title_whole, (SCREEN_CENTER[0] - gfx.img_title_whole.get_width() / 2 + 20, 300))

            for _ in range(1):
                if anim < 20:
                    ship_image = gfx.title_ship_a
                elif anim > 20:
                    ship_image = gfx.title_ship_b
                self.screen.blit(ship_image, (SCREEN_CENTER[0] - (gfx.title_ship_a.get_width() / 2) + 20, 600))

                if anim < 50:
                    menu = self.font.render("PRESS ENTER", True, WHITE)
                    self.screen.blit(menu, (SCREEN_CENTER[0] - menu.get_width() / 2, SCREEN_CENTER[1]))
                elif anim > 50:
                    menu = self.font.render("PRESS ENTER", True, BLACK)
                    self.screen.blit(menu, (SCREEN_CENTER[0] - menu.get_width() / 2, SCREEN_CENTER[1]))

            anim += 1
            if anim >= 100:
                anim = 0

            pg.display.update()

            e = pg.event.poll()
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_RETURN:
                    snd.load_sound("takeoff.wav")
                    while True:
                        for i in range(255):
                            self.screen.fill((255 - i, 255 - i, 255 - i))
                            helper_functions.scanlines()
                            pg.display.update()
                        break
                    break

        while True:
            text = self.font.render("GET READY", True, WHITE)
            count_list = ["5", "4", "3", "2", "1", "GO!"]
            for i in range(6):
                countdown = self.font.render(count_list[i], True, WHITE)
                self.screen.fill(BLACK)
                self.screen.blit(text, (SCREEN_CENTER[0] - text.get_width() / 2, SCREEN_CENTER[1]))
                self.screen.blit(countdown, (SCREEN_CENTER[0] - countdown.get_width() / 2, SCREEN_CENTER[1] + 30))
                helper_functions.scanlines()
                pg.display.update()
                pg.time.wait(1000)
            break

        snd.play_song("saturns_folly.ogg")
        self.started = True

    def game_over(self):
        pg.mixer.music.stop()
        snd.load_sound("music/death.ogg")
        self.screen.fill((255, 255, 255))
        for i in range(255):
            self.screen.fill((255 - i, 255 - i, 255 - i))
            pg.display.update()
        import glob
        for image in sorted(glob.glob(path.join("graphics/GAMEOVER", "*.png"))):
            self.screen.fill(BLACK)
            part = pg.image.load(image).convert()
            self.screen.blit(part, (SCREEN_CENTER[0] - 250, SCREEN_CENTER[1]))
            pg.display.update()
        pg.time.wait(2000)

    def end_message(self):
        pg.mixer.music.stop()
        snd.load_sound("music/winning.ogg")

        message = self.font.render("Thanks for playing!", True, WHITE)
        self.screen.blit(message, SCREEN_CENTER)

        pg.display.flip()
        pg.time.wait(5000)

    def loop(self):
        if self._is_running:
            self.title_screen()
            # if self.started:
            #     self.start_time = time()
            while self._is_running:
                self.on_event()
                self.update_loop()
                self.on_render()

        if self.boss_defeated:
            self.end_message()
        else:
            self.game_over()


if __name__ == "__main__":
    game = GameControl()
    game.on_init()
    game.loop()
    game.on_cleanup()
