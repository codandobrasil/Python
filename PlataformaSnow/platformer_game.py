# -*- coding: utf-8 -*-

import pgzrun
import random
import sys
from pygame.rect import Rect
from pgzero.actor import Actor

# --- 1. CONSTANTES E CONFIGURAÇÃO ---
WIDTH = 800
HEIGHT = 600
TITLE = "Aventura na Plataforma"

GRAVITY = 800
PLAYER_SPEED = 200
JUMP_STRENGTH = 600  # Salto aumentado para alcançar plataformas intermediárias

# Estado do jogo
game_state = 'menu'
is_music_on = True

# --- 2. CLASSES AUXILIARES ---

class AnimatedCharacter:
    def __init__(self, pos, animations, initial_animation='idle'):
        self.animations = animations
        self.current_animation = initial_animation
        self.actor = Actor(self.animations[self.current_animation][0], anchor=('center', 'bottom'))
        self.actor.pos = pos
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.15
        self.flip_x = False

    def update_animation(self, dt):
        self.animation_timer += dt
        if self.animation_timer > self.animation_speed:
            self.animation_timer = 0
            anim = self.animations[self.current_animation]
            self.frame_index = (self.frame_index + 1) % len(anim)
            self.actor.image = anim[self.frame_index]
            self.actor.flip_x = self.flip_x

    def set_animation(self, name):
        if self.current_animation != name:
            self.current_animation = name
            self.frame_index = 0


class Player(AnimatedCharacter):
    def __init__(self, pos, animations):
        super().__init__(pos, animations)
        self.velocity_y = 0
        self.is_on_ground = False
        self.projectiles = []

    def update(self, dt, platforms):
        velocity_x = 0
        if keyboard.left:
            velocity_x = -PLAYER_SPEED
            self.flip_x = True
            self.set_animation('run')
        elif keyboard.right:
            velocity_x = PLAYER_SPEED
            self.flip_x = False
            self.set_animation('run')
        else:
            self.set_animation('idle')

        self.actor.x += velocity_x * dt

        if keyboard.space and self.is_on_ground:
            self.velocity_y = -JUMP_STRENGTH
            try:
                sounds.jump_sound.play()
            except:
                print("Som de pulo não encontrado.")

        self.velocity_y += GRAVITY * dt
        self.actor.y += self.velocity_y * dt

        self.is_on_ground = False
        for platform in platforms:
            if self.actor.colliderect(platform) and self.velocity_y >= 0:
                if self.actor.bottom < platform.bottom:
                    self.actor.bottom = platform.top
                    self.velocity_y = 0
                    self.is_on_ground = True

        for proj in self.projectiles[:]:
            proj['x'] += proj['speed'] * dt
            if proj['x'] > WIDTH or proj['x'] < 0:
                self.projectiles.remove(proj)

        super().update_animation(dt)

    def attack(self):
        direction = 1 if not self.flip_x else -1
        self.projectiles.append({'x': self.actor.x, 'y': self.actor.y - 40, 'speed': 400 * direction})


class Enemy(AnimatedCharacter):
    def __init__(self, pos, animations, patrol_range):
        super().__init__(pos, animations, initial_animation='walk')
        self.start_x = pos[0] - patrol_range
        self.end_x = pos[0] + patrol_range
        self.speed = 60

    def update(self, dt):
        self.actor.x += self.speed * dt
        if self.actor.right > self.end_x or self.actor.left < self.start_x:
            self.speed *= -1
            self.flip_x = not self.flip_x

        super().update_animation(dt)


class Button:
    def __init__(self, pos, image_normal, image_hover, on_click_func):
        self.actor = Actor(image_normal, pos)
        # Corrigido redimensionamento com pygame.transform.scale
        surf = self.actor._surf
        import pygame
        surf = pygame.transform.scale(surf, (surf.get_width() * 2, surf.get_height() * 2))
        self.actor._surf = surf
        self.image_normal = image_normal
        self.image_hover = image_hover
        self.on_click = on_click_func
        self.is_hovered = False

    def draw(self):
        self.actor.image = self.image_hover if self.is_hovered else self.image_normal
        self.actor.draw()

    def check_hover(self, mouse_pos):
        self.is_hovered = self.actor.collidepoint(mouse_pos)

    def check_click(self, mouse_pos):
        if self.is_hovered:
            self.on_click()

# --- 3. INICIALIZAÇÃO DO JOGO ---
player = None
enemies = []
platforms = []
buttons = []


def setup_game():
    global player, enemies, platforms

    platforms = [
        Rect(0, HEIGHT - 40, WIDTH, 40),
        Rect(100, HEIGHT - 200, 200, 20),
        Rect(500, HEIGHT - 200, 200, 20),
        Rect(300, HEIGHT - 350, 200, 20)
    ]

    player_animations = {
        'idle': ['player_idle/0', 'player_idle/1'],
        'run': ['player_run/0', 'player_run/1']
    }
    player = Player(pos=(WIDTH / 2, 50), animations=player_animations)

    enemy_animations = {'walk': ['enemy_walk/0', 'enemy_walk/1']}
    enemies[:] = [
        Enemy(pos=(200, HEIGHT - 200), animations=enemy_animations, patrol_range=50),
        Enemy(pos=(600, HEIGHT - 200), animations=enemy_animations, patrol_range=60),
        Enemy(pos=(400, HEIGHT - 40), animations=enemy_animations, patrol_range=150)
    ]


def start_game():
    global game_state
    setup_game()
    game_state = 'playing'
    if is_music_on:
        try:
            music.play('background_music')
        except:
            print("Erro ao tocar background_music.")


def toggle_music():
    global is_music_on
    is_music_on = not is_music_on
    if is_music_on:
        music.unpause()
        buttons[1].image_normal = 'button_music_on'
        buttons[1].image_hover = 'button_music_off'
    else:
        music.pause()
        buttons[1].image_normal = 'button_music_off'
        buttons[1].image_hover = 'button_music_on'


def exit_game():
    sys.exit()


buttons = [
    Button(pos=(WIDTH / 2 - 180, 250), image_normal='button_start', image_hover='button_start_hover', on_click_func=start_game),
    Button(pos=(WIDTH / 2, 250), image_normal='button_music_on', image_hover='button_music_off', on_click_func=toggle_music),
    Button(pos=(WIDTH / 2 + 180, 250), image_normal='button_exit', image_hover='button_exit_hover', on_click_func=exit_game)
]

try:
    music.play('menu_music')
    music.set_volume(0.3)
except:
    print("Música do menu não encontrada.")

# --- 4. FUNÇÕES DO JOGO ---
def draw():
    screen.blit('background', (0, 0))

    if game_state == 'menu':
        screen.draw.text("Aventura na Plataforma", center=(WIDTH / 2, 100), fontsize=60, color="blue")
        for button in buttons:
            button.draw()

        # Legenda dos controles
        legend = [
            "CONTROLES:",
            "Setas direcionais - Movimentar",
            "Barra de espaço - Saltar",
            "Tecla D - Atirar",
            "By Marcelo Neves"
        ]
        y = 350
        for line in legend:
            screen.draw.text(line, center=(WIDTH / 2, y), fontsize=28, color="blue")
            y += 40

    elif game_state == 'playing':
        for p in platforms:
            for x in range(p.left, p.right, 32):
                screen.blit('platform_tile', (x, p.top))

        for proj in player.projectiles:
            screen.draw.text('-', (proj['x'], proj['y']), fontsize=40, color="white")

        player.actor.draw()
        for enemy in enemies:
            enemy.actor.draw()

        if len(enemies) == 0:
            screen.draw.text("VOCÊ É O VENCEDOR!!!", center=(WIDTH / 2, HEIGHT / 2), fontsize=70, color="red")

    elif game_state == 'game_over':
        screen.draw.text("FIM DE JOGO", center=(WIDTH / 2, HEIGHT / 2), fontsize=80, color="red")
        screen.draw.text("Pressione Enter para voltar ao menu", center=(WIDTH / 2, HEIGHT / 2 + 60), fontsize=40)


def update(dt):
    global game_state

    if game_state == 'menu':
        if not is_music_on:
            music.pause()
        elif is_music_on:
            try:
                if not music.is_playing('menu_music'):
                    music.play('menu_music')
            except:
                pass

    elif game_state == 'playing':
        # Se venceu, não atualiza mais o jogo, espera o Enter
        if len(enemies) == 0:
            return

        player.update(dt, platforms)
        for enemy in enemies[:]:
            enemy.update(dt)
            if player.actor.colliderect(enemy.actor):
                game_state = 'game_over'
                try:
                    sounds.hit_sound.play()
                except:
                    print("Som de impacto não encontrado.")
                music.stop()
            for proj in player.projectiles:
                if enemy.actor.collidepoint((proj['x'], proj['y'])):
                    enemies.remove(enemy)
                    try:
                        sounds.attack_hit.play()
                    except:
                        print("Som de ataque não encontrado.")

def on_mouse_move(pos):
    if game_state == 'menu':
        for button in buttons:
            button.check_hover(pos)

def on_mouse_down(pos, button):
    if game_state == 'menu' and button == mouse.LEFT:
        for b in buttons:
            b.check_click(pos)

def on_key_down(key):
    global game_state
    if game_state == 'game_over' and key == keys.RETURN:
        game_state = 'menu'
        try:
            music.play('menu_music')
        except:
            print("Música do menu não encontrada ao retornar ao menu.")
    elif game_state == 'playing':
        if len(enemies) == 0 and key == keys.RETURN:
            game_state = 'menu'
            try:
                music.play('menu_music')
            except:
                print("Música do menu não encontrada ao retornar ao menu.")
        elif key == keys.D:
            player.attack()

pgzrun.go()
