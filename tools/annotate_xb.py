"""annotate_xb.py ANNOTATIONS.json : add this survey's labels, RAM names and comments to Crossbow's
annotations (idempotent)."""
import json
import sys

LABELS = {
    "f8:FEA8": "Nmi", "f8:FEE2": "DliNext", "f8:FECB": "Dli_Bottom", "f8:FABC": "WaitFrame",
    "f8:FD2E": "AppendHeader", "f8:FCB2": "PlaceObject", "f8:FCED": "SaveListHeads", "f8:FCFC": "RestoreListHeads",
    "f8:FD0B": "ResetListHeads", "f8:FB78": "DrawRecordStream", "f8:FBF7": "DrawFillStream",
    "f8:F843": "LoadActorTemplate", "f8:F89B": "ActorStep", "f8:F8C4": "ActorScript", "f8:FDA8": "Random",
    "f8:FDBB": "PlaySound", "f8:E50A": "SelectSceneBank", "f8:E52B": "LoadScenePalettes", "f8:D772": "SceneDispatch",
    "f8:D78F": "Scene_Map", "f8:D9BE": "Scene_Desert", "f8:E370": "BoxOverlap", "f8:FA49": "FadePalettes",
    "f8:E8EA": "FriendStep", "f8:C000": "RowToZone", "f8:C010": "ListBases", "f8:D214": "SceneBank",
    "f8:C0EE": "SceneHandlers",
}
RAM = {
    "65": "DliVectorLo", "66": "DliVectorHi", "5E": "DliChainIndex", "48": "PlaceZone", "4B": "PlaceGfxLo",
    "4C": "PlaceGfxHi", "4F": "PlacePalWidth", "50": "PlaceX", "51": "PlaceY", "53": "PlaceRows",
    "8D": "ActorState", "AD": "ActorX", "CD": "ActorY", "2107": "Scene", "2120": "FrameDone",
    "2121": "FriendsLeft", "2200": "ActorRows", "2240": "ActorPalWidth", "2260": "ActorTimer",
    "2280": "ActorGfxLo", "22A0": "ActorGfxHi", "22C0": "ActorScriptLo", "22E0": "ActorScriptHi",
    "23C0": "ActorLoopCount", "24E0": "ListFill", "24F8": "ListFillSaved", "253C": "DliChainTable",
    "257A": "SceneVisits", "251A": "PaletteShadow",
}
COMMENTS = {
    "f8:FEA8": "NMI: WSYNC, then JMP ($65). Each handler ends in DliNext, which loads the next handler's address from a 9-entry RAM table ($253C, index $5E) -- a scene picks its band colours by poking that table. The last handler (Dli_Bottom) sets FrameDone for WaitFrame. No bank switch in any interrupt (live: runs/xb/xt1/banks.txt).",
    "f8:FD2E": "Append one 4-byte header [lo, palette/width, hi, x] to zone $48's list through that zone's fill pointer ($24E0,zone*2), then a zero terminator. 12 lists of 128 bytes at $1800-$1DFF. No cap test.",
    "f8:FCB2": "Place an object: zone = RowToZone[y >> 4], fine = y & 15; a misaligned object takes one more zone and starts fine pages lower; each further zone steps the high byte by $10. One column, one palette, one width for the whole figure (friends are 48 lines = 3 zones). No holey DMA: the art carries blank pages.",
    "f8:FCFC": "Start of a frame's drawing: the fill pointers go back to the values saved after the scene's fixed background was laid (SaveListHeads), so only the moving objects are redrawn.",
    "f8:F8C4": "Actor animation script: [frames to hold, gfx lo, dx, dy] per step (no dx/dy if $2360 bit 7). A zero hold is an escape: next byte / 2 selects sound, loop (count in $23C0, 16-bit target), set state, score popup, set loop count, move.",
    "f8:E50A": "The only bank switch: once when a scene is loaded, in vblank (raster 255, live). SceneBank = 0,3,2,4,3,6,1,5,4,2,0 for scenes 0-10 (file bank = value + 1).",
    "f8:D772": "Each scene is its own routine (table SceneHandlers): it draws the fixed background from record streams, then loops calling that scene's actor routines once a frame until no friend is left.",
}


def main():
    p = sys.argv[1]
    a = json.load(open(p))
    a.setdefault("labels", {}).update(LABELS)
    a.setdefault("ram", {}).update(RAM)
    a.setdefault("comments", {}).update(COMMENTS)
    json.dump(a, open(p, "w"), indent=2)
    print("labels %d ram %d comments %d" % (len(a["labels"]), len(a["ram"]), len(a["comments"])))


if __name__ == "__main__":
    main()
