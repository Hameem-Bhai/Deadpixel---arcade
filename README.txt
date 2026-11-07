HAMEEM'S GAMING ZONE - IMPROVED COPY

This is a targeted revision of your uploaded Pygame game, not a replacement
with fewer mini-games. Keep your original as a backup.

RUN (Windows / VS Code terminal)
  python -m pip install pygame
  python gaming_zone_improved.py

Or install requirements:
  python -m pip install -r requirements.txt

CHANGES
- Removed repeated Particle, Button, SessionStats, settings and theme blocks.
- Redesigned main menu and seven-game selection grid.
- Consistent buttons with fitting labels and hover outlines.
- Fixed Enter being processed twice during name entry.
- Name entry now includes every selected player (2-4).
- Game cards explicitly show which games support 2 vs 2-4 players.
- F1 help replaces H, freeing H for ordinary game input.
- Player 3 racing movement: T up, B down, V left, N right.
  Player 1 WASD; Player 2 arrows; Player 4 IJKL.
- ESC is left to each scene instead of also triggering a global transition.
- Two-sided fade transitions and protection against restarting active fades.
- Scoreboard includes all seven categories in a compact table.
- Snake result uses survival, not food score, to identify the winner.
- Timing bar and 3-second marker use the same 7-second scale.
- Cached menu gradients instead of rebuilding them each frame.
- Fixed-step 120 Hz updates preserve existing frame-based physics speeds.
- F11 toggles scaled fullscreen.
- Moved audio preconfiguration ahead of pygame initialization.
- Reduced dice area width so it stays inside the game window.

TEST STATUS AND LIMITATIONS
Python parsing and compilation checks passed. Pygame is not installed in the
editing environment, so graphical execution, audio, fullscreen behavior, and
complete playthroughs have NOT been tested. Treat this as a preview build.

Only Yatzy and Racing support 3-4 players; other games remain 2-player.
Statistics remain session-only. Settings save beside the script.
Help is informational, NOT a pause screen: timed games keep running.
The original gameplay and many original rendering routines are retained.
enjoy!