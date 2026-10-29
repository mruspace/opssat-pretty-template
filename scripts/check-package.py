#!/usr/bin/env python3
"""check-package.py: check an OPS-SAT PRETTY experiment package before it goes to ESA.

    scripts/check-package.py PACKAGE.tar.gz
    scripts/check-package.py --binary FILE     check one binary only

Errors (exit 1) are things the runner or the SEPP will not accept; warnings
are things that have cost experimenters a round trip. It reads the archive
with Python's tarfile, which shows every entry: the macOS tar listing hides
the "._NAME" entries that macOS tar adds.

The SEPP runs 32-bit ARM Linux with hard float, musl libc and busybox. A
binary built for it must be static (no program interpreter) or link only
what the image has; a script must use /bin/sh, not bash or python.
"""
import stat
import struct
import sys
import tarfile

EM_ARM = 40
EF_ARM_ABI_FLOAT_HARD = 0x400
PT_INTERP = 3

errors, warnings = [], []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def check_elf(name, data):
    """Check an ELF file for the SEPP: 32-bit ARM, little-endian, static."""
    if data[:4] != b"\x7fELF":
        return False
    if data[4] != 1:
        err(f"{name}: 64-bit binary; the SEPP runs 32-bit ARM (armhf)")
        return True
    if data[5] != 1:
        err(f"{name}: big-endian binary; the SEPP is little-endian")
        return True
    e_machine, = struct.unpack_from("<H", data, 18)
    if e_machine != EM_ARM:
        err(f"{name}: built for machine {e_machine}, not ARM ({EM_ARM}); cross-compile for armhf")
        return True
    e_flags, = struct.unpack_from("<I", data, 36)
    if not e_flags & EF_ARM_ABI_FLOAT_HARD:
        warn(f"{name}: not marked hard float (soft float runs, but slower; armhf is the target)")
    e_phoff, = struct.unpack_from("<I", data, 28)
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 42)
    interp = None
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type, p_offset, _, _, p_filesz = struct.unpack_from("<IIIII", data, off)
        if p_type == PT_INTERP:
            interp = data[p_offset:p_offset + p_filesz].rstrip(b"\0").decode(errors="replace")
    if interp:
        warn(f"{name}: dynamically linked ({interp}); a static build needs nothing from the image")
    return True


def check_script(name, data):
    first = data.split(b"\n", 1)[0]
    if b"\r\n" in data[:4096]:
        err(f"{name}: Windows line endings (CRLF); the shell will fail on them")
    if first.startswith(b"#!"):
        shell = first[2:].strip().decode(errors="replace")
        if "bash" in shell or "python" in shell or "zsh" in shell:
            err(f"{name}: '#!{shell}': the SEPP image has busybox sh only, no bash or python")
    elif name == "run":
        err("run: no '#!' line; start it with #!/bin/sh")


def check_binary_file(path):
    with open(path, "rb") as f:
        data = f.read()
    if not check_elf(path, data):
        err(f"{path}: not an ELF binary")


def check_package(path):
    try:
        t = tarfile.open(path, "r:gz")
    except (tarfile.TarError, OSError) as e:
        err(f"{path}: not a gzip tar archive ({e})")
        return
    with t:
        members = t.getmembers()
        total = 0
        names = []
        for m in members:
            n = m.name
            names.append(n)
            print(f"  {stat.filemode(m.mode | (stat.S_IFDIR if m.isdir() else stat.S_IFREG))} "
                  f"{m.uname or m.uid}/{m.gname or m.gid} {m.size:>9} {n}")
            base = n.rsplit("/", 1)[-1]
            if n.startswith("/") or ".." in n.split("/"):
                err(f"{n}: absolute or parent path; all paths must be relative")
            if base.startswith("._") or base == ".DS_Store":
                err(f"{n}: macOS metadata; build with COPYFILE_DISABLE=1 (scripts/package.sh does)")
            elif base.startswith("."):
                warn(f"{n}: hidden file; the operators may not expect it")
            if m.uname != "exp" or m.gname != "exp":
                err(f"{n}: owned by {m.uname or m.uid}:{m.gname or m.gid}, must be exp:exp")
            if n.split("/")[0] == "toGround":
                warn(f"{n}: the package holds a toGround/ entry; outputs belong to the run, not the package")
            if m.issym() or m.islnk():
                warn(f"{n}: a link; prefer plain files")
            if not m.isfile():
                continue
            total += m.size
            data = t.extractfile(m).read()
            is_elf = check_elf(n, data)
            if not is_elf and (data[:2] == b"#!" or base == "run"):
                check_script(base, data)
            if base == "run" and "/" not in n:
                if not m.mode & 0o100:
                    err("run: not executable; the runner executes ./run")
        if "run" not in names and "./run" not in names:
            err("no 'run' at the top of the package; the runner executes ./run in $HOME")
        if not any(n.rsplit("/", 1)[-1].lower().startswith("readme") for n in names):
            warn("no README.txt; a short note for the operators saves questions")
        print(f"  {len(members)} entries, {total:,} bytes unpacked")


def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--binary":
        check_binary_file(args[1])
    elif len(args) == 1:
        check_package(args[0])
    else:
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"ok: no errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
