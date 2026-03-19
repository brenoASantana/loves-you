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
        default=None,
        help="Preset inicial de qualidade.",
    )
    parser.add_argument(
        "--auto-quality",
        choices=["on", "off"],
        default=None,
        help="Liga ou desliga o auto quality no inicio.",
    )
    parser.add_argument(
        "--auto-profile",
        choices=["agressivo", "balanceado", "conservador"],
        default=None,
        help="Perfil de ajuste automatico por FPS.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    Game(
        initial_quality=args.quality,
        auto_quality_enabled=(None if args.auto_quality is None else args.auto_quality == "on"),
        auto_quality_profile=args.auto_profile,
    ).run()
