# Project: marmoset_autolink — Toolbag auto texture linker

## Status
✅ Basic linking confirmed working in Toolbag 5 (2026-07-02).
🆕 v2 same day: packed maps (ORM/ARM/RMA/MRAO via "Channel" field) + UDIM grouping —
packed/UDIM paths not yet tested in-app. UDIM API switch is undocumented; script
introspects the Texture object and reports what it finds.

## Goal
One-click texture assignment in Marmoset Toolbag 4/5: pick a folder, script matches
files to scene materials by name + map suffix and fills the material slots.

## Files
- `autolink_textures.py` — the whole script (master copy; edit here).
- Installed copy: `C:\Users\atika\AppData\Local\Marmoset Toolbag 5\plugins\AutoLink Textures.py`
  — re-copy after edits, then Edit → Plugins → Refresh in Toolbag.

## Running (Toolbag 5)
Edit → Plugins → AutoLink Textures. Console output: Ctrl+~ or Help → Dev → Console.
(There is no "Run Script" menu — scripts run as plugins from the user plugin folder.)

## Matching rules
- File must contain a known map token (`_BaseColor`, `_Normal`, `_Roughness`, `_Metallic`,
  `_AO`, `_Emissive`, `_Height`, `_Opacity`, + aliases) — see `MAP_ALIASES` — or a packed
  token (`_ORM`, `_ARM`, `_RMA`, `_MRAO`) — see `PACKED_ALIASES`.
- When both appear, the token later in the filename wins (`Robot_Arm_BaseColor` → BaseColor,
  not ARM).
- Material = longest material name found inside the filename (handles the sp_exporter
  pattern `Mesh_TextureSet_BaseColor_sRGB.1001.png` and plain Painter exports).
- sRGB on only for BaseColor/Emissive; `_NormalDirectX` tries to set "Flip Y".
- Packed maps: same texture into 3 slots, `sub.setField("Channel", 0/1/2)` per slot.
- UDIM: `.1001`/`_1001` tiles grouped; lowest tile assigned once; script tries to find a
  UDIM attribute on `mset.Texture` via `dir()` and prints what it did.

## API facts (verified against official example
`D:\Program Files\Marmoset\Toolbag 5\data\plugin\Examples\Creating Materials from Images.py`)
- Shader models: Albedo, Normals, Roughness, Gloss, Metalness, Occlusion, Emissive,
  Height, Dither (transparency).
- Fields: "Albedo Map", "Normal Map" (+"Flip Y", "Object Space"), "Roughness Map",
  "Metalness Map", "Occlusion Map", "Alpha Map", **"Displacement Map"** (not "Height Map"),
  and **"Channel"** (int 0=R,1=G,2=B).
- `setField` accepts a plain path string or `mset.Texture`.
- RBM = user's in-house naming for *separate* maps (not packed) — intentionally not a token.

## Known limitations / next steps
- Non-recursive folder scan.
- UDIM API switch undocumented — first UDIM test will tell us the attribute name.
- Could grow a small `mset.UIWindow` UI (folder field + button) like the official example.
