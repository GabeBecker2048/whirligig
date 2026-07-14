# Demo recording for the README.
#
# Regenerate with:   vhs demo.tape          -> writes demo.gif
# Needs vhs (which needs ttyd + ffmpeg): https://github.com/charmbracelet/vhs
#
# vhs runs the command in a fresh shell, so `whirligig` must be on PATH --
# either `pip install whirligig` first, or run with the project venv active:
#   source .venv/bin/activate && vhs demo.tape

Output demo.gif

# the 7-label wheel renders rows 91 chars wide and 22 lines tall; the terminal
# must fit that (roughly 100x26 at this font size) or lines wrap, the redraw
# misaligns, and the gif ghosts with the top of the wheel scrolled off
Set FontSize 14
Set Width 980
Set Height 520
Set Padding 16

# the venv's activate script exports the full shell PS1, which leaks into
# vhs's recording shell; reset it to vhs's default prompt off-camera
Hide
Type `PS1='\[\e[38;2;90;86;224m\]> \[\e[0m\]'`
Enter
Type "clear"
Enter
Show

Type 'whirligig Pizza Sushi Tacos Thai "Chicken Wings" Poke Burgers'
Sleep 800ms
Enter

# worst-case spin at the default delay is ~4.5s; wait it out
Sleep 6s

# linger on the result before the gif loops
Sleep 3s