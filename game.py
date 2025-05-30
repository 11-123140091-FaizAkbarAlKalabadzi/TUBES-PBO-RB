# Import library yang diperlukan
import pygame
import sys
import math
import random

# Inisialisasi Pygame
pygame.init()

# ------------------------- KONFIGURASI DASAR -------------------------
# Ukuran map dan layar
map_width, map_height = 2400, 600  # Ukuran dunia game
screen_width, screen_height = 800, 600  # Ukuran tampilan layar
ground_height = 85  # Tinggi tanah dari bawah layar

# Inisialisasi layar utama
screen = pygame.display.set_mode((screen_width, screen_height))

# ------------------------- LOAD ASSETS -------------------------
# Load gambar background dan karakter
sky_image = pygame.image.load('BG.png')
original_idle = pygame.image.load('Idle.png').convert_alpha()

# Load dan scale gambar karakter utama
character_image_right = pygame.transform.scale(original_idle, (80, 80))
attack_images_right = [pygame.transform.scale(pygame.image.load(f'Serang{i}.png').convert_alpha(), (80, 80)) for i in range(2)]

# Load dan scale gambar enemy
enemy_run_images_right = [pygame.transform.scale(pygame.image.load(f'KananEnemy{i}.png').convert_alpha(), (80, 80)) for i in range(7)]
enemy_attack_images_right = [pygame.transform.scale(pygame.image.load(f'SerangEnemy{i}.png').convert_alpha(), (80, 80)) for i in range(2)]

# Buat versi flip horizontal untuk arah kiri
character_image_left = pygame.transform.flip(character_image_right, True, False)
attack_images_left = [pygame.transform.flip(img, True, False) for img in attack_images_right]
enemy_run_images_left = [pygame.transform.flip(img, True, False) for img in enemy_run_images_right]
enemy_attack_images_left = [pygame.transform.flip(img, True, False) for img in enemy_attack_images_right]

# ------------------------- VARIABEL KARAKTER UTAMA -------------------------
character_image = character_image_right  # Gambar default menghadap kanan
character_rect = character_image.get_rect()  # Hitbox karakter
character_rect.x = 100  # Posisi awal x
character_rect.y = map_height - ground_height - character_rect.height  # Posisi awal y

# Variabel pergerakan karakter
character_velocity = 5  # Kecepatan gerakan horizontal
is_jumping = False
jump_count = 10
direction = "right"  # Arah hadap karakter
vertical_velocity = 0  # Kecepatan vertikal (untuk lompat)
gravity = 0.5  # Gaya gravitasi
jump_strength = -10  # Kekuatan lompat
on_ground = True  # Status apakah karakter di tanah

# ------------------------- SISTEM STATISTIK KARAKTER -------------------------
choose_upgrade = False  # Flag untuk menampilkan pilihan upgrade
upgrade_message = ""  # Pesan upgrade

max_hp = 100  # HP maksimum
current_hp = 100  # HP saat ini
strength = 10  # Kekuatan serangan
max_hearts = 2  # Jumlah nyawa maksimum
current_hearts = 2  # Nyawa saat ini

# ------------------------- SISTEM KAMERA -------------------------
camera_x = 0  # Posisi kamera horizontal
camera_y = 0  # Posisi kamera vertikal

# ------------------------- KELAS ENEMY -------------------------
class Enemy:
    def __init__(self, x, y):
        # Properti dasar enemy
        self.rect = pygame.Rect(x, y, 80, 80)  # Hitbox enemy
        self.max_hp = 50  # HP maksimum
        self.current_hp = 50  # HP saat ini
        self.strength = 5  # Kekuatan serangan
        self.attack_cooldown = 0  # Cooldown serangan
        self.is_alive = True  # Status hidup/mati
        
        # Properti pergerakan enemy
        self.start_x = x  # Posisi x awal untuk patroli
        self.move_range = 100  # Jarak patroli maksimal
        self.move_speed = 2  # Kecepatan gerakan
        self.moving_right = True  # Arah gerakan
        
        # Animasi enemy
        self.run_images_right = enemy_run_images_right
        self.run_images_left = enemy_run_images_left
        self.attack_images_right = enemy_attack_images_right
        self.attack_images_left = enemy_attack_images_left
        self.direction = "right"  # Arah hadap
        self.run_frame = 0  # Frame animasi berjalan
        self.animation_timer = 0  # Timer animasi
        self.animation_speed = 0.2  # Kecepatan animasi
        self.just_died = False  # Flag kematian baru
        self.attacking = False  # Status sedang menyerang
        self.attack_frame = 0  # Frame animasi serangan
        self.attack_animation_timer = 0  # Timer animasi serangan
        self.attack_animation_speed = 0.15  # Kecepatan animasi serangan

    def draw(self, camera_x, camera_y):
        """Menggambar enemy di layar"""
        if not self.is_alive:
            return
            
        # Pilih gambar berdasarkan status (menyerang/berjalan)
        if self.attacking:
            image = self.attack_images_right[self.attack_frame] if self.direction == "right" else self.attack_images_left[self.attack_frame]
        else:
            image = self.run_images_right[self.run_frame] if self.direction == "right" else self.run_images_left[self.run_frame]
            
        # Gambar enemy dan health bar
        screen.blit(image, (self.rect.x - camera_x, self.rect.y - camera_y))
        hp_bar_width = 80
        hp_bar_height = 5
        hp_ratio = self.current_hp / self.max_hp
        pygame.draw.rect(screen, (255, 0, 0), (self.rect.x - camera_x, self.rect.y - camera_y - 10, hp_bar_width * hp_ratio, hp_bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (self.rect.x - camera_x, self.rect.y - camera_y - 10, hp_bar_width, hp_bar_height), 1)

    def attack(self, character_rect, character_hp):
        """Logika serangan enemy ke karakter utama"""
        if not self.is_alive:
            return character_hp
            
        # Cek collision dan cooldown
        if self.rect.colliderect(character_rect) and self.attack_cooldown <= 0:
            character_hp -= self.strength
            self.attack_cooldown = 30
            self.attacking = True  # Trigger animasi serangan
            self.attack_frame = 0
            self.attack_animation_timer = 0
            return character_hp
        return character_hp

    def update(self, character_rect):
        """Update logika enemy setiap frame"""
        if not self.is_alive:
            return
            
        # Update cooldown serangan
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            
        # Update animasi serangan
        if self.attacking:
            self.attack_animation_timer += 1/60
            if self.attack_animation_timer >= self.attack_animation_speed:
                self.attack_frame += 1
                self.attack_animation_timer = 0
                if self.attack_frame >= len(self.attack_images_right):
                    self.attacking = False
                    
        # Logika patroli (jika tidak dekat dengan karakter)
        dx = abs(self.rect.centerx - character_rect.centerx)
        if dx < 150:  # Jika dekat dengan karakter, berhenti bergerak
            return
            
        if not self.attacking:
            # Gerakan patroli kiri-kanan
            if self.moving_right:
                self.rect.x += self.move_speed
                if self.rect.x > self.start_x + self.move_range:
                    self.moving_right = False
            else:
                self.rect.x -= self.move_speed
                if self.rect.x < self.start_x - self.move_range:
                    self.moving_right = True
                    
        # Cek kematian enemy
        if self.current_hp <= 0:
            self.is_alive = False
            self.just_died = True
            
        # Update arah hadap berdasarkan gerakan
        self.direction = "right" if self.moving_right else "left"
        
        # Update animasi berjalan
        if not self.attacking:
            self.animation_timer += 1/60
            if self.animation_timer >= self.animation_speed:
                self.run_frame = (self.run_frame + 1) % len(self.run_images_right)
                self.animation_timer = 0

# ------------------------- INISIALISASI ENEMY -------------------------
enemies = [
    Enemy(500, map_height - ground_height - 80),
    Enemy(900, map_height - ground_height - 80),
    Enemy(1300, map_height - ground_height - 80),
    Enemy(1700, map_height - ground_height - 80),
    Enemy(2100, map_height - ground_height - 80)
]

# ------------------------- FUNGSI UTILITAS -------------------------
def draw_map():
    """Menggambar background dengan tiling horizontal"""
    bg_width = sky_image.get_width()
    bg_repeat = math.ceil(map_width / bg_width) + 1
    for i in range(bg_repeat):
        bg_x = i * bg_width - camera_x % bg_width
        screen.blit(sky_image, (bg_x, -camera_y))

def draw_stats():
    """Menggambar HUD statistik karakter"""
    # Health bar
    hp_bar_width = 200
    hp_bar_height = 20
    hp_ratio = current_hp / max_hp
    pygame.draw.rect(screen, (255, 0, 0), (10, 10, hp_bar_width * hp_ratio, hp_bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (10, 10, hp_bar_width, hp_bar_height), 2)
    
    # Strength text
    font = pygame.font.SysFont(None, 24)
    str_text = font.render(f"STR: {strength}", True, (255, 165, 0))
    screen.blit(str_text, (10, 40))
    
    # Hearts (nyawa)
    heart_size = 30
    for i in range(current_hearts):
        pygame.draw.rect(screen, (255, 0, 0), (10 + i * (heart_size + 5), 70, heart_size, heart_size))

def update_camera():
    """Update posisi kamera untuk mengikuti karakter"""
    global camera_x, camera_y
    camera_x = character_rect.centerx - screen_width // 2  # Pusatkan kamera ke karakter
    camera_y = character_rect.centery - screen_height // 2
    
    # Batasi kamera agar tidak keluar dari map
    camera_x = max(0, min(camera_x, map_width - screen_width))
    camera_y = max(0, min(camera_y, map_height - screen_height))

# ------------------------- LOAD ANIMASI KARAKTER -------------------------
run_images_right = [pygame.transform.scale(pygame.image.load(f'Kanan{i}.png').convert_alpha(), (80, 80)) for i in range(7)]
run_images_left = [pygame.transform.flip(img, True, False) for img in run_images_right]

# Variabel animasi karakter
run_frame = 0
animation_timer = 0
animation_speed = 0.1
attacking = False
attack_frame = 0
attack_animation_timer = 0
attack_animation_speed = 0.1

# Variabel serangan karakter
attack_range = 50  # Jarak serangan
attack_cooldown = 0  # Timer cooldown
attack_cooldown_time = 30  # Durasi cooldown

def show_game_over():
    """Menampilkan layar game over"""
    font = pygame.font.SysFont(None, 72)
    text = font.render("Game Over", True, (255, 0, 0))
    rect = text.get_rect(center=(screen_width // 2, screen_height // 2))
    screen.blit(text, rect)
    pygame.display.flip()
    pygame.time.wait(2000)

# ------------------------- SISTEM MENU -------------------------
menu_active = True
font = pygame.font.SysFont(None, 48)

def draw_main_menu():
    """Menggambar menu utama"""
    draw_map()
    title_text = font.render("PETUALANGAN ANOMALI", True, (255, 255, 255))
    play_text = font.render("Press ENTER to Play", True, (0, 255, 0))
    exit_text = font.render("Press ESC to Exit", True, (255, 0, 0))
    screen.blit(title_text, (screen_width//2 - title_text.get_width()//2, 200))
    screen.blit(play_text, (screen_width//2 - play_text.get_width()//2, 300))
    screen.blit(exit_text, (screen_width//2 - exit_text.get_width()//2, 360))
    pygame.display.flip()

def draw_upgrade_message():
    """Menampilkan pesan pilihan upgrade"""
    if choose_upgrade:
        font = pygame.font.SysFont(None, 36)
        text = font.render(upgrade_message, True, (255, 0, 0))
        rect = text.get_rect(center=(screen_width // 2, screen_height // 2))
        screen.blit(text, rect)

# ------------------------- GAME LOOP -------------------------
clock = pygame.time.Clock()

while True:
    dt = clock.tick(60) / 1000  # Delta time untuk frame rate konsisten

    # Tampilkan menu jika aktif
    if menu_active:
        draw_main_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    menu_active = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        continue

    # Handle event quit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Input keyboard
    keys = pygame.key.get_pressed()

    # Handle pilihan upgrade
    if choose_upgrade:
        if keys[pygame.K_h]:  # Upgrade HP
            max_hp += 20
            current_hp = max_hp
            choose_upgrade = False
        elif keys[pygame.K_s]:  # Upgrade Strength
            strength += 5
            choose_upgrade = False
    else:
        # Gerakan karakter kiri-kanan
        if keys[pygame.K_LEFT]:
            character_rect.x -= character_velocity
            direction = "left"
            character_image = character_image_left
        if keys[pygame.K_RIGHT]:
            character_rect.x += character_velocity
            direction = "right"
            character_image = character_image_right
        character_rect.x = max(0, min(character_rect.x, map_width - character_rect.width))

        # Animasi berjalan
        moving = False
        if keys[pygame.K_LEFT]:
            character_rect.x -= character_velocity
            direction = "left"
            moving = True
        elif keys[pygame.K_RIGHT]:
            character_rect.x += character_velocity
            direction = "right"
            moving = True

        character_rect.x = max(0, min(character_rect.x, map_width - character_rect.width))

        if moving:
            animation_timer += dt
            if animation_timer >= animation_speed:
                run_frame = (run_frame + 1) % len(run_images_right)
                animation_timer = 0
            character_image = run_images_right[run_frame] if direction == "right" else run_images_left[run_frame]
        else:
            run_frame = 0
            character_image = character_image_right if direction == "right" else character_image_left

        # Animasi serangan
        if attacking:
            attack_animation_timer += dt
            if attack_animation_timer >= attack_animation_speed:
                attack_frame += 1
                attack_animation_timer = 0
            if attack_frame >= len(attack_images_right):
                attack_frame = 0
                attacking = False
            character_image = attack_images_right[attack_frame] if direction == "right" else attack_images_left[attack_frame]

        # Lompat
        if keys[pygame.K_SPACE] and on_ground:
            vertical_velocity = jump_strength
            on_ground = False

        # Pergerakan vertikal (gravitasi)
        character_rect.y += vertical_velocity
        vertical_velocity += gravity

        # Cek collision dengan tanah
        if character_rect.y >= map_height - ground_height - character_rect.height:
            character_rect.y = map_height - ground_height - character_rect.height
            vertical_velocity = 0
            on_ground = True

        # Update semua enemy
        for enemy in enemies:
            enemy.update(character_rect)
            current_hp = enemy.attack(character_rect, current_hp)

        # Cek game over
        if current_hp <= 0:
            current_hearts -= 1
            if current_hearts > 0:
                current_hp = max_hp
            else:
                show_game_over()
                pygame.quit()
                sys.exit()

        # Update kamera
        update_camera()
        
        # Render game
        screen.fill((0, 0, 0))
        draw_map()
        screen.blit(character_image, (character_rect.x - camera_x, character_rect.y - camera_y))

        # Gambar semua enemy
        for enemy in enemies:
            if enemy.is_alive:
                enemy.draw(camera_x, camera_y)

        # Cooldown serangan karakter
        if attack_cooldown > 0:
            attack_cooldown -= 1

        # Serangan karakter (tombol Z)
        if keys[pygame.K_z] and attack_cooldown == 0:
            attacking = True
            attack_frame = 0
            attack_animation_timer = 0
            attack_cooldown = attack_cooldown_time
            for enemy in enemies:
                if enemy.is_alive:
                    # Hitung jarak ke enemy
                    dx = abs(character_rect.centerx - enemy.rect.centerx)
                    dy = abs(character_rect.centery - enemy.rect.centery)
                    distance = math.hypot(dx, dy)
                    if distance <= attack_range:  # Jika dalam jangkauan serang
                        enemy.current_hp -= strength

        # Cek kematian enemy untuk trigger upgrade
        if not choose_upgrade:
            for enemy in enemies:
                if enemy.just_died:
                    choose_upgrade = True
                    upgrade_message = "Press H to increase HP or S to increase Strength"
                    enemy.just_died = False
                    break

    # Gambar HUD dan pesan upgrade
    draw_stats()
    draw_upgrade_message()
    pygame.display.flip()