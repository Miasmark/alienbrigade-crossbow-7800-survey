"""run.py: one windowless MAME run of a cartridge with a Lua script, in its own folder.

usage: python run.py GAME RUNNAME [--lua tools/probe.lua] [KEY=VALUE ...]
  GAME      ab | xb          (roms/ab.a78, roms/xb.a78)
  RUNNAME   folder under runs/<GAME>/ (recreated)
  KEY=VALUE environment for the Lua script (SCRIPT, SNAPS, DUMPS, END, XT, REGS, BANKS, ...)

MAME is the user's fork, always -video none -sound none -nothrottle, with its own cfg, nvram and
snapshot directories and a ui.ini holding skip_warnings 1 (no window, no warning dialog).
"""
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAME = os.environ.get("A7800_MAME", "a78.exe")


def main():
    game, name = sys.argv[1:3]
    lua = os.path.join(HERE, "probe.lua")
    env = dict(os.environ)
    extra = []
    args = sys.argv[3:]
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--lua":
            lua = os.path.abspath(args[i + 1])
            i += 2
            continue
        if a == "--mame":
            extra += args[i + 1].split()
            i += 2
            continue
        k, v = a.split("=", 1)
        env[k] = v
        i += 1
    rd = os.path.join(ROOT, "runs", game, name)
    shutil.rmtree(rd, ignore_errors=True)
    os.makedirs(os.path.join(rd, "cfg"))
    open(os.path.join(rd, "ui.ini"), "w").write("skip_warnings 1\n")
    shutil.copy(os.path.join(ROOT, "roms", game + ".a78"), os.path.join(rd, "cart.a78"))
    cmd = [MAME, "a7800", "-cart", "cart.a78", "-bios", "skip", "-skip_gameinfo", "-video", "none",
           "-sound", "none", "-nothrottle", "-inipath", ".", "-cfg_directory", "cfg",
           "-nvram_directory", "nv", "-snapshot_directory", "snap", "-autoboot_script", lua] + extra
    with open(os.path.join(rd, "mame.out"), "w") as o:
        subprocess.run(cmd, cwd=rd, env=env, stdout=o, stderr=subprocess.STDOUT, timeout=3000)
    snaps = sorted(int(s) for s in env.get("SNAPS", "").replace(",", " ").split())
    files = sorted(glob.glob(os.path.join(rd, "snap", "a7800", "*.png")))
    for fpath, fr in zip(files, snaps):
        os.replace(fpath, os.path.join(rd, "snap", "f%05d.png" % fr))
    out = open(os.path.join(rd, "mame.out")).read().strip()
    print("run %s/%s: %d snaps%s" % (game, name, len(files), ("\n" + out[-800:]) if out else ""))


if __name__ == "__main__":
    main()
