import argparse
import random
import sys

from whirligig.spinner import DELAY, WHEEL_RADIUS, spin

# CLI conveniences only -- the Python API just takes label lists
PRESETS = {
    "coin": ["heads", "tails"],
    "dice": [str(i + 1) for i in range(6)],
    # ordered so each number lands where it sits on a clock face
    "clock": [str((i + 2) % 12 + 1) for i in range(12)],
    "alphabet": [chr(c) for c in range(ord("a"), ord("z") + 1)],
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="whirligig",
        description="Spin a wheel and pick one of the given labels at random.",
        epilog='example: whirligig Pizza Sushi Mexican Thai "Chicken Wings" Poke Other',
    )
    parser.add_argument(
        "labels",
        nargs="*",
        metavar="LABEL",
        help="the choices to put on the wheel; quote any that contain spaces",
    )
    parser.add_argument(
        "-p",
        "--preset",
        choices=[*PRESETS, "random"],
        help="spin a ready-made wheel instead of giving labels; 'random' picks one of the others",
    )
    parser.add_argument(
        "-r",
        "--radius",
        type=int,
        default=WHEEL_RADIUS,
        help=f"radius of the wheel, in characters (default: {WHEEL_RADIUS})",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=DELAY,
        help=f"seconds each frame is held; lower spins faster (default: {DELAY})",
    )
    args = parser.parse_args(argv)

    if args.labels and args.preset:
        parser.error("pass labels or --preset, not both")
    if not args.labels and not args.preset:
        parser.error("nothing to spin; pass labels (whirligig heads tails) or try --preset random")
    if args.radius < 2:
        parser.error("--radius must be at least 2")
    if args.delay < 0:
        parser.error("--delay must not be negative")

    labels = args.labels
    if args.preset:
        labels = PRESETS[args.preset if args.preset != "random" else random.choice(list(PRESETS))]

    try:
        spin(labels, w_radius=args.radius, delay=args.delay)
    except KeyboardInterrupt:
        # spin() restores the terminal in a finally, so there is nothing to undo
        # here; just exit quietly instead of dumping a traceback on Ctrl-C
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())