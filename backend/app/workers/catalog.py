import csv

def load_catalog_map(path: str):
    mapping = {}
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                mapping[(row.get("raw_block_name","") or "").upper()] = row
    except FileNotFoundError:
        pass
    return mapping

def normalize_row(row: dict, catalog: dict):
    raw = (row["block"] or "").upper()
    m = catalog.get(raw)
    # Base fields from attrs
    attrs = row["attrs"]
    item_code = attrs.get("ITEM_CODE") or attrs.get("CODE") or ""
    desc      = attrs.get("DESC") or attrs.get("DESCRIPTION") or row["block"]
    size      = attrs.get("SIZE","")
    material  = attrs.get("MATERIAL","")
    room      = attrs.get("ROOM") or attrs.get("ZONE") or ""
    # Apply catalog if present
    if m:
        item_code = m.get("std_item_code") or item_code
        desc      = m.get("std_desc") or desc
        size      = m.get("std_size") or size
        material  = m.get("std_material") or material
        category  = m.get("std_category") or ""
        uom       = m.get("std_uom") or "NOS"
    else:
        category = ""
        uom      = "NOS"
    return {
        "block": row["block"],
        "layer": row["layer"],
        "item_code": item_code,
        "desc": desc,
        "size": size,
        "material": material,
        "room": room,
        "category": category,
        "uom": uom,
    }
