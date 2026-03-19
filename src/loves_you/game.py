from __future__ import annotations

import math
import random
import sys

import pygame

from .audio import AudioManager
from .config import (
    AUTO_QUALITY,
    AUTO_QUALITY_PROFILES,
    BG,
    CUTSCENE_LINES,
    DEFAULT_AUTO_PROFILE,
    DEFAULT_QUALITY,
    ENTITY_SPEED_ANGRY,
    ENTITY_SPEED_BASE,
    FPS,
    GOOD,
    HEIGHT,
    HUG_DECAY_PER_SEC,
    HUG_DISTANCE,
    HUG_FILL_PER_SEC,
    PLAYER_SPEED,
    QUALITY_PRESETS,
    STAGES,
    TEXT,
    WALL,
    WARN,
    WIDTH,
)
from .models import Interactable, RoomLight


class Game:
    def __init__(
        self,
        initial_quality=DEFAULT_QUALITY,
        auto_quality_enabled=None,
        auto_quality_profile=DEFAULT_AUTO_PROFILE,
    ):
        pygame.init()
        pygame.display.set_caption("Ama você")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.world_surface = pygame.Surface((WIDTH, HEIGHT)).convert_alpha()
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("consolas", 22)
        self.small_font = pygame.font.SysFont("consolas", 18)
        self.big_font = pygame.font.SysFont("consolas", 64, bold=True)
        self.cut_font = pygame.font.SysFont("consolas", 28)

        self.audio = AudioManager()
        if initial_quality not in QUALITY_PRESETS:
            initial_quality = DEFAULT_QUALITY
        self.quality_name = initial_quality
        self.quality = QUALITY_PRESETS[self.quality_name]
        self.noise_accumulator = 0.0
        if auto_quality_profile not in AUTO_QUALITY_PROFILES:
            auto_quality_profile = DEFAULT_AUTO_PROFILE
        self.auto_quality_profile = auto_quality_profile
        self.auto_quality_cfg = dict(AUTO_QUALITY)
        self.auto_quality_cfg.update(AUTO_QUALITY_PROFILES[self.auto_quality_profile])
        if auto_quality_enabled is None:
            self.auto_quality_enabled = self.auto_quality_cfg["enabled"]
        else:
            self.auto_quality_enabled = bool(auto_quality_enabled)
        self.auto_quality_check_accumulator = 0.0
        self.auto_quality_cooldown = 0.0
        self.fps_samples = []
        self.current_fps_avg = float(FPS)
        self._init_postfx_surfaces()

        self.running = True
        self.reset()

    def reset(self):
        self.player = pygame.Rect(80, HEIGHT // 2, 28, 28)
        self.entity = pygame.Rect(WIDTH - 120, HEIGHT // 2, 34, 34)

        self.fragment_count = 0
        self.journal = []

        self.stage_index = 0
        self.stage_time = 0.0
        self.total_time = 0.0

        self.hug_meter = 0.0
        self.tension = 0.15
        self.ama_flash = 0.0
        self.ama_glitch = []

        self.game_state = "playing"
        self.victory_choice = None

        self.walls: list[pygame.Rect] = []
        self.interactables: list[Interactable] = []
        self.stage_data = {}
        self.house_shift_timer = 0.0
        self.room_lights: list[RoomLight] = []

        self.cutscene_lines: list[str] = []
        self.cutscene_reveal = 0.0
        self.cutscene_min_hold = 0.0

        self.setup_stage()

    def _init_postfx_surfaces(self):
        self.noise_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.scanline_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.vignette_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        self._build_scanlines()
        self._build_vignette()

    def _build_scanlines(self):
        self.scanline_surface.fill((0, 0, 0, 0))
        step = self.quality["scanline_step"]
        for y in range(0, HEIGHT, step):
            alpha = self.quality["scanline_a"] if (y // step) % 2 == 0 else self.quality["scanline_b"]
            pygame.draw.line(self.scanline_surface, (0, 0, 0, alpha), (0, y), (WIDTH, y), 1)

    def _build_vignette(self):
        self.vignette_surface.fill((0, 0, 0, 0))
        center = (WIDTH // 2, HEIGHT // 2)
        max_radius = int(math.hypot(WIDTH / 2, HEIGHT / 2))
        rings = self.quality["vignette_rings"]
        width = self.quality["vignette_width"]
        alpha_base = self.quality["vignette_alpha_base"]
        alpha_step = self.quality["vignette_alpha_step"]
        for i in range(rings):
            radius = int(max_radius * (1.0 - i * 0.11))
            alpha = alpha_base + i * alpha_step
            pygame.draw.circle(self.vignette_surface, (0, 0, 0, alpha), center, radius, width=width)

    def set_quality(self, name):
        if name not in QUALITY_PRESETS:
            return
        self.quality_name = name
        self.quality = QUALITY_PRESETS[name]
        self._init_postfx_surfaces()

    def _set_manual_quality(self, name):
        self.auto_quality_enabled = False
        self.set_quality(name)

    def _quality_index(self):
        return {"alto": 0, "medio": 1, "baixo": 2}[self.quality_name]

    def _quality_from_index(self, idx):
        return ["alto", "medio", "baixo"][idx]

    def _update_auto_quality(self, dt):
        if dt <= 0:
            return

        fps_now = 1.0 / dt
        self.fps_samples.append(fps_now)
        max_samples = self.auto_quality_cfg["sample_window"]
        if len(self.fps_samples) > max_samples:
            self.fps_samples = self.fps_samples[-max_samples:]

        if self.fps_samples:
            self.current_fps_avg = sum(self.fps_samples) / len(self.fps_samples)

        if not self.auto_quality_enabled:
            return

        self.auto_quality_check_accumulator += dt
        self.auto_quality_cooldown = max(0.0, self.auto_quality_cooldown - dt)

        if self.auto_quality_check_accumulator < self.auto_quality_cfg["check_interval"]:
            return

        self.auto_quality_check_accumulator = 0.0
        if self.auto_quality_cooldown > 0:
            return

        idx = self._quality_index()
        fps_avg = self.current_fps_avg

        if fps_avg < self.auto_quality_cfg["downgrade_fps"] and idx < 2:
            self.set_quality(self._quality_from_index(idx + 1))
            self.auto_quality_cooldown = self.auto_quality_cfg["switch_cooldown"]
            return

        if fps_avg > self.auto_quality_cfg["upgrade_fps"] and idx > 0:
            self.set_quality(self._quality_from_index(idx - 1))
            self.auto_quality_cooldown = self.auto_quality_cfg["switch_cooldown"]

    def setup_stage(self):
        self.stage_time = 0.0
        self.house_shift_timer = 0.0
        self.generate_house_layout(initial=True)
        self.interactables.clear()
        self.stage_data = {}

        name = STAGES[self.stage_index]

        if name == "Negacao":
            spots = [
                pygame.Rect(250, 140, 42, 42),
                pygame.Rect(460, 300, 42, 42),
                pygame.Rect(710, 170, 42, 42),
            ]
            self.interactables = [
                Interactable(r, "Reflexo quebrado", True, "reflection", i)
                for i, r in enumerate(spots)
            ]
            self.stage_data["found"] = 0
            self.stage_data["target"] = 3

        elif name == "Barganha":
            sequence = [2, 0, 3, 1]
            pads = [
                pygame.Rect(250, 390, 52, 52),
                pygame.Rect(400, 140, 52, 52),
                pygame.Rect(560, 390, 52, 52),
                pygame.Rect(730, 180, 52, 52),
            ]
            self.interactables = [
                Interactable(r, f"Bilhete {i + 1}", True, "note", i) for i, r in enumerate(pads)
            ]
            self.stage_data["sequence"] = sequence
            self.stage_data["progress"] = 0
            self.stage_data["mistakes"] = 0

        elif name == "Raiva":
            shards = []
            for i in range(6):
                x = random.randint(140, WIDTH - 180)
                y = random.randint(120, HEIGHT - 140)
                shards.append(Interactable(pygame.Rect(x, y, 30, 30), "Caco", True, "shard", i))
            self.interactables = shards
            self.stage_data["collected"] = 0
            self.stage_data["target"] = 6

        elif name == "Depressao":
            pools = [
                pygame.Rect(220, 200, 55, 55),
                pygame.Rect(450, 310, 55, 55),
                pygame.Rect(680, 190, 55, 55),
            ]
            self.interactables = [
                Interactable(r, f"Fita {i + 1}", True, "tape", i) for i, r in enumerate(pools)
            ]
            self.stage_data["order"] = [1, 2, 0]
            self.stage_data["progress"] = 0
            self.stage_data["failures"] = 0

        elif name == "Aceitacao Distorcida":
            altar = pygame.Rect(WIDTH // 2 - 45, HEIGHT // 2 - 45, 90, 90)
            self.interactables = [Interactable(altar, "Altar da memoria", True, "altar", 0)]
            self.stage_data["charged"] = 0.0
            self.stage_data["needed"] = 3.5

        self.player.center = (100, HEIGHT // 2)
        self.entity.center = (WIDTH - 120, HEIGHT // 2)

    def generate_house_layout(self, initial=False):
        self.walls = [
            pygame.Rect(0, 0, WIDTH, 24),
            pygame.Rect(0, HEIGHT - 24, WIDTH, 24),
            pygame.Rect(0, 0, 24, HEIGHT),
            pygame.Rect(WIDTH - 24, 0, 24, HEIGHT),
        ]

        count = 3 + self.stage_index
        seed = random.randint(0, 9999) if not initial else self.stage_index * 111 + 7
        rng = random.Random(seed)

        for _ in range(count):
            if rng.random() < 0.5:
                w = rng.randint(120, 260)
                h = 24
            else:
                w = 24
                h = rng.randint(100, 220)
            x = rng.randint(60, WIDTH - w - 60)
            y = rng.randint(60, HEIGHT - h - 60)
            self.walls.append(pygame.Rect(x, y, w, h))

        self._build_room_lights(seed + 17)

    def _build_room_lights(self, seed):
        rng = random.Random(seed)
        half_w = WIDTH // 2
        half_h = HEIGHT // 2
        base_rooms = [
            pygame.Rect(24, 24, half_w - 24, half_h - 24),
            pygame.Rect(half_w, 24, half_w - 24, half_h - 24),
            pygame.Rect(24, half_h, half_w - 24, half_h - 24),
            pygame.Rect(half_w, half_h, half_w - 24, half_h - 24),
        ]

        palette = [
            (22, 26, 36),
            (30, 24, 24),
            (20, 30, 26),
            (34, 22, 28),
        ]

        self.room_lights = []
        for room in base_rooms:
            tint = palette[rng.randint(0, len(palette) - 1)]
            base_alpha = rng.randint(24, 64) + self.stage_index * 5
            flicker_speed = rng.uniform(1.0, 3.4)
            phase = rng.uniform(0.0, 6.2)
            self.room_lights.append(RoomLight(room, tint, base_alpha, flicker_speed, phase))

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._update_auto_quality(dt)
            self.handle_events()
            self.update(dt)
            self.draw()

        self.audio.shutdown()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_F1:
                    self._set_manual_quality("alto")
                if event.key == pygame.K_F2:
                    self._set_manual_quality("medio")
                if event.key == pygame.K_F3:
                    self._set_manual_quality("baixo")
                if event.key == pygame.K_F4:
                    self.auto_quality_enabled = not self.auto_quality_enabled
                    self.auto_quality_check_accumulator = 0.0
                if event.key == pygame.K_r and self.game_state in {"captured", "ending"}:
                    self.reset()
                if self.game_state == "playing" and event.key == pygame.K_e:
                    self.try_interact()
                if self.game_state == "ending" and event.key in (pygame.K_y, pygame.K_n):
                    self.victory_choice = "quebra" if event.key == pygame.K_y else "fica"
                if self.game_state == "cutscene" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if self.cutscene_min_hold <= 0:
                        self.game_state = "playing"

    def update(self, dt):
        self.total_time += dt

        if self.game_state == "playing":
            self._update_playing(dt)
        elif self.game_state == "cutscene":
            self._update_cutscene(dt)

        if self.ama_flash > 0:
            self.ama_flash = max(0.0, self.ama_flash - dt)

        self.noise_accumulator += dt
        if self.noise_accumulator >= self.quality["noise_interval"]:
            self.noise_accumulator = 0.0
            self._refresh_noise_layer()

    def _refresh_noise_layer(self):
        # Ruido procedural em blocos para manter custo baixo em runtime.
        self.noise_surface.fill((0, 0, 0, 0))
        block = self.quality["noise_block"]
        density = (
            self.quality["noise_base"]
            + self.stage_index * self.quality["noise_stage"]
            + int(self.tension * self.quality["noise_tension"])
        )

        for _ in range(density):
            x = random.randint(0, WIDTH - block)
            y = random.randint(0, HEIGHT - block)
            shade = random.randint(90, 180)
            alpha = random.randint(8, 24)
            self.noise_surface.fill((shade, shade, shade, alpha), (x, y, block, block))

    def _update_cutscene(self, dt):
        self.cutscene_reveal += 58 * dt
        self.cutscene_min_hold = max(0.0, self.cutscene_min_hold - dt)

        if self.cutscene_reveal >= sum(len(line) for line in self.cutscene_lines) + 6:
            self.cutscene_min_hold = min(self.cutscene_min_hold, 0.8)

    def _update_playing(self, dt):
        self.stage_time += dt
        self.house_shift_timer += dt

        if self.house_shift_timer >= max(5.0 - self.stage_index * 0.6, 2.0):
            self.house_shift_timer = 0.0
            self.generate_house_layout(initial=False)
            self.raise_tension(0.06)

        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * PLAYER_SPEED * dt
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * PLAYER_SPEED * dt

        self.move_rect(self.player, dx, 0)
        self.move_rect(self.player, 0, dy)

        near_dist = self.update_entity(dt)
        self.update_stage_logic(dt)
        self.audio.update(
            near_dist,
            self.tension,
            self.stage_index,
            audio_mul=self.quality["audio_mul"],
            hiss_mul=self.quality["hiss_mul"],
        )

    def move_rect(self, rect, dx, dy):
        rect.x += int(dx)
        for wall in self.walls:
            if rect.colliderect(wall):
                if dx > 0:
                    rect.right = wall.left
                elif dx < 0:
                    rect.left = wall.right

        rect.y += int(dy)
        for wall in self.walls:
            if rect.colliderect(wall):
                if dy > 0:
                    rect.bottom = wall.top
                elif dy < 0:
                    rect.top = wall.bottom

    def update_entity(self, dt):
        px, py = self.player.center
        ex, ey = self.entity.center
        vx = px - ex
        vy = py - ey
        dist = math.hypot(vx, vy) + 1e-6

        speed = ENTITY_SPEED_BASE + (ENTITY_SPEED_ANGRY - ENTITY_SPEED_BASE) * self.tension
        if STAGES[self.stage_index] in {"Raiva", "Aceitacao Distorcida"}:
            speed *= 1.15

        step = speed * dt
        nx = ex + vx / dist * step
        ny = ey + vy / dist * step

        candidate = self.entity.copy()
        candidate.center = (int(nx), int(ny))
        blocked = any(candidate.colliderect(w) for w in self.walls)

        if not blocked:
            self.entity.center = candidate.center

        near_dist = math.hypot(px - self.entity.centerx, py - self.entity.centery)

        if near_dist < 150:
            self.raise_tension(0.28 * dt)
        else:
            self.tension = max(0.06, self.tension - 0.08 * dt)

        if near_dist <= HUG_DISTANCE:
            self.hug_meter = min(1.0, self.hug_meter + HUG_FILL_PER_SEC * dt)
            self.raise_tension(0.45 * dt)
            if random.random() < 0.035:
                self.trigger_ama_flash()
        else:
            self.hug_meter = max(0.0, self.hug_meter - HUG_DECAY_PER_SEC * dt)

        if self.hug_meter >= 1.0:
            self.game_state = "captured"

        return near_dist

    def update_stage_logic(self, dt):
        stage = STAGES[self.stage_index]

        if stage == "Negacao":
            if self.stage_data.get("found", 0) >= self.stage_data.get("target", 3):
                self.complete_stage("Voce para de negar o espelho e encara a lembranca.")

        elif stage == "Barganha":
            mistakes = self.stage_data.get("mistakes", 0)
            if mistakes >= 3:
                self.stage_data["mistakes"] = 0
                self.stage_data["progress"] = 0
                self.raise_tension(0.18)
                self.trigger_ama_flash(force=True)

            if self.stage_data.get("progress", 0) >= len(self.stage_data.get("sequence", [])):
                self.complete_stage("Voce aceita que promessas nao desfazem feridas.")

        elif stage == "Raiva":
            if self.stage_data.get("collected", 0) >= self.stage_data.get("target", 6):
                self.complete_stage("Entre estilhacos, a raiva revela o que foi quebrado.")

        elif stage == "Depressao":
            if self.stage_data.get("progress", 0) >= len(self.stage_data.get("order", [])):
                self.complete_stage("No silencio pesado, a memoria finalmente respira.")

        elif stage == "Aceitacao Distorcida":
            if self.fragment_count >= 4 and self.stage_data["charged"] >= self.stage_data["needed"]:
                self.game_state = "ending"

            if self.fragment_count < 4:
                self.stage_data["charged"] = 0.0

            if self.stage_time > 12 and random.random() < 0.008:
                self.trigger_ama_flash(force=True)

        if self.tension > 0.8 and random.random() < 0.02:
            self.trigger_ama_flash()

        self.tension = max(0.0, min(1.0, self.tension))

    def complete_stage(self, journal_text):
        completed_stage = self.stage_index
        self.fragment_count += 1
        self.journal.append(journal_text)
        self.raise_tension(0.12)

        if self.stage_index < len(STAGES) - 1:
            self.stage_index += 1
            self.setup_stage()
            self.start_cutscene(completed_stage, journal_text)
        else:
            self.game_state = "ending"

    def start_cutscene(self, completed_stage, journal_text):
        memory_lines = CUTSCENE_LINES.get(completed_stage, [])
        self.cutscene_lines = [
            f"Memoria Fragmentada {completed_stage + 1}",
            *memory_lines,
            "",
            journal_text,
            "",
            "Pressione ESPACO para continuar.",
        ]
        self.cutscene_reveal = 0.0
        self.cutscene_min_hold = 0.8
        self.game_state = "cutscene"

    def try_interact(self):
        for item in self.interactables:
            if not item.active:
                continue
            if self.player.colliderect(item.rect.inflate(28, 28)):
                self.resolve_interaction(item)
                return

    def resolve_interaction(self, item):
        stage = STAGES[self.stage_index]

        if stage == "Negacao" and item.kind == "reflection":
            item.active = False
            self.stage_data["found"] += 1
            self.raise_tension(0.05)

        elif stage == "Barganha" and item.kind == "note":
            sequence = self.stage_data["sequence"]
            prog = self.stage_data["progress"]
            expected = sequence[prog]

            if item.index == expected:
                self.stage_data["progress"] += 1
                self.raise_tension(0.02)
            else:
                self.stage_data["progress"] = 0
                self.stage_data["mistakes"] += 1
                self.raise_tension(0.07)
                self.trigger_ama_flash(force=True)

        elif stage == "Raiva" and item.kind == "shard":
            item.active = False
            self.stage_data["collected"] += 1
            self.raise_tension(0.04)

        elif stage == "Depressao" and item.kind == "tape":
            order = self.stage_data["order"]
            prog = self.stage_data["progress"]
            expected = order[prog]

            if item.index == expected:
                item.active = False
                self.stage_data["progress"] += 1
                self.raise_tension(0.02)
            else:
                self.stage_data["progress"] = 0
                self.stage_data["failures"] += 1
                for tape in self.interactables:
                    tape.active = True
                self.raise_tension(0.1)
                self.trigger_ama_flash(force=True)

        elif stage == "Aceitacao Distorcida" and item.kind == "altar":
            if self.fragment_count >= 4:
                self.stage_data["charged"] += 0.28
                self.raise_tension(0.03)
                if random.random() < 0.2:
                    self.trigger_ama_flash()
            else:
                self.raise_tension(0.05)
                self.trigger_ama_flash(force=True)

    def trigger_ama_flash(self, force=False):
        if not force and self.ama_flash > 0.2:
            return

        self.ama_flash = 0.7
        self.ama_glitch = []
        self.audio.trigger_ama_whisper()

        for _ in range(random.randint(4, 9)):
            x = random.randint(80, WIDTH - 220)
            y = random.randint(70, HEIGHT - 70)
            jitter = random.randint(-25, 25)
            self.ama_glitch.append((x, y, jitter))

    def raise_tension(self, amount):
        self.tension = min(1.0, self.tension + amount)

    def draw(self):
        pulse = int(16 * (0.5 + 0.5 * math.sin(self.total_time * 1.8)))
        bg_col = (BG[0] + pulse // 5, BG[1], BG[2] + pulse // 8)
        self.world_surface.fill(bg_col)

        for wall in self.walls:
            pygame.draw.rect(self.world_surface, WALL, wall)

        stage = STAGES[self.stage_index]
        for item in self.interactables:
            if not item.active:
                continue

            color = (80, 120, 150)
            if item.kind in {"reflection", "note", "tape"}:
                color = (95, 110, 140)
            if item.kind == "shard":
                color = (180, 180, 200)
            if item.kind == "altar":
                color = (130, 70, 70)

            pygame.draw.rect(self.world_surface, color, item.rect, border_radius=4)
            pygame.draw.rect(self.world_surface, (20, 20, 26), item.rect, 2, border_radius=4)

            if self.player.colliderect(item.rect.inflate(28, 28)):
                hint = self.small_font.render("E", True, TEXT)
                self.world_surface.blit(hint, (item.rect.centerx - 6, item.rect.top - 20))

        pygame.draw.rect(self.world_surface, (65, 175, 200), self.player, border_radius=4)
        pygame.draw.rect(self.world_surface, (200, 80, 80), self.entity, border_radius=6)

        self.draw_room_lighting()
        self.apply_post_fx()

        self.screen.blit(self.world_surface, (0, 0))
        self.draw_hud(stage)

        if self.game_state == "cutscene":
            self.draw_cutscene()

        if self.ama_flash > 0:
            alpha = int(170 * self.ama_flash)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 0, 0, min(100, alpha // 2)))
            self.screen.blit(overlay, (0, 0))

            for x, y, jitter in self.ama_glitch:
                text = self.big_font.render("Ama você", True, (255, 80, 80))
                self.screen.blit(text, (x + jitter * 0.08, y))

                ghost = self.big_font.render("Ama você", True, (255, 255, 255))
                ghost.set_alpha(90)
                self.screen.blit(ghost, (x - 3, y + 2))

        if self.game_state == "captured":
            self.draw_center_card(
                "Abraco Eterno",
                "Ela nao quer matar voce. Quer guardar voce para sempre.\nPressione R para recomecar.",
                (110, 20, 20),
            )

        if self.game_state == "ending":
            self.draw_ending_screen()

        pygame.display.flip()

    def draw_room_lighting(self):
        light_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        base_dark = 150 + int(self.tension * 40)
        light_overlay.fill((0, 0, 0, base_dark))

        for room in self.room_lights:
            flicker = 0.5 + 0.5 * math.sin(self.total_time * room.flicker_speed + room.phase)
            alpha = int(room.base_alpha + flicker * (25 + self.stage_index * 4))
            alpha = max(10, min(170, alpha))
            tint_surface = pygame.Surface((room.rect.width, room.rect.height), pygame.SRCALPHA)
            tint_surface.fill((room.tint[0], room.tint[1], room.tint[2], alpha))
            light_overlay.blit(tint_surface, room.rect.topleft)

        light_radius = int(130 + 35 * math.sin(self.total_time * 3.4) - self.tension * 26)
        light_radius = max(70, light_radius)
        for i in range(5):
            r = int(light_radius * (1.5 - i * 0.24))
            a = max(0, 220 - i * 55)
            pygame.draw.circle(light_overlay, (0, 0, 0, 255 - a), self.player.center, r)

        self.world_surface.blit(light_overlay, (0, 0))

    def apply_post_fx(self):
        # Pequena aberracao cromatica por deslocamento horizontal em alta tensao.
        if self.quality["chroma_enabled"] and self.tension > 0.5:
            glitch = int(1 + self.tension * 2)
            red_ghost = self.world_surface.copy()
            red_ghost.fill((255, 0, 0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            red_ghost.set_alpha(22)
            self.world_surface.blit(red_ghost, (glitch, 0))

        stage_tint = [
            (10, 16, 26, 14),
            (22, 10, 10, 17),
            (34, 8, 8, 20),
            (8, 16, 24, 18),
            (30, 0, 0, 24),
        ][self.stage_index]

        tint_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        tint_surface.fill(stage_tint)
        self.world_surface.blit(tint_surface, (0, 0))

        self.world_surface.blit(self.noise_surface, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.world_surface.blit(self.scanline_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        self.world_surface.blit(self.vignette_surface, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    def draw_hud(self, stage):
        top = pygame.Surface((WIDTH, 70), pygame.SRCALPHA)
        top.fill((0, 0, 0, 120))
        self.screen.blit(top, (0, 0))

        title = self.font.render(f"Casa Liminal - {stage}", True, TEXT)
        frag = self.small_font.render(f"Fragmentos: {self.fragment_count}/4", True, GOOD)
        instruction = self.small_font.render("WASD mover | E interagir | ESC sair", True, TEXT)
        quality = self.small_font.render("F1 Alto | F2 Medio | F3 Baixo | F4 Auto", True, (170, 170, 180))
        self.screen.blit(title, (24, 12))
        self.screen.blit(frag, (24, 40))
        self.screen.blit(instruction, (310, 42))
        self.screen.blit(quality, (310, 20))

        quality_now = self.small_font.render(f"Preset: {self.quality_name.title()}", True, (205, 205, 215))
        auto_txt = "ON" if self.auto_quality_enabled else "OFF"
        perf = self.small_font.render(
            f"Auto: {auto_txt} ({self.auto_quality_profile}) | FPS medio: {self.current_fps_avg:0.1f}",
            True,
            (205, 205, 215),
        )
        self.screen.blit(quality_now, (24, 58))
        self.screen.blit(perf, (310, 58))

        tension_w = 220
        bx, by = WIDTH - 260, 20
        pygame.draw.rect(self.screen, (40, 40, 45), (bx, by, tension_w, 14), border_radius=6)
        pygame.draw.rect(
            self.screen,
            (190, 70, 70),
            (bx, by, int(tension_w * self.tension), 14),
            border_radius=6,
        )
        txt_tension = self.small_font.render("Tensao", True, TEXT)
        self.screen.blit(txt_tension, (bx, by - 18))

        hug_w = 220
        by2 = 48
        pygame.draw.rect(self.screen, (40, 40, 45), (bx, by2, hug_w, 12), border_radius=6)
        pygame.draw.rect(
            self.screen,
            WARN,
            (bx, by2, int(hug_w * self.hug_meter), 12),
            border_radius=6,
        )
        txt_hug = self.small_font.render("Abraco da entidade", True, TEXT)
        self.screen.blit(txt_hug, (bx, by2 - 18))

        stage_msg = self.get_stage_hint()
        msg = self.small_font.render(stage_msg, True, (200, 200, 210))
        self.screen.blit(msg, (24, HEIGHT - 32))

    def get_stage_hint(self):
        stage = STAGES[self.stage_index]
        if stage == "Negacao":
            found = self.stage_data.get("found", 0)
            return f"Negacao: encontre reflexos falsos ({found}/3)."
        if stage == "Barganha":
            return "Barganha: acerte a sequencia dos bilhetes 3-1-4-2."
        if stage == "Raiva":
            c = self.stage_data.get("collected", 0)
            return f"Raiva: junte os cacos da foto ({c}/6)."
        if stage == "Depressao":
            return "Depressao: ative as fitas na ordem 2-3-1."
        if stage == "Aceitacao Distorcida":
            needed = self.stage_data.get("needed", 3.5)
            charged = self.stage_data.get("charged", 0.0)
            if self.fragment_count < 4:
                return "Altar: faltam fragmentos para reconstruir a memoria."
            return f"Altar: mantenha E para carregar ({charged:.1f}/{needed:.1f})."
        return ""

    def draw_cutscene(self):
        panel = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        panel.fill((8, 8, 12, 210))
        self.screen.blit(panel, (0, 0))

        # Ruido leve em cutscene para manter textura de fita analógica.
        cut_noise = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for _ in range(self.quality["cutscene_noise_points"]):
            x = random.randint(0, WIDTH - 2)
            y = random.randint(0, HEIGHT - 2)
            g = random.randint(120, 220)
            cut_noise.fill((g, g, g, 10), (x, y, 2, 2))
        self.screen.blit(cut_noise, (0, 0))

        total_chars = int(self.cutscene_reveal)
        y = 90
        for line in self.cutscene_lines:
            shown = line[:total_chars]
            total_chars -= len(line)
            if total_chars < 0:
                total_chars = 0
            txt = self.cut_font.render(shown, True, (228, 228, 236))
            self.screen.blit(txt, (70, y))
            y += 54

        if self.cutscene_min_hold <= 0:
            hint = self.small_font.render("ESPACO para continuar", True, (190, 190, 205))
            self.screen.blit(hint, (WIDTH - 250, HEIGHT - 38))

    def draw_center_card(self, title, body, tint):
        panel = pygame.Surface((700, 230), pygame.SRCALPHA)
        panel.fill((tint[0], tint[1], tint[2], 210))
        x = WIDTH // 2 - panel.get_width() // 2
        y = HEIGHT // 2 - panel.get_height() // 2
        self.screen.blit(panel, (x, y))

        t = self.big_font.render(title, True, (245, 245, 245))
        self.screen.blit(t, (x + 30, y + 22))

        lines = body.split("\n")
        for i, line in enumerate(lines):
            txt = self.font.render(line, True, (235, 235, 235))
            self.screen.blit(txt, (x + 34, y + 120 + i * 30))

    def draw_ending_screen(self):
        if self.victory_choice is None:
            body = (
                "A memoria esta completa.\n"
                "Y: romper o ciclo e sair da casa.\n"
                "N: aceitar o abraco eterno."
            )
            self.draw_center_card("Ultima Escolha", body, (35, 40, 60))
            return

        if self.victory_choice == "quebra":
            body = "Voce sai, mas o eco ainda sussurra: 'Ama você'.\nPressione R para jogar novamente."
            self.draw_center_card("Final: Ciclo Quebrado", body, (35, 65, 45))
        else:
            body = "A casa fecha os corredores. O abraco nunca termina.\nPressione R para jogar novamente."
            self.draw_center_card("Final: Abraco Eterno", body, (75, 30, 30))
