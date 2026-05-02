# Agent Instructions for GenshinChartPlayer

## Project shape
- Start from [main.py](main.py), which only parses `--admin` and calls `gui.app.run_app()`.
- Keep changes aligned with the main boundaries: [gui/](gui), [chart/](chart), [player/](player), [session/](session), and [shared/](shared).
- Treat [audio/](audio) as user-provided assets, not source code.

## What to read first
- Use [README.md](README.md) for installation, usage, packaging, permissions, and platform notes.
- Inspect [player/handlers/](player/handlers) before changing playback behavior; handlers are loaded dynamically and must keep their exported interface.

## Working conventions
- This project is primarily Windows-focused because keyboard simulation depends on platform permissions.
- Preserve the dynamic handler pattern when adding or modifying handlers; packaging must include [player/handlers/](player/handlers) and [audio/](audio).
- Avoid `PyInstaller --onefile`; follow the customtkinter packaging guidance linked from the README.
- Prefer focused changes in the owning module instead of cross-cutting edits.

## Validation
- Use `python test.py` for the lightweight test check when applicable.
- Use `python main.py` to verify the GUI entry path, and `python main.py --admin` when testing admin-aware behavior.
- If a change touches packaging or runtime assumptions, re-check the relevant section of [README.md](README.md) instead of duplicating instructions here.
