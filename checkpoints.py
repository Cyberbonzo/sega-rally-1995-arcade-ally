"""Add ten seconds to checkpoint awards in a private Revision C arcade set."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import struct
import tempfile
from zipfile import ZipFile

PROGRAM = "epr-17888c.12"
STOCK = "33abf9cdcee9583dc600c94e1e29ce260e8c5d32"
HIGH_LANE = "4b1efb3d5644fed1753da1750bf5c300d3a15d2c"


def update_lane(original):
    if hashlib.sha1(original).hexdigest() != STOCK:
        raise ValueError("Programa incompatÃ­vel com a revisÃ£o C.")
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
    return lane


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    path = args.archive.resolve()
    backup = path.with_suffix(".original.zip")
    source = backup if backup.exists() else path
    with ZipFile(source) as game:
        original = game.read(PROGRAM)
        if hashlib.sha1(game.read("epr-17889c.13")).hexdigest() != HIGH_LANE:
            raise ValueError("Segunda ROM de programa incompatÃ­vel.")
        modified = update_lane(original)
        if backup.exists():
            with ZipFile(path) as current:
                if current.read(PROGRAM) == modified:
                    return
            if not os.path.samefile(path, backup) and path.read_bytes() != backup.read_bytes():
                raise ValueError("O arquivo atual diverge da instalação anterior.")
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temp:
            dest = Path(temp.name)
    try:
        with ZipFile(source) as game, ZipFile(dest, "w") as output:
            for item in game.infolist():
                output.writestr(item, modified if item.filename == PROGRAM else game.read(item))
        with ZipFile(dest) as output:
            if output.testzip() is not None or output.read(PROGRAM) != modified:
                raise ValueError("Falha na verificação do conjunto.")
        shutil.copymode(path, dest)
        if not backup.exists():
            os.link(path, backup)
        os.replace(dest, path)
    finally:
        dest.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
