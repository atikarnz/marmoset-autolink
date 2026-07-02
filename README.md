# AutoLink Textures — for Marmoset Toolbag 4 / 5

One-click texture assignment for Marmoset Toolbag. Pick a folder, and the script matches every texture file to the scene's materials by name, plugs each map into the correct material slot, and sets sRGB, normal-map flipping, and packed-map channels for you.

Works with typical Substance 3D Painter exports out of the box.

## What it handles

- **All the common maps:** Base Color / Albedo / Diffuse, Normal (OpenGL and DirectX), Roughness, Gloss, Metallic, AO, Emissive, Height / Displacement, Opacity / Alpha — plus many alias spellings (`_nrm`, `_rough`, `_metal`, ...).
- **Packed maps:** `_ORM`, `_ARM`, `_RMA`, `_MRAO` (and `OcclusionRoughnessMetallic`) are linked into all three slots with the right R/G/B channel set on each.
- **UDIM tile sets:** `name.1001.png` / `name_1001.png` tiles are grouped and linked once.
- **Correct color settings:** sRGB is enabled only for Base Color and Emissive; DirectX normals get "Flip Y" so they display correctly in Toolbag.

## Install

1. In Toolbag, go to **Edit → Plugins → Show User Plugin Folder**.
2. Copy `autolink_textures.py` into that folder (you can rename it, e.g. `AutoLink Textures.py` — the filename becomes the menu entry).
3. **Edit → Plugins → Refresh**.

## Usage

1. Open your scene with materials already created (e.g. imported with your mesh).
2. **Edit → Plugins → AutoLink Textures**.
3. Pick the folder that contains your exported textures.
4. Done. Open the console (**Ctrl+~** or **Help → Dev → Console**) to see a report of what was linked and what was skipped.

## How matching works

- A file is recognized when its name contains a known map token, e.g. `Robot_BaseColor.png` or `Helmet_Normal.1002.png`.
- The file is assigned to the material whose name appears in the filename. When several material names match, the **longest** one wins, so `Robot_Arm` beats `Robot` for `Robot_Arm_BaseColor.png`.
- When a filename contains more than one token, the one **later** in the name wins — `Robot_Arm_BaseColor.png` is treated as Base Color, not as an ARM packed map.
- Supported formats: PNG, TGA, TIF/TIFF, JPG/JPEG, EXR, PSD, BMP.

## Limitations

- The folder scan is non-recursive — point it at the folder that directly contains the textures.
- Materials must already exist in the scene; the script links textures, it doesn't create materials.
- The UDIM on-switch isn't documented in the `mset` API; the script auto-detects it on the Texture object and reports in the console what it did. If tiles beyond the first don't show, enable UDIM on the texture manually.
- Packed-map and UDIM paths are newer additions and less battle-tested than single-map linking.

## Compatibility

Written and tested against **Toolbag 5**; the shader/field names were verified against the official Toolbag example scripts and should also work in **Toolbag 4**.
