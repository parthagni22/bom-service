import os, subprocess, shutil
from collections import defaultdict
from openpyxl import Workbook
from .dxf_extract import read_dxf_entities
from .catalog import load_catalog_map, normalize_row
from .validators import validate_required

def run_pipeline(job_id: str, in_path: str, base_dir: str) -> dict:
    """
    job_id: UUID
    in_path: path to uploaded DWG
    base_dir: backend/../data/jobs
    """
    job_root = os.path.join(base_dir, job_id)
    in_dir   = os.path.join(job_root, "in")
    out_dir  = os.path.join(job_root, "out")
    tmp_dir  = os.path.join(job_root, "tmp")
    os.makedirs(out_dir, exist_ok=True); os.makedirs(tmp_dir, exist_ok=True)

    # 1) Convert DWG -> DXF (using ODA or LibreDWG; pick via env)
    converter = os.getenv("CONVERTER", "oda")  # 'oda' or 'libredwg'
    dxf_path = os.path.join(tmp_dir, "layout.dxf")

    if converter == "oda":
        # ODAFileConverter <inDir> <outDir> <outVer> <outType> <recurse> <audit>
        oda_bin = os.getenv("CONVERTER_BIN", r"C:\Program Files\ODA\ODAFileConverter.exe")
        # Fix path: remove any wrapping quotes
        oda_bin = oda_bin.strip('"').strip("'")
        cmd = [oda_bin, in_dir, tmp_dir, os.getenv("DXF_VERSION","ACAD2018"), "DXF", "0", "1"]
        print("Running command:", cmd)

        subprocess.check_call(cmd)
        # find first .dxf in tmp_dir (ODA preserves names)
        candidates = [os.path.join(tmp_dir, f) for f in os.listdir(tmp_dir) if f.lower().endswith(".dxf")]
        if not candidates:
            raise RuntimeError("DXF not produced by ODA converter")
        dxf_path = candidates[0]
    else:
        # LibreDWG
        lib_bin = os.getenv("CONVERTER_BIN", r"dwg2dxf")
        subprocess.check_call([lib_bin, in_path, "-o", dxf_path])
        if not os.path.exists(dxf_path):
            raise RuntimeError("DXF not produced by LibreDWG")

    # 2) Parse DXF -> rows
    entities = list(read_dxf_entities(dxf_path))

    # 3) Normalize via catalog
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "resources", "catalog_map.csv")
    catalog = load_catalog_map(os.path.abspath(catalog_path))
    rows = [normalize_row(e, catalog) for e in entities]

    # 4) Validate
    exceptions = validate_required(rows)

    # 5) Aggregate -> BOQ
    agg = defaultdict(lambda: {"qty": 0, "layers": set()})
    for r in rows:
        key = (r["item_code"] or r["block"], r["desc"], r["size"], r["material"], r["uom"])
        agg[key]["qty"] += 1
        agg[key]["layers"].add(r["layer"])

    # 6) Write Excel
    xlsx = os.path.join(out_dir, "BOQ_Output.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "BOQ_Master"
    ws.append(["Item Code","Description","Size/Spec","Material","UOM","Qty","Layers"])
    for (code, desc, size, material, uom), info in agg.items():
        ws.append([code, desc, size, material, uom, info["qty"], ", ".join(sorted(info["layers"]))])

    # Room-wise (optional, only if room present)
    room_ws = wb.create_sheet("Room_Wise")
    room_ws.append(["Room/Zone","Item Code","Description","Qty"])
    room_totals = defaultdict(int)
    for r in rows:
        room = r["room"] or ""
        if room:
            room_totals[(room, r["item_code"] or r["block"], r["desc"])] += 1
    for (room, code, desc), qty in room_totals.items():
        room_ws.append([room, code, desc, qty])

    # Exceptions
    ex = wb.create_sheet("Unmapped_Exceptions")
    ex.append(["Block","Layer","Item Code","Desc","Size","Material","Room","Issue"])
    for bad in exceptions:
        ex.append([bad["block"], bad["layer"], bad["item_code"], bad["desc"], bad["size"], bad["material"], bad["room"], bad["issue"]])

    wb.save(xlsx)
    return {"job_id": job_id, "output": xlsx, "items_parsed": len(rows)}
