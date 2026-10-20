"""driver.py — a device driver stub backed by a file.

Models a character device: open/close/read/write/ioctl, with a real
file underneath and a small ioctl command set.
"""

from __future__ import annotations
import json
from pathlib import Path

DEV = Path.home() / "ucs" / "systems" / "driver" / "device.bin"


class Device:
    def __init__(self, path: Path = DEV):
        self.path = path
        self.fd = None
        self.cursor = 0
        self.ioctls = {
            "GET_POS": "return cursor",
            "SET_POS": "set cursor",
            "GET_SIZE": "return file size",
            "RESET": "cursor = 0",
        }

    def open(self):
        self.path.touch(exist_ok=True)
        self.fd = self.path.open("r+b")
        return 0

    def close(self):
        if self.fd:
            self.fd.close()
            self.fd = None
        return 0

    def write(self, data: bytes) -> int:
        if not self.fd:
            raise OSError("device not open")
        self.fd.seek(self.cursor)
        n = self.fd.write(data)
        self.cursor += n
        return n

    def read(self, n: int) -> bytes:
        if not self.fd:
            raise OSError("device not open")
        self.fd.seek(self.cursor)
        data = self.fd.read(n)
        self.cursor += len(data)
        return data

    def ioctl(self, cmd: str, arg=None):
        if cmd == "GET_POS":
            return self.cursor
        if cmd == "SET_POS":
            self.cursor = int(arg)
            return 0
        if cmd == "GET_SIZE":
            return self.path.stat().st_size
        if cmd == "RESET":
            self.cursor = 0
            return 0
        raise ValueError(f"unknown ioctl: {cmd}")


if __name__ == "__main__":
    d = Device()
    d.open()
    d.write(b"hello, driver\n")
    d.ioctl("RESET")
    print(f"read back: {d.read(20)!r}")
    print(f"size:      {d.ioctl('GET_SIZE')}")
    print(f"cursor:    {d.ioctl('GET_POS')}")
    d.close()
    print("self-test OK")
