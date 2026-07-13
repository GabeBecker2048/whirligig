import argparse
import sys

from whirligig.spinner import DELAY, WHEEL_RADIUS, spin


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="whirligig",
        description="Spin a wheel and pick one of the given labels at random.",
        epilog='example: whirligig Pizza Sushi Mexican Thai "Chicken Wings" Poke Other',
    )
    parser.add_argument(
        "labels",
        nargs="+",
        metavar="LABEL",
        help="the choices to put on the wheel; quote any that contain spaces",
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

    if args.radius < 2:
        parser.error("--radius must be at least 2")
    if args.delay < 0:
        parser.error("--delay must not be negative")

    try:
        spin(args.labels, w_radius=args.radius, delay=args.delay)
    except KeyboardInterrupt:
        # spin() restores the terminal in a finally, so there is nothing to undo
        # here; just exit quietly instead of dumping a traceback on Ctrl-C
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())