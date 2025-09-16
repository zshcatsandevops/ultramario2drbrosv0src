#!/usr/bin/env python3
"""
Super Mario Bros 2D - Modern Graphics Edition
Enhanced with Wii-era visual effects, animations, and polish
"""

import pygame
import random
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
import colorsys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
GRAVITY = 0.8
JUMP_STRENGTH = -16
MOVE_SPEED = 6
FPS = 60

# Enhanced Color Palette
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
SKY_BLUE = (135, 206, 250)
GRASS_GREEN = (34, 139, 34)
BRIGHT_RED = (255, 69, 58)
GOLD = (255, 215, 0)
EARTH_BROWN = (101, 67, 33)
SUNSET_ORANGE = (255, 140, 90)
ROYAL_PURPLE = (147, 112, 219)
OCEAN_BLUE = (0, 119, 190)
CLOUD_WHITE = (245, 245, 245)
SHADOW_COLOR = (0, 0, 0, 100)

class PowerUpType(Enum):
    NONE = 0
    MUSHROOM = 1
    FIRE_FLOWER = 2
    STAR = 3
    ICE_FLOWER = 4

class EnemyType(Enum):
    GOOMBA = 1
    KOOPA = 2
    PIRANHA = 3
    BULLET = 4
    HAMMER_BRO = 5
    BOO = 6
    SPIKE = 7

@dataclass
class WorldTheme:
    name: str
    bg_gradient: List[Tuple[int, int, int]]
    platform_colors: List[Tuple[int, int, int]]
    accent_color: Tuple[int, int, int]
    particle_color: Tuple[int, int, int]
    has_clouds: bool
    has_parallax: bool

class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime, size=3, gravity=True):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size
        self.gravity = gravity
        self.alpha = 255
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.gravity:
            self.vy += 0.3
        self.lifetime -= 1
        self.alpha = int(255 * (self.lifetime / self.max_lifetime))
        return self.lifetime > 0
    
    def draw(self, screen, camera_x):
        if self.alpha > 0:
            color = (*self.color, min(self.alpha, 255))
            pos = (int(self.x - camera_x), int(self.y))
            
            # Draw with glow effect
            for i in range(3):
                glow_alpha = max(0, self.alpha - i * 80)
                if glow_alpha > 0:
                    glow_size = self.size + i * 2
                    glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*self.color, glow_alpha // 3), 
                                     (glow_size, glow_size), glow_size)
                    screen.blit(glow_surf, (pos[0] - glow_size, pos[1] - glow_size))
            
            # Main particle
            particle_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, color, (self.size, self.size), self.size)
            screen.blit(particle_surf, (pos[0] - self.size, pos[1] - self.size))

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_particle(self, x, y, vx, vy, color, lifetime=30, size=3, gravity=True):
        self.particles.append(Particle(x, y, vx, vy, color, lifetime, size, gravity))
    
    def create_explosion(self, x, y, color, count=20):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.randint(2, 5)
            lifetime = random.randint(20, 40)
            self.add_particle(x, y, vx, vy, color, lifetime, size)
    
    def create_sparkle(self, x, y, color):
        for _ in range(5):
            vx = random.uniform(-2, 2)
            vy = random.uniform(-3, -1)
            self.add_particle(x, y, vx, vy, color, 20, 2, True)
    
    def create_trail(self, x, y, color, direction=1):
        for i in range(3):
            offset_x = -direction * i * 5
            vx = -direction * random.uniform(0.5, 1.5)
            vy = random.uniform(-0.5, 0.5)
            self.add_particle(x + offset_x, y, vx, vy, color, 15, 2, False)
    
    def update(self):
        self.particles = [p for p in self.particles if p.update()]
    
    def draw(self, screen, camera_x):
        for particle in self.particles:
            particle.draw(screen, camera_x)

class GameObject(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color):
        super().__init__()
        self.base_image = self.create_styled_surface(width, height, color)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vx = 0
        self.vy = 0
        self.animation_time = 0
        self.scale = 1.0
        
    def create_styled_surface(self, width, height, base_color):
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Create gradient effect
        for y in range(height):
            progress = y / height
            color = self.blend_colors(base_color, (255, 255, 255), 1 - progress * 0.3)
            pygame.draw.line(surface, color, (0, y), (width, y))
        
        # Add border highlight
        pygame.draw.rect(surface, (255, 255, 255, 100), surface.get_rect(), 2)
        
        # Add shadow
        shadow_surf = pygame.Surface((width + 4, height + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50), shadow_surf.get_rect())
        
        return surface
    
    def blend_colors(self, color1, color2, ratio):
        return tuple(int(c1 * ratio + c2 * (1 - ratio)) for c1, c2 in zip(color1, color2))

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 36, 36, BRIGHT_RED)
        self.power_up = PowerUpType.NONE
        self.invincible_timer = 0
        self.fire_cooldown = 0
        self.lives = 3
        self.coins = 0
        self.on_ground = False
        self.facing_right = True
        self.jump_particles_created = False
        self.run_animation = 0
        self.star_colors = []
        self.create_character_sprite()
    
    def create_character_sprite(self):
        size = (36, 48) if self.power_up in [PowerUpType.MUSHROOM, PowerUpType.FIRE_FLOWER, PowerUpType.ICE_FLOWER] else (36, 36)
        self.image = pygame.Surface(size, pygame.SRCALPHA)
        
        # Body color based on power-up
        if self.power_up == PowerUpType.FIRE_FLOWER:
            body_color = (255, 100, 100)
            accent_color = WHITE
        elif self.power_up == PowerUpType.ICE_FLOWER:
            body_color = (100, 200, 255)
            accent_color = WHITE
        elif self.power_up == PowerUpType.STAR:
            # Rainbow effect
            hue = (self.animation_time * 5) % 360
            body_color = self.hsv_to_rgb(hue / 360, 1, 1)
            accent_color = WHITE
        else:
            body_color = BRIGHT_RED
            accent_color = (139, 69, 19)
        
        # Draw character with details
        if self.power_up in [PowerUpType.MUSHROOM, PowerUpType.FIRE_FLOWER, PowerUpType.ICE_FLOWER]:
            # Super Mario (taller)
            # Head
            pygame.draw.ellipse(self.image, body_color, (8, 4, 20, 20))
            # Eyes
            pygame.draw.circle(self.image, WHITE, (14, 12), 3)
            pygame.draw.circle(self.image, BLACK, (15, 12), 2)
            pygame.draw.circle(self.image, WHITE, (22, 12), 3)
            pygame.draw.circle(self.image, BLACK, (21, 12), 2)
            # Body
            pygame.draw.rect(self.image, accent_color, (10, 20, 16, 20))
            # Arms
            pygame.draw.rect(self.image, body_color, (5, 24, 6, 12))
            pygame.draw.rect(self.image, body_color, (25, 24, 6, 12))
            # Legs
            pygame.draw.rect(self.image, accent_color, (12, 36, 6, 12))
            pygame.draw.rect(self.image, accent_color, (18, 36, 6, 12))
        else:
            # Small Mario
            # Head
            pygame.draw.ellipse(self.image, body_color, (8, 2, 20, 18))
            # Eyes
            pygame.draw.circle(self.image, WHITE, (14, 9), 2)
            pygame.draw.circle(self.image, BLACK, (14, 9), 1)
            pygame.draw.circle(self.image, WHITE, (22, 9), 2)
            pygame.draw.circle(self.image, BLACK, (22, 9), 1)
            # Body
            pygame.draw.rect(self.image, accent_color, (11, 16, 14, 14))
            # Arms
            pygame.draw.rect(self.image, body_color, (6, 18, 5, 8))
            pygame.draw.rect(self.image, body_color, (25, 18, 5, 8))
            # Legs
            pygame.draw.rect(self.image, accent_color, (12, 26, 5, 10))
            pygame.draw.rect(self.image, accent_color, (19, 26, 5, 10))
        
        # Add glow effect for star power
        if self.power_up == PowerUpType.STAR:
            glow_surf = pygame.Surface((size[0] + 20, size[1] + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (*body_color, 50), glow_surf.get_rect())
            self.image.blit(glow_surf, (-10, -10))
        
        # Flip if facing left
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
        
        # Update rect
        old_rect = self.rect
        self.rect = self.image.get_rect()
        self.rect.centerx = old_rect.centerx
        self.rect.bottom = old_rect.bottom
    
    def hsv_to_rgb(self, h, s, v):
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)
    
    def jump(self):
        if self.on_ground:
            self.vy = JUMP_STRENGTH
            self.jump_particles_created = False
    
    def update(self):
        self.vy += GRAVITY
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        self.animation_time += 1
        
        if self.vx != 0:
            self.run_animation += abs(self.vx) * 0.2
        
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            if self.invincible_timer == 0 and self.power_up == PowerUpType.STAR:
                self.power_up = PowerUpType.NONE
                self.create_character_sprite()
        
        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        
        # Update sprite
        self.create_character_sprite()

class AnimatedPlatform(GameObject):
    def __init__(self, x, y, width, height, colors):
        super().__init__(x, y, width, height, colors[0])
        self.colors = colors
        self.is_moving = False
        self.move_range = 0
        self.move_speed = 0
        self.start_x = x
        self.start_y = y
        self.direction = 1
        self.vertical_moving = False
        self.create_platform_visual()
    
    def create_platform_visual(self):
        # Create a detailed platform with texture
        self.image = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Base gradient
        for y in range(self.rect.height):
            progress = y / self.rect.height
            if progress < 0.1:  # Top highlight
                color = self.blend_colors(self.colors[0], WHITE, 0.7)
            elif progress < 0.3:  # Main color
                color = self.colors[0]
            else:  # Shadow
                color = self.blend_colors(self.colors[0], BLACK, 0.7 - progress * 0.3)
            
            pygame.draw.line(self.image, color, (0, y), (self.rect.width, y))
        
        # Add texture details
        for i in range(0, self.rect.width, 20):
            pygame.draw.line(self.image, (0, 0, 0, 30), (i, 0), (i, self.rect.height), 1)
        
        # Edge highlights
        pygame.draw.rect(self.image, (255, 255, 255, 100), (0, 0, self.rect.width, 3))
        pygame.draw.rect(self.image, (0, 0, 0, 100), (0, self.rect.height - 3, self.rect.width, 3))
    
    def update(self):
        if self.is_moving:
            if self.vertical_moving:
                self.rect.y += self.move_speed * self.direction
                if abs(self.rect.y - self.start_y) > self.move_range:
                    self.direction *= -1
            else:
                self.rect.x += self.move_speed * self.direction
                if abs(self.rect.x - self.start_x) > self.move_range:
                    self.direction *= -1

class AnimatedEnemy(GameObject):
    def __init__(self, x, y, enemy_type):
        self.enemy_type = enemy_type
        colors = {
            EnemyType.GOOMBA: (139, 90, 43),
            EnemyType.KOOPA: (0, 200, 0),
            EnemyType.PIRANHA: (255, 0, 100),
            EnemyType.BULLET: (64, 64, 64),
            EnemyType.HAMMER_BRO: (0, 150, 0),
            EnemyType.BOO: (255, 255, 255),
            EnemyType.SPIKE: (200, 0, 200)
        }
        sizes = {
            EnemyType.GOOMBA: (32, 32),
            EnemyType.KOOPA: (36, 52),
            EnemyType.PIRANHA: (44, 64),
            EnemyType.BULLET: (32, 24),
            EnemyType.HAMMER_BRO: (44, 56),
            EnemyType.BOO: (40, 40),
            EnemyType.SPIKE: (36, 36)
        }
        size = sizes[enemy_type]
        super().__init__(x, y, size[0], size[1], colors[enemy_type])
        
        self.vx = random.choice([-2, 2])
        self.patrol_distance = 150
        self.start_x = x
        self.alive = True
        self.animation_frame = 0
        self.squash_timer = 0
        self.create_enemy_sprite()
    
    def create_enemy_sprite(self):
        self.image = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        if self.enemy_type == EnemyType.GOOMBA:
            # Goomba with animation
            body_squash = 1.0 - self.squash_timer * 0.3
            
            # Body
            body_rect = pygame.Rect(4, 8 * body_squash, 24, 20 * body_squash)
            pygame.draw.ellipse(self.image, (139, 90, 43), body_rect)
            
            # Feet animation
            foot_offset = math.sin(self.animation_frame * 0.2) * 2
            pygame.draw.ellipse(self.image, BLACK, (6, 24 + foot_offset, 8, 6))
            pygame.draw.ellipse(self.image, BLACK, (18, 24 - foot_offset, 8, 6))
            
            # Eyes
            pygame.draw.circle(self.image, WHITE, (10, 14), 3)
            pygame.draw.circle(self.image, BLACK, (10, 15), 2)
            pygame.draw.circle(self.image, WHITE, (22, 14), 3)
            pygame.draw.circle(self.image, BLACK, (22, 15), 2)
            
        elif self.enemy_type == EnemyType.KOOPA:
            # Koopa turtle
            # Shell
            shell_color = (0, 200, 0)
            pygame.draw.ellipse(self.image, shell_color, (4, 16, 28, 24))
            
            # Shell pattern
            for i in range(3):
                pygame.draw.arc(self.image, (0, 150, 0), 
                               (8 + i*8, 18, 8, 20), 0, math.pi, 2)
            
            # Head
            pygame.draw.ellipse(self.image, (255, 200, 150), (10, 4, 16, 14))
            
            # Eyes
            pygame.draw.circle(self.image, WHITE, (14, 9), 2)
            pygame.draw.circle(self.image, BLACK, (14, 9), 1)
            pygame.draw.circle(self.image, WHITE, (20, 9), 2)
            pygame.draw.circle(self.image, BLACK, (20, 9), 1)
            
            # Legs
            leg_offset = math.sin(self.animation_frame * 0.15) * 3
            pygame.draw.rect(self.image, (255, 200, 150), (8, 36 + leg_offset, 6, 10))
            pygame.draw.rect(self.image, (255, 200, 150), (22, 36 - leg_offset, 6, 10))
        
        elif self.enemy_type == EnemyType.BOO:
            # Ghost enemy
            alpha = 200 if self.alive else 100
            
            # Body (circular ghost)
            ghost_color = (*WHITE, alpha)
            pygame.draw.circle(self.image, ghost_color, (20, 20), 18)
            
            # Wavy bottom
            for i in range(5):
                wave_y = 32 + math.sin(self.animation_frame * 0.1 + i) * 3
                pygame.draw.circle(self.image, ghost_color, (8 + i*6, int(wave_y)), 4)
            
            # Face
            if self.vx > 0:  # Facing right
                # Eyes
                pygame.draw.ellipse(self.image, BLACK, (12, 14, 4, 6))
                pygame.draw.ellipse(self.image, BLACK, (24, 14, 4, 6))
                # Mouth
                pygame.draw.arc(self.image, BLACK, (14, 22, 12, 8), 0, math.pi, 2)
            else:  # Shy (facing away)
                # Blush
                pygame.draw.circle(self.image, (255, 150, 150, 100), (10, 20), 3)
                pygame.draw.circle(self.image, (255, 150, 150, 100), (30, 20), 3)
        
        elif self.enemy_type == EnemyType.BULLET:
            # Bullet Bill
            # Body
            pygame.draw.ellipse(self.image, (64, 64, 64), self.image.get_rect())
            # Highlight
            pygame.draw.ellipse(self.image, (128, 128, 128), (4, 4, 24, 16))
            # Eyes
            pygame.draw.circle(self.image, WHITE, (8, 12), 3)
            pygame.draw.circle(self.image, BLACK, (8, 12), 2)
            pygame.draw.circle(self.image, WHITE, (16, 12), 3)
            pygame.draw.circle(self.image, BLACK, (16, 12), 2)
        
        # Add shadow
        shadow_surf = pygame.Surface((self.rect.width + 8, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50), shadow_surf.get_rect())
        
        # Direction flip
        if self.vx < 0 and self.enemy_type != EnemyType.BOO:
            self.image = pygame.transform.flip(self.image, True, False)
    
    def update(self):
        self.animation_frame += 1
        
        if self.squash_timer > 0:
            self.squash_timer -= 1
        
        if self.enemy_type == EnemyType.BULLET:
            self.rect.x += self.vx * 3
        elif self.enemy_type == EnemyType.PIRANHA:
            # Bobbing motion
            self.rect.y = self.start_x + math.sin(self.animation_frame * 0.05) * 20
        elif self.enemy_type == EnemyType.BOO:
            # Float toward player when not looking
            pass  # Implement if player reference available
        else:
            self.rect.x += self.vx
            if abs(self.rect.x - self.start_x) > self.patrol_distance:
                self.vx *= -1
        
        self.vy += GRAVITY
        self.rect.y += self.vy
        
        # Update sprite
        self.create_enemy_sprite()

class AnimatedPowerUp(GameObject):
    def __init__(self, x, y, power_type):
        self.power_type = power_type
        colors = {
            PowerUpType.MUSHROOM: BRIGHT_RED,
            PowerUpType.FIRE_FLOWER: SUNSET_ORANGE,
            PowerUpType.STAR: GOLD,
            PowerUpType.ICE_FLOWER: (150, 200, 255)
        }
        super().__init__(x, y, 28, 28, colors[power_type])
        self.collected = False
        self.float_offset = random.random() * math.pi * 2
        self.glow_animation = 0
        self.create_powerup_sprite()
    
    def create_powerup_sprite(self):
        self.image = pygame.Surface((40, 40), pygame.SRCALPHA)
        
        # Glow effect
        glow_radius = 18 + math.sin(self.glow_animation * 0.1) * 3
        glow_alpha = 100 + math.sin(self.glow_animation * 0.15) * 30
        
        if self.power_type == PowerUpType.MUSHROOM:
            # Mushroom
            # Stem
            pygame.draw.rect(self.image, WHITE, (16, 22, 8, 10))
            # Cap
            pygame.draw.ellipse(self.image, BRIGHT_RED, (8, 10, 24, 16))
            # Dots
            pygame.draw.circle(self.image, WHITE, (14, 16), 2)
            pygame.draw.circle(self.image, WHITE, (26, 16), 2)
            pygame.draw.circle(self.image, WHITE, (20, 14), 2)
            
        elif self.power_type == PowerUpType.FIRE_FLOWER:
            # Fire Flower
            # Stem
            pygame.draw.rect(self.image, (0, 200, 0), (18, 24, 4, 8))
            # Petals (animated)
            petal_colors = [SUNSET_ORANGE, GOLD, BRIGHT_RED]
            for i in range(8):
                angle = (i * 45 + self.glow_animation) * math.pi / 180
                x = 20 + math.cos(angle) * 8
                y = 16 + math.sin(angle) * 8
                color = petal_colors[i % 3]
                pygame.draw.circle(self.image, color, (int(x), int(y)), 4)
            # Center
            pygame.draw.circle(self.image, GOLD, (20, 16), 3)
            
        elif self.power_type == PowerUpType.STAR:
            # Animated Star
            # Draw star shape
            star_points = []
            for i in range(10):
                angle = (i * 36 - 90 + self.glow_animation * 2) * math.pi / 180
                if i % 2 == 0:
                    radius = 12
                else:
                    radius = 6
                x = 20 + math.cos(angle) * radius
                y = 20 + math.sin(angle) * radius
                star_points.append((x, y))
            
            # Rainbow color
            hue = (self.glow_animation * 3) % 360
            color = self.hsv_to_rgb(hue / 360, 1, 1)
            pygame.draw.polygon(self.image, color, star_points)
            
            # Inner glow
            pygame.draw.polygon(self.image, WHITE, star_points, 2)
            
        elif self.power_type == PowerUpType.ICE_FLOWER:
            # Ice Flower
            # Stem
            pygame.draw.rect(self.image, (100, 150, 200), (18, 24, 4, 8))
            # Ice crystal petals
            for i in range(6):
                angle = (i * 60 + self.glow_animation * 0.5) * math.pi / 180
                x1 = 20 + math.cos(angle) * 4
                y1 = 16 + math.sin(angle) * 4
                x2 = 20 + math.cos(angle) * 10
                y2 = 16 + math.sin(angle) * 10
                pygame.draw.line(self.image, (150, 200, 255), 
                               (int(x1), int(y1)), (int(x2), int(y2)), 3)
                # Crystal branches
                branch_angle1 = angle - 0.3
                branch_angle2 = angle + 0.3
                bx1 = x2 - math.cos(branch_angle1) * 4
                by1 = y2 - math.sin(branch_angle1) * 4
                bx2 = x2 - math.cos(branch_angle2) * 4
                by2 = y2 - math.sin(branch_angle2) * 4
                pygame.draw.line(self.image, (200, 230, 255),
                               (int(x2), int(y2)), (int(bx1), int(by1)), 2)
                pygame.draw.line(self.image, (200, 230, 255),
                               (int(x2), int(y2)), (int(bx2), int(by2)), 2)
            # Center
            pygame.draw.circle(self.image, WHITE, (20, 16), 3)
        
        # Add glow
        glow_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*self.get_glow_color(), int(glow_alpha)), 
                         (25, 25), int(glow_radius))
        self.image.blit(glow_surf, (-5, -5))
    
    def get_glow_color(self):
        colors = {
            PowerUpType.MUSHROOM: BRIGHT_RED,
            PowerUpType.FIRE_FLOWER: SUNSET_ORANGE,
            PowerUpType.STAR: GOLD,
            PowerUpType.ICE_FLOWER: (150, 200, 255)
        }
        return colors[self.power_type]
    
    def hsv_to_rgb(self, h, s, v):
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)
    
    def update(self):
        self.glow_animation += 1
        # Floating animation
        self.rect.y += math.sin(pygame.time.get_ticks() * 0.003 + self.float_offset) * 0.5
        self.create_powerup_sprite()

class AnimatedCoin(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 24, 24, GOLD)
        self.collected = False
        self.spin_angle = random.random() * math.pi * 2
        self.float_offset = random.random() * math.pi * 2
        
    def create_coin_sprite(self):
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        # Spinning effect
        width_scale = abs(math.cos(self.spin_angle))
        coin_width = int(20 * width_scale)
        if coin_width < 2:
            coin_width = 2
        
        # Draw coin
        coin_rect = pygame.Rect(16 - coin_width // 2, 6, coin_width, 20)
        
        # Metallic gradient
        if width_scale > 0.3:
            # Coin face visible
            pygame.draw.ellipse(self.image, GOLD, coin_rect)
            pygame.draw.ellipse(self.image, (255, 245, 100), coin_rect.inflate(-4, -4))
            
            # Embossed effect
            if width_scale > 0.7:
                font = pygame.font.Font(None, 16)
                text = font.render("$", True, GOLD)
                text_rect = text.get_rect(center=(16, 16))
                self.image.blit(text, text_rect)
        else:
            # Edge view
            pygame.draw.rect(self.image, (200, 180, 0), coin_rect)
        
        # Sparkle effect
        sparkle_angle = pygame.time.get_ticks() * 0.01
        sparkle_x = 16 + math.cos(sparkle_angle) * 8
        sparkle_y = 16 + math.sin(sparkle_angle) * 8
        pygame.draw.circle(self.image, WHITE, (int(sparkle_x), int(sparkle_y)), 2)
    
    def update(self):
        self.spin_angle += 0.15
        # Floating animation
        self.rect.y += math.sin(pygame.time.get_ticks() * 0.003 + self.float_offset) * 0.3
        self.create_coin_sprite()

class Fireball(GameObject):
    def __init__(self, x, y, direction, is_ice=False):
        color = (150, 200, 255) if is_ice else SUNSET_ORANGE
        super().__init__(x, y, 16, 16, color)
        self.vx = 10 * direction
        self.vy = -5
        self.bounces = 0
        self.max_bounces = 3
        self.is_ice = is_ice
        self.rotation = 0
        self.trail_positions = []
        
    def create_fireball_sprite(self):
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        
        if self.is_ice:
            # Ice ball
            # Core
            pygame.draw.circle(self.image, (200, 230, 255), (12, 12), 8)
            pygame.draw.circle(self.image, WHITE, (12, 12), 5)
            
            # Ice crystals
            for i in range(6):
                angle = i * 60 + self.rotation
                x = 12 + math.cos(math.radians(angle)) * 10
                y = 12 + math.sin(math.radians(angle)) * 10
                pygame.draw.line(self.image, (150, 200, 255), 
                               (12, 12), (int(x), int(y)), 2)
        else:
            # Fireball with flame effect
            # Core
            pygame.draw.circle(self.image, GOLD, (12, 12), 6)
            pygame.draw.circle(self.image, WHITE, (12, 12), 3)
            
            # Flames
            for i in range(8):
                angle = i * 45 + self.rotation
                flame_length = 8 + math.sin(angle * 0.1) * 3
                x = 12 + math.cos(math.radians(angle)) * flame_length
                y = 12 + math.sin(math.radians(angle)) * flame_length
                pygame.draw.line(self.image, SUNSET_ORANGE, 
                               (12, 12), (int(x), int(y)), 2)
    
    def update(self):
        self.rotation += 15
        self.vy += GRAVITY * 0.5
        self.rect.x += self.vx
        self.rect.y += self.vy
        
        # Store trail positions
        self.trail_positions.append((self.rect.centerx, self.rect.centery))
        if len(self.trail_positions) > 5:
            self.trail_positions.pop(0)
        
        self.create_fireball_sprite()

class Cloud:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.speed = random.uniform(0.2, 0.5)
        self.shape = self.generate_cloud_shape()
    
    def generate_cloud_shape(self):
        circles = []
        for _ in range(random.randint(4, 7)):
            cx = random.randint(-self.size//2, self.size//2)
            cy = random.randint(-self.size//4, self.size//4)
            radius = random.randint(self.size//4, self.size//2)
            circles.append((cx, cy, radius))
        return circles
    
    def update(self):
        self.x += self.speed
    
    def draw(self, screen, camera_x):
        # Parallax effect
        draw_x = self.x - camera_x * 0.3
        
        for cx, cy, radius in self.shape:
            # Shadow
            pygame.draw.circle(screen, (200, 200, 200, 100), 
                             (int(draw_x + cx + 2), int(self.y + cy + 2)), radius)
            # Main cloud
            pygame.draw.circle(screen, CLOUD_WHITE, 
                             (int(draw_x + cx), int(self.y + cy)), radius)
            # Highlight
            pygame.draw.circle(screen, WHITE, 
                             (int(draw_x + cx - radius//3), int(self.y + cy - radius//3)), 
                             radius//3)

class World:
    def __init__(self, world_num, theme):
        self.world_num = world_num
        self.theme = theme
        self.platforms = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.power_ups = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.fireballs = pygame.sprite.Group()
        self.flag = None
        self.spawn_point = (100, 400)
        self.camera_x = 0
        self.level_width = 4000 + world_num * 500
        self.clouds = []
        self.background_objects = []
        self.particle_system = ParticleSystem()
        
        self.generate_level()
        self.generate_background()
    
    def generate_level(self):
        # Generate varied terrain
        for i in range(0, self.level_width, 100):
            if random.random() > 0.15 or i < 300:
                height = random.randint(100, 200)
                
                # Platform colors based on theme
                platform = AnimatedPlatform(i, SCREEN_HEIGHT - height, 100, height, 
                                           self.theme.platform_colors)
                self.platforms.add(platform)
                
                # Floating platforms
                if i > 400 and random.random() > 0.5:
                    float_y = SCREEN_HEIGHT - height - random.randint(180, 350)
                    float_width = random.randint(80, 150)
                    float_platform = AnimatedPlatform(i + random.randint(-50, 50), float_y,
                                                     float_width, 25, self.theme.platform_colors)
                    
                    if random.random() > 0.6:  # Moving platform
                        float_platform.is_moving = True
                        float_platform.move_range = random.randint(100, 200)
                        float_platform.move_speed = random.uniform(1, 3)
                        float_platform.vertical_moving = random.random() > 0.5
                    
                    self.platforms.add(float_platform)
        
        # Add enemies with variety
        enemy_count = 8 + self.world_num * 4
        enemy_types = list(EnemyType)[:min(self.world_num + 2, len(EnemyType))]
        
        for _ in range(enemy_count):
            x = random.randint(400, self.level_width - 300)
            y = random.randint(100, 400)
            enemy_type = random.choice(enemy_types)
            enemy = AnimatedEnemy(x, y, enemy_type)
            self.enemies.add(enemy)
        
        # Add power-ups
        power_count = 4 + self.world_num * 2
        for _ in range(power_count):
            x = random.randint(500, self.level_width - 400)
            y = random.randint(200, 400)
            power_types = [PowerUpType.MUSHROOM, PowerUpType.FIRE_FLOWER, 
                          PowerUpType.STAR, PowerUpType.ICE_FLOWER]
            power_type = random.choice(power_types)
            power_up = AnimatedPowerUp(x, y, power_type)
            self.power_ups.add(power_up)
        
        # Add coins in patterns
        coin_count = 30 + self.world_num * 10
        for i in range(coin_count):
            if random.random() > 0.5:
                # Arc pattern
                base_x = random.randint(300, self.level_width - 500)
                for j in range(5):
                    x = base_x + j * 30
                    y = 300 - abs(j - 2) * 40
                    coin = AnimatedCoin(x, y)
                    self.coins.add(coin)
            else:
                # Random placement
                x = random.randint(200, self.level_width - 100)
                y = random.randint(150, 450)
                coin = AnimatedCoin(x, y)
                self.coins.add(coin)
        
        # Add flag
        self.flag = GameObject(self.level_width - 200, 150, 30, 300, self.theme.accent_color)
    
    def generate_background(self):
        if self.theme.has_clouds:
            # Generate clouds
            for i in range(20):
                x = random.randint(0, self.level_width)
                y = random.randint(50, 200)
                size = random.randint(60, 120)
                cloud = Cloud(x, y, size)
                self.clouds.append(cloud)
        
        if self.theme.has_parallax:
            # Generate background objects (hills, trees, etc.)
            for i in range(0, self.level_width, 300):
                if random.random() > 0.5:
                    obj = {
                        'x': i + random.randint(-50, 50),
                        'y': SCREEN_HEIGHT - 100,
                        'width': random.randint(150, 250),
                        'height': random.randint(100, 200),
                        'color': self.blend_color_with_alpha(self.theme.platform_colors[0], 0.3),
                        'layer': random.choice([0.5, 0.7])  # Parallax depth
                    }
                    self.background_objects.append(obj)
    
    def blend_color_with_alpha(self, color, alpha):
        return tuple(int(c * alpha) for c in color)
    
    def update_camera(self, player_x):
        target_x = player_x - SCREEN_WIDTH // 2
        # Smooth camera movement
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_x = max(0, min(self.camera_x, self.level_width - SCREEN_WIDTH))
    
    def draw_gradient_background(self, screen):
        # Draw gradient sky
        for i, color in enumerate(self.theme.bg_gradient):
            y = i * (SCREEN_HEIGHT // len(self.theme.bg_gradient))
            height = SCREEN_HEIGHT // len(self.theme.bg_gradient) + 1
            
            # Smooth gradient between colors
            if i < len(self.theme.bg_gradient) - 1:
                next_color = self.theme.bg_gradient[i + 1]
                for j in range(height):
                    progress = j / height
                    blended = tuple(int(color[k] * (1 - progress) + next_color[k] * progress) 
                                  for k in range(3))
                    pygame.draw.line(screen, blended, (0, y + j), (SCREEN_WIDTH, y + j))
            else:
                pygame.draw.rect(screen, color, (0, y, SCREEN_WIDTH, height))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Super Mario Bros 2D - Modern Graphics Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        
        self.world_themes = [
            WorldTheme("Mushroom Kingdom", 
                      [(135, 206, 250), (180, 220, 255), (255, 255, 255)],
                      [(34, 180, 34), (20, 150, 20)], 
                      GOLD, (255, 255, 100), True, True),
            
            WorldTheme("Desert Dunes",
                      [(255, 200, 100), (255, 150, 50), (255, 100, 0)],
                      [(194, 154, 108), (164, 124, 78)],
                      SUNSET_ORANGE, (255, 200, 100), False, True),
            
            WorldTheme("Ocean Paradise",
                      [(0, 100, 200), (0, 150, 255), (100, 200, 255)],
                      [(0, 64, 128), (0, 100, 150)],
                      (173, 216, 230), (100, 150, 255), True, True),
            
            WorldTheme("Crystal Caverns",
                      [(100, 50, 150), (150, 100, 200), (200, 150, 255)],
                      [(105, 105, 150), (80, 80, 120)],
                      (200, 150, 255), (150, 100, 200), False, True),
            
            WorldTheme("Bowser's Castle",
                      [(50, 0, 0), (100, 20, 20), (150, 50, 50)],
                      [(139, 0, 0), (100, 0, 0)],
                      (255, 100, 0), (255, 50, 0), False, False)
        ]
        
        self.current_world_index = 0
        self.world = None
        self.player = None
        self.game_state = "MENU"
        self.score = 0
        self.high_score = 0
        self.transition_alpha = 0
        self.menu_animation = 0
    
    def start_world(self, world_index):
        self.current_world_index = world_index
        theme = self.world_themes[world_index]
        self.world = World(world_index + 1, theme)
        self.player = Player(*self.world.spawn_point)
        self.transition_alpha = 255
    
    def handle_collisions(self):
        # Platform collisions with improved physics
        self.player.on_ground = False
        for platform in self.world.platforms:
            if self.player.rect.colliderect(platform.rect):
                if self.player.vy > 0:  # Falling
                    self.player.rect.bottom = platform.rect.top
                    self.player.vy = 0
                    self.player.on_ground = True
                    
                    # Create landing particles
                    if not self.player.jump_particles_created:
                        for _ in range(5):
                            self.world.particle_system.add_particle(
                                self.player.rect.centerx + random.randint(-10, 10),
                                self.player.rect.bottom,
                                random.uniform(-2, 2), random.uniform(-2, 0),
                                self.world.theme.particle_color, 20, 2
                            )
                        self.player.jump_particles_created = True
                    
                    # Move with platform
                    if platform.is_moving:
                        self.player.rect.x += platform.move_speed * platform.direction
        
        # Update platforms
        for platform in self.world.platforms:
            platform.update()
        
        # Enemy collisions
        for enemy in self.world.enemies:
            if not enemy.alive:
                continue
            
            if self.player.rect.colliderect(enemy.rect):
                if self.player.vy > 0 and self.player.rect.bottom < enemy.rect.centery:
                    # Stomp enemy
                    enemy.alive = False
                    enemy.squash_timer = 10
                    self.world.particle_system.create_explosion(
                        enemy.rect.centerx, enemy.rect.centery,
                        (255, 100, 0), 15
                    )
                    self.world.enemies.remove(enemy)
                    self.score += 100
                    self.player.vy = JUMP_STRENGTH // 2
                elif self.player.invincible_timer > 0:
                    enemy.alive = False
                    self.world.particle_system.create_explosion(
                        enemy.rect.centerx, enemy.rect.centery,
                        GOLD, 20
                    )
                    self.world.enemies.remove(enemy)
                    self.score += 200
                else:
                    self.take_damage()
        
        # Power-up collisions
        for power_up in self.world.power_ups:
            if not power_up.collected and self.player.rect.colliderect(power_up.rect):
                power_up.collected = True
                self.world.particle_system.create_sparkle(
                    power_up.rect.centerx, power_up.rect.centery,
                    power_up.get_glow_color()
                )
                self.world.power_ups.remove(power_up)
                
                if power_up.power_type == PowerUpType.STAR:
                    self.player.invincible_timer = 600
                
                self.player.power_up = power_up.power_type
                self.player.create_character_sprite()
                self.score += 500
        
        # Coin collisions
        for coin in self.world.coins:
            if not coin.collected and self.player.rect.colliderect(coin.rect):
                coin.collected = True
                self.world.particle_system.create_sparkle(
                    coin.rect.centerx, coin.rect.centery, GOLD
                )
                self.world.coins.remove(coin)
                self.player.coins += 1
                self.score += 50
                
                if self.player.coins >= 100:
                    self.player.coins = 0
                    self.player.lives += 1
        
        # Fireball collisions
        for fireball in self.world.fireballs:
            # Platform bouncing
            for platform in self.world.platforms:
                if fireball.rect.colliderect(platform.rect):
                    fireball.vy = -8
                    fireball.bounces += 1
                    self.world.particle_system.create_sparkle(
                        fireball.rect.centerx, fireball.rect.centery,
                        (150, 200, 255) if fireball.is_ice else SUNSET_ORANGE
                    )
                    if fireball.bounces >= fireball.max_bounces:
                        self.world.fireballs.remove(fireball)
                        break
            
            # Enemy hits
            for enemy in self.world.enemies:
                if enemy.alive and fireball.rect.colliderect(enemy.rect):
                    enemy.alive = False
                    
                    if fireball.is_ice:
                        # Freeze effect
                        self.world.particle_system.create_explosion(
                            enemy.rect.centerx, enemy.rect.centery,
                            (150, 200, 255), 25
                        )
                    else:
                        # Burn effect
                        self.world.particle_system.create_explosion(
                            enemy.rect.centerx, enemy.rect.centery,
                            SUNSET_ORANGE, 20
                        )
                    
                    self.world.enemies.remove(enemy)
                    if fireball in self.world.fireballs:
                        self.world.fireballs.remove(fireball)
                    self.score += 150
        
        # Flag collision
        if self.world.flag and self.player.rect.colliderect(self.world.flag.rect):
            self.complete_level()
    
    def take_damage(self):
        if self.player.power_up in [PowerUpType.MUSHROOM, PowerUpType.FIRE_FLOWER, PowerUpType.ICE_FLOWER]:
            self.player.power_up = PowerUpType.NONE
            self.player.invincible_timer = 120
            self.player.create_character_sprite()
            
            # Damage particles
            self.world.particle_system.create_explosion(
                self.player.rect.centerx, self.player.rect.centery,
                BRIGHT_RED, 10
            )
        else:
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.game_over()
            else:
                self.respawn()
    
    def respawn(self):
        self.player.rect.x, self.player.rect.y = self.world.spawn_point
        self.player.vx = 0
        self.player.vy = 0
        self.player.power_up = PowerUpType.NONE
        self.player.create_character_sprite()
        self.player.invincible_timer = 180
        self.transition_alpha = 200
    
    def complete_level(self):
        # Victory particles
        for _ in range(50):
            self.world.particle_system.add_particle(
                self.world.flag.rect.centerx + random.randint(-50, 50),
                self.world.flag.rect.centery + random.randint(-100, 100),
                random.uniform(-5, 5), random.uniform(-5, 5),
                random.choice([GOLD, BRIGHT_RED, WHITE, self.world.theme.accent_color]),
                random.randint(40, 80), random.randint(2, 6), True
            )
        
        bonus_score = 1000 * (self.current_world_index + 1)
        self.score += bonus_score
        
        if self.current_world_index < len(self.world_themes) - 1:
            self.current_world_index += 1
            self.start_world(self.current_world_index)
        else:
            self.victory()
    
    def game_over(self):
        self.high_score = max(self.high_score, self.score)
        self.game_state = "GAME_OVER"
    
    def victory(self):
        self.high_score = max(self.high_score, self.score)
        self.game_state = "VICTORY"
    
    def shoot_fireball(self):
        if self.player.fire_cooldown == 0:
            if self.player.power_up == PowerUpType.FIRE_FLOWER:
                direction = 1 if self.player.facing_right else -1
                fireball = Fireball(
                    self.player.rect.centerx + direction * 20,
                    self.player.rect.centery,
                    direction, False
                )
                self.world.fireballs.add(fireball)
                self.player.fire_cooldown = 20
                
                # Shooting particles
                self.world.particle_system.create_sparkle(
                    fireball.rect.centerx, fireball.rect.centery, SUNSET_ORANGE
                )
                
            elif self.player.power_up == PowerUpType.ICE_FLOWER:
                direction = 1 if self.player.facing_right else -1
                fireball = Fireball(
                    self.player.rect.centerx + direction * 20,
                    self.player.rect.centery,
                    direction, True
                )
                self.world.fireballs.add(fireball)
                self.player.fire_cooldown = 25
                
                # Ice particles
                self.world.particle_system.create_sparkle(
                    fireball.rect.centerx, fireball.rect.centery, (150, 200, 255)
                )
    
    def update(self):
        if self.game_state != "PLAYING":
            self.menu_animation += 1
            return
        
        # Update player
        self.player.update()
        
        # Create running particles
        if abs(self.player.vx) > MOVE_SPEED and self.player.on_ground and random.random() > 0.7:
            self.world.particle_system.add_particle(
                self.player.rect.centerx - self.player.vx,
                self.player.rect.bottom,
                -self.player.vx * 0.2, -1,
                self.world.theme.particle_color, 15, 2
            )
        
        # Update world objects
        for enemy in self.world.enemies:
            enemy.update()
        
        for coin in self.world.coins:
            coin.update()
        
        for power_up in self.world.power_ups:
            power_up.update()
        
        for fireball in self.world.fireballs:
            fireball.update()
            
            # Fireball trail
            if random.random() > 0.3:
                color = (150, 200, 255) if fireball.is_ice else SUNSET_ORANGE
                self.world.particle_system.add_particle(
                    fireball.rect.centerx, fireball.rect.centery,
                    random.uniform(-1, 1), random.uniform(-1, 1),
                    color, 10, 2, False
                )
            
            # Remove off-screen fireballs
            if fireball.rect.x < 0 or fireball.rect.x > self.world.level_width:
                self.world.fireballs.remove(fireball)
        
        # Update clouds
        for cloud in self.world.clouds:
            cloud.update()
            if cloud.x > self.world.level_width + 200:
                cloud.x = -200
        
        # Update particles
        self.world.particle_system.update()
        
        # Handle collisions
        self.handle_collisions()
        
        # Keep player in bounds
        self.player.rect.x = max(0, min(self.player.rect.x, self.world.level_width - self.player.rect.width))
        if self.player.rect.y > SCREEN_HEIGHT:
            self.take_damage()
        
        # Update camera
        self.world.update_camera(self.player.rect.centerx)
        
        # Update transition
        if self.transition_alpha > 0:
            self.transition_alpha -= 5
    
    def render_menu(self):
        # Animated gradient background
        self.world_themes[0].bg_gradient[0] = (
            135 + math.sin(self.menu_animation * 0.01) * 20,
            206 + math.cos(self.menu_animation * 0.015) * 20,
            250
        )
        
        # Draw gradient
        for i in range(SCREEN_HEIGHT):
            progress = i / SCREEN_HEIGHT
            color = (
                135 + progress * 50,
                206 - progress * 50,
                250 - progress * 100
            )
            pygame.draw.line(self.screen, color, (0, i), (SCREEN_WIDTH, i))
        
        # Floating particles
        for _ in range(2):
            if random.random() > 0.95:
                x = random.randint(0, SCREEN_WIDTH)
                y = SCREEN_HEIGHT
                self.world_themes[0].bg_gradient
        
        # Title with glow effect
        title_surf = pygame.Surface((600, 100), pygame.SRCALPHA)
        
        # Glow
        for i in range(5):
            glow_alpha = 100 - i * 20
            glow_size = 48 + i * 4
            title_text = pygame.font.Font(None, glow_size).render("SUPER MARIO BROS 2D", True, 
                                                                  (*GOLD, glow_alpha))
            title_rect = title_text.get_rect(center=(300, 50))
            title_surf.blit(title_text, title_rect)
        
        # Main title
        title_text = self.font.render("SUPER MARIO BROS 2D", True, WHITE)
        title_rect = title_text.get_rect(center=(300, 50))
        title_surf.blit(title_text, title_rect)
        
        self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - 300, 80))
        
        # Subtitle
        subtitle_text = self.font.render("Modern Graphics Edition", True, GOLD)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # World selection with preview boxes
        for i, theme in enumerate(self.world_themes):
            y = 300 + i * 80
            
            # Preview box
            preview_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, y - 20, 500, 60)
            
            # Gradient background for each world
            for j in range(60):
                progress = j / 60
                if len(theme.bg_gradient) > 1:
                    color = tuple(int(theme.bg_gradient[0][k] * (1 - progress) + 
                                    theme.bg_gradient[1][k] * progress) for k in range(3))
                else:
                    color = theme.bg_gradient[0]
                pygame.draw.line(self.screen, color, 
                               (preview_rect.left, preview_rect.top + j),
                               (preview_rect.right, preview_rect.top + j))
            
            # Border
            pygame.draw.rect(self.screen, theme.accent_color, preview_rect, 3)
            
            # Hover effect
            if preview_rect.collidepoint(pygame.mouse.get_pos()):
                hover_surf = pygame.Surface((500, 60), pygame.SRCALPHA)
                pygame.draw.rect(hover_surf, (*theme.accent_color, 50), hover_surf.get_rect())
                self.screen.blit(hover_surf, preview_rect)
                
                # Pulsing border
                pulse = abs(math.sin(self.menu_animation * 0.1))
                pygame.draw.rect(self.screen, 
                               tuple(int(c + (255 - c) * pulse) for c in theme.accent_color),
                               preview_rect.inflate(4, 4), 3)
            
            # World text
            world_text = self.small_font.render(f"[{i+1}] World {i+1}: {theme.name}", True, WHITE)
            world_rect = world_text.get_rect(center=(SCREEN_WIDTH // 2, y + 10))
            self.screen.blit(world_text, world_rect)
        
        # Controls
        controls_surf = pygame.Surface((600, 40), pygame.SRCALPHA)
        pygame.draw.rect(controls_surf, (0, 0, 0, 100), controls_surf.get_rect(), border_radius=10)
        self.screen.blit(controls_surf, (SCREEN_WIDTH // 2 - 300, 680))
        
        controls_text = self.small_font.render("↑↓←→ Move | SPACE Jump | X Fire/Ice | SHIFT Run", True, WHITE)
        controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH // 2, 700))
        self.screen.blit(controls_text, controls_rect)
        
        # High score with glow
        if self.high_score > 0:
            high_score_text = self.small_font.render(f"High Score: {self.high_score:,}", True, GOLD)
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, 750))
            
            # Glow effect
            for i in range(3):
                glow_surf = pygame.Surface((300, 40), pygame.SRCALPHA)
                pygame.draw.ellipse(glow_surf, (*GOLD, 30 - i * 10), glow_surf.get_rect())
                self.screen.blit(glow_surf, (high_score_rect.left - 50, high_score_rect.top - 5))
            
            self.screen.blit(high_score_text, high_score_rect)
    
    def render_game(self):
        # Draw gradient background
        self.world.draw_gradient_background(self.screen)
        
        # Draw parallax background objects
        for obj in self.world.background_objects:
            draw_x = obj['x'] - self.world.camera_x * obj['layer']
            if -obj['width'] < draw_x < SCREEN_WIDTH:
                # Mountain/hill shape
                points = [
                    (draw_x, obj['y'] + obj['height']),
                    (draw_x + obj['width'] // 4, obj['y']),
                    (draw_x + obj['width'] * 3 // 4, obj['y'] + obj['height'] // 3),
                    (draw_x + obj['width'], obj['y'] + obj['height'])
                ]
                pygame.draw.polygon(self.screen, obj['color'], points)
        
        # Draw clouds
        for cloud in self.world.clouds:
            cloud.draw(self.screen, self.world.camera_x)
        
        # Draw shadows for all objects
        shadow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        for platform in self.world.platforms:
            adjusted_rect = platform.rect.copy()
            adjusted_rect.x -= self.world.camera_x
            if -platform.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                shadow_rect = adjusted_rect.copy()
                shadow_rect.y += 5
                pygame.draw.rect(shadow_surf, (0, 0, 0, 50), shadow_rect)
        
        self.screen.blit(shadow_surf, (0, 0))
        
        # Draw world objects
        for platform in self.world.platforms:
            adjusted_rect = platform.rect.copy()
            adjusted_rect.x -= self.world.camera_x
            if -platform.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                self.screen.blit(platform.image, adjusted_rect)
        
        # Draw collectibles with glow
        for coin in self.world.coins:
            if not coin.collected:
                adjusted_rect = coin.rect.copy()
                adjusted_rect.x -= self.world.camera_x
                if -coin.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                    # Glow
                    glow_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, (*GOLD, 30), (24, 24), 20)
                    self.screen.blit(glow_surf, (adjusted_rect.x - 12, adjusted_rect.y - 12))
                    # Coin
                    self.screen.blit(coin.image, adjusted_rect)
        
        for power_up in self.world.power_ups:
            if not power_up.collected:
                adjusted_rect = power_up.rect.copy()
                adjusted_rect.x -= self.world.camera_x
                if -power_up.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                    self.screen.blit(power_up.image, adjusted_rect)
        
        # Draw enemies
        for enemy in self.world.enemies:
            if enemy.alive:
                adjusted_rect = enemy.rect.copy()
                adjusted_rect.x -= self.world.camera_x
                if -enemy.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                    self.screen.blit(enemy.image, adjusted_rect)
        
        # Draw fireballs with trail
        for fireball in self.world.fireballs:
            # Draw trail
            for i, pos in enumerate(fireball.trail_positions):
                alpha = 100 * (i / len(fireball.trail_positions))
                trail_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                color = (150, 200, 255) if fireball.is_ice else SUNSET_ORANGE
                pygame.draw.circle(trail_surf, (*color, int(alpha)), (4, 4), 4 - i)
                self.screen.blit(trail_surf, (pos[0] - self.world.camera_x - 4, pos[1] - 4))
            
            # Draw fireball
            adjusted_rect = fireball.rect.copy()
            adjusted_rect.x -= self.world.camera_x
            if -fireball.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                self.screen.blit(fireball.image, adjusted_rect)
        
        # Draw flag with glow
        if self.world.flag:
            adjusted_rect = self.world.flag.rect.copy()
            adjusted_rect.x -= self.world.camera_x
            if -self.world.flag.rect.width < adjusted_rect.x < SCREEN_WIDTH:
                # Pulsing glow
                glow_size = 40 + math.sin(pygame.time.get_ticks() * 0.005) * 10
                glow_surf = pygame.Surface((int(glow_size * 2), int(glow_size * 2)), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.world.theme.accent_color, 50), 
                                 (int(glow_size), int(glow_size)), int(glow_size))
                self.screen.blit(glow_surf, 
                               (adjusted_rect.centerx - glow_size, adjusted_rect.centery - glow_size))
                self.screen.blit(self.world.flag.image, adjusted_rect)
        
        # Draw player
        adjusted_rect = self.player.rect.copy()
        adjusted_rect.x -= self.world.camera_x
        
        # Player shadow
        shadow_surf = pygame.Surface((self.player.rect.width + 10, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 50), shadow_surf.get_rect())
        self.screen.blit(shadow_surf, (adjusted_rect.x - 5, adjusted_rect.bottom - 5))
        
        # Draw player with flashing
        if self.player.invincible_timer == 0 or self.player.invincible_timer % 10 < 5:
            self.screen.blit(self.player.image, adjusted_rect)
        
        # Draw particles
        self.world.particle_system.draw(self.screen, self.world.camera_x)
        
        # Draw HUD
        self.render_hud()
        
        # Transition effect
        if self.transition_alpha > 0:
            transition_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            transition_surf.fill((255, 255, 255, self.transition_alpha))
            self.screen.blit(transition_surf, (0, 0))
    
    def render_hud(self):
        # HUD background
        hud_surf = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, (0, 0, 0, 100), hud_surf.get_rect())
        pygame.draw.line(hud_surf, (*self.world.theme.accent_color, 200), 
                        (0, 99), (SCREEN_WIDTH, 99), 2)
        self.screen.blit(hud_surf, (0, 0))
        
        # Score with style
        score_text = self.small_font.render(f"SCORE: {self.score:,}", True, WHITE)
        self.screen.blit(score_text, (20, 15))
        
        # Lives with heart icons
        lives_text = self.small_font.render("LIVES:", True, WHITE)
        self.screen.blit(lives_text, (20, 45))
        for i in range(self.player.lives):
            heart_x = 120 + i * 35
            # Draw heart shape
            heart_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(heart_surf, BRIGHT_RED, (10, 12), 6)
            pygame.draw.circle(heart_surf, BRIGHT_RED, (20, 12), 6)
            points = [(5, 16), (15, 26), (25, 16)]
            pygame.draw.polygon(heart_surf, BRIGHT_RED, points)
            self.screen.blit(heart_surf, (heart_x, 42))
        
        # Coins with spinning icon
        coin_icon = pygame.Surface((30, 30), pygame.SRCALPHA)
        coin_scale = abs(math.cos(pygame.time.get_ticks() * 0.005))
        if coin_scale < 0.1:
            coin_scale = 0.1
        coin_width = int(20 * coin_scale)
        pygame.draw.ellipse(coin_icon, GOLD, (15 - coin_width // 2, 5, coin_width, 20))
        if coin_scale > 0.3:
            pygame.draw.ellipse(coin_icon, (255, 245, 100), (15 - coin_width // 2 + 2, 7, coin_width - 4, 16))
        
        self.screen.blit(coin_icon, (250, 40))
        coins_text = self.small_font.render(f"× {self.player.coins}", True, WHITE)
        self.screen.blit(coins_text, (285, 45))
        
        # World info
        world_text = self.small_font.render(f"WORLD {self.current_world_index + 1}", True, WHITE)
        self.screen.blit(world_text, (SCREEN_WIDTH - 200, 15))
        
        world_name = self.small_font.render(self.world.theme.name.upper(), True, 
                                           self.world.theme.accent_color)
        self.screen.blit(world_name, (SCREEN_WIDTH - 200, 45))
        
        # Power-up indicator with icon
        if self.player.power_up != PowerUpType.NONE:
            power_rect = pygame.Rect(SCREEN_WIDTH // 2 - 60, 20, 120, 60)
            pygame.draw.rect(self.screen, self.world.theme.accent_color, power_rect, 3)
            
            power_names = {
                PowerUpType.MUSHROOM: "SUPER",
                PowerUpType.FIRE_FLOWER: "FIRE",
                PowerUpType.STAR: "STAR",
                PowerUpType.ICE_FLOWER: "ICE"
            }
            
            power_text = self.small_font.render(power_names[self.player.power_up], True, WHITE)
            power_text_rect = power_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            
            # Glow effect for power-up text
            for i in range(3):
                glow_surf = pygame.Surface((140, 70), pygame.SRCALPHA)
                glow_alpha = 30 - i * 10
                pygame.draw.rect(glow_surf, (*self.world.theme.accent_color, glow_alpha), 
                               glow_surf.get_rect(), border_radius=10)
                self.screen.blit(glow_surf, (SCREEN_WIDTH // 2 - 70, 15))
            
            self.screen.blit(power_text, power_text_rect)
    
    def render_game_over(self):
        # Dark gradient background
        for i in range(SCREEN_HEIGHT):
            progress = i / SCREEN_HEIGHT
            color = (50 - progress * 50, 0, 0)
            pygame.draw.line(self.screen, color, (0, i), (SCREEN_WIDTH, i))
        
        # Falling particles
        if random.random() > 0.9:
            x = random.randint(0, SCREEN_WIDTH)
            # Particles would be managed by a persistent particle system
        
        # Game Over text with dramatic effect
        game_over_surf = pygame.Surface((600, 150), pygame.SRCALPHA)
        
        # Red glow
        for i in range(10):
            glow_alpha = 100 - i * 10
            glow_text = pygame.font.Font(None, 72 + i * 2).render("GAME OVER", True, 
                                                                 (255, 0, 0, glow_alpha))
            glow_rect = glow_text.get_rect(center=(300, 75))
            game_over_surf.blit(glow_text, glow_rect)
        
        # Main text
        game_over_text = pygame.font.Font(None, 72).render("GAME OVER", True, WHITE)
        game_over_rect = game_over_text.get_rect(center=(300, 75))
        game_over_surf.blit(game_over_text, game_over_rect)
        
        self.screen.blit(game_over_surf, (SCREEN_WIDTH // 2 - 300, 200))
        
        # Score display
        score_text = self.font.render(f"Final Score: {self.score:,}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 400))
        self.screen.blit(score_text, score_rect)
        
        if self.score >= self.high_score:
            # New high score animation
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
            high_color = tuple(int(255 * pulse + c * (1 - pulse)) for c in GOLD)
            new_high_text = self.font.render("NEW HIGH SCORE!", True, high_color)
            new_high_rect = new_high_text.get_rect(center=(SCREEN_WIDTH // 2, 480))
            self.screen.blit(new_high_text, new_high_rect)
        
        # Continue prompt
        continue_text = self.small_font.render("Press SPACE to return to menu", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, 600))
        
        # Blinking effect
        if pygame.time.get_ticks() % 1000 < 700:
            self.screen.blit(continue_text, continue_rect)
    
    def render_victory(self):
        # Rainbow gradient background
        for i in range(SCREEN_HEIGHT):
            hue = (i / SCREEN_HEIGHT + pygame.time.get_ticks() * 0.0001) % 1
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 1)
            color = tuple(int(c * 255) for c in rgb)
            pygame.draw.line(self.screen, color, (0, i), (SCREEN_WIDTH, i))
        
        # Fireworks effect (simplified)
        if random.random() > 0.95:
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = random.randint(100, 300)
            # Create burst of particles
        
        # Victory text with golden glow
        victory_surf = pygame.Surface((800, 200), pygame.SRCALPHA)
        
        # Golden rays
        for i in range(12):
            angle = i * 30 + pygame.time.get_ticks() * 0.1
            x1 = 400 + math.cos(math.radians(angle)) * 100
            y1 = 100 + math.sin(math.radians(angle)) * 100
            x2 = 400 + math.cos(math.radians(angle)) * 300
            y2 = 100 + math.sin(math.radians(angle)) * 300
            pygame.draw.line(victory_surf, (*GOLD, 50), (x1, y1), (x2, y2), 3)
        
        # Main text
        victory_text = pygame.font.Font(None, 96).render("VICTORY!", True, GOLD)
        victory_rect = victory_text.get_rect(center=(400, 100))
        victory_surf.blit(victory_text, victory_rect)
        
        self.screen.blit(victory_surf, (SCREEN_WIDTH // 2 - 400, 100))
        
        # Completion message
        complete_text = self.font.render("All 5 Worlds Completed!", True, WHITE)
        complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH // 2, 300))
        self.screen.blit(complete_text, complete_rect)
        
        # Score with celebration
        score_surf = pygame.Surface((600, 100), pygame.SRCALPHA)
        pygame.draw.rect(score_surf, (0, 0, 0, 100), score_surf.get_rect(), border_radius=20)
        pygame.draw.rect(score_surf, GOLD, score_surf.get_rect(), 3, border_radius=20)
        self.screen.blit(score_surf, (SCREEN_WIDTH // 2 - 300, 380))
        
        score_text = self.font.render(f"Final Score: {self.score:,}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 430))
        self.screen.blit(score_text, score_rect)
        
        if self.score >= self.high_score:
            # Trophy icon
            trophy_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            # Draw trophy shape
            pygame.draw.ellipse(trophy_surf, GOLD, (10, 10, 40, 30))
            pygame.draw.rect(trophy_surf, GOLD, (25, 35, 10, 15))
            pygame.draw.rect(trophy_surf, GOLD, (15, 45, 30, 10))
            self.screen.blit(trophy_surf, (SCREEN_WIDTH // 2 - 30, 500))
            
            new_record_text = self.small_font.render("NEW RECORD!", True, GOLD)
            new_record_rect = new_record_text.get_rect(center=(SCREEN_WIDTH // 2, 580))
            self.screen.blit(new_record_text, new_record_rect)
        
        # Continue prompt with animation
        continue_alpha = 128 + 127 * math.sin(pygame.time.get_ticks() * 0.003)
        continue_surf = pygame.Surface((500, 40), pygame.SRCALPHA)
        continue_text = self.small_font.render("Press SPACE to return to menu", True, 
                                              (*WHITE, int(continue_alpha)))
        continue_rect = continue_text.get_rect(center=(250, 20))
        continue_surf.blit(continue_text, continue_rect)
        self.screen.blit(continue_surf, (SCREEN_WIDTH // 2 - 250, 650))
    
    def render(self):
        if self.game_state == "MENU":
            self.render_menu()
        elif self.game_state == "PLAYING":
            self.render_game()
        elif self.game_state == "GAME_OVER":
            self.render_game_over()
        elif self.game_state == "VICTORY":
            self.render_victory()
        
        pygame.display.flip()
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        if self.game_state == "MENU":
            # Number keys or mouse click to select world
            for i in range(1, 6):
                if keys[getattr(pygame, f'K_{i}')]:
                    if i - 1 < len(self.world_themes):
                        self.start_world(i - 1)
                        self.game_state = "PLAYING"
                        self.score = 0
                        break
            
            # Mouse selection
            if pygame.mouse.get_pressed()[0]:
                mouse_pos = pygame.mouse.get_pos()
                for i in range(len(self.world_themes)):
                    y = 300 + i * 80
                    rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, y - 20, 500, 60)
                    if rect.collidepoint(mouse_pos):
                        self.start_world(i)
                        self.game_state = "PLAYING"
                        self.score = 0
                        break
        
        elif self.game_state == "PLAYING":
            # Movement
            self.player.vx = 0
            
            if keys[pygame.K_LEFT]:
                self.player.vx = -MOVE_SPEED
                self.player.facing_right = False
            if keys[pygame.K_RIGHT]:
                self.player.vx = MOVE_SPEED
                self.player.facing_right = True
            
            # Run with shift
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                self.player.vx *= 1.7
                
                # Speed particles
                if self.player.on_ground and abs(self.player.vx) > MOVE_SPEED:
                    self.world.particle_system.create_trail(
                        self.player.rect.centerx,
                        self.player.rect.bottom,
                        self.world.theme.particle_color,
                        1 if self.player.vx > 0 else -1
                    )
            
            if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
                self.player.jump()
            
            if keys[pygame.K_x]:
                self.shoot_fireball()
        
        elif self.game_state in ["GAME_OVER", "VICTORY"]:
            if keys[pygame.K_SPACE]:
                self.game_state = "MENU"
                self.menu_animation = 0
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_state == "PLAYING":
                            self.game_state = "MENU"
                        else:
                            running = False
            
            self.handle_input()
            self.update()
            self.render()
            self.clock.tick(FPS)
        
        pygame.quit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
