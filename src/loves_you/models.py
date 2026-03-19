from dataclasses import dataclass

import pygame


@dataclass
class Interactable:
    rect: pygame.Rect
    label: str
    active: bool = True
    kind: str = "generic"
    index: int = 0


@dataclass
class RoomLight:
    rect: pygame.Rect
    tint: tuple[int, int, int]
    base_alpha: int
    flicker_speed: float
    phase: float
