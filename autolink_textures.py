# Marmoset Toolbag (4/5) — Auto-link textures to materials
#
# How it works:
#   1. Asks for a texture folder.
#   2. For every material in the scene, finds texture files whose name contains
#      the material name plus a known map suffix (_BaseColor, _Normal, ...).
#   3. Plugs each map into the right material slot with correct sRGB settings.
#   4. Packed maps (_ORM, _ARM, _RMA, _MRAO) are linked to all three slots with
#      the right Channel (R/G/B) set on each.
#   5. UDIM tile sets (name.1001.png / name_1001.png) are grouped and linked once.
#
# Install: copy into the user plugin folder (Edit -> Plugins -> Show User Plugin Folder),
# then Edit -> Plugins -> Refresh. Run via Edit -> Plugins -> AutoLink Textures.
# Console for output: Ctrl+~ or Help -> Dev -> Console.
#
# Field/shader names verified against the official Toolbag 5 example
# "Creating Materials from Images.py" (data\plugin\Examples).

import os
import re

import mset

# ---------------------------------------------------------------------------
# Single-map aliases -> slot. Keys are lowercase tokens found in the filename.
# ---------------------------------------------------------------------------
MAP_ALIASES = {
    "basecolor":        "albedo",
    "base_color":       "albedo",
    "albedo":           "albedo",
    "diffuse":          "albedo",
    "color":            "albedo",

    "normal":           "normal",
    "normals":          "normal",
    "normaldirectx":    "normal_dx",
    "normal_directx":   "normal_dx",
    "normalopengl":     "normal",
    "normal_opengl":    "normal",
    "nrm":              "normal",

    "roughness":        "roughness",
    "rough":            "roughness",
    "glossiness":       "gloss",
    "gloss":            "gloss",

    "metallic":         "metalness",
    "metalness":        "metalness",
    "metal":            "metalness",

    "ambientocclusion": "occlusion",
    "ambient_occlusion":"occlusion",
    "mixedao":          "occlusion",
    "occlusion":        "occlusion",
    "ao":               "occlusion",

    "emissive":         "emissive",
    "emission":         "emissive",
    "emit":             "emissive",

    "height":           "displacement",
    "displacement":     "displacement",
    "disp":             "displacement",

    "opacity":          "opacity",
    "alpha":            "opacity",
}

# ---------------------------------------------------------------------------
# Packed-map aliases -> ordered slots for channels R, G, B.
# ---------------------------------------------------------------------------
PACKED_ALIASES = {
    "orm":  ("occlusion", "roughness", "metalness"),
    "arm":  ("occlusion", "roughness", "metalness"),
    "rma":  ("roughness", "metalness", "occlusion"),
    "mrao": ("metalness", "roughness", "occlusion"),
    "occlusionroughnessmetallic": ("occlusion", "roughness", "metalness"),
}

# slot -> (subroutine slot, shader model to set, texture field name, is_srgb)
# Shader/field names from the official TB5 example scripts.
SLOT_CONFIG = {
    "albedo":       ("albedo",        "Albedo",    "Albedo Map",       True),
    "normal":       ("surface",       "Normals",   "Normal Map",       False),
    "normal_dx":    ("surface",       "Normals",   "Normal Map",       False),
    "roughness":    ("microsurface",  "Roughness", "Roughness Map",    False),
    "gloss":        ("microsurface",  "Gloss",     "Gloss Map",        False),
    "metalness":    ("reflectivity",  "Metalness", "Metalness Map",    False),
    "occlusion":    ("occlusion",     "Occlusion", "Occlusion Map",    False),
    "emissive":     ("emissive",      "Emissive",  "Emissive Map",     True),
    "displacement": ("displacement",  "Height",    "Displacement Map", False),
    "opacity":      ("transparency",  "Dither",    "Alpha Map",        False),
}

TEXTURE_EXTS = (".png", ".tga", ".tif", ".tiff", ".jpg", ".jpeg", ".exr", ".psd", ".bmp")

# Trailing .1001 or _1001 on the stem. Restricted to 1xxx (UDIM tiles start at
# 1001) so resolution suffixes like _2048 / _4096 are not mistaken for tiles.
UDIM_RE = re.compile(r"[\._](1\d{3})$")


def find_map_token(stem):
    """Return ('single'|'packed', value) for the LAST alias in the stem,
    or (None, None) if no alias is found.

    The last match wins so 'Robot_Arm_BaseColor' resolves to BaseColor
    and not the ARM packed alias.
    """
    tokens = re.split(r"[_\.\-\s]+", stem.lower())
    best = None
    for i, tok in enumerate(tokens):
        joined = tokens[i - 1] + "_" + tok if i > 0 else None
        if tok in MAP_ALIASES:
            best = ("single", MAP_ALIASES[tok], i)
        elif joined in MAP_ALIASES:
            best = ("single", MAP_ALIASES[joined], i)
        elif tok in PACKED_ALIASES:
            best = ("packed", PACKED_ALIASES[tok], i)
    if best is None:
        return None, None
    return best[0], best[1]


def collect_textures(folder):
    """Scan folder (non-recursive) -> list of (path, stem_lower, kind, value, tiles).

    UDIM tile sets are grouped: one entry per set, path = lowest tile,
    tiles = number of tiles found.
    """
    groups = {}  # base stem lower -> {"paths": {tile: path}, "kind":..., "value":...}
    for name in sorted(os.listdir(folder)):
        base, ext = os.path.splitext(name)
        if ext.lower() not in TEXTURE_EXTS:
            continue
        m = UDIM_RE.search(base)
        tile = int(m.group(1)) if m else 0
        stem = UDIM_RE.sub("", base)
        kind, value = find_map_token(stem)
        if not kind:
            continue
        g = groups.setdefault(stem.lower(), {"paths": {}, "kind": kind, "value": value})
        g["paths"][tile] = os.path.join(folder, name)

    found = []
    for stem, g in sorted(groups.items()):
        first_tile = min(g["paths"])
        found.append((g["paths"][first_tile], stem, g["kind"], g["value"], len(g["paths"])))
    return found


def best_material_for(stem, materials):
    """Longest material name that appears in the filename stem wins.

    `materials` is a list of (lowercase_name, material) pairs.
    """
    best_name, best_mat = "", None
    for name, mat in materials:
        if name in stem and len(name) > len(best_name):
            best_name, best_mat = name, mat
    return best_mat


def make_texture(path, is_srgb, tiles):
    tex = mset.Texture(path)
    try:
        tex.sRGB = is_srgb
    except Exception:
        pass
    if tiles > 1:
        # Look for a UDIM switch on the texture object (API name not documented).
        udim_attrs = [a for a in dir(tex) if "udim" in a.lower()]
        if udim_attrs:
            for a in udim_attrs:
                try:
                    setattr(tex, a, True)
                    print("  (UDIM: enabled '%s' on texture, %d tiles)" % (a, tiles))
                except Exception:
                    pass
        else:
            print("  ! UDIM set of %d tiles, but no UDIM switch found on the"
                  " texture — only %s was linked." % (tiles, os.path.basename(path)))
            print("    If the other tiles don't show, enable UDIM on the texture"
                  " manually and report the setting name.")
    return tex


def assign(mat, slot, path, tiles, channel=None):
    sub_slot, model, field, is_srgb = SLOT_CONFIG[slot]
    try:
        mat.setSubroutine(sub_slot, model)
    except Exception as e:
        print("  ! could not set %s -> %s: %s" % (sub_slot, model, e))
        return False
    sub = mat.getSubroutine(sub_slot)
    try:
        sub.setField(field, make_texture(path, is_srgb, tiles))
    except Exception as e:
        print("  ! could not set field '%s': %s" % (field, e))
        return False
    if channel is not None:
        try:
            sub.setField("Channel", channel)
        except Exception:
            print("  ! no 'Channel' field on %s — set channel %d manually"
                  % (sub_slot, channel))
    if slot == "normal_dx":
        # Painter DirectX normals need Y flipped for Toolbag (OpenGL-style)
        try:
            sub.setField("Flip Y", True)
        except Exception:
            print("  ! DirectX normal detected but 'Flip Y' field not found — flip manually")
    return True


def main():
    folder = mset.showOpenFolderDialog()
    if not folder:
        print("No folder selected — aborted.")
        return

    materials = [(m.name.lower(), m) for m in mset.getAllMaterials() if m.name]
    textures = collect_textures(folder)
    if not textures:
        print("No recognizable texture files in: %s" % folder)
        return

    linked, skipped, matched_mats = 0, [], set()
    for path, stem, kind, value, tiles in textures:
        mat = best_material_for(stem, materials)
        if mat is None:
            skipped.append(os.path.basename(path))
            continue
        matched_mats.add(mat.name)
        tag = " (UDIM x%d)" % tiles if tiles > 1 else ""
        if kind == "single":
            print("%s  ->  %s [%s]%s" % (os.path.basename(path), mat.name, value, tag))
            if assign(mat, value, path, tiles):
                linked += 1
        else:  # packed: value = (slot for R, slot for G, slot for B)
            print("%s  ->  %s [packed R/G/B -> %s]%s"
                  % (os.path.basename(path), mat.name, "/".join(value), tag))
            for channel, slot in enumerate(value):
                if assign(mat, slot, path, tiles, channel=channel):
                    linked += 1

    print("-" * 50)
    print("Linked %d map slot(s) across %d material(s)." % (linked, len(matched_mats)))
    if skipped:
        print("Skipped (no matching material name):")
        for s in skipped:
            print("  - %s" % s)


main()
