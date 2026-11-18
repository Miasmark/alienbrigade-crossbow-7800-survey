# Alien Brigade and Crossbow (Atari 7800): findings

Survey of 2026-11-18. Alien Brigade (Atari, 1990, programmed by Ken Grant) was read in depth;
Crossbow (Atari, 1988) was read for comparison. Both are 144K carts: SuperGame banking plus a
16K ROM at `$4000` (header type `$000A`).

Evidence tags: **(live)** watched in MAME (a list dump, a tap, a trace, a poke that changed
behaviour); **(code)** read from the disassembly only; **(hint)** a guess.

Addresses: `f0:` is file bank 0, fixed at `$4000-$7FFF`; `b1:`..`b7:` are file banks 1-7 in the
`$8000-$BFFF` window (a write of value *v* shows file bank *v*+1); `f8:` is file bank 8, fixed at
`$C000-$FFFF`. That is the toolkit's naming (`docs/cartridges.md`, "SuperGame", the `$0008`
layout). Both games fit it (live: every bank the traces saw executing or drawn from matches).

## What is in this folder

- `alienbrigade/annotations.json`, `crossbow/annotations.json`: entries, labels, RAM names and
  comments. `src/*.asm` are generated from them (toolkit `disasm.py`) and rebuild byte for byte
  (toolkit `verify.py`: ROUND-TRIP PASSED for both, 2026-11-18).
- `alienbrigade/code_*c.txt`, `crossbow/code_*c.txt`: the same listings with the data rows
  removed (made before the labels were added, so they show `sub_F56B`-style names).
- `alienbrigade/bankpics`, `crossbow/bankpics`: every bank drawn as MARIA reads it in 16-line
  zones. Art shows as pictures, code as noise.
- `tools/`: `run.py` + `probe.lua` (one windowless MAME run in its own folder: inputs by frame,
  snapshots, RAM dumps, exec trace, bank-switch log, register log, write watch, pokes),
  `abmodel.lua` (asserts the builder model on every build), `abcheck.py` (the same on a dump),
  `abtypes.py` (type table and script decoder), `dll.py` (display lists from a dump),
  `bankpic.py`, `xbcols.py`, `annotate_ab.py`, `annotate_xb.py`, `codeonly.py`.
- `runs/ab/*`, `runs/xb/*`: the runs behind every **(live)** tag below.
- `roms/ab.a78`, `roms/xb.a78`: work copies of the Joystick images. Not to be published.

### Coverage, stated honestly

| | traced as code | executed in my runs | notes |
|---|---|---|---|
| Alien Brigade f0 | 1,582 bytes (9.7%) | 478 instr. | the rest is tile art; all tail code reached |
| b1 (level 1) | 1,149 (7.0%) | 411 | read in full |
| b2-b5 (levels 2-5) | 1,187 / 2,155 / 2,152 / 837 | b3, b4 shared routines only | entered at their `$B000` jump tables; level code skimmed, not read |
| b6 (HUD, title, sound) | 2,142 (13.1%) | 746 | the NMI part and the start read; sound driver skimmed |
| b7 | none | never selected | byte-identical to b5 |
| f8 (engine) | 4,285 (26.2%) | 1,393 | `$F000-$FE9F` read in full; `$DD0F-$DF18` (light gun, switches) skimmed |
| Crossbow f8 | 10,540 (64.3%) | 2,691 | builder, object step, NMI, scene loader read; the ten scene routines skimmed |
| Crossbow f0 | 322 (2.0%) | none | light-gun code at `$4D00`, not read |
| Crossbow b1-b7 | none | none | art only |

The Alien Brigade trace ran level 1 only (6,009 frames, `runs/ab/xt1`). Levels 2-5 were started
by a poke and watched, not traced.

---

# Alien Brigade

## The 144K layout (question 5)

- **f0, `$4000-$7FFF`, fixed.** Tile sets of levels 2-5, one per 4K (`CHARBASE` `$40`, `$50`,
  `$60`, `$70`; live: `runs/ab/lvl1-4`, register `$34`). The tiles use only columns `$00-$9F` of
  each page (80 two-byte characters). **Every page's tail `$xxA0-$xxFF` holds code**: the NMI
  (`$60A0`), the DLI glue, the bank wrappers, the main tick (`$6FA0`), the spawn queue
  (`$46B0`), fades, controls, and a display list list in ROM at `$66A0` for the text screens.
  (code; the NMI's address is live.) This is the page-tail trick of Centipede, used here
  because holey DMA does not exist below `$8000`.
- **b1-b5: one bank per level** (window values 0-4; live: poking the level byte `$77` to 1-4
  started the river, underwater, mine and base levels with file banks 2-5 in,
  `runs/ab/lvl1-4/banks.txt`, `runs/ab/levels.png`). Each is laid out by 4K block:
  - `$8000-$8FFF`: art. Level 1: its tile set. Levels 2-5: sprite art.
  - `$9000-$9FFF`: object scripts (and in b3, b4, b5 some shared code or a font, below).
  - `$A000-$AFFF`: sprite art.
  - `$B000-$BBFF`: a jump table (`$B000` DLI chain start, `$B003` level tick), the scroll
    script at `$B010`, the level's DLI handlers, its spawner code, more scripts.
  - `$BC00-$BFE7`: the tile map, 10 rows of 100 bytes.
  - **Why this order:** the play zones are 16 lines with holey DMA (DLL bytes `$CF`/`$4F`), so
    MARIA reads the odd 4K blocks as zeros. Art sits in the even blocks, and code, scripts and
    maps fill the blind odd blocks. Code and art share the bank and never collide. (live for
    the DLL flags and the art addresses; code for the rest.)
  - **Shared scripts are duplicated per bank at the same addresses.** `$9000-$9CB3` (3,252
    bytes) is byte-identical in b1 and b2; `$9000-$97FF` in b4, `$9000-$97A7` in b5, and
    `$9000-$90EF` + `$9A00-$9CAF` in b3 (measured on the ROM). The type tables in f8 hold one
    pointer per type, so every level bank must carry the common types' scripts where the
    pointers say.
  - **Extras tucked into level banks:** b3 `$9800-$9FFF` is the level-start code
    (`b3:9E74`: copies 1,320 bytes of list templates from `b3:9809` to RAM `$1990`, sets the
    difficulty bytes) and b3 `$B006-$B00E` three more entries; b4 `$9800-$9809` four entries
    used at boot, on the title and between levels (hint: title and intermission screens); b5
    `$9800` a text font (`CHARBASE $98`, live on the title).
- **b6 (window value 5): HUD, title, sound.** Code at `$8000-$8FFF` (options, HUD upkeep, BCD
  score, the sound driver at `$873B`) and `$B800+`; title art; HUD characters at `$B000`
  (`CHARBASE $B0`). (code; live that it is in while the HUD is drawn.)
- **b7 (window value 6): a byte-identical copy of b5.** No run ever selected it. Its purpose
  is not determined.
- **f8, `$C000-$FFFF`, fixed.** `$C000-$CFFF` and `$E000-$EFFF`: sprite art common to all
  levels (soldiers, shots, explosions, the cursor). `$D000-$DCFF`: the type tables. `$DD00-$DF18`
  and `$F000-$FE9F`: the engine, 4.3K of code. Same even/odd split as the level banks.
- **No graphics packing.** Art is raw line-planar 160A, 16 pages to a block.
- **Bank switches in play: exactly two a frame, both inside the NMI** (live: 5,213 frames,
  5,213 writes at `f0:60C4` on raster 16 selecting b6 and 5,213 at `f0:60DE` on raster 81
  selecting the level bank; `runs/ab/xt1/banks.txt`). None per object, none from the main
  program. Other switches happen only at boot, on the title and at level load.

Total code traced: about 15.5K of the 144K. The rest is art, scripts, tables and maps.

## Frame architecture (question 6)

- **A DLI chain through `JMP ($DD)`** (`f0:60A7`). Each handler stores the next one's address.
  Targets seen live: `f0:60B6` (top), `f0:61CA` (the HUD's foot), seven in the level bank
  (`b1:B604`-`B68B`), and `f0:62A0`/`f0:60AA` on the title.
- **The top DLI holds the CPU for the whole HUD.** `Dli_HudTop` (`f0:60B6`, raster 16) pages
  in b6, sets `CHARBASE $B0` and `CTRL $40`, calls `b6:8003` (uploads seven palettes from
  shadows `$2200-$2214`, counts ammo and score, redraws the HUD parts whose dirty bits are set
  in `$76`), then **spins inside the NMI** at `f0:60D2` until `$FE` is set. `$FE` is set by a
  nested NMI: the DLI at the HUD's foot (`f0:61CA`). Then it sets `CTRL $50`, pages the level
  bank back, restores `CHARBASE` from `$FF` and jumps to the level bank's `$B000`, which arms
  the level's own chain and uploads the playfield's eight palettes from shadows `$221B-$2231`.
  This is Midnight Mutants' "nested DLI as a raster timer" (`bankset` skill, "SuperGame
  contrast"). The main program gets nothing from raster 16 to 81: 65 of 263 lines. (live for
  the rasters; code for the rest.)
- **Level DLIs recolour P0 and P1 by band.** The tile rows alternate palettes 0 and 1 (the
  row's palette byte comes from `$2262,row`), and DLIs on the zone boundaries rewrite P0C1-3
  or P1C1-3 from RAM shadows (`b1:B616`-`B671`; live: rasters 121, 137, 153, 169, 201 in
  `runs/ab/xt1/regs.txt`). That is the ping-pong palette recipe already in
  `7800-maria-display-recipes`. In MAME some of these writes land up to 6 lines late in heavy
  frames (same file); not investigated.
- **Double-buffered lists, flipped by the bottom DLI.** Two DLLs (`$1A34`, `$1A76`) share the
  HUD's lists (`$1990-$1A33`) and each owns a 512-byte block for the ten play zones (`$1AB8`,
  `$1CB8`). The builder sets `$F3` when a set is finished; the last DLI (`b1:B68B`, raster
  249) writes DPPL/DPPH and toggles `$F2` only if `$F3` is set. The builder waits for `$F3`
  to clear before it starts the next set. (live: both DLL addresses seen in register dumps.)
- **Pacing: a RIOT timer gate and the flip wait.** The main loop (`f8:DE4B` to `f0:6FA0`) runs
  a tick when `INTIM` has fallen below `$2102` (`$FE`; `T1024T` is reloaded with `$FF` each
  tick). A tick is: the level's tick routine, the scroll every `$2104` (7) ticks, the player,
  the object scripts every `$2103` (2) ticks, the list build. Because the build waits for the
  flip, a tick cannot run more than once a frame. **Nothing makes up for a slow tick:** the
  game simply slows. Measured on level 1 (live, `runs/ab/tick`): 53.6 flips a second over
  3,721 frames, 59 with about 23 draw-list entries, 40 with about 37.
- **Fades** step every palette shadow's luminance toward a target (`f0:42B0`, `f0:43B0`), as
  the skill's "fades on brightness nibbles".

## Large objects from pieces (question 1)

**A figure is one to three "cells" stacked downward. Each cell is one display-list object of
at most 16 lines, with its own width, palette and x offset. Each cell is drawn by one or two
slots: one in the zone its top falls in, one in the zone below.**

- **The type table** (f8, indexed by a type id 0-255; 13 bytes a type, 3.3K in all):
  - `$D000,T`: bits 0-1 cells - 1; bit 2 "one zone is enough"; bit 3 "one zone is enough when
    y is on the 16-line grid"; bits 4-7 the draw class.
  - `$D700+2T`, `$D900+2T`, `$DB00+2T`: the script of cell 0, 1, 2 (high byte 0: no cell).
  - `$D200,T`: hit points (`$FF` cannot be hit). `$D100,T`: low nibble the hit box's width in
    4-pixel units, high nibble the speed its death type starts with. `$D500,T`: the type it
    becomes when killed. `$D300,T`, `$D400,T`: that type's offset. `$D600,T`: a further type to
    spawn (a chain).
  - Of the 256 ids, 123 have one cell, 79 two, 54 three (the table; not every id is used in
    every level).
- **A frame record** is five bytes in a cell's script:
  `[palette<<5 | (32-width), gfx low, gfx high, dx, dy]`. The first three are a display-list
  header's bytes 1, 0 and 2 as they stand. dx and dy are applied when the frame is left.
- **A slot** (110 of them, struct of arrays): `$2381`/`$23EF` script pointer, `$24CB` script
  offset, `$2615` x, `$25A7` y, `$245D` flags (bit 7 in use; low bits `$00` upper zone, `$10`
  lower zone), `$26F1` the cell's x offset, `$2539` loop count, `$2683` speed, `$275F` hit
  points (only the first slot of an object has them: it is the "primary").
- **Spawning** (`SpawnObject`, `f8:F687`): for each cell, a slot with flags `$80` at (x, y) in
  the row of y, then unless the zone flags say otherwise a slot with flags `$90` at (x, y+16)
  in the row below; y then steps 16 for the next cell. So a three-cell figure off the grid is
  six slots and six list entries; on the grid, with bit 3 set, three.
- **Vertical position by holey DMA, with no clipping code.** The header's high byte is
  `base + (y & 15) - (flags & $7F)`. The upper slot reads up into the next 4K block, the lower
  slot (minus `$10`) down into the previous one, and both neighbours are odd blocks that the
  holey zones read as zeros. This is the skills' "per-pixel Y by writing an object into two
  zones", with the twist that the lower half is a separate slot rather than a second write.
- **Cells animate in lockstep, each from its own script.** Every slot runs its own copy of the
  figure's script: the same control flow, the same dx/dy, different graphics. Commands with
  side effects (spawn, hurt, sound) act only in the primary slot. The price is script bytes:
  type `$11`'s two cells carry two near-identical streams.
- **Sharing.** A script can be shared between types (types `$08`/`$09`; type `$1F` uses type
  `$1E`'s cells 1 and 2). A missing part is a one-byte object at a blank byte (`$E087`).
  Facing left and right are separate art; nothing is mirrored (MARIA cannot). There are no
  deltas. A per-cell x offset (command `$0A`) lets a narrow part sit off the figure's left
  edge, so each cell is only as wide as its own part.
- **Things bigger than 48 lines are not objects.** The hut, the tank and the fences are
  characters in the scrolling tile map, and a state change rewrites a few map cells
  (`b1:B6FC` stores four cells at `$186C`/`$1894`). A taller creature is a parent that spawns
  a child below itself (type `$2D` spawns type `$38` at +10,+32) and removes it with
  command `$09`. (code; the tile map is live.)
- **Everything is 160A.** Lists hold 4-byte headers only, apart from each zone's tile row.

Evidence: the slot and frame formats are **live**. `tools/abmodel.lua` rebuilt the lists from
the draw list, the slot arrays and the scripts at the moment each build finished, on all five
levels: 16,465 builds, 16,465 byte-exact, none differing (`runs/ab/model0-4/model.txt`). The
type table columns other than `$D000` and the script pointers are **(code)**.

## The display-list builder (question 2)

**The game keeps a draw list that is always in drawing order. The builder is one pass that
copies it out. All ordering work is done when an object is inserted.**

- **The draw list**: two parallel arrays, `$227D` (type) and `$22FF` (slot), up to `$82` = 130
  entries, count in `$2114`. It is grouped by zone: `$FF` ends a zone's entries, ten times.
  `$FE` stands for the zone's tile row.
- **The builder** (`BuildDisplayLists`, `f8:F56B`): walks the list once and writes the ten
  lists back to back in the hidden 512-byte block.
  - a slot entry: `[script[offset+1], script[offset+0], script[offset+2] + (y & 15) - zone
    bits, x]`. An entry whose y is `$A0` or more, or whose script byte is a command, is skipped.
  - `$FE`: a 5-byte indirect header for the tile row (map pointer from `$224E`/`$2258`,
    palette and width from `$2262`, x = `$FF` minus the fine scroll).
  - `$FF`: two zero bytes, then the next zone's DLL entry is pointed just past them.
  - About 166 CPU cycles a slot entry (summed from the listing, an estimate). No zone lookup,
    no sort, no multiply.
- **Draw order = the list's order within a zone**, set by `DrawListInsert` (`f8:F8C2`): skip
  to the zone's bucket, then insert before the first entry of a higher class, or of the same
  class and a larger y. So within a zone: class ascending, then y ascending (lower on the
  screen is in front).
- **The tile row has a class too** (`f0:64B4`: 2 for rows 0-7, 13 for rows 8-9). Objects of
  class 3-12 in the bottom two rows are therefore entered before the tile row and drawn
  behind it: soldiers walk behind the foreground wall with no masking. Shots and the cursor
  are class 14-15 and stay in front. (live: `tools/abcheck.py --list` on
  `runs/ab/xt1/dump_f02400.bin` shows the tile-row marker after three class-10 entries in
  rows 8 and 9, and the lists agree.)
- **Moving between zones.** When a script step changes y's row, the object is removed
  (`RemoveObject`, `f8:F99F`, which finds it by type and position and closes the gap) and
  queued for respawn at its new place with its script offset, loop count and speed. The queue
  (`$1EB8-$1F6B`, six arrays of 30, count `$211B`) is run after the update loop
  (`RunSpawnQueue`, `f0:46B0`). Insertion and removal shift the arrays one entry at a time.
- **What bounds it.** Only totals: 130 list entries (20 are markers, so 110 objects' worth),
  110 slots, 30 queued spawns. 110 four-byte headers, ten tile-row headers and ten
  terminators are 510 bytes: the 512-byte block was sized to the cap. A spawn past a cap is
  dropped silently. **There is no cap per zone and no DMA accounting.** (code.) Seen live:
  at most 53 entries and 194 list bytes.
- **What keeps it affordable** is design, not code:
  - walkers stand on the 16-line grid and their types carry the "one zone on the grid" bit,
    so they cost one header a cell;
  - each cell is only as wide as its part;
  - the tile row is one header a zone however much scenery it shows.
  The tile row itself is expensive: 31 two-byte characters a line.

## Scenes as scripts (question 3)

There are three layers, and only the first is a table.

1. **The scroll script** (`ScrollScriptStep`, `f8:F3FE`; table at the level bank's `$B010`).
   One byte per segment of 80 scroll ticks (80 pixels): `$00` stand still (then 40 ticks),
   `$01` scroll right, `$FF` scroll left, `$10` start (sets a flag, then moves), `$20` hold
   here until event counter 3 (`$226F`) is zero, `$80` the end (finishes the level if event
   counter 15 is set). Level 1: `00 00 10 01 01 01 01 01 FF FF 01 01 01 01 80`.
   - Live on level 1 (`runs/ab/tick`): the index stepped at scroll positions 0, 20, 40, 60, 80,
     99 and the step byte matched the table each time.
   - The map is a ring of 100 columns, copied into a 40-column RAM map 20 columns at a time
     (`f0:6EA0`, `f8:F4F0`). **Left steps walk back over ground already seen**, so the level
     lasts longer than its map. Objects are shifted with the ground (`ScrollObjects`,
     `f0:6BA0`).
2. **The level's tick routine** (level bank `$B003`; level 1: `b1:B6BF`). Hand-written code,
   different in every level bank. Two shapes:
   - **Timers with random picks**: five or seven countdown bytes (`$2122-$2126`), each
     reloading and choosing a spawn routine with the random generator, gated on windows of the
     scroll position `$2100` (`CMP #$05`, `CMP #$4A`...). A spawn routine sets x (`$F0` just
     off the left, `$9D` the right edge), y (a lane, sometimes random), the type, and a speed.
   - **Set pieces at exact positions**: a chain of compares of `$2100` against constants with
     a "done this one" latch in `$2128` (`b2:B6EE`: `$1A`, `$58`, `$7E`, `$86`, `$8E`, `$96`,
     `$97`, `$9F`), each spawning a named type. `$9F` is the map's end, where each level runs
     its boss.
   (code; the counts per bank are in the listings: 10-17 random calls, 24-51 spawn loads.)
3. **The objects' own scripts** (next section), which do the moving, shooting and dying, and
   talk back through **sixteen event counters** `$226C-$227B`: script commands raise and clear
   them, the scroll script and the level code read them.

**Difficulty** (`b3:9E74`; code, with one poke test):
- The skill chosen on the title (`$75`, 0-3) picks random mask 4 (`$2131`) from a table and
  takes 1 off the four spawn speeds `$2135-$2138` at skill 3. Level 5 forces the mask to 7.
- Scripts branch on `random AND mask[i]` (command `$0B`); masks 0-3 are fixed (0, 1, 3, 7).
- Level code picks a tougher variant when `random AND $212F` is zero.
- The hit box's slop (`$1F6C-$1F6F`) differs for stick and light gun.
- **Poke test (live):** with `$2131` poked to `$00`, `$03` (as set) and `$FF` from frame 900,
  the same 7,080-frame input queued the pickup type `$19` 13, 2 and 0 times
  (`runs/ab/drop00`, `drop03`, `dropFF`, `counts.txt`, PC `f8:FC8D`): the script line
  `randskip mask[4]` in front of `become type $19` behaves as read.

## Object records and behaviour (question 4)

- **One script format is animation and behaviour.** The interpreter (`UpdateObjects`,
  `f8:FA44`; `ScriptStep`, `f8:FBFE`) runs one step per slot when the slot's speed divider
  fires (`$2683`: low nibble the period in object ticks, high nibble the count). A step is
  either a frame record (leave it: add its dx, dy; show the next) or commands until the next
  frame record:

  | byte | operands | meaning |
  |---|---|---|
  | `$00`, `$01` | | skip. Two `$01` in a row mark a loop start |
  | `$02` | | jump back to the last mark (or the start) |
  | `$03` | n | count a pass; jump back to the mark until n passes are done |
  | `$04` | | restart the script |
  | `$05` | k, v | k 0: hurt the player by v; 1: sound v; 2: a blast at this place; 3: add v to a score counter (primary slot only) |
  | `$06` | n | set the loop count |
  | `$07` / `$08` | n | raise / clear event counter n (`$0C`: health up, `$0D`: grenades, `$0F`: a scroll delay) |
  | `$09` | t | remove every object of type t |
  | `$0A` | d | this cell's x offset |
  | `$0B` | i, n | skip n bytes if `random AND mask[i]` is not zero |
  | `$0C` | t, dx, dy, s | spawn type t at an offset with speed s (0: mine) |
  | `$0D` | t, dx, dy, s | become type t: queue it and remove myself |
  | `$0E`, `$0F` | | remove myself |

  Scripts are at most 256 bytes a cell (one-byte offset). State changes (walk, aim, fire,
  duck, die) are `become` jumps between types.
  - Evidence: the frame records and the offset arithmetic are **live** (the builder model).
    The exec trace ran every command's branch except `$07`, `$08` and `$05` k=2/3
    (`runs/ab/xt1`). `$0B` and `$0D` passed the poke test above. The rest is **(code)**.
- **Off-screen:** a step that takes a primary slot's x into `$A0-$D9` or y into `$A0-$CF`
  removes the object.
- **The hit test** (`HitTest`, `f8:F24A`): for each draw-list entry whose type has a death
  type and whose slot has hit points, a box of `width nibble * 4` pixels by `cells * 16`
  lines, widened by the four slop bytes. Damage is 1 for the first weapon, 8 for the others,
  16 times the grenade's size for a blast. At zero the object is removed and its death type
  spawned at the table's offset, then the `$D600` chain (several pieces of debris). Otherwise
  a "hit" sound. (code; the hit-point writes at `f8:F396` were seen live.)
- **Hit points** are 1-3 for troops and `$1E`-`$36` for bosses (`$D200`).
- **The player's shots** are objects too (types 1-4, class 15); the cursor is type 0, slot 0.

## RAM, for scale

Slots 10 arrays of 110 = 1,100 bytes. Draw list 260. Spawn queue 180. Two list blocks 1,024.
Two DLLs and the HUD lists about 300. The RAM tile map 400. About 3.3K of the 4K at
`$1800-$27FF`.

---

# Crossbow

## Layout and frame

- **All the code is in f8** (10.5K, 64% of the bank) plus a little in f0 (`$4D00`, the light
  gun). **b1-b7 are art only**, one or two scenes each. (live: every one of 2,691 executed
  instructions is in f8; `runs/xb/xt1/exectrace.log`.)
- **One bank switch per scene, in vblank** (`SelectSceneBank`, `f8:E50A`, table `f8:D214` =
  0,3,2,4,3,6,1,5,4,2,0 for scenes 0-10; live: 8 writes in 7,420 frames, all on raster 255-256;
  the map screen has file bank 1 in, the desert 5, the town 3). No switch in play, none in an
  interrupt.
- **f0, `$4000-$7FFF`**: sound scripts (pointer table at `$4000`), scene palettes (`$4F00`),
  then art common to every scene: the friends' walk frames as 48-line columns, digits and
  messages as bitmaps.
- **A scene bank** holds the scene's background as 20-byte strips (80 pixels) in columns
  `$00-$9F` of pages `$80-$9F`, and its sprites in the columns beside it (`$A0-$FF`) and in
  `$A000-$BFFF`. A third to a half of those sprite columns are the same bytes in every scene
  bank (measured against bank 5: 30-56% of pages `$80-$9F`, columns `$A0+`; `tools/xbcols.py`):
  **common sprites are copied into each scene's bank**.
- **No holey DMA** (DLL bytes `$8F`/`$0F`). Art carries its own blank pages.
- **12 zones of 16 lines, one list each, 128 bytes apart** (`$1800-$1DFF`, table `f8:C010`).
  A single buffer: the main loop waits for the bottom DLI (`WaitFrame`, `f8:FABC`), then
  rewrites the lists.
- **Fixed head, rebuilt tail.** A scene lays its background into the lists once
  (`DrawRecordStream`, `f8:FB78`: records `[zone | block high nibble, gfx low, palette/width,
  x]`, `$FF` ends), saves each list's fill pointer (`f8:FCED`), and each frame restores them
  (`f8:FCFC`) before the moving objects are appended (`AppendHeader`, `f8:FD2E`). No cap
  test. This is the skill's "static head plus dynamic tail".
- **A figure is one column.** `PlaceObject` (`f8:FCB2`): rows (16-line cells), one low byte,
  one palette and width for the whole figure; zone from `y >> 4` through a table; one more
  zone when y is off the grid; the high byte steps `$10` a zone. The friends are 3 rows. (live:
  `$92DB`, `$82DB`, `$72DB` in three zones, `runs/xb/xt1/dump_f02400.bin`.)
- **DLI chain from a RAM table** (`f8:FEA8`): `JMP ($65)`, and every handler ends by loading
  the next address from a 9-entry table at `$253C`. A scene sets its band colours (three
  BACKGRND values) by poking the table.
- **Fades**: every palette shadow's luminance minus a fade level, clamped (`f8:FA49`).

## Objects and scenes

- **32 slots, struct of arrays 32 apart** (`$2200`..`$23C0`, plus `$8D` state, `$AD` x, `$CD`
  y), with **slots reserved by role**: 0-1 the friends, 2 the shot, the rest per scene.
- **A 13-byte spawn template** copied in one loop (`f8:F843`): rows, palette/width, x, y,
  state, timer, gfx low and high, script pointer, flags.
- **An animation script per actor** (`f8:F8C4`): `[frames to hold, gfx low, dx, dy]` per step.
  The high byte never changes, so a figure's frames sit side by side in one block. A zero
  hold escapes to a command: sound, loop with a count and a 16-bit target, set the state
  byte, score popup, set the loop count, move.
- **Each scene is its own routine** (table `f8:C0EE`, ten handlers `$D78F`-`$DF5E`): draw the
  background, then loop once a frame calling that scene's actor routines in a fixed order
  until no friend is left. Events are those routines' timers and random numbers. There is no
  scene table. (code; three handlers ran in the trace.)
- **Difficulty**: a visit count per scene (`$257A`) halves the actors' start delays on each
  return (`f8:F802`). (code.)
- **Hits**: a generic box overlap between two slots (`f8:E370`); one hit kills. Anything
  touching a friend kills the friend.

## Which Alien Brigade findings hold in Crossbow

| | Alien Brigade | Crossbow |
|---|---|---|
| art and code per bank | a level's art, scripts, code and map in one bank; code in the holey blocks | scene banks are art only; all code fixed |
| bank switches | 2 a frame, inside the NMI | 1 a scene, in vblank |
| common art | fixed bank | copied into every scene bank |
| lists | double buffer, packed back to back, rebuilt whole | single buffer, 128 bytes a zone, fixed head + tail |
| draw order | class, then y, kept sorted in a draw list | the order the scene's routines run in |
| vertical placing | holey DMA, two slots a cell | blank pages in the art, one column |
| a figure | 1-3 cells, each its own width, palette, x offset | one column, one width, one palette |
| scripts | frames + 14 commands; spawn, become, random, counters | frames + 6 commands |
| scene sequencing | scroll table + level code + event counters | scene code only |
| background | scrolling tile map, one header a zone | fixed bitmap strips, two headers a zone |
| pacing | RIOT gate + flip wait; slows under load | one frame a pass |

---

# Dead ends and corrections

- **Poking the level byte on the title** (`$77` at frame 250) hung the title, which uses the
  byte itself. Poking it at frame 672, between the second fire press (frame 610) and the
  level load (frame 675), works.
- **The first level-select runs never left the title**: the title needs two fire presses.
- **My first play script never hit an enemy** (the hit path `f8:F37C` did not run in
  `runs/ab/xt1`): the cursor had wandered to the bottom wall. Sweeping left and right at the
  start height hits. The poke test used that.
- **`abcheck.py` on end-of-frame dumps** matched only when nothing had moved since the last
  build (74/74, 86/86, 122/122...) and otherwise showed false differences. The assertion was
  moved to the builder's last store (`abmodel.lua`): 100%.
- **`abtypes.py` runs past a script's end**: scripts carry no length, so a decode continues
  into the next script. A type's listing is good up to its first unconditional end; counts
  taken over the whole table are not, and none are quoted here.
- **The exec trace added nothing the tracer had not found.** With the vectors, the `$DD/$DE`
  vector pair and the jump tables at `$B000`/`$9800` declared, the static tracer reaches every
  one of the 3,622 instructions that ran. (The read tap does see fetches on the fork.)
- **A shell heredoc mangled `\n`** in a Lua patch; fixed by hand. Scripts here are written
  with the Write tool.
- **The listing's labels can name the wrong bank** for a call made through the window:
  `JSR sub3_9800` at `f0:6DAA` runs with file bank 4 in. The trace's bank is the one to trust.
- **Crossbow's off-grid arithmetic** in `f8:FCB2` (`hi - fine`, an extra zone) was not worked
  through against the art's padding. The three-zone friend is live; where the blank pages sit
  is not determined.

# Not determined

- Why b7 duplicates b5, and whether window values 6 and 7 are ever written (not in any run).
- What Alien Brigade does when a zone overflows MARIA's time: no code handles it; not
  provoked.
- Whether objects with art in `$8000-$8FFF` (levels 2-5) are ever drawn off the grid: their
  lower half would read `$7000-$7FFF`, which is tile art and not a hole. (hint: such types are
  kept to one zone.)
- Alien Brigade's levels 2-5 code beyond its shape, b4's `$9800` routines, the sound driver,
  the light-gun reader.
- Crossbow's ten scene routines in detail, its f0 code, the scenes each bank holds beyond the
  three seen.
- The late DLI colour writes in MAME (up to 6 lines) in heavy Alien Brigade frames.
