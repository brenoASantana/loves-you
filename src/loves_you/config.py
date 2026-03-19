WIDTH, HEIGHT = 960, 540
FPS = 60

BG = (12, 14, 18)
WALL = (30, 34, 42)
TEXT = (220, 220, 220)
GOOD = (120, 200, 120)
WARN = (230, 170, 80)

PLAYER_SPEED = 220
ENTITY_SPEED_BASE = 90
ENTITY_SPEED_ANGRY = 135
HUG_DISTANCE = 40
HUG_FILL_PER_SEC = 0.48
HUG_DECAY_PER_SEC = 0.22

STAGES = [
    "Negacao",
    "Barganha",
    "Raiva",
    "Depressao",
    "Aceitacao Distorcida",
]

CUTSCENE_LINES = {
    0: [
        "Fragmento I: O espelho nao mentia.",
        "Voce chamava de cuidado.",
        "Mas o cuidado virava vigilancia.",
    ],
    1: [
        "Fragmento II: Promessas em papel molhado.",
        "Cada desculpa pedia mais uma chance.",
        "Cada chance apertava mais o peito.",
    ],
    2: [
        "Fragmento III: O som de pratos no chao.",
        "A raiva nao era odio.",
        "Era o pedido bruto por espaco.",
    ],
    3: [
        "Fragmento IV: O banheiro virou mar.",
        "A casa ficou muda.",
        "E o silencio aprendeu seu nome.",
    ],
}

DEFAULT_QUALITY = "medio"
DEFAULT_AUTO_PROFILE = "balanceado"

AUTO_QUALITY = {
    "enabled": False,
    "downgrade_fps": 49.0,
    "upgrade_fps": 57.0,
    "sample_window": 90,
    "check_interval": 2.0,
    "switch_cooldown": 3.0,
}

AUTO_QUALITY_PROFILES = {
    "agressivo": {
        "downgrade_fps": 53.0,
        "upgrade_fps": 58.0,
        "check_interval": 1.4,
        "switch_cooldown": 2.2,
    },
    "balanceado": {
        "downgrade_fps": 49.0,
        "upgrade_fps": 57.0,
        "check_interval": 2.0,
        "switch_cooldown": 3.0,
    },
    "conservador": {
        "downgrade_fps": 45.0,
        "upgrade_fps": 58.0,
        "check_interval": 2.8,
        "switch_cooldown": 4.0,
    },
}

QUALITY_PRESETS = {
    "alto": {
        "noise_interval": 0.025,
        "noise_block": 3,
        "noise_base": 140,
        "noise_stage": 28,
        "noise_tension": 110,
        "scanline_step": 3,
        "scanline_a": 18,
        "scanline_b": 10,
        "vignette_rings": 7,
        "vignette_width": 85,
        "vignette_alpha_base": 14,
        "vignette_alpha_step": 14,
        "cutscene_noise_points": 180,
        "chroma_enabled": True,
        "audio_mul": 1.0,
        "hiss_mul": 1.0,
    },
    "medio": {
        "noise_interval": 0.04,
        "noise_block": 4,
        "noise_base": 95,
        "noise_stage": 22,
        "noise_tension": 80,
        "scanline_step": 4,
        "scanline_a": 13,
        "scanline_b": 7,
        "vignette_rings": 6,
        "vignette_width": 74,
        "vignette_alpha_base": 11,
        "vignette_alpha_step": 12,
        "cutscene_noise_points": 120,
        "chroma_enabled": True,
        "audio_mul": 0.92,
        "hiss_mul": 0.86,
    },
    "baixo": {
        "noise_interval": 0.075,
        "noise_block": 5,
        "noise_base": 62,
        "noise_stage": 14,
        "noise_tension": 54,
        "scanline_step": 6,
        "scanline_a": 8,
        "scanline_b": 4,
        "vignette_rings": 4,
        "vignette_width": 62,
        "vignette_alpha_base": 9,
        "vignette_alpha_step": 9,
        "cutscene_noise_points": 70,
        "chroma_enabled": False,
        "audio_mul": 0.82,
        "hiss_mul": 0.68,
    },
}
