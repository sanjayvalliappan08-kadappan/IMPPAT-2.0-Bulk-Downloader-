
#!/usr/bin/env python3
"""
IMPPAT 2.0 bulk downloader — filtering, display, and download.

━━━ SINGLE COMPOUND ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  # Show all property tabs for one compound:
    python imppat_downloader.py --id IMPHY011396 --show physchem druglike admet

  # Download one compound (PDBQT):
    python imppat_downloader.py --id IMPHY011396

  # Show + download:
    python imppat_downloader.py --id IMPHY011396 --show admet --format sdf

━━━ BULK (by plant species) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  # Download all compounds (no filter):
    python imppat_downloader.py --plant "Ocimum tenuiflorum"

  # Show ADMET for every compound (no download):
    python imppat_downloader.py --plant "Ocimum tenuiflorum" --show admet --no-download

  # Lipinski filter then download PDBQT:
    python imppat_downloader.py --plant "Ocimum tenuiflorum" --filter lipinski

  # Lipinski + Veber, show physicochemical, download SDF:
    python imppat_downloader.py --plant "Ocimum tenuiflorum" \
        --filter lipinski veber --show physchem --format sdf

  # All six filters, both formats:
    python imppat_downloader.py --plant "Ocimum tenuiflorum" \
        --filter lipinski ghose veber egan gsk pfizer --format pdbqt sdf

━━━ --show choices ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    physchem   Physicochemical properties (MW, logP, HBD, HBA, ...)
    druglike   Drug-likeness rules (Lipinski, Ghose, Veber, Egan, GSK, Pfizer)
    admet      ADMET properties (absorption, distribution, metabolism, ...)
"""

import argparse
import time
import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# URLs
BASE_URL         = "https://cb.imsc.res.in/imppat"
PLANT_SEARCH_URL = f"{BASE_URL}/phytochemical/{{plant}}"
DRUGLIKE_URL     = f"{BASE_URL}/druglikeproperties/{{imphy_id}}"
PHYSCHEM_URL     = f"{BASE_URL}/physicochemicalproperties/{{imphy_id}}"
ADMET_URL        = f"{BASE_URL}/admetproperties/{{imphy_id}}"

HEADERS = {"User-Agent": "Mozilla/5.0"}
DELAY   = 0.5

# Drug-likeness row matchers
# The table has TWO rows per rule:
#   Row A  "Number of X violations"  -> integer (skip)
#   Row B  "X rule / rule of 5"      -> Passed/Failed/Good/Bad (use)
# We skip Row A via startswith("number of"), then do keyword substring match
# -- robust to Unicode apostrophe U+2019 in "Lipinski's".
FILTER_ROWS = {
    "lipinski": ("lipinski", "passed"),
    "ghose":    ("ghose",    "passed"),
    "veber":    ("veber",    "good"),
    "egan":     ("egan",     "good"),
    "gsk":      ("gsk",      "good"),
    "pfizer":   ("pfizer",   "good"),
}

VALID_FILTERS = list(FILTER_ROWS.keys())

SHOW_LABELS = {
    "physchem": "Physicochemical",
    "druglike":  "Drug-likeness",
    "admet":     "ADMET",
}

SHOW_URLS = {
    "physchem": PHYSCHEM_URL,
    "druglike":  DRUGLIKE_URL,
    "admet":     ADMET_URL,
}


def get_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def parse_property_table(session, url):
    """Fetch an IMPPAT property page, return {name: value} dict or None."""
    try:
        r = session.get(url)
        r.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(r.text, "html.parser")
    data = {}
    for row in soup.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 3:
            key = cols[0].get_text(strip=True)
            val = cols[2].get_text(strip=True)
            if key:
                data[key] = val
    return data


def show_properties(session, imphy_id, show_opts):
    """Print requested property tabs for a single compound."""
    for tab in show_opts:
        label = SHOW_LABELS[tab]
        url   = SHOW_URLS[tab].format(imphy_id=imphy_id)
        data  = parse_property_table(session, url)
        print(f"\n  -- {label} --")
        if not data:
            print("    (no data)")
            continue
        for k, v in data.items():
            print(f"    {k:<55} {v}")


def fetch_phytochemical_ids(session, plant_name):
    """
    Fetch ALL compound IDs via DataTables AJAX pagination.
    Falls back to HTML scraping if the server returns non-JSON.
    """
    quoted = requests.utils.quote(plant_name)
    url    = PLANT_SEARCH_URL.format(plant=quoted)

    print(f"\n[*] Querying IMPPAT for: {plant_name}")

    ids    = []
    seen   = set()
    start  = 0
    length = 100
    total  = None

    def _dt_payload(draw, start):
        p = {
            "draw":             draw,
            "start":            start,
            "length":           length,
            "search[value]":    "",
            "search[regex]":    "false",
            "order[0][column]": "0",
            "order[0][dir]":    "asc",
        }
        for i in range(5):
            p[f"columns[{i}][data]"]          = i
            p[f"columns[{i}][searchable]"]    = "true"
            p[f"columns[{i}][orderable]"]     = "true"
            p[f"columns[{i}][search][value]"] = ""
            p[f"columns[{i}][search][regex]"] = "false"
        return p

    draw = 1
    while True:
        try:
            r = session.post(url, data=_dt_payload(draw, start))
            r.raise_for_status()
            data = r.json()

            if total is None:
                total = data.get("recordsTotal", 0)
                print(f"[+] Total compounds reported: {total}")

            rows = data.get("data", [])
            if not rows:
                break

            for row in rows:
                if isinstance(row, list):
                    cell_id   = row[2]
                    cell_name = row[3]
                elif isinstance(row, dict):
                    cell_id   = str(row.get(2, row.get("2", "")))
                    cell_name = str(row.get(3, row.get("3", "")))
                else:
                    continue

                m = re.search(r"IMPHY\d+", str(cell_id))
                if not m:
                    m = re.search(r"IMPHY\d+", str(cell_name))
                if not m:
                    continue

                imphy_id  = m.group(0)
                name_soup = BeautifulSoup(str(cell_name), "html.parser")
                name      = name_soup.get_text(strip=True) or imphy_id

                if imphy_id not in seen:
                    seen.add(imphy_id)
                    ids.append({"id": imphy_id, "name": name})

            start += length
            draw  += 1

            if total is not None and len(ids) >= total:
                break

        except (ValueError, KeyError):
            print("[!] DataTables AJAX unavailable -- falling back to HTML scrape")
            r2 = session.get(url)
            r2.raise_for_status()
            soup = BeautifulSoup(r2.text, "html.parser")
            for a in soup.find_all("a", href=True):
                m = re.search(r"IMPHY\d+", a["href"])
                if m:
                    imphy_id = m.group(0)
                    if imphy_id not in seen:
                        seen.add(imphy_id)
                        ids.append({"id": imphy_id, "name": a.text.strip()})
            break

    print(f"[+] Collected {len(ids)} unique compounds")
    return ids


def build_download_url(imphy_id, fmt):
    fmt = fmt.lower()
    if fmt == "pdbqt":
        return f"{BASE_URL}/images/3D/PDBQT/{imphy_id}_3D.pdbqt"
    elif fmt == "sdf":
        return f"{BASE_URL}/images/3D/SDF/{imphy_id}_3D.sdf"
    else:
        raise ValueError(f"Unsupported format: {fmt!r}  (choose pdbqt or sdf)")


def download_file(session, url, dest):
    if dest.exists():
        print(f"    [skip] {dest.name}  (already downloaded)")
        return "skip"
    try:
        r = session.get(url)
        if r.status_code == 404:
            print(f"    [miss] {dest.name}  (404 - not on server)")
            return "miss"
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"    [OK]   {dest.name}")
        return "ok"
    except Exception as e:
        print(f"    [ERR]  {dest.name}  - {e}")
        return "err"


def check_druglikeness(session, imphy_id, filters):
    """Returns {filter_key: bool} for each filter. None on fetch failure."""
    url = DRUGLIKE_URL.format(imphy_id=imphy_id)
    try:
        r = session.get(url)
        r.raise_for_status()
    except Exception:
        return None

    soup    = BeautifulSoup(r.text, "html.parser")
    results = {}

    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        prop_name = cells[0].get_text(strip=True).lower()
        prop_val  = cells[2].get_text(strip=True).lower()

        if prop_name.startswith("number of"):
            continue

        for key in filters:
            if key in results:
                continue
            keyword, pass_fragment = FILTER_ROWS[key]
            if keyword in prop_name:
                results[key] = pass_fragment in prop_val

    return results


def parse_args():
    p = argparse.ArgumentParser(
        description="IMPPAT 2.0 -- bulk download, drug-likeness filtering, property display.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--plant", metavar="NAME",
        help='Plant species name, e.g. "Ocimum tenuiflorum"',
    )
    src.add_argument(
        "--id", metavar="IMPHY_ID",
        help="Single compound ID, e.g. IMPHY011396",
    )

    p.add_argument(
        "--show", nargs="+",
        choices=list(SHOW_LABELS.keys()),
        metavar="TAB",
        help="Property tab(s) to display: physchem  druglike  admet",
    )
    p.add_argument(
        "--filter", nargs="+",
        choices=VALID_FILTERS,
        metavar="RULE",
        help=(
            "Keep only compounds passing ALL listed rules "
            f"({', '.join(VALID_FILTERS)}). Bulk mode only."
        ),
    )
    p.add_argument(
        "--format", nargs="+",
        default=["pdbqt"],
        choices=["pdbqt", "sdf"],
        metavar="FMT",
        help="Format(s) to download: pdbqt  sdf  (default: pdbqt)",
    )
    p.add_argument(
        "--no-download", action="store_true",
        help="Display properties only -- do not save structure files.",
    )
    p.add_argument(
        "--delay", type=float, default=DELAY, metavar="SEC",
        help=f"Seconds between HTTP requests (default: {DELAY})",
    )

    return p.parse_args()


def main():
    args = parse_args()

    active_filters = [f.lower() for f in args.filter] if args.filter else []
    show_opts      = args.show or []

    session = get_session()

    # ── Single compound mode ──────────────────────────────────────────────────
    if args.id:
        imphy_id = args.id.strip().upper()
        print(f"\n[*] Single compound: {imphy_id}")

        if show_opts:
            show_properties(session, imphy_id, show_opts)

        if not args.no_download:
            out_dir = Path("IMPPAT_OUTPUT")
            out_dir.mkdir(exist_ok=True)
            print()
            for fmt in args.format:
                url  = build_download_url(imphy_id, fmt)
                dest = out_dir / f"{imphy_id}.{fmt}"
                download_file(session, url, dest)
                time.sleep(args.delay)
        return

    # ── Bulk (plant) mode ─────────────────────────────────────────────────────
    compounds = fetch_phytochemical_ids(session, args.plant)

    if not compounds:
        print("[!] No compounds found. Check the plant name spelling.")
        return

    out_dir = Path(f"IMPPAT_{args.plant.replace(' ', '_')}")
    if not args.no_download:
        out_dir.mkdir(exist_ok=True)

    ok = fail = skip_filter = 0

    print(f"\n[*] Output folder : {out_dir}/")
    if active_filters:
        print(f"[*] Active filters: {', '.join(active_filters)}")
    if show_opts:
        print(f"[*] Show tabs     : {', '.join(show_opts)}")
    print(f"[*] Formats       : {', '.join(args.format)}")
    if args.no_download:
        print(f"[*] --no-download : structure files will NOT be saved")
    print(f"\n{'─'*55}")

    for i, compound in enumerate(compounds, 1):
        imphy_id = compound["id"]
        name     = compound["name"]

        print(f"\n[{i}/{len(compounds)}] {imphy_id}  {name}")

        # Filter
        if active_filters:
            props = check_druglikeness(session, imphy_id, active_filters)
            time.sleep(args.delay)

            if props is None:
                print("    [skip] could not fetch drug-likeness page")
                skip_filter += 1
                continue

            failed = [f for f in active_filters if not props.get(f, False)]
            if failed:
                print(f"    [skip] failed: {', '.join(failed)}")
                skip_filter += 1
                continue

            print(f"    [pass] {', '.join(active_filters)}")

        # Display properties
        if show_opts:
            show_properties(session, imphy_id, show_opts)
            time.sleep(args.delay)

        # Download
        if not args.no_download:
            for fmt in args.format:
                url    = build_download_url(imphy_id, fmt)
                dest   = out_dir / f"{imphy_id}.{fmt}"
                result = download_file(session, url, dest)
                if result == "ok":
                    ok += 1
                elif result in ("miss", "err"):
                    fail += 1
                time.sleep(args.delay)

    print(f"\n{'='*55}")
    print(f"Plant      : {args.plant}")
    if not args.no_download:
        print(f"Downloaded : {ok}")
        print(f"Missing    : {fail}")
    print(f"Filtered   : {skip_filter}")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()

