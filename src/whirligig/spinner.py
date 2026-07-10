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
                wheel.m[y] = wheel.m[y].replace(f" {label} *", f" {Colors.colors[i%len(Colors.colors)]}{label} *{Colors.RESET}")
                wheel.m[y] = wheel.m[y].replace(f"* {label} ", f"{Colors.colors[i%len(Colors.colors)]}* {label}{Colors.RESET} ")

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
    lines.append(f"You got {Colors.colors[i%len(Colors.colors)]}{wheel.labels[i]}{Colors.RESET}!")
    return "\n".join(lines)

# draws the frame over the previous one, waits DELAY
def display(wheel: Wheel, i: int) -> None:
    frame = render_frame(wheel, i)
    # \033[H jumps to the top-left of the screen; \033[K erases any leftover
    # characters from the previous frame on each line
    print("\033[H" + "\n".join(line + "\033[K" for line in frame.split("\n")))
    time.sleep(DELAY)

## THE MAIN FUNCTION ##
# given a list, this function will create and print a spinning wheel ASCII animation
def spin(labels: list[str], w_radius=WHEEL_RADIUS):
    wheel = Wheel(w_radius, labels)

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
    print("\033[?1007s\033[?1007l\033[?1049h\033[?25l", end="")
    try:
        # full rotations
        for j in range(random.randint(2, 5)):
            for i in range(wheel.num_labels):
                display(wheel, i=i)

        # actual choice
        for i in range(random.randint(1, wheel.num_labels)):
            display(wheel, i=i)
    finally:
        print("\033[?1049l\033[?1007r\033[?25h", end="")
        if old_tty is not None:
            # discards any input buffered during the spin (scrolls, keypresses)
            # so it doesn't leak into the shell prompt, then re-enables echo
            termios.tcflush(fd, termios.TCIFLUSH)
            termios.tcsetattr(fd, termios.TCSANOW, old_tty)

    # everything drawn in the alternate screen vanishes when it exits, so
    # reprint the final frame to the normal screen to keep the result visible
    print(render_frame(wheel, i))


if __name__ == "__main__":
    dice_roll = [str(i+1) for i in range(6)]
    clock = [str((i+2)%12 + 1) for i in range(12)]
    alphabet = list(map(chr, range(ord('a'), ord('z')+1)))
    coin_flip = ["heads", "tails"]
    spin(random.choice([dice_roll, clock, alphabet, coin_flip]))
