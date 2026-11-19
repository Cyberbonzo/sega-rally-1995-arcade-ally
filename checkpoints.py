"""Adjust checkpoint time and optionally CPU pace in a private Revision C arcade set."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import struct
import tempfile
from zipfile import ZipFile

PROGRAM = "epr-17888c.12"
SECOND = "epr-17889c.13"
STOCK = "33abf9cdcee9583dc600c94e1e29ce260e8c5d32"
HIGH_LANE = "4b1efb3d5644fed1753da1750bf5c300d3a15d2c"


def update_lane(original):
    if hashlib.sha1(original).hexdigest() != STOCK:
        raise ValueError("Programa incompatível com a revisão C.")
    lane = bytearray(original)
    for table in (0x466F0, 0x46D10):
        for course in range(4):
            for row in range(24):
                for column in range(4):
                    # Row group zero is reused after lap one. In the other
                    # groups column zero supplies the starting time.
                    if row >= 4 and column == 0:
                        continue
                    offset = (table + course * 384 + row * 16 + column * 4) // 2
                    value = struct.unpack_from("<h", lane, offset)[0]
                    if value > 0:
                        struct.pack_into("<h", lane, offset, value + 600)
    return bytes(lane)


def cpu_pace(low, high):
    """Change only the aligned float speed fields read by the CPU driver."""
    lanes = bytearray(low), bytearray(high)

    def word(address):
        offset = address // 2
        return lanes[0][offset:offset + 2] + lanes[1][offset:offset + 2]

    def scale(address):
        speed, = struct.unpack("<f", word(address))
        if not 0 < speed < 400:
            raise ValueError("Velocidade de adversário fora da faixa esperada.")
        encoded = struct.pack("<f", speed * 0.8)
        offset = address // 2
        lanes[0][offset:offset + 2] = encoded[:2]
        lanes[1][offset:offset + 2] = encoded[2:]

    # Championship has separate lists for cars ahead of and behind the player.
    # Each row holds the model, target pace, grid offset and an extra field.
    for entry in range(8):
        pointer, = struct.unpack("<I", word(0x3E490 + entry * 4))
        row = pointer - 0x59F000
        while struct.unpack("<i", word(row))[0] != -1:
            scale(row + 4)
            row += 16

    # Alternate CPU driver profiles end with a zero; later slots reuse the
    # last speed. Never scale the player or the grid/track coordinates.
    for course in range(4):
        address = 0x3DEF0 + 32 * course
        for slot in range(8):
            if word(address + slot * 4) == bytes(4):
                break
            scale(address + slot * 4)
    return tuple(bytes(lane) for lane in lanes)


def read_pair(archive):
    return archive.read(PROGRAM), archive.read(SECOND)


def apply(path, requested_pace):
    backup = path.with_suffix(".original.zip")
    if path == backup or path.name.endswith(".original.zip"):
        raise ValueError("Escolha o arquivo de jogo ativo.")
    with ZipFile(backup if backup.exists() else path) as game:
        stock = read_pair(game)
    if hashlib.sha1(stock[1]).hexdigest() != HIGH_LANE:
        raise ValueError("Segunda ROM de programa incompatível.")
    normal = update_lane(stock[0]), stock[1]
    slower = cpu_pace(*normal)
    with ZipFile(path) as game:
        active = read_pair(game)
        if active not in (stock, normal, slower):
            raise ValueError("O programa atual diverge das versões compatíveis.")
        desired = slower if requested_pace == 80 or (requested_pace is None and active == slower) else normal
        if active == desired:
            return
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
            destination = Path(temp.name)
        try:
            replacements = dict(zip((PROGRAM, SECOND), desired))
            with ZipFile(destination, "w") as output:
                output.comment = game.comment
                for item in game.infolist():
                    data = replacements[item.filename] if item.filename in replacements else game.read(item)
                    output.writestr(item, data)
            with ZipFile(destination) as check:
                if check.testzip() is not None or read_pair(check) != desired:
                    raise ValueError("Falha na verificação do conjunto.")
            shutil.copymode(path, destination)
            if not backup.exists():
                os.link(path, backup)
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
    try:
        os.replace(destination, path)
    finally:
        destination.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--ritmo", type=int, choices=(80, 100),
                        help="Velocidade-alvo dos adversários em porcentagem.")
    args = parser.parse_args()
    apply(args.archive.resolve(), args.ritmo)


if __name__ == "__main__":
    main()
