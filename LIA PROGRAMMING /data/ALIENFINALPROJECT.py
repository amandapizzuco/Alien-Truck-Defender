

import os
import random
import pygame

# -----------------------------
# Basic game settings
# -----------------------------
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 40

MAX_SHOTS = 9
ALIEN_ODDS = 55
MIN_ALIEN_ODDS = 14
BOMB_ODDS = 75
MIN_BOMB_ODDS = 35
ALIEN_RELOAD = 40
MIN_ALIEN_RELOAD = 10
MAX_ALIENS_ONSCREEN = 10

DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# These will change while the game runs.
score = 0
high_score = 0


# -----------------------------
# Loading images and sounds
# -----------------------------
def load_image(filename):
    path = os.path.join(DATA_FOLDER, filename)
    try:
        image = pygame.image.load(path)
        return image.convert()
    except pygame.error:
        raise SystemExit("Could not load image: " + path)
    except FileNotFoundError:
        raise SystemExit("Could not find image: " + path)


def load_sound(filename):
    if not pygame.mixer:
        return None

    path = os.path.join(DATA_FOLDER, filename)
    try:
        sound = pygame.mixer.Sound(path)
        return sound
    except pygame.error:
        print("Could not load sound: " + path)
        return None
    except FileNotFoundError:
        print("Could not find sound: " + path)
        return None


# -----------------------------
# Small helper functions
# -----------------------------
def tint_image(image, color):
    tinted = image.copy().convert_alpha()
    overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
    overlay.fill(color)
    tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted.convert()


def make_truck_options(base_player, chosen_color):
    coloured = tint_image(base_player, chosen_color)
    classic = coloured
    speedster = pygame.transform.scale(
        coloured,
        (base_player.get_width() + 10, max(10, base_player.get_height() - 2))
    )
    heavy = pygame.transform.scale(
        coloured,
        (base_player.get_width() + 4, base_player.get_height() + 8)
    )
    return [classic, speedster, heavy]


def make_background(tile):
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    for x in range(0, SCREEN_WIDTH, tile.get_width()):
        background.blit(tile, (x, 0))
    return background


def draw_text(screen, text, size, color, center_x, center_y):
    font = pygame.font.Font(None, size)
    image = font.render(text, True, color)
    rect = image.get_rect(center=(center_x, center_y))
    screen.blit(image, rect)


# -----------------------------
# Start screen
# -----------------------------
def choose_truck(screen, background, base_player):
    colors = [
        (255, 255, 255, 255),
        (255, 150, 150, 255),
        (150, 200, 255, 255),
        (170, 255, 170, 255),
        (230, 170, 255, 255)
    ]

    truck_choice = 0
    color_choice = 0
    clock = pygame.time.Clock()

    choosing = True
    while choosing:
        chosen_color = colors[color_choice]
        truck_options = make_truck_options(base_player, chosen_color)

        screen.blit(background, (0, 0))
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 130))
        screen.blit(shade, (0, 0))

        draw_text(screen, "ALIEN TRUCK DEFENDER", 54, "white", SCREEN_WIDTH // 2, 70)
        draw_text(screen, "Choose truck with 1, 2, or 3", 26, "white", SCREEN_WIDTH // 2, 120)
        draw_text(screen, "Press C to change colour", 26, "white", SCREEN_WIDTH // 2, 148)
        draw_text(screen, "Press ENTER to start", 26, "white", SCREEN_WIDTH // 2, 176)
        draw_text(screen, "Arrow keys move, SPACE shoots", 26, "white", SCREEN_WIDTH // 2, 204)
        draw_text(screen, "During the game, press M to change truck", 22, "yellow", SCREEN_WIDTH // 2, 230)

        names = ["Classic", "Speedster", "Heavy"]
        abilities = ["balanced", "fast + combo", "slow + strong"]

        for i in range(len(truck_options)):
            x = 185 + i * 135
            y = 300
            truck_rect = truck_options[i].get_rect(center=(x, y))

            if i == truck_choice:
                pygame.draw.rect(screen, "yellow", truck_rect.inflate(26, 26), 3)

            screen.blit(truck_options[i], truck_rect)
            draw_text(screen, names[i], 22, "white", x, y + 50)
            draw_text(screen, abilities[i], 22, "yellow", x, y + 72)

        draw_text(screen, "Colour option: " + str(color_choice + 1), 26, "white", SCREEN_WIDTH // 2, 410)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_1:
                    truck_choice = 0
                elif event.key == pygame.K_2:
                    truck_choice = 1
                elif event.key == pygame.K_3:
                    truck_choice = 2
                elif event.key == pygame.K_c:
                    color_choice = color_choice + 1
                    if color_choice >= len(colors):
                        color_choice = 0
                elif event.key == pygame.K_RETURN:
                    choosing = False

        clock.tick(30)

    chosen_image = truck_options[truck_choice]
    left_image = chosen_image
    right_image = pygame.transform.flip(chosen_image, True, False)
    speeds = [10, 14, 8]
    abilities = ["classic", "speedster", "heavy"]
    names = ["Classic", "Speedster", "Heavy"]
    max_lives = [3, 3, 5]
    shot_damage = [1, 1, 2]

    truck = {
        "left_image": left_image,
        "right_image": right_image,
        "speed": speeds[truck_choice],
        "ability": abilities[truck_choice],
        "name": names[truck_choice],
        "max_lives": max_lives[truck_choice],
        "shot_damage": shot_damage[truck_choice]
    }
    return truck


# -----------------------------
# Creating game objects
# -----------------------------
def create_player(truck):
    image = truck["left_image"]
    rect = image.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT))
    player = {
        "image": image,
        "left_image": truck["left_image"],
        "right_image": truck["right_image"],
        "rect": rect,
        "speed": truck["speed"],
        "ability": truck["ability"],
        "name": truck["name"],
        "max_lives": truck["max_lives"],
        "shot_damage": truck["shot_damage"],
        "facing": -1,
        "reloading": False,
        "lives": truck["max_lives"],
        "alive": True
    }
    return player


def change_player_truck(player, truck):
    # This changes the truck while keeping the same game going.
    old_center = player["rect"].center
    old_bottom = player["rect"].bottom
    old_lives = player["lives"]

    player["left_image"] = truck["left_image"]
    player["right_image"] = truck["right_image"]
    player["speed"] = truck["speed"]
    player["ability"] = truck["ability"]
    player["name"] = truck["name"]
    player["max_lives"] = truck["max_lives"]
    player["shot_damage"] = truck["shot_damage"]

    if player["facing"] < 0:
        player["image"] = player["left_image"]
    else:
        player["image"] = player["right_image"]

    player["rect"] = player["image"].get_rect(center=old_center)
    player["rect"].bottom = old_bottom

    # Do not give extra lives just because the player changed truck.
    if old_lives > player["max_lives"]:
        player["lives"] = player["max_lives"]
    else:
        player["lives"] = old_lives

    if player["rect"].left < 0:
        player["rect"].left = 0
    if player["rect"].right > SCREEN_WIDTH:
        player["rect"].right = SCREEN_WIDTH


def create_alien(alien_images):
    image = alien_images[0]
    rect = image.get_rect()
    direction = random.choice([-1, 1]) * 5

    if direction < 0:
        rect.right = SCREEN_WIDTH
    else:
        rect.left = 0

    alien = {
        "images": alien_images,
        "image": image,
        "rect": rect,
        "direction": direction,
        "frame": 0,
        "type": "alien"
    }
    return alien


def create_boss(alien_images, level):
    boss_images = []
    for image in alien_images:
        boss_images.append(pygame.transform.scale(image, (96, 66)))

    image = boss_images[0]
    rect = image.get_rect(midtop=(SCREEN_WIDTH // 2, 8))

    boss = {
        "images": boss_images,
        "image": image,
        "rect": rect,
        "direction": 4,
        "frame": 0,
        "health": 8 + level * 2,
        "max_health": 8 + level * 2
    }
    return boss


def create_shot(x, y, damage):
    width = 6
    height = 18
    image = pygame.Surface((width, height), pygame.SRCALPHA)

    pygame.draw.rect(image, "white", (2, 4, 2, 10))
    pygame.draw.polygon(image, "red", [(3, 0), (0, 5), (6, 5)])
    pygame.draw.polygon(image, "orange", [(1, 14), (5, 14), (3, 18)])

    rect = image.get_rect(midbottom=(x, y))
    shot = {
        "image": image,
        "rect": rect,
        "speed": -14,
        "damage": damage
    }
    return shot


def create_bomb(alien, bomb_image):
    rect = bomb_image.get_rect(midbottom=alien["rect"].move(0, 5).midbottom)
    bomb = {
        "image": bomb_image,
        "rect": rect,
        "speed": 9
    }
    return bomb


def create_boss_shot(boss):
    image = pygame.Surface((8, 18), pygame.SRCALPHA)
    pygame.draw.rect(image, "purple", (2, 0, 4, 14))
    pygame.draw.circle(image, "white", (4, 15), 3)
    rect = image.get_rect(midtop=boss["rect"].midbottom)
    boss_shot = {
        "image": image,
        "rect": rect,
        "speed": 7
    }
    return boss_shot


def create_powerup():
    kinds = ["triple", "lightning", "shield"]
    kind = random.choice(kinds)
    image = pygame.Surface((28, 28), pygame.SRCALPHA)

    if kind == "triple":
        pygame.draw.circle(image, "orange", (14, 14), 13)
        font = pygame.font.Font(None, 18)
        label = font.render("3", True, "black")
        image.blit(label, label.get_rect(center=(14, 14)))
    elif kind == "lightning":
        pygame.draw.circle(image, "yellow", (14, 14), 13)
        points = [(16, 3), (7, 16), (14, 16), (11, 26), (23, 11), (16, 11)]
        pygame.draw.polygon(image, "black", points)
    else:
        pygame.draw.circle(image, "deepskyblue", (14, 14), 13)
        pygame.draw.circle(image, "white", (14, 14), 9, 2)

    x = random.randint(40, SCREEN_WIDTH - 40)
    rect = image.get_rect(midtop=(x, 0))
    powerup = {
        "kind": kind,
        "image": image,
        "rect": rect,
        "speed": 3
    }
    return powerup


def create_explosion(rect, explosion_images):
    explosion = {
        "images": explosion_images,
        "image": explosion_images[0],
        "rect": explosion_images[0].get_rect(center=rect.center),
        "life": 12
    }
    return explosion


def create_popup(text, pos):
    font = pygame.font.Font(None, 24)
    image = font.render(text, True, "yellow")
    popup = {
        "image": image,
        "rect": image.get_rect(center=pos),
        "life": 35
    }
    return popup


# -----------------------------
# Updating game objects
# -----------------------------
def move_player(player, keys):
    direction = 0
    if keys[pygame.K_LEFT]:
        direction = -1
    elif keys[pygame.K_RIGHT]:
        direction = 1

    if direction != 0:
        player["facing"] = direction

    player["rect"].x = player["rect"].x + direction * player["speed"]

    if player["rect"].left < 0:
        player["rect"].left = 0
    if player["rect"].right > SCREEN_WIDTH:
        player["rect"].right = SCREEN_WIDTH

    if direction < 0:
        player["image"] = player["left_image"]
    elif direction > 0:
        player["image"] = player["right_image"]


def update_aliens(aliens):
    for alien in aliens:
        alien["rect"].x = alien["rect"].x + alien["direction"]

        if alien["rect"].left < 0 or alien["rect"].right > SCREEN_WIDTH:
            alien["direction"] = -alien["direction"]
            alien["rect"].y = alien["rect"].y + alien["rect"].height + 1

        if alien["rect"].bottom > SCREEN_HEIGHT:
            alien["rect"].bottom = SCREEN_HEIGHT

        alien["frame"] = alien["frame"] + 1
        image_number = (alien["frame"] // 12) % len(alien["images"])
        alien["image"] = alien["images"][image_number]


def update_bosses(bosses):
    for boss in bosses:
        boss["rect"].x = boss["rect"].x + boss["direction"]

        if boss["rect"].left <= 0 or boss["rect"].right >= SCREEN_WIDTH:
            boss["direction"] = -boss["direction"]
            boss["rect"].y = boss["rect"].y + 16
            if boss["rect"].y > 150:
                boss["rect"].y = 150

        boss["frame"] = boss["frame"] + 1
        image_number = (boss["frame"] // 8) % len(boss["images"])
        boss["image"] = boss["images"][image_number]


def update_shots(shots):
    for shot in shots[:]:
        shot["rect"].y = shot["rect"].y + shot["speed"]
        if shot["rect"].bottom < 0:
            shots.remove(shot)


def update_bombs(bombs, explosions, explosion_images):
    for bomb in bombs[:]:
        bomb["rect"].y = bomb["rect"].y + bomb["speed"]
        if bomb["rect"].bottom >= 470:
            explosions.append(create_explosion(bomb["rect"], explosion_images))
            bombs.remove(bomb)


def update_boss_shots(boss_shots):
    for boss_shot in boss_shots[:]:
        boss_shot["rect"].y = boss_shot["rect"].y + boss_shot["speed"]
        if boss_shot["rect"].top > SCREEN_HEIGHT:
            boss_shots.remove(boss_shot)


def update_powerups(powerups):
    for powerup in powerups[:]:
        powerup["rect"].y = powerup["rect"].y + powerup["speed"]
        if powerup["rect"].top > SCREEN_HEIGHT:
            powerups.remove(powerup)


def update_explosions(explosions):
    for explosion in explosions[:]:
        explosion["life"] = explosion["life"] - 1
        image_number = (explosion["life"] // 3) % len(explosion["images"])
        explosion["image"] = explosion["images"][image_number]
        if explosion["life"] <= 0:
            explosions.remove(explosion)


def update_popups(popups):
    for popup in popups[:]:
        popup["rect"].y = popup["rect"].y - 1
        popup["life"] = popup["life"] - 1
        if popup["life"] <= 0:
            popups.remove(popup)


# -----------------------------
# Collisions and drawing
# -----------------------------
def draw_objects(screen, objects):
    for item in objects:
        screen.blit(item["image"], item["rect"])


def handle_player_damage(player, explosions, explosion_images, now, timers):
    if now >= timers["shield_until"] and now >= timers["invincible_until"]:
        player["lives"] = player["lives"] - 1
        timers["invincible_until"] = now + 2000
        timers["shake_until"] = now + 300
        explosions.append(create_explosion(player["rect"], explosion_images))

        if player["lives"] <= 0:
            player["alive"] = False


def draw_hud(screen, player, level, goal, timers, combo, bosses):
    global score, high_score

    font = pygame.font.Font(None, 20)
    lines = []
    lines.append("Truck: " + player["name"] + "  (M = menu)")
    lines.append("Lives: " + str(player["lives"]))
    lines.append("Score: " + str(score))
    lines.append("High Score: " + str(high_score))
    lines.append("Level: " + str(level))
    lines.append("Goal: " + goal)

    now = pygame.time.get_ticks()

    if now < timers["triple_until"]:
        seconds = (timers["triple_until"] - now) // 1000 + 1
        lines.append("Triple Rockets: " + str(seconds) + "s")

    if now < timers["shield_until"]:
        seconds = (timers["shield_until"] - now) // 1000 + 1
        lines.append("Shield: " + str(seconds) + "s")

    if len(bosses) > 0:
        boss = bosses[0]
        lines.append("Boss Health: " + str(boss["health"]) + "/" + str(boss["max_health"]))

    for i in range(len(lines)):
        image = font.render(lines[i], True, "white")
        screen.blit(image, (10, 10 + i * 18))


    # Combo counter UI for the Speedster truck.
    if player["ability"] == "speedster":
        combo_text = "Speedster Combo: x" + str(combo)
        combo_image = font.render(combo_text, True, "yellow")
        screen.blit(combo_image, (SCREEN_WIDTH - 170, 10))

        pygame.draw.rect(screen, "white", (SCREEN_WIDTH - 170, 32, 140, 10), 1)
        if combo > 0 and now < timers["combo_until"]:
            time_left = timers["combo_until"] - now
            bar = int(140 * time_left / 2600)
            pygame.draw.rect(screen, "yellow", (SCREEN_WIDTH - 170, 32, bar, 10))


def game_over_screen(screen, background):
    global score, high_score

    clock = pygame.time.Clock()
    while True:
        screen.blit(background, (0, 0))
        shade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 180))
        screen.blit(shade, (0, 0))

        draw_text(screen, "GAME OVER", 64, "white", SCREEN_WIDTH // 2, 145)
        draw_text(screen, "Final Score: " + str(score), 30, "white", SCREEN_WIDTH // 2, 220)
        draw_text(screen, "High Score: " + str(high_score), 30, "yellow", SCREEN_WIDTH // 2, 255)
        draw_text(screen, "Press R to try again", 30, "white", SCREEN_WIDTH // 2, 315)
        draw_text(screen, "Press ESC to quit", 24, "white", SCREEN_WIDTH // 2, 350)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_ESCAPE:
                    return False

        clock.tick(30)


# -----------------------------
# Main game
# -----------------------------
def play_game(screen, background, images, sounds, truck):
    global score, high_score

    score = 0
    combo = 0
    combo_until = 0

    player = create_player(truck)

    aliens = []
    shots = []
    bombs = []
    bosses = []
    boss_shots = []
    powerups = []
    explosions = []
    popups = []

    aliens.append(create_alien(images["aliens"]))

    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    next_powerup_time = pygame.time.get_ticks() + 8000
    next_boss_shot_time = pygame.time.get_ticks() + 1200
    next_boss_score = 20
    goal = "Reach 20 points to spawn the first boss"
    alien_reload = ALIEN_RELOAD
    timers = {
        "triple_until": 0,
        "shield_until": 0,
        "invincible_until": 0,
        "shake_until": 0,
        "combo_until": 0
    }

    while player["alive"]:
        now = pygame.time.get_ticks()

        # -----------------------------
        # Events
        # -----------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_m:
                    new_truck = choose_truck(screen, background, images["base_player"])
                    if new_truck is not None:
                        change_player_truck(player, new_truck)
                        player["reloading"] = True

        keys = pygame.key.get_pressed()
        move_player(player, keys)

        # -----------------------------
        # Shooting
        # -----------------------------
        firing = keys[pygame.K_SPACE]

        shot_damage = player["shot_damage"]

        if player["reloading"] == False and firing == True and len(shots) < MAX_SHOTS:
            x = player["rect"].centerx + player["facing"] * -11
            y = player["rect"].top

            if now < timers["triple_until"]:
                offsets = [-18, 0, 18]
                for offset in offsets:
                    shots.append(create_shot(x + offset, y, shot_damage))
            else:
                shots.append(create_shot(x, y, shot_damage))

            if sounds["shoot"] is not None:
                sounds["shoot"].play()

        player["reloading"] = firing

        # -----------------------------
        # Difficulty
        # -----------------------------
        seconds_played = (now - start_time) // 1000
        level = 1 + seconds_played // 15
        current_alien_odds = ALIEN_ODDS - level * 5
        if current_alien_odds < MIN_ALIEN_ODDS:
            current_alien_odds = MIN_ALIEN_ODDS

        current_alien_reload = ALIEN_RELOAD - level * 4
        if current_alien_reload < MIN_ALIEN_RELOAD:
            current_alien_reload = MIN_ALIEN_RELOAD

        current_bomb_odds = BOMB_ODDS - level * 4
        if current_bomb_odds < MIN_BOMB_ODDS:
            current_bomb_odds = MIN_BOMB_ODDS

        max_aliens_now = 3 + level
        if max_aliens_now > MAX_ALIENS_ONSCREEN:
            max_aliens_now = MAX_ALIENS_ONSCREEN

        # -----------------------------
        # Create aliens and bosses
        # -----------------------------
        if alien_reload > 0:
            alien_reload = alien_reload - 1
        else:
            random_number = random.randint(1, current_alien_odds)
            if len(bosses) == 0 and len(aliens) < max_aliens_now and random_number == 1:
                aliens.append(create_alien(images["aliens"]))
                alien_reload = current_alien_reload

        if score >= next_boss_score and len(bosses) == 0:
            for alien in aliens[:]:
                explosions.append(create_explosion(alien["rect"], images["explosions"]))
                aliens.remove(alien)
            bosses.append(create_boss(images["aliens"], level))
            goal = "Defeat the boss!"
            next_boss_score = next_boss_score + 30

        # -----------------------------
        # Bombs and powerups
        # -----------------------------
        if len(aliens) > 0:
            last_alien = aliens[-1]
            random_number = random.randint(1, current_bomb_odds)
            if random_number == 1:
                bombs.append(create_bomb(last_alien, images["bomb"]))

        if now >= next_powerup_time:
            powerups.append(create_powerup())
            next_powerup_time = now + 60000

        # Boss shooting
        if len(bosses) > 0 and now >= next_boss_shot_time:
            boss_shots.append(create_boss_shot(bosses[0]))
            next_boss_shot_time = now + 1000

        # -----------------------------
        # Update positions
        # -----------------------------
        update_aliens(aliens)
        update_bosses(bosses)
        update_shots(shots)
        update_bombs(bombs, explosions, images["explosions"])
        update_boss_shots(boss_shots)
        update_powerups(powerups)
        update_explosions(explosions)
        update_popups(popups)

        # -----------------------------
        # Player collecting powerups
        # -----------------------------
        for powerup in powerups[:]:
            if player["rect"].colliderect(powerup["rect"]):
                if powerup["kind"] == "triple":
                    timers["triple_until"] = now + 10000
                elif powerup["kind"] == "lightning":
                    for alien in aliens[:]:
                        explosions.append(create_explosion(alien["rect"], images["explosions"]))
                        aliens.remove(alien)
                    score = score + 5
                elif powerup["kind"] == "shield":
                    timers["shield_until"] = now + 15000

                powerups.remove(powerup)

        # -----------------------------
        # Shots hitting aliens
        # -----------------------------
        for alien in aliens[:]:
            for shot in shots[:]:
                if alien["rect"].colliderect(shot["rect"]):
                    if sounds["boom"] is not None:
                        sounds["boom"].play()

                    explosions.append(create_explosion(alien["rect"], images["explosions"]))
                    popups.append(create_popup("+1", alien["rect"].center))
                    aliens.remove(alien)
                    shots.remove(shot)

                    combo = combo + 1
                    if player["ability"] == "speedster":
                        combo_until = now + 2600
                    else:
                        combo_until = now + 2000
                    timers["combo_until"] = combo_until

                    points = 1 + combo // 3
                    score = score + points
                    break

        # -----------------------------
        # Shots hitting bosses
        # -----------------------------
        for boss in bosses[:]:
            for shot in shots[:]:
                if boss["rect"].colliderect(shot["rect"]):
                    boss["health"] = boss["health"] - shot["damage"]
                    popups.append(create_popup("-" + str(shot["damage"]), boss["rect"].center))
                    shots.remove(shot)

                    if boss["health"] <= 0:
                        if sounds["boom"] is not None:
                            sounds["boom"].play()

                        explosions.append(create_explosion(boss["rect"], images["explosions"]))
                        bosses.remove(boss)
                        boss_shots.clear()
                        combo = combo + 1
                        if player["ability"] == "speedster":
                            combo_until = now + 2600
                        else:
                            combo_until = now + 2000
                        timers["combo_until"] = combo_until
                        points = 10 + min(combo, 5)
                        score = score + points
                        popups.append(create_popup("BOSS +" + str(points), boss["rect"].center))
                        goal = "Goal complete! Reach the next boss checkpoint."
                        timers["shake_until"] = now + 300
                    break

        # -----------------------------
        # Enemies hitting player
        # -----------------------------
        for alien in aliens[:]:
            if player["rect"].colliderect(alien["rect"]):
                if sounds["boom"] is not None:
                    sounds["boom"].play()
                explosions.append(create_explosion(alien["rect"], images["explosions"]))
                aliens.remove(alien)
                score = score + 1
                combo = 0
                timers["combo_until"] = 0
                handle_player_damage(player, explosions, images["explosions"], now, timers)

        for boss in bosses:
            if player["rect"].colliderect(boss["rect"]):
                combo = 0
                timers["combo_until"] = 0
                handle_player_damage(player, explosions, images["explosions"], now, timers)

        for bomb in bombs[:]:
            if player["rect"].colliderect(bomb["rect"]):
                if sounds["boom"] is not None:
                    sounds["boom"].play()
                explosions.append(create_explosion(bomb["rect"], images["explosions"]))
                bombs.remove(bomb)
                combo = 0
                timers["combo_until"] = 0
                handle_player_damage(player, explosions, images["explosions"], now, timers)

        for boss_shot in boss_shots[:]:
            if player["rect"].colliderect(boss_shot["rect"]):
                if sounds["boom"] is not None:
                    sounds["boom"].play()
                explosions.append(create_explosion(boss_shot["rect"], images["explosions"]))
                boss_shots.remove(boss_shot)
                combo = 0
                timers["combo_until"] = 0
                handle_player_damage(player, explosions, images["explosions"], now, timers)

        if combo > 0 and now > combo_until:
            combo = 0
            timers["combo_until"] = 0

        # -----------------------------
        # Draw everything
        # -----------------------------
        screen.blit(background, (0, 0))

        draw_objects(screen, aliens)
        draw_objects(screen, bosses)
        draw_objects(screen, shots)
        draw_objects(screen, bombs)
        draw_objects(screen, boss_shots)
        draw_objects(screen, powerups)
        draw_objects(screen, explosions)
        draw_objects(screen, popups)
        screen.blit(player["image"], player["rect"])

        # Extra visual differences for truck type.
        if player["ability"] == "classic":
            pygame.draw.rect(screen, "white", player["rect"], 1)
        elif player["ability"] == "speedster":
            pygame.draw.line(screen, "yellow", (player["rect"].left - 12, player["rect"].centery), (player["rect"].left, player["rect"].centery), 3)
            pygame.draw.line(screen, "yellow", (player["rect"].left - 20, player["rect"].centery + 8), (player["rect"].left, player["rect"].centery + 8), 2)
        elif player["ability"] == "heavy":
            pygame.draw.rect(screen, "limegreen", player["rect"].inflate(6, 6), 2)

        if now < timers["shield_until"]:
            pygame.draw.circle(screen, "deepskyblue", player["rect"].center, 32, 2)
        elif now < timers["invincible_until"]:
            pygame.draw.circle(screen, "white", player["rect"].center, 30, 1)

        draw_hud(screen, player, level, goal, timers, combo, bosses)

        if now < timers["shake_until"]:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 35))
            screen.blit(flash, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    if score > high_score:
        high_score = score

    return True


def main():
    pygame.init()

    if pygame.mixer and not pygame.mixer.get_init():
        print("Warning: no sound")

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Alien Truck Defender")
    pygame.mouse.set_visible(False)

    # Load all images once.
    explosion1 = load_image("explosion1.gif")
    explosion2 = pygame.transform.flip(explosion1, True, True)

    images = {
        "explosions": [explosion1, explosion2],
        "aliens": [load_image("alien1.gif"), load_image("alien2.gif"), load_image("alien3.gif")],
        "bomb": load_image("bomb.gif"),
        "base_player": load_image("player1.gif")
    }

    icon = pygame.transform.scale(images["aliens"][0], (32, 32))
    pygame.display.set_icon(icon)

    tile = load_image("background.gif")
    background = make_background(tile)

    sounds = {
        "boom": load_sound("boom.wav"),
        "shoot": load_sound("car_door.wav")
    }

    if pygame.mixer:
        music_path = os.path.join(DATA_FOLDER, "house_lo.wav")
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(-1)
        except pygame.error:
            print("Could not load background music")
        except FileNotFoundError:
            print("Could not find background music")

    playing = True
    while playing:
        truck = choose_truck(screen, background, images["base_player"])
        if truck is None:
            playing = False
        else:
            keep_going = play_game(screen, background, images, sounds, truck)
            if keep_going == False:
                playing = False
            else:
                playing = game_over_screen(screen, background)

    if pygame.mixer:
        pygame.mixer.music.fadeout(1000)
    pygame.quit()


if __name__ == "__main__":
    main()
