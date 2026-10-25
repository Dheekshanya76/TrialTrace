"""Parse NCRB 'Court Disposal of Crimes (Crime Head-wise)' PDF tables.

Layout of the source PDFs (Tables 18B.1 IPC and 18B.3 SLL, 2023):
each group of crime heads is printed on 4 consecutive pages, and each page
holds 5 of the 20 numeric columns (Col 3-7, 8-12, 13-17, 18-22).
We read the 4 pages of a group and stitch the rows back together.
"""
import re
import pdfplumber
import pandas as pd

# NCRB column number -> readable name
COLS = {
    3: "pending_prev", 4: "sent_for_trial", 5: "total_for_trial",
    6: "abated", 7: "withdrawn", 8: "compounded", 9: "plea_bargain",
    10: "quashed", 11: "disposed_without_trial", 12: "stayed_or_record_room",
    13: "conv_prev_year", 14: "conv_current_year", 15: "convicted",
    16: "discharged", 17: "acquitted", 18: "trials_completed",
    19: "disposed_by_courts", 20: "pending_end",
    21: "conviction_rate_pub", 22: "pendency_pct_pub",
}
COUNT_COLS = [COLS[i] for i in range(3, 21)]   # additive counts

_NUM = r"(?:-|\d+(?:\.\d+)?)"
_ROW = re.compile(rf"^(.*?)((?:\s+{_NUM}){{5}})$")      # name + 5 numbers
_CODE = re.compile(r"^(\d+(?:\.\d+)?[A-G]?)\s+(.+)$")   # '3.1A Hit and Run'
_SKIP = ("●", "TABLE", "Court Disposal", "[1]", "SL Crime Head")


def _page_rows(text):
    """Return [(label, [5 values])] for one PDF page, in order.
    Row labels wrap over several lines, so lines are buffered until
    the buffer ends with 5 numeric tokens."""
    rows, buf = [], ""
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith(_SKIP):
            buf = ""
            continue
        buf = f"{buf} {line}".strip()
        m = _ROW.match(buf)
        if m and re.search(r"[A-Za-z]", m.group(1)):
            rows.append((m.group(1).strip(), m.group(2).split()))
            buf = ""
    return rows


def parent_code(code):
    """'3.1A' -> '3.1', '10.1' -> '10', '10' -> None."""
    if code is None or (isinstance(code, float)):
        return None
    if code[-1].isalpha():
        return code[:-1]
    if "." in code:
        return code.rsplit(".", 1)[0]
    return None


def parse_pdf(path, table_name):
    """Parse one court-disposal PDF into a tidy DataFrame."""
    with pdfplumber.open(path) as pdf:
        pages = [_page_rows(p.extract_text(use_text_flow=True) or "") for p in pdf.pages]
    if len(pages) % 4:
        raise ValueError(f"{path}: {len(pages)} pages is not a multiple of 4")

    records = []
    for g in range(len(pages) // 4):
        blocks = pages[4 * g: 4 * g + 4]
        labels = [[lab for lab, _ in b] for b in blocks]
        if any(l != labels[0] for l in labels):
            raise ValueError(f"{path}: row labels differ across pages of group {g}")
        for i, label in enumerate(labels[0]):
            vals = [v for b in blocks for v in b[i][1]]          # 20 values
            m = _CODE.match(label)
            code, name = (m.group(1), m.group(2)) if m else (None, label)
            rec = {"table": table_name, "sl_code": code, "crime_head": name}
            for col_no, v in zip(range(3, 23), vals):
                rec[COLS[col_no]] = float("nan") if v == "-" else float(v)
            records.append(rec)
    return _classify(pd.DataFrame(records))


def _classify(df):
    """Add row_type (detail / parent / subtotal / grand_total), parent_code
    and group (the subtotal each top-level head rolls up into)."""
    df["parent_code"] = df["sl_code"].map(parent_code)
    has_children = set(df["parent_code"].dropna())
    row_type, grp, pending = [], [None] * len(df), []
    for i, r in enumerate(df.itertuples()):
        if pd.isna(r.sl_code):
            if r.crime_head.startswith("Total Cognizable"):
                rtype, label = "grand_total", "Ungrouped"
            else:
                rtype, label = "subtotal", r.crime_head
            for j in pending:
                grp[j] = label
            pending = []
            grp[i] = r.crime_head
            row_type.append(rtype)
        else:
            row_type.append("parent" if r.sl_code in has_children else "detail")
            pending.append(i)
    df["row_type"] = row_type
    df["group"] = grp
    # children inherit the group of their top-level ancestor
    def root(c):
        while parent_code(c):
            c = parent_code(c)
        return c
    top = dict(zip(df.loc[df.parent_code.isna() & df.sl_code.notna(), "sl_code"],
                   df.loc[df.parent_code.isna() & df.sl_code.notna(), "group"]))
    m = df.sl_code.notna()
    df.loc[m, "group"] = df.loc[m, "sl_code"].map(lambda c: top.get(root(c)))
    df["geography"] = "Metropolitan cities (aggregate)"
    df["year"] = 2023
    return df


def load_all(ipc_pdf, sll_pdf):
    return pd.concat([parse_pdf(ipc_pdf, "IPC"), parse_pdf(sll_pdf, "SLL")], ignore_index=True)
