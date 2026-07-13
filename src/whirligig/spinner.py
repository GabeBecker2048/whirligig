from math import sin, cos, pi
from copy import deepcopy
import os
import random
import sys
import time

try:
    import termios
except ImportError:
    termios = None  # Windows has no termios (and no scroll-to-arrow-keys behavior)

WHEEL_RADIUS = 10
DELAY = 0.1

class Colors:
    """ ANSI color codes """
    RESET = "\033[0m"
    colors = [
        "\033[0;31m",
        "\033[0;32m",
        "\033[0;33m",
        "\033[0;34m",
        "\033[0;35m",
        "\033[0;36m",
        "\033[0;37m",
        "\033[1;31m",
        "\033[1;32m",
        "\033[1;33m",
        "\033[1;34m",
        "\033[1;35m",
        "\033[1;36m",
    ]


class Wheel:
    def __init__(self, radius, labels) -> None:
        self.r = radius
        self.d = radius*2
        self.labels = labels
        # a fresh shuffle of the palette per wheel: label colors are random on
        # every spin, but stable across the frames of one spin
        self.colors = random.sample(Colors.colors, k=len(Colors.colors))
        self.m = [" " * (self.d+1)] * (self.d+1)
        self.num_labels = len(labels)
        self.angles = [pi/(self.num_labels/2) * p for p in range(self.num_labels)]
        self.points = []
        for i in range(self.num_labels):
            p = self.get_coords(i, self.r) 
            self[p] = "*"
            self.points.append(p)

    def __setitem__(self, key: tuple[int, int], value: str) -> None:
        x, y = key
        lrow = list(self.m[y])
        lrow[x] = value
        self.m[y] = "".join(lrow)

    def __getitem__(self, key: tuple[int, int]) -> str:
        x, y = key
        return self.m[y][x]
    
    def __str__(self) -> str:
        return "\n".join(self.m)

    def add_labels(self, inplace = False):
        wheel = self if inplace else deepcopy(self)

        # adds whitespace
        whitespace = " " * (len(max(wheel.labels, key=len)) + 1)
        for y in range(len(wheel.m)):
            wheel.m[y] = wheel.m[y].replace(" ", "   ").replace("*", " * ")
            wheel.m[y] = whitespace + wheel.m[y] + whitespace
        
        # adds labels
        for label, point in zip(wheel.labels, wheel.points):
            x, y = point
            if x<wheel.r or (x==wheel.r and y<wheel.r):
                for i in range(len(label)):
                    ix = x-len(label) + i + len(whitespace) + (x * 2)
                    wheel[ix, y] = label[i]
            elif x>wheel.r or (x==wheel.r and y>wheel.r):
                for i in range(len(label)):
                    ix = x+3 + i + len(whitespace) + (x * 2)
                    wheel[ix, y] = label[i]

        # adds color
        for y in range(len(wheel.m)):
            for i, label in enumerate(wheel.labels):
                color = wheel.colors[i % len(wheel.colors)]
                wheel.m[y] = wheel.m[y].replace(f" {label} *", f" {color}{label} *{Colors.RESET}")
                wheel.m[y] = wheel.m[y].replace(f"* {label} ", f"{color}* {label}{Colors.RESET} ")

        return wheel

    # given an angle and a scaler, returns a tuple of coords to the point
    def get_coords(self, idx: int, scaler: int) -> tuple[int, int]:
        a = self.angles[idx]
        return round(cos(a)*scaler) + self.r, round(sin(a)*scaler) + self.r
    
    # given an angle and the circle array, we return a deepcopy with a line drawn from the center
    def draw_line(self, idx: int):
        c = deepcopy(self)
        for line_scaler in range(1, c.r):
            p = c.get_coords(idx, line_scaler)
            c[p] = "*"
        return c


# renders one frame: the wheel with the spinner pointing at label i, plus the result line
def render_frame(wheel: Wheel, i: int) -> str:
    wheel = wheel.draw_line(i)
    wheel = wheel.add_labels()
    lines = str(wheel).split("\n")
    lines.append(f"You got {wheel.colors[i%len(wheel.colors)]}{wheel.labels[i]}{Colors.RESET}!")
    return "\n".join(lines)

# draws the frame over the previous one, waits delay
def display(wheel: Wheel, i: int, delay=DELAY, stream=None) -> None:
    stream = sys.stdout if stream is None else stream
    frame = render_frame(wheel, i)
    # \033[H jumps to the top-left of the screen; \033[K erases any leftover
    # characters from the previous frame on each line
    print("\033[H" + "\n".join(line + "\033[K" for line in frame.split("\n")), file=stream)
    time.sleep(delay)


# the animation is a terminal effect, not data, so it only ever goes to a stream
# that is a tty: stdout when it is one, stderr when stdout has been redirected
# (the wheel still spins on screen while `$(whirligig ...)` captures the answer),
# and nowhere at all when neither is -- in CI or under `whirligig ... &> file`
# there is no terminal to draw on, so we skip straight to the result
def animation_stream():
    if sys.stdout.isatty():
        return sys.stdout
    if sys.stderr.isatty():
        return sys.stderr
    return None


# runs the wheel animation on `stream`, landing on `choice`
def animate(wheel: Wheel, choice: int, delay: float, stream) -> None:
    # enables ANSI escape codes in the legacy Windows console
    if os.name == 'nt':
        os.system('')

    # in the alternate screen, terminals turn mouse scrolls into arrow key
    # presses on stdin; we never read stdin, so stop the tty from echoing
    # them onto the wheel while we animate
    old_tty = None
    if termios is not None and sys.stdin.isatty():
        fd = sys.stdin.fileno()
        old_tty = termios.tcgetattr(fd)
        new_tty = termios.tcgetattr(fd)
        new_tty[3] &= ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, new_tty)

    # animates in the alternate screen buffer (like vim/less) with the cursor
    # hidden -- it has no scrollback, so scrolling can't break the redraws;
    # \033[?1007s + \033[?1007l saves then disables scroll-to-arrow-keys mode;
    # always restores the terminal state afterwards
    print("\033[?1007s\033[?1007l\033[?1049h\033[?25l", end="", file=stream)
    try:
        # full rotations
        for j in range(random.randint(2, 5)):
            for i in range(wheel.num_labels):
                display(wheel, i=i, delay=delay, stream=stream)

        # the partial rotation that lands on the choice
        for i in range(choice + 1):
            display(wheel, i=i, delay=delay, stream=stream)
    finally:
        print("\033[?1049l\033[?1007r\033[?25h", end="", file=stream)
        if old_tty is not None:
            # discards any input buffered during the spin (scrolls, keypresses)
            # so it doesn't leak into the shell prompt, then re-enables echo
            termios.tcflush(fd, termios.TCIFLUSH)
            termios.tcsetattr(fd, termios.TCSANOW, old_tty)

    # everything drawn in the alternate screen vanishes when it exits, so
    # reprint the final frame to the normal screen to keep the result visible
    print(render_frame(wheel, choice), file=stream)

## THE MAIN FUNCTION ##
# given a list, this function will create and print a spinning wheel ASCII
# animation, and return the label it landed on
def spin(labels: list[str], w_radius=WHEEL_RADIUS, delay=DELAY) -> str:
    # the renderer assumes every label occupies one row
    for label in labels:
        if any(c in label for c in "\n\r\t"):
            raise ValueError(f"label {label!r} contains a newline or tab, which would break the wheel's shape")

    wheel = Wheel(w_radius, labels)
    choice = random.randrange(wheel.num_labels)

    stream = animation_stream()
    if stream is not None:
        animate(wheel, choice, delay, stream)

    # stdout's contract is the choice itself: when it is not a terminal something
    # is capturing it, so it gets the bare label and nothing else -- no frames, no
    # color. When it is a terminal, the animation above already announced the
    # result, so printing it again would just be noise
    if not sys.stdout.isatty():
        print(labels[choice])

    return labels[choice]
