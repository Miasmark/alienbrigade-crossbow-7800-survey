# Alien Brigade and Crossbow (Atari 7800): a survey

A study of *Alien Brigade* (`Alien Brigade (NTSC) (Joystick) (Atari) (1990) (C8849D36).a78`) with *Crossbow* (`Crossbow (NTSC) (Joystick) (Atari) (1988) (D2EA5686).a78`) read for comparison. Both are 144K: SuperGame banking plus 16K of ROM at `$4000`.

## How this was made, and how far to trust it

This is the output of **one automated research pass** on 2026-11-18: a single AI agent
session (Claude, working through the a7800-toolkit and MAME) given a list of questions and
about half an hour, not a long-running hand disassembly like
[galaga-7800-disassembly](https://github.com/Miasmark/galaga-7800-disassembly) and its
siblings. A second session then checked the report's main tables and routines against the
ROM's bytes; they matched. Nothing here was checked on a console.

Treat a **live** tag as "one agent saw this in MAME once", a **code** tag as a reading, and
the coverage figures below as what the tracer reached, not what was understood.

## Effort: one game in depth, one for comparison

One agent, about 28 minutes, 127 tool calls.

| Game | Depth | What was done |
|---|---|---|
| Alien Brigade | deep on three questions | the engine `f8:F000-FE9F` and level 1's bank read in full; large objects, the builder and scene scripts answered and confirmed live (16,465 list builds rebuilt byte-exact from the reading, on all five levels; one poke test on the random masks). Levels 2-5 skimmed; object records and the bank layout largely from code; sound and the light gun not read |
| Crossbow | comparison | the builder, the object step, the NMI and the scene loader read; the ten scene routines skimmed. All code is in the fixed bank (64.3% traced) |

Both listings rebuild byte for byte. Not determined: why Alien Brigade's bank 7 duplicates
bank 5; what it does on a zone's DMA overflow.

## What is here, and what is not

- `annotations.json`: entry points, labels, RAM names, data blocks and comments, in the
  [a7800-toolkit](https://github.com/Miasmark/a7800-toolkit)'s format.
- `docs/FINDINGS.md`: what the code does, with addresses, record formats and an evidence
  tag on every claim: **live** (watched in MAME: a tap, a trace, a RAM model, a poke that
  changed behaviour), **code** (read from the listing only), **hint** (a guess). Dead ends
  and corrections are kept in it.
- `tools/`: the probes and scripts the findings were made with.

**No ROM is here, and no listing.** A listing is the game's machine code in readable form;
it is rebuilt from `annotations.json` and your own legally owned dump with the toolkit's
`disasm.py`, and checked byte for byte with its `verify.py`. Captures, memory dumps,
renders of the graphics and traces are left out for the same reason.

## Running the tools

The scripts look for three things in the environment:

| Variable | What | Default |
|---|---|---|
| `A7800_ROMS` | the folder with your ROM dumps, named as below | `roms` |
| `A7800_TOOLKIT` | the a7800-toolkit's `tools` folder | `a7800-toolkit/tools` |
| `A7800_MAME` | a MAME with the Atari 7800 driver | `a78.exe` |

The live runs were made on [Miasmark/mame-Atari8bit7800](https://github.com/Miasmark/mame-Atari8bit7800),
windowless (`-video none -sound none -nothrottle`).

## Licence

MIT (see `LICENSE`) for the annotations, the findings and the tools. It does not cover the
games, which belong to their owners; nothing of theirs is distributed here.

## The session's own notes

A reading of two retail 144K carts (SuperGame banking plus 16K of ROM at `$4000`) for
techniques worth reusing: Alien Brigade (Atari, 1990) in depth, Crossbow (Atari, 1988) for
comparison. Made on 2026-11-18 with the a7800-toolkit and the MAME Atari fork.

**No ROM belongs in a published copy of this folder.** `roms/ab.a78` and `roms/xb.a78` are work
copies of the Joystick images, which the tools and runs need.

## Start here

- `docs/FINDINGS.md`: what each game does, with bank:addresses, record formats and evidence
  tags (live, code, hint), the dead ends and what was not determined.

## Layout

| | |
|---|---|
| `alienbrigade/annotations.json`, `crossbow/annotations.json` | entries, labels, RAM names, comments: the hand work |
| `alienbrigade/src`, `crossbow/src` | listings generated from the annotations; they rebuild byte for byte |
| `alienbrigade/code_*c.txt`, `crossbow/code_*c.txt` | the listings without their data rows (older, unlabelled names) |
| `*/bankpics` | each bank drawn as MARIA reads it in 16-line zones |
| `tools/` | the runner, the probes and the decoders (each file's header says what it does) |
| `runs/ab`, `runs/xb` | one folder per MAME run: logs, dumps, snapshots |

## Doing it again

Listings (toolkit at `Documents\Atari 7800\a7800-toolkit`):

    python tools/disasm.py roms/ab.a78 -c alienbrigade/annotations.json -o alienbrigade/src --cycles
    python tools/verify.py roms/ab.a78 -d alienbrigade/src

A run (this folder's `tools/run.py`; MAME is windowless, each run in its own folder):

    python tools/run.py ab NAME "SCRIPT=300:-:0;10:-:1;300:-:0;10:-:1;2000:l:1" SNAPS=1000,2000 DUMPS=2000 BANKS=1
    python tools/run.py ab NAME --lua tools/abmodel.lua "SCRIPT=..." "POKES=672:77=02"

- Alien Brigade needs two fire presses to start (frames 300 and 610 above); the level loads at
  frame 675. `POKES=672:77=0N` starts level N+1.
- `tools/abmodel.lua` checks the display-list builder model on every build and writes
  `model.txt`. `tools/abcheck.py ROM DUMP --list` prints a dump's draw list.
- `tools/abtypes.py roms/ab.a78 --type 11 --bank 1` decodes a type and its scripts.
- `tools/dll.py DUMP.bin` decodes the display lists in a RAM dump.
