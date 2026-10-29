"""Tests for scripts/check-package.py: one good package and the mistakes it must catch.

    python3 -m unittest discover -s tests
"""
import io
import os
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK = os.path.join(ROOT, "scripts", "check-package.py")
RUN = b"#!/bin/sh\necho hello >toGround/out.txt\n"


def elf(machine=40, bits=1, flags=0x05000400, interp=None):
    """A minimal ELF header with one optional PT_INTERP program header."""
    ident = b"\x7fELF" + bytes([bits, 1, 1]) + b"\0" * 9
    phoff, phnum = 52, 1 if interp else 0
    head = ident + struct.pack("<HHIIIIIHHHHHH", 2, machine, 1, 0, phoff, 0, flags, 52, 32, phnum, 40, 0, 0)
    if interp:
        off = 52 + 32
        head += struct.pack("<IIIIIIII", 3, off, 0, 0, len(interp) + 1, len(interp) + 1, 4, 1)
        head += interp + b"\0"
    return head + b"\0" * 64


def package(entries):
    """entries: list of (name, data, mode, uname)."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for name, data, mode, owner in entries:
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.uname, info.gname = len(data), mode, owner, owner
            info.uid = info.gid = 1024
            t.addfile(info, io.BytesIO(data))
    return buf.getvalue()


GOOD = [("run", RUN, 0o755, "exp"), ("app", elf(), 0o755, "exp"), ("README.txt", b"note\n", 0o644, "exp")]


class CheckPackage(unittest.TestCase):
    def check(self, entries):
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as f:
            f.write(package(entries))
        try:
            p = subprocess.run([sys.executable, "-I", CHECK, f.name], capture_output=True, text=True)
        finally:
            os.unlink(f.name)
        return p.returncode, p.stdout

    def assertError(self, entries, text):
        rc, out = self.check(entries)
        self.assertEqual(rc, 1, out)
        self.assertIn(text, out)

    def test_good_package_passes(self):
        rc, out = self.check(GOOD)
        self.assertEqual(rc, 0, out)

    def test_macos_metadata(self):
        self.assertError(GOOD + [("._run", b"x", 0o644, "exp")], "macOS metadata")

    def test_owner_must_be_exp(self):
        self.assertError([("run", RUN, 0o755, "root")] + GOOD[1:], "must be exp:exp")

    def test_run_missing(self):
        self.assertError(GOOD[1:], "no 'run'")

    def test_run_not_executable(self):
        self.assertError([("run", RUN, 0o644, "exp")] + GOOD[1:], "not executable")

    def test_bash_shebang(self):
        self.assertError([("run", b"#!/bin/bash\necho hi\n", 0o755, "exp")] + GOOD[1:], "busybox sh only")

    def test_crlf(self):
        self.assertError([("run", b"#!/bin/sh\r\necho hi\r\n", 0o755, "exp")] + GOOD[1:], "CRLF")

    def test_x86_64_binary(self):
        self.assertError(GOOD[:1] + [("app", elf(machine=62, bits=2), 0o755, "exp")], "64-bit")

    def test_wrong_machine(self):
        self.assertError(GOOD[:1] + [("app", elf(machine=3), 0o755, "exp")], "not ARM")

    def test_parent_path(self):
        self.assertError(GOOD + [("../evil", b"x", 0o644, "exp")], "relative")

    def test_dynamic_binary_warns(self):
        rc, out = self.check(GOOD[:1] + [("app", elf(interp=b"/lib/ld-musl-armhf.so.1"), 0o755, "exp")])
        self.assertEqual(rc, 0, out)
        self.assertIn("dynamically linked", out)

    def test_soft_float_warns(self):
        rc, out = self.check(GOOD[:1] + [("app", elf(flags=0x05000200), 0o755, "exp")])
        self.assertEqual(rc, 0, out)
        self.assertIn("hard float", out)


if __name__ == "__main__":
    unittest.main()
