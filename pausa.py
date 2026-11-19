"""Pause this local Sega Rally arcade process with the right stick button."""
import os
from pathlib import Path
import select
import signal
import time

from evdev import InputDevice, ecodes, list_devices


ROOT = Path(__file__).resolve().parent


def find_game():
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            if (entry / "comm").read_text().strip().lower() != "segarally.exe":
                continue
            fd = os.pidfd_open(int(entry.name))
            try:
                if (entry / "cwd").resolve() == ROOT and not select.select([fd], [], [], 0)[0]:
                    return fd
            except OSError:
                pass
            os.close(fd)
        except (OSError, ValueError):
            continue
    return None


def open_steam_pad():
    for path in list_devices():
        try:
            pad = InputDevice(path)
        except OSError:
            continue
        if pad.name == "Microsoft X-Box 360 pad 0":
            return pad
        pad.close()
    return None


def watch(game):
    paused = False
    pad = None
    try:
        while True:
            if pad is None:
                pad = open_steam_pad()
            ready, _, _ = select.select([game, pad] if pad else [game], [], [], 1)
            if game in ready:
                return
            if pad is None or pad not in ready:
                continue
            try:
                for event in pad.read():
                    if (event.type, event.code, event.value) != (ecodes.EV_KEY, ecodes.BTN_THUMBR, 1):
                        continue
                    signal.pidfd_send_signal(game, signal.SIGCONT if paused else signal.SIGSTOP)
                    paused = not paused
                    print("Pausa" if paused else "Continuar", flush=True)
            except OSError:
                pad.close()
                pad = None
                if paused:
                    signal.pidfd_send_signal(game, signal.SIGCONT)
                    paused = False
    finally:
        if paused:
            try:
                signal.pidfd_send_signal(game, signal.SIGCONT)
            except ProcessLookupError:
                pass
        if pad:
            pad.close()
        os.close(game)


def stop(_signum, _frame):
    raise SystemExit


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGHUP, stop)
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        target = find_game()
        if target is not None:
            watch(target)
            break
        time.sleep(0.3)
