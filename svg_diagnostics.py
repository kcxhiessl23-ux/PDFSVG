# file: svg_diagnostics.py
# Python 3.12, Windows, no external libraries.
# Input: one SVG file or a folder of SVGs.
# Output: concise console summary + detailed CSVs per SVG in a DIAG folder.
#
# Default paths (edit as needed):
#   INPUT  = r"C:\Users\kschi\OneDrive\Desktop\Placards\TEST_SVGs"
#   OUTPUT = r"C:\Users\kschi\OneDrive\Desktop\Placards\DIAG"

import os
import re
import csv
import math
import glob
import argparse
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

# ---------- Config ----------
DEFAULT_INPUT  = r"C:\Users\kschi\OneDrive\Desktop\Placards\TEST_SVGs"
DEFAULT_OUTPUT = r"C:\Users\kschi\OneDrive\Desktop\Placards\DIAG"

# Cap for terminal prints
TOP_N_SHOW = 10

# ---------- Utilities ----------

NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")

def parse_viewbox(vb: str):
    try:
        parts = [float(x) for x in vb.strip().split()]
        if len(parts) == 4:
            return tuple(parts)  # (minx, miny, width, height)
    except Exception:
        pass
    return None

def parse_transform_matrix(t: str):
    # Supports matrix(a,b,c,d,e,f) and translate/scale/rotate partially.
    if not t:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    t = t.strip()
    # matrix(a,b,c,d,e,f)
    m = re.search(r"matrix\(\s*([^\)]+)\)", t)
    if m:
        nums = [float(x) for x in m.group(1).replace(',', ' ').split()]
        if len(nums) == 6:
            return tuple(nums)
    # scale(sx[, sy])
    m = re.search(r"scale\(\s*([^\)]+)\)", t)
    if m:
        nums = [float(x) for x in m.group(1).replace(',', ' ').split()]
        if len(nums) == 1:
            sx = sy = nums[0]
        elif len(nums) >= 2:
            sx, sy = nums[:2]
        else:
            sx = sy = 1.0
        return (sx, 0.0, 0.0, sy, 0.0, 0.0)
    # translate(tx[, ty])
    m = re.search(r"translate\(\s*([^\)]+)\)", t)
    if m:
        nums = [float(x) for x in m.group(1).replace(',', ' ').split()]
        tx = nums[0] if len(nums) > 0 else 0.0
        ty = nums[1] if len(nums) > 1 else 0.0
        return (1.0, 0.0, 0.0, 1.0, tx, ty)
    # rotate(θ) — ignore for bbox; return identity
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

def apply_matrix(pt, m):
    x, y = pt
    a, b, c, d, e, f = m
    return (a*x + c*y + e, b*x + d*y + f)

def path_command_freq(d: str):
    # Count SVG path commands
    cmds = re.findall(r"[MmLlHhVvCcQqSsTtAaZz]", d or "")
    cnt = Counter(c.upper() for c in cmds)
    return cnt

def bbox_from_path(d: str, transform: str):
    """
    Approximate bbox using only M/L/H/V/Z.
    Curves (C,Q,S,T,A) are ignored for bbox; we use any absolute/relative coords we can parse.
    """
    if not d:
        return None
    # Tokenize commands and numbers
    tokens = re.findall(r"[MmLlHhVvZz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", d)
    if not tokens:
        return None

    # Current point
    x = y = 0.0
    pts = []
    cmd = None

    def add_point(px, py):
        pts.append((px, py))

    i = 0
    while i < len(tokens):
        t = tokens[i]
        if re.fullmatch(r"[MmLlHhVvZz]", t):
            cmd = t
            i += 1
            continue

        # number encountered; interpret per last cmd
        if cmd in ('M', 'L'):
            # absolute x,y
            if i + 1 < len(tokens):
                try:
                    x = float(tokens[i]); y = float(tokens[i+1])
                    add_point(x, y)
                except Exception:
                    pass
                i += 2
                continue
        elif cmd in ('m', 'l'):
            # relative x,y
            if i + 1 < len(tokens):
                try:
                    dx = float(tokens[i]); dy = float(tokens[i+1])
                    x += dx; y += dy
                    add_point(x, y)
                except Exception:
                    pass
                i += 2
                continue
        elif cmd in ('H',):
            try:
                x = float(tokens[i])
                add_point(x, y)
            except Exception:
                pass
            i += 1
            continue
        elif cmd in ('h',):
            try:
                dx = float(tokens[i])
                x += dx
                add_point(x, y)
            except Exception:
                pass
            i += 1
            continue
        elif cmd in ('V',):
            try:
                y = float(tokens[i])
                add_point(x, y)
            except Exception:
                pass
            i += 1
            continue
        elif cmd in ('v',):
            try:
                dy = float(tokens[i])
                y += dy
                add_point(x, y)
            except Exception:
                pass
            i += 1
            continue
        else:
            # Z or curves; skip numeric payload
            i += 1
            continue

    if not pts:
        return None

    # Apply transform approx: matrix(a,b,c,d,e,f)
    m = parse_transform_matrix(transform or "")
    tx_pts = [apply_matrix(p, m) for p in pts]
    xs = [p[0] for p in tx_pts]
    ys = [p[1] for p in tx_pts]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    return (minx, miny, maxx, maxy)

def area_from_bbox(bb):
    if not bb:
        return 0.0
    minx, miny, maxx, maxy = bb
    return max(0.0, (maxx - minx)) * max(0.0, (maxy - miny))

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def bin_value(v, binsize):
    return math.floor(v / binsize) * binsize

def short(el):
    return f"{el.tag.split('}')[-1]}#{el.get('id','')}"

def ns_clean(tag):
    return tag.split('}')[-1]

def is_visible(elem):
    style = elem.get("style", "")
    fill = elem.get("fill")
    disp  = elem.get("display")
    op    = elem.get("opacity") or elem.get("fill-opacity") or elem.get("stroke-opacity")
    if disp and disp.strip().lower() == "none":
        return False
    if op is not None:
        try:
            if float(op) <= 0.0:
                return False
        except Exception:
            pass
    if "display:none" in style.replace(" ", "").lower():
        return False
    # treat fill=none as still potentially visible if stroke present; here only hide if fill=none and no stroke
    stroke = elem.get("stroke") or ("stroke:" in style.lower())
    if (fill == "none" or "fill:none" in style.lower()) and not stroke:
        return False
    return True

def color_of(elem):
    style = elem.get("style","").lower()
    fill = elem.get("fill")
    stroke = elem.get("stroke")
    def v(prop, inline):
        if inline:
            return inline
        m = re.search(fr"{prop}\s*:\s*([^;]+)", style)
        return m.group(1).strip() if m else None
    return (v("fill", fill), v("stroke", stroke))

def stroke_width(elem):
    style = elem.get("style","").lower()
    sw = elem.get("stroke-width")
    if sw is None:
        m = re.search(r"stroke-width\s*:\s*([^;]+)", style)
        sw = m.group(1).strip() if m else None
    try:
        return float(sw)
    except Exception:
        return None

def opacity_of(elem):
    for attr in ("opacity","fill-opacity","stroke-opacity"):
        v = elem.get(attr)
        if v is not None:
            try:
                return float(v)
            except Exception:
                pass
    style = elem.get("style","").lower()
    for attr in ("opacity","fill-opacity","stroke-opacity"):
        m = re.search(fr"{attr}\s*:\s*([^;]+)", style)
        if m:
            try:
                return float(m.group(1).strip())
            except Exception:
                pass
    return None

def gather_defs(root):
    defs = {}
    for d in root.iter():
        if ns_clean(d.tag) == "defs":
            for child in list(d):
                _id = child.get("id")
                if _id:
                    defs[_id] = child
    return defs

def href_of(elem):
    for k in ("{http://www.w3.org/1999/xlink}href","href"):
        if k in elem.attrib:
            return elem.attrib[k]
    return None

# ---------- Diagnostics Runner ----------

def diagnose_svg(svg_path: str, out_dir: str):
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
    except Exception as e:
        print(f"✗ Parse error: {svg_path} :: {e}")
        return

    svg_name = os.path.splitext(os.path.basename(svg_path))[0]
    file_out_dir = os.path.join(out_dir, svg_name)
    os.makedirs(file_out_dir, exist_ok=True)

    # Namespaces / integrity
    namespaces = {k:v for k,v in root.attrib.items() if k.startswith("xmlns")}
    viewBox = root.get("viewBox")
    vb = parse_viewbox(viewBox) if viewBox else None
    width_attr  = root.get("width")
    height_attr = root.get("height")

    # Collect elements in document order
    elements = []
    defs_map = gather_defs(root)
    id_to_elem = {}
    tag_counter = Counter()
    cmd_counter = Counter()
    color_counter = Counter()
    stroke_widths = []
    opacity_vals = []
    use_refs = Counter()
    orphan_refs = []
    duplicate_ids = []
    seen_ids = set()

    # For histograms and area estimates
    x_hist = Counter()
    y_hist = Counter()
    COLORS_PER_TAG = Counter()
    ELEMENT_ROWS = []  # detailed rows CSV
    LARGE_AREAS = []

    # Track render order for "covering shapes"
    covering_candidates = []  # (index, area, tag, fill, stroke, id)
    text_like_indices = []    # indices of <text> and <use> glyphs
    blackish = set(["#000","black","#000000","rgb(0,0,0)"])

    # Collect defs usage
    defs_children_total = len(defs_map)

    # Walk
    idx = 0
    for el in root.iter():
        tag = ns_clean(el.tag)
        if tag == "svg" or tag == "defs":
            continue
        _id = el.get("id")
        if _id:
            if _id in seen_ids:
                duplicate_ids.append(_id)
            else:
                seen_ids.add(_id)
                id_to_elem[_id] = el

        tag_counter[tag] += 1

        # Colors
        fill, stroke = color_of(el)
        COLORS_PER_TAG[(tag, fill or "none")] += 1
        COLORS_PER_TAG[(tag, stroke or "none")] += 1
        if fill:   color_counter[("fill", fill)] += 1
        if stroke: color_counter[("stroke", stroke)] += 1

        # Stroke widths
        sw = stroke_width(el)
        if sw is not None:
            stroke_widths.append(sw)

        # Opacity
        op = opacity_of(el)
        if op is not None:
            opacity_vals.append(op)

        # Path commands + bbox/area
        d_attr = el.get("d") if tag == "path" else None
        if d_attr:
            cc = path_command_freq(d_attr)
            cmd_counter.update(cc)

        # BBox estimation
        bb = None
        if tag in ("path","rect","image","use","text","circle","ellipse","line","polygon","polyline"):
            if tag == "rect":
                try:
                    x = float(el.get("x","0")); y = float(el.get("y","0"))
                    w = float(el.get("width","0")); h = float(el.get("height","0"))
                    m = parse_transform_matrix(el.get("transform"))
                    # Apply only translation for rect to keep simple
                    minx, miny = apply_matrix((x,y), m)
                    maxx, maxy = apply_matrix((x+w, y+h), m)
                    bb = (min(minx,maxx), min(miny,maxy), max(minx,maxx), max(miny,maxy))
                except Exception:
                    bb = None
            elif tag == "path":
                bb = bbox_from_path(d_attr, el.get("transform",""))
            else:
                # Attempt to pull any coords to bin in hist
                # For <use>, we rely on transform translate.
                # For text, x/y attributes if present.
                try:
                    if el.get("x") and el.get("y"):
                        x = float(el.get("x")); y = float(el.get("y"))
                        m = parse_transform_matrix(el.get("transform",""))
                        x2,y2 = apply_matrix((x,y), m)
                        bb = (x2,y2,x2,y2)
                except Exception:
                    bb = None

        area = area_from_bbox(bb)
        if bb:
            minx, miny, maxx, maxy = bb
            # Coordinate histograms with coarse bins
            bx = bin_value((minx+maxx)/2.0, 100.0)
            by = bin_value((miny+maxy)/2.0, 100.0)
            x_hist[bx] += 1
            y_hist[by] += 1

        # Record large potential covering shapes
        if area > 0:
            fill_lower = (fill or "").strip().lower()
            if tag in ("path","rect","polygon","polyline"):
                covering_candidates.append((idx, area, tag, fill_lower, stroke or "", _id or ""))

        # Track text-like for render order layering
        if tag in ("text","use"):
            text_like_indices.append(idx)

        # HREFs
        if tag == "use":
            href = href_of(el)
            if href:
                use_refs[href] += 1
                if href.startswith("#"):
                    refid = href[1:]
                    if refid not in id_to_elem and refid not in defs_map:
                        orphan_refs.append(href)

        # Store per-element row (thin)
        ELEMENT_ROWS.append({
            "index": idx,
            "tag": tag,
            "id": _id or "",
            "fill": fill or "",
            "stroke": stroke or "",
            "stroke_width": sw if sw is not None else "",
            "opacity": op if op is not None else "",
            "area_est": f"{area:.2f}" if area else "",
            "has_HV": "1" if (d_attr and ("H" in d_attr or "V" in d_attr)) else "0",
            "commands": " ".join([f"{k}:{v}" for k,v in path_command_freq(d_attr).items()]) if d_attr else "",
        })

        # Keep top areas
        if area > 0:
            LARGE_AREAS.append((area, tag, _id or "", fill or "", stroke or ""))

        idx += 1

    # Duplicated paths by "d" exact text
    d_map = defaultdict(int)
    for el in root.iter():
        if ns_clean(el.tag) == "path":
            d_map[el.get("d","")] += 1
    duplicated_paths = sum(1 for k,v in d_map.items() if k and v > 1)
    duplicate_paths_examples = [k for k,v in d_map.items() if k and v > 1][:TOP_N_SHOW]

    # Element visibility false items
    invisible_count = 0
    for el in root.iter():
        t = ns_clean(el.tag)
        if t in ("path","rect","polygon","polyline","use","text","circle","ellipse","line"):
            if not is_visible(el):
                invisible_count += 1

    # Command frequency quick features
    hv_rect_like = cmd_counter.get("H",0) > 0 and cmd_counter.get("V",0) > 0

    # Render order analysis: any very large filled dark shapes early?
    covering_candidates.sort(key=lambda x: x[0])  # keep document order
    large_sorted = sorted(covering_candidates, key=lambda x: x[1], reverse=True)[:50]
    potential_cover = []
    if text_like_indices:
        first_text_idx = min(text_like_indices)
        # flag any big shapes appearing before first text
        for idx0, area0, tag0, fill0, stroke0, id0 in large_sorted:
            if idx0 < first_text_idx and (fill0 in blackish or fill0 == "" or fill0 == "currentcolor"):
                potential_cover.append((idx0, area0, tag0, fill0, id0))
                if len(potential_cover) >= TOP_N_SHOW:
                    break

    # Colors summary
    top_colors = Counter()
    for (kind, val), cnt in color_counter.items():
        key = f"{kind}:{val}"
        top_colors[key] += cnt
    top_colors = top_colors.most_common(TOP_N_SHOW)

    # Stroke stats
    sw_min = f"{min(stroke_widths):.3f}" if stroke_widths else ""
    sw_max = f"{max(stroke_widths):.3f}" if stroke_widths else ""
    sw_avg = f"{(sum(stroke_widths)/len(stroke_widths)):.3f}" if stroke_widths else ""

    # Opacity stats
    if opacity_vals:
        op_min = f"{min(opacity_vals):.3f}"
        op_max = f"{max(opacity_vals):.3f}"
        op_avg = f"{(sum(opacity_vals)/len(opacity_vals)):.3f}"
    else:
        op_min = op_max = op_avg = ""

    # Unused defs
    referenced_ids = set()
    for href, cnt in use_refs.items():
        if href.startswith("#"):
            referenced_ids.add(href[1:])
    unused_defs = [d for d in defs_map.keys() if d not in referenced_ids]

    # Coverage by tag
    tag_areas = defaultdict(float)
    vb_area = None
    if vb:
        vb_area = vb[2] * vb[3]
    # recompute per tag areas
    idx2 = 0
    for el in root.iter():
        tag = ns_clean(el.tag)
        if tag in ("path","rect","polygon","polyline"):
            area = 0.0
            if tag == "rect":
                try:
                    x = float(el.get("x","0")); y = float(el.get("y","0"))
                    w = float(el.get("width","0")); h = float(el.get("height","0"))
                    m = parse_transform_matrix(el.get("transform",""))
                    minx, miny = apply_matrix((x,y), m)
                    maxx, maxy = apply_matrix((x+w, y+h), m)
                    area = area_from_bbox((min(minx,maxx), min(miny,maxy), max(minx,maxx), max(miny,maxy)))
                except Exception:
                    pass
            elif tag == "path":
                bb = bbox_from_path(el.get("d",""), el.get("transform",""))
                area = area_from_bbox(bb)
            # polygons etc: skip precise; bbox approach too noisy. Leave 0.
            tag_areas[tag] += area
        idx2 += 1

    # ---------- Write CSVs ----------
    # 1) summary.csv
    sum_csv = os.path.join(file_out_dir, "summary.csv")
    with open(sum_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", svg_path])
        w.writerow(["viewBox", viewBox or ""])
        w.writerow(["width_attr", width_attr or ""])
        w.writerow(["height_attr", height_attr or ""])
        w.writerow(["namespaces", "|".join(f"{k}={v}" for k,v in namespaces.items())])
        w.writerow([])
        w.writerow(["tag", "count"])
        for t,c in tag_counter.most_common():
            w.writerow([t, c])
        w.writerow([])
        w.writerow(["cmd", "count"])
        for k,c in cmd_counter.most_common():
            w.writerow([k, c])
        w.writerow([])
        w.writerow(["invisible_elements", invisible_count])
        w.writerow(["duplicated_paths_exact_d", duplicated_paths])
        w.writerow(["duplicate_ids", len(duplicate_ids)])
        w.writerow(["orphan_use_refs", len(orphan_refs)])
        w.writerow(["defs_total", defs_children_total])
        w.writerow(["unused_defs", len(unused_defs)])
        w.writerow(["has_rectlike_HV_presence", int(hv_rect_like)])
        w.writerow([])
        w.writerow(["stroke_width_min", sw_min])
        w.writerow(["stroke_width_max", sw_max])
        w.writerow(["stroke_width_avg", sw_avg])
        w.writerow(["opacity_min", op_min])
        w.writerow(["opacity_max", op_max])
        w.writerow(["opacity_avg", op_avg])

    # 2) elements.csv
    elem_csv = os.path.join(file_out_dir, "elements.csv")
    with open(elem_csv, "w", newline="", encoding="utf-8") as f:
        cols = ["index","tag","id","fill","stroke","stroke_width","opacity","area_est","has_HV","commands"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in ELEMENT_ROWS:
            w.writerow(row)

    # 3) top_areas.csv
    top_area_csv = os.path.join(file_out_dir, "top_areas.csv")
    with open(top_area_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rank","area_est","tag","id","fill","stroke"])
        for i,(a,tag,_id,fill,stroke) in enumerate(sorted(LARGE_AREAS, key=lambda x: x[0], reverse=True)[:200], start=1):
            w.writerow([i, f"{a:.2f}", tag, _id, fill, stroke])

    # 4) colors.csv
    colors_csv = os.path.join(file_out_dir, "colors.csv")
    with open(colors_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["kind_prop","value","count"])
        for (kind, val), cnt in color_counter.most_common():
            w.writerow([kind, val, cnt])

    # 5) coords_hist.csv
    coords_csv = os.path.join(file_out_dir, "coords_hist.csv")
    with open(coords_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["axis","bin_center","count"])
        for bx, ct in sorted(x_hist.items()):
            w.writerow(["x", bx, ct])
        for by, ct in sorted(y_hist.items()):
            w.writerow(["y", by, ct])

    # 6) refs.csv
    refs_csv = os.path.join(file_out_dir, "refs.csv")
    with open(refs_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["href","count"])
        for href, cnt in use_refs.most_common():
            w.writerow([href, cnt])
        if orphan_refs:
            w.writerow([])
            w.writerow(["orphan_href"])
            for o in orphan_refs:
                w.writerow([o])

    # 7) layers_order_cover.csv
    layers_csv = os.path.join(file_out_dir, "layers_order_cover.csv")
    with open(layers_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["index","area","tag","fill","id"])
        for idx0, area0, tag0, fill0, id0 in potential_cover:
            w.writerow([idx0, f"{area0:.2f}", tag0, fill0, id0])

    # 8) fonts_defs_map.csv
    fonts_csv = os.path.join(file_out_dir, "fonts_defs_map.csv")
    with open(fonts_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["def_id","tag"])
        for _id, node in defs_map.items():
            w.writerow([_id, ns_clean(node.tag)])

    # 9) tag_coverage.csv
    cover_csv = os.path.join(file_out_dir, "tag_coverage.csv")
    with open(cover_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tag","bbox_area_sum","vb_area","coverage_percent"])
        for t, a in sorted(tag_areas.items(), key=lambda x: x[1], reverse=True):
            cov = (a / vb_area * 100.0) if vb_area and vb_area > 0 else ""
            w.writerow([t, f"{a:.2f}", f"{vb_area:.2f}" if vb_area else "", f"{cov:.4f}" if cov != "" else ""])

    # 10) integrity.csv
    integ_csv = os.path.join(file_out_dir, "integrity.csv")
    with open(integ_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["check","value"])
        w.writerow(["duplicate_id_count", len(duplicate_ids)])
        if duplicate_ids:
            for d in duplicate_ids[:200]:
                w.writerow(["duplicate_id", d])
        w.writerow(["orphan_use_ref_count", len(orphan_refs)])
        w.writerow(["xmlns_count", len(namespaces)])
        w.writerow(["has_viewBox", int(vb is not None)])

    # ---------- Concise console summary ----------
    print(f"\n[{svg_path}]")
    print(f"  tags: {dict(tag_counter)}")
    print(f"  cmds: {{'M':{cmd_counter.get('M',0)}, 'L':{cmd_counter.get('L',0)}, 'H':{cmd_counter.get('H',0)}, 'V':{cmd_counter.get('V',0)}, 'C':{cmd_counter.get('C',0)}, 'A':{cmd_counter.get('A',0)}}}")
    print(f"  invisible: {invisible_count} | dup_paths(d): {duplicated_paths} | dup_ids: {len(duplicate_ids)} | orphan_refs: {len(orphan_refs)} | defs: {defs_children_total} unused_defs: {len(unused_defs)}")
    if top_colors:
        print("  colors(top): " + ", ".join([f"{k}={v}" for k,v in top_colors[:5]]))
    if potential_cover:
        print(f"  potential_covering_shapes(before first text): {len(potential_cover)} (see layers_order_cover.csv)")
    if vb_area:
        top_cov = sorted(tag_areas.items(), key=lambda x: x[1], reverse=True)[:3]
        print("  coverage(top): " + ", ".join([f"{t}={a/vb_area*100:.2f}%" for t,a in top_cov if vb_area > 0]))
    print(f"  out: {file_out_dir}")

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description="SVG diagnostics with concise console output and detailed CSV logs.")
    ap.add_argument("--input",  type=str, default=DEFAULT_INPUT, help="SVG file or folder")
    ap.add_argument("--output", type=str, default=DEFAULT_OUTPUT, help="Output diagnostics folder")
    args = ap.parse_args()

    in_path = args.input
    out_dir = args.output
    os.makedirs(out_dir, exist_ok=True)

    paths = []
    if os.path.isdir(in_path):
        paths = sorted(glob.glob(os.path.join(in_path, "*.svg")))
    elif os.path.isfile(in_path) and in_path.lower().endswith(".svg"):
        paths = [in_path]
    else:
        print("No SVG found.")
        return

    print("SVG diagnostics running...")
    print(f"Input:  {in_path}")
    print(f"Output: {out_dir}")

    for p in paths:
        diagnose_svg(p, out_dir)

    print("Done.")

if __name__ == "__main__":
    main()
    
    
    
    
import glob
import csv

diag_root = r"C:\Users\kschi\OneDrive\Desktop\Placards\DIAG"
combined_csv = os.path.join(diag_root, "ALL_DIAGNOSTICS.csv")

csv_files = glob.glob(os.path.join(diag_root, "*", "*.csv"))
if not csv_files:
    print("✗ No CSV files found to combine.")
else:
    all_headers = set()
    csv_data = []

    # Read all CSVs first, store rows, track unique headers
    for file in csv_files:
        with open(file, "r", encoding="utf-8") as infile:
            reader = csv.reader(infile)
            headers = next(reader, [])
            if not headers:
                continue
            all_headers.update(headers)
            for row in reader:
                csv_data.append({
                    "source_file": os.path.basename(os.path.dirname(file)),
                    "csv_name": os.path.basename(file),
                    **{headers[i]: row[i] if i < len(row) else "" for i in range(len(headers))}
                })

    all_headers = ["source_file", "csv_name"] + sorted(list(all_headers))

    # Write unified CSV
    with open(combined_csv, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=all_headers)
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"✓ Combined diagnostics written to: {combined_csv}")
