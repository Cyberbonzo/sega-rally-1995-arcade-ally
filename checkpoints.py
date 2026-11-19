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


def write_words(lanes, address, values):
    for index, value in enumerate(values):
        offset = address // 2 + 2 * index
        data = struct.pack("<I", value)
        lanes[0][offset:offset + 2] = data[:2]
        lanes[1][offset:offset + 2] = data[2:]


def countdown_hud(low, high):
    """Render hundreds, tens and units within the Revision C timer routine.

    The HUD caches rounded-up seconds in r4 and selects the digit palette
    in r5. Local i960 registers survive the arcade's tile drawing calls.
    Game time, checkpoint awards and race state are outside these edits.
    """
    lanes = bytearray(low), bytearray(high)

    # Both immediates are the existing HUD display limit.
    write_words(lanes, 0x1E514, [0x8CA803E7])
    write_words(lanes, 0x1E51C, [0x8C2003E7])

    # Start one digit to the left of the original tens position.
    # r6 = divisor, r7 = x, r8 = y, r9 = tile sheet.
    write_words(lanes, 0x1E554, [
        0x90383000,  # ld 0x20aebc, r7
        0x0020AEBC,  # absolute address
        0x5939C904,  # subo 4, r7, r7
        0x90403000,  # ld 0x20aec0, r8
        0x0020AEC0,  # absolute address
        0x90483000,  # ld 0x20ac7c, r9
        0x0020AC7C,  # absolute address
        0x8C300064,  # lda 100, r6
        0x5C801607,  # mov r7, r16
        0x5C881608,  # mov r8, r17
        0x5C901609,  # mov r9, r18
        0x5C981E00,  # mov 0, r19
        0x5CA01E00,  # mov 0, r20
        0x5A01A084,  # cmpi r4, r6
        0x1300000C,  # bge draw
        0x3D09A01C,  # cmpibne 1, r6, blank
        0x39012018,  # cmpibg 0, r4, blank
        0x74990586,  # divi r6, r4, r19
        0x749CCC0A,  # remi 10, r19, r19
        0x599CC005,  # addo r5, r19, r19
        0x0900B66C,  # call 0x29c10
        0x08000008,  # b next
        0x0900B7B4,  # call 0x29d60
        0x5939C804,  # addo 4, r7, r7
        0x74318D8A,  # divi 10, r6, r6
        0x3D01BFBC,  # cmpibne 0, r6, digit
        0x0A000000,  # ret
    ])

    # The hide callback clears the same three positions in the primary HUD.
    write_words(lanes, 0x1E5D0, [
        0x5C381E17,  # mov 23, r7
        0x5C401E09,  # mov 9, r8
        0x90483000,  # ld 0x20ac7c, r9
        0x0020AC7C,  # absolute address
        0x8C300064,  # lda 100, r6
        0x59201901,  # subo 1, 0, r4
        0x5C281E00,  # mov 0, r5
        0x08FFFF88,  # b digit
    ])
    return tuple(bytes(lane) for lane in lanes)


def cap_race_clock(low, high):
    """Store min(remaining ticks, 99 * 60) at every time-grant site."""
    lanes = bytearray(low), bytearray(high)
    # countdown_hud's hide handler branches away at 0x1E5EC. Its old
    # tail is unused and fits this leaf function without moving any code.
    routine = 0x1E5F0
    write_words(lanes, routine, [
        0x8C203000, 99 * 60,  # lda maximum ticks, r4 (callee-local)
        0x3EA10008,           # cmpible r20, r4, store
        0x5CA01604,           # mov r4, r20
        0x92A03000, 0x20B0B0, # store: st r20, remaining race ticks
        0x0A000000,           # ret
    ])
    # Stage start supplies ticks in r4. The other four paths (stage
    # carryover and checkpoint awards) already have the new time in r20.
    for site in (0x1C884, 0x1CDFC, 0x1D244, 0x1D2F4, 0x1D4DC):
        prepare = 0x5CA01604 if site == 0x1C884 else 0x5CA01614
        displacement = routine - (site + 4)
        write_words(lanes, site, [prepare, 0x09000000 | (displacement & 0xFFFFFC)])
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
    normal_hud = countdown_hud(*normal)
    slower_hud = countdown_hud(*slower)
    normal_cap = cap_race_clock(*normal_hud)
    slower_cap = cap_race_clock(*slower_hud)
    with ZipFile(path) as game:
        active = read_pair(game)
        if active not in (stock, normal, slower, normal_hud, slower_hud, normal_cap, slower_cap):
            raise ValueError("O programa atual diverge das versões compatíveis.")
        use_slower = requested_pace == 80 or (requested_pace is None and active in (slower, slower_hud, slower_cap))
        desired = slower_cap if use_slower else normal_cap
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
