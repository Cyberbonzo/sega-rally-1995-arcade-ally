"""Persist the local srallyc cabinet's NVRAM while the PC wrapper is running."""
import argparse
import errno
import hashlib
import os
from pathlib import Path
import struct
import tempfile
import time

ROOT = Path(__file__).resolve().parent
CABINET = ROOT / "nvram/srallyc/backup1"
SNAPSHOT = ROOT / "saves/arcade/backup1"
EXE = ROOT / "segarally.exe"
BUILD = "44543d1661469096607e554c1d897e1a63917f567abc2e759686e11fcafdd56b"
SIZE = 16384
BLOCK = 0xC68


def valid(data):
    return (len(data) == SIZE and data[2:4] == BLOCK.to_bytes(2, "little")
            and data[:BLOCK] == data[BLOCK:2 * BLOCK])


def read_file(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return b""


def write_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        name = Path(tmp.name)
        try:
            tmp.write(data)
            tmp.flush()
            os.fsync(tmp.fileno())
        except BaseException:
            tmp.close()
            name.unlink(missing_ok=True)
            raise
    try:
        os.replace(name, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        name.unlink(missing_ok=True)


def restore():
    saved = read_file(SNAPSHOT)
    native = read_file(CABINET)
    if (valid(saved) and native != saved
            and (not valid(native) or SNAPSHOT.stat().st_mtime_ns > CABINET.stat().st_mtime_ns)):
        write_file(CABINET, saved)
        print("Ranking restaurado", flush=True)


def find_process():
    for path in Path("/proc").glob("[0-9]*"):
        try:
            if (path / "comm").read_text().strip() == "segarally.exe" and (path / "cwd").resolve() == ROOT:
                return path
        except (OSError, RuntimeError):
            continue
    return None


def devices(process, fd):
    maps = [line.split(maxsplit=5) for line in (process / "maps").read_text().splitlines()]
    base = next((int(m[0].split("-")[0], 16) for m in maps
                 if m[2] == "00000000" and len(m) == 6 and m[5] == str(EXE)), None)
    if base is None:
        return []
    # The stock 1.0.0c build uses a secondary MSVC vtable for its MAME
    # NVRAM interface. Check both vtables and the device's declared length.
    interface = struct.pack("<Q", base + 0x5060A8)
    primary = struct.pack("<Q", base + 0x506028)
    matches = []
    for region in maps:
        low, high = (int(part, 16) for part in region[0].split("-"))
        if region[1] != "rw-p" or low >= 2**32 or len(region) != 5:
            continue
        for start in range(low, high, 1024 * 1024):
            chunk = os.pread(fd, min(1024 * 1024, high - start), start)
            i = chunk.find(interface)
            while i != -1:
                obj = start + i
                if obj % 8 == 0 and os.pread(fd, 8, obj - 0x460) == primary:
                    fields = os.pread(fd, 16, obj + 0x78)
                    if len(fields) == 16:
                        address, length = struct.unpack("<QQ", fields)
                        if length == SIZE and valid(os.pread(fd, SIZE, address)):
                            matches.append((obj, interface, address))
                i = chunk.find(interface, i + 1)
    return matches


def watch(process):
    last = read_file(SNAPSHOT)
    device = None
    last_save = 0
    with (process / "mem").open("rb", buffering=0) as memory:
        fd = memory.fileno()
        while process.exists():
            try:
                if device is None:
                    matches = devices(process, fd)
                    if len(matches) != 1:
                        time.sleep(2)
                        continue
                    device = matches[0]
                obj, interface, address = device
                if (os.pread(fd, 8, obj) != interface or
                        os.pread(fd, 16, obj + 0x78) != struct.pack("<QQ", address, SIZE)):
                    device = None
                    continue
                data = os.pread(fd, SIZE, address)
            except OSError as error:
                if error.errno not in (errno.EIO, errno.EFAULT):
                    raise
                device = None
                time.sleep(1)
                continue
            now = time.monotonic()
            if valid(data) and data != last and (data[0x2E8:BLOCK] != last[0x2E8:BLOCK] or now - last_save >= 15):
                write_file(SNAPSHOT, data)
                last, last_save = data, now
            time.sleep(0.25)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("restore", "watch"))
    mode = parser.parse_args().mode
    if hashlib.sha256(EXE.read_bytes()).hexdigest() != BUILD:
        print("VersÃ£o nÃ£o reconhecida para cÃ³pias em tempo real.", flush=True)
        return
    if mode == "restore":
        restore()
        return
    for _ in range(240):
        process = find_process()
        if process:
            try:
                watch(process)
            except (FileNotFoundError, ProcessLookupError):
                pass
            except OSError:
                if process.exists():
                    raise
            return
        time.sleep(0.5)


if __name__ == "__main__":
    main()
