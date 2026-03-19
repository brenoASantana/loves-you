from __future__ import annotations

import math
from array import array

import pygame


class AudioManager:
    def __init__(self):
        self.available = False
        self.ambient_low_channel = None
        self.ambient_high_channel = None
        self.hiss_channel = None
        self.heartbeat_channel = None
        self.fx_channel = None

        self.ambient_low_sound = None
        self.ambient_high_sound = None
        self.hiss_sound = None
        self.heartbeat_sound = None
        self.whisper_sound = None

        self._try_init()

    def _try_init(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)

            self.ambient_low_channel = pygame.mixer.Channel(0)
            self.ambient_high_channel = pygame.mixer.Channel(1)
            self.hiss_channel = pygame.mixer.Channel(2)
            self.heartbeat_channel = pygame.mixer.Channel(3)
            self.fx_channel = pygame.mixer.Channel(4)

            self.ambient_low_sound = self._make_tone(78, 2.4, 0.22, mod=0.5)
            self.ambient_high_sound = self._make_tone(164, 1.7, 0.15, mod=1.9)
            self.hiss_sound = self._make_hiss(1.3, 0.16)
            self.heartbeat_sound = self._make_heartbeat(0.65, 0.35)
            self.whisper_sound = self._make_tone(330, 0.35, 0.28)

            self.ambient_low_channel.play(self.ambient_low_sound, loops=-1)
            self.ambient_high_channel.play(self.ambient_high_sound, loops=-1)
            self.hiss_channel.play(self.hiss_sound, loops=-1)
            self.ambient_low_channel.set_volume(0.1)
            self.ambient_high_channel.set_volume(0.07)
            self.hiss_channel.set_volume(0.04)
            self.available = True
        except pygame.error:
            self.available = False

    def _make_tone(self, freq: float, duration: float, volume: float, mod: float = 1.2):
        sample_rate = 22050
        total = int(sample_rate * duration)
        amplitude = int(32767 * volume)
        samples = array("h")

        for i in range(total):
            t = i / sample_rate
            wave = math.sin(2.0 * math.pi * freq * t)
            wave += 0.35 * math.sin(2.0 * math.pi * (freq * 0.5) * t)
            wave *= 0.72 + 0.28 * math.sin(2.0 * math.pi * mod * t)
            samples.append(int(amplitude * wave))

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _make_hiss(self, duration: float, volume: float):
        sample_rate = 22050
        total = int(sample_rate * duration)
        amplitude = int(32767 * volume)
        samples = array("h")

        seed = 1337
        for i in range(total):
            seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
            n = (seed / 0x7FFFFFFF) * 2.0 - 1.0
            lp = 0.35 * math.sin(2.0 * math.pi * 90 * (i / sample_rate))
            wave = 0.66 * n + lp
            samples.append(int(amplitude * wave))

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _make_heartbeat(self, duration: float, volume: float):
        sample_rate = 22050
        total = int(sample_rate * duration)
        samples = array("h")
        amplitude = int(32767 * volume)

        for i in range(total):
            t = i / sample_rate
            pulse_a = math.exp(-220 * (t - 0.08) ** 2)
            pulse_b = math.exp(-240 * (t - 0.20) ** 2)
            wave = (pulse_a + 0.85 * pulse_b) * math.sin(2.0 * math.pi * 56 * t)
            samples.append(int(amplitude * wave))

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def update(
        self,
        distance_to_entity: float,
        tension: float,
        stage_index: int,
        audio_mul: float = 1.0,
        hiss_mul: float = 1.0,
    ):
        if (
            not self.available
            or self.ambient_low_channel is None
            or self.ambient_high_channel is None
            or self.hiss_channel is None
            or self.heartbeat_channel is None
        ):
            return

        proximity = max(0.0, min(1.0, 1.0 - distance_to_entity / 330.0))
        stage_weight = min(1.0, 0.15 + stage_index * 0.18)

        low_volume = 0.08 + tension * 0.12 + stage_weight * 0.12
        high_volume = 0.03 + stage_weight * 0.14 + proximity * 0.08 + tension * 0.09
        hiss_volume = 0.02 + stage_weight * 0.11 + tension * 0.08

        self.ambient_low_channel.set_volume(max(0.0, min(0.55, low_volume * audio_mul)))
        self.ambient_high_channel.set_volume(max(0.0, min(0.52, high_volume * audio_mul)))
        self.hiss_channel.set_volume(max(0.0, min(0.38, hiss_volume * hiss_mul)))

        heartbeat_volume = (proximity**1.7) * (0.25 + 0.7 * tension)
        heartbeat_volume = max(0.0, min(0.9, heartbeat_volume))

        if heartbeat_volume > 0.04 and not self.heartbeat_channel.get_busy():
            if self.heartbeat_sound is not None:
                self.heartbeat_channel.play(self.heartbeat_sound, loops=-1)
        if heartbeat_volume <= 0.04 and self.heartbeat_channel.get_busy():
            self.heartbeat_channel.stop()

        self.heartbeat_channel.set_volume(heartbeat_volume * audio_mul)

    def trigger_ama_whisper(self, volume: float = 1.0):
        if not self.available or self.fx_channel is None or self.whisper_sound is None:
            return
        self.fx_channel.set_volume(max(0.0, min(1.0, volume)))
        self.fx_channel.play(self.whisper_sound)

    def shutdown(self):
        if not self.available:
            return
        if self.ambient_low_channel is not None:
            self.ambient_low_channel.stop()
        if self.ambient_high_channel is not None:
            self.ambient_high_channel.stop()
        if self.hiss_channel is not None:
            self.hiss_channel.stop()
        if self.heartbeat_channel is not None:
            self.heartbeat_channel.stop()
        if self.fx_channel is not None:
            self.fx_channel.stop()
