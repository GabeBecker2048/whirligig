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
        "-f",
        "--file",
        type=argparse.FileType("r"),
        metavar="FILE",
        help="read labels from FILE, one per line; blank lines are skipped, '-' reads stdin",
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

    sources = [bool(args.labels), bool(args.preset), bool(args.file)]
    if sum(sources) > 1:
        parser.error("pass labels, --preset, or --file, but only one of them")
    if sum(sources) == 0:
        # given nothing else, read labels from a piped/redirected stdin -- but
        # never from a tty, where blocking on EOF would look like a hang
        if sys.stdin is not None and not sys.stdin.closed and not sys.stdin.isatty():
            args.file = sys.stdin
        else:
            parser.error(
                "nothing to spin; pass labels (whirligig heads tails), pipe them in, or try --preset random"
            )
    if args.radius < 2:
        parser.error("--radius must be at least 2")
    if args.delay < 0:
        parser.error("--delay must not be negative")

    labels = args.labels
    if args.preset:
        labels = PRESETS[args.preset if args.preset != "random" else random.choice(list(PRESETS))]
    elif args.file:
        labels = [label for label in (line.strip() for line in args.file) if label]
        if args.file is not sys.stdin:
            args.file.close()
        if not labels:
            parser.error(f"{args.file.name} has no labels; expected one per line")

    try:
        spin(labels, w_radius=args.radius, delay=args.delay)
    except ValueError as e:
        parser.error(str(e))
    except KeyboardInterrupt:
        # spin() restores the terminal in a finally, so there is nothing to undo
        # here; just exit quietly instead of dumping a traceback on Ctrl-C
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())