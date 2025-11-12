def validate_required(rows):
    problems = []
    for r in rows:
        if not (r["item_code"] or r["block"]):
            problems.append({**r, "issue": "missing identity"})
        if not r["desc"]:
            problems.append({**r, "issue": "missing desc"})
    return problems
