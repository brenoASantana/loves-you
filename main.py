import argparse
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loves_you.game import Game


def parse_args():
    parser = argparse.ArgumentParser(description="Ama voce - horror psicologico em pygame")
    parser.add_argument(
        "--quality",
        choices=["alto", "medio", "baixo"],
        default="medio",
        help="Preset inicial de qualidade.",
    )
    parser.add_argument(
        "--auto-quality",
        choices=["on", "off"],
        default="off",
        help="Liga ou desliga o auto quality no inicio.",
    )
    parser.add_argument(
        "--auto-profile",
        choices=["agressivo", "balanceado", "conservador"],
        default="balanceado",
        help="Perfil de ajuste automatico por FPS.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    Game(
        initial_quality=args.quality,
        auto_quality_enabled=args.auto_quality == "on",
        auto_quality_profile=args.auto_profile,
    ).run()
