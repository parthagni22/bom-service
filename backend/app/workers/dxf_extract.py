import ezdxf

MANDATORY_ATTRS = ["ITEM_CODE", "DESC"]
OPTIONAL_ATTRS = ["SIZE", "MATERIAL", "ROOM", "ZONE"]

def read_dxf_entities(dxf_path: str):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    for ins in msp.query("INSERT"):
        attrs = {a.dxf.tag.upper(): (a.dxf.text or "").strip() for a in ins.attribs}
        yield {
            "block": ins.dxf.name,
            "layer": ins.dxf.layer,
            "attrs": attrs,
            "scale": (ins.dxf.xscale, ins.dxf.yscale),
            "rotation": ins.dxf.rotation
        }
