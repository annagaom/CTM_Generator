import re
import random
from datetime import datetime, timedelta
from pathlib import Path

MALE_FIRST = ["Mika", "Jon", "Henrik", "Rami", "Eero", "Leo", "Antti", "Jukka", "Ville", "Tuomas"]
FEMALE_FIRST = ["Laura", "Sanna", "Veera", "Aino", "Noora", "Emma", "Sara", "Helmi", "Iida", "Emilia"]
LAST_NAMES = ["Virtanen", "Korhonen", "Laine", "Heikkinen", "Mäkinen", "Hämäläinen", "Koskinen", "Järvinen"]

SPEED_OPTIONS = [(30,30), (60,60), (120,120), (180,180), (240,240), (30,300)]
PROGRAM_TYPES = [
    ("isokin. ballistinen kons/kons", 63),
    ("isokin. ballistinen eks/eks", 66),
    ("isokin. ballistinen CPM/eks", 208)
]

def pick_names(content: str):
    sex_line = next((l for l in content.splitlines() if l.startswith("subject sex")), "")
    is_male = sex_line.split("\t")[1:2] == ["1"]
    first = random.choice(MALE_FIRST if is_male else FEMALE_FIRST)
    last = random.choice(LAST_NAMES)
    return first, last

def make_session_meta(example_content: str):
    first, last = pick_names(example_content)
    base_day = datetime.now() - timedelta(days=random.randint(1, 90))
    start = base_day.replace(hour=random.randint(8,18), minute=random.randint(0,59), second=random.randint(0,59))

    return {
        "first": first,
        "last": last,
        "date": base_day.strftime("%d.%m.%Y"),
        "start": start
    }

def detect_original_side(content: str):
    m = re.search(r"^side\s+(\d+)", content, flags=re.MULTILINE)
    if not m:
        return 1  # fallback: left
    return int(m.group(1))  # 1 = left, 0 = right

def per_copy_meta(session_meta, index, original_content):
    dt = session_meta["start"] + timedelta(minutes=10 * (index-1))
    time = dt.strftime("%H.%M.%S")

    orig_side = detect_original_side(original_content)

    # flip original side
    side_code = 0 if orig_side == 1 else 1
    side_text = "right" if side_code == 0 else "left"

    sp1, sp2 = random.choice(SPEED_OPTIONS)
    program_text, program_code = random.choice(PROGRAM_TYPES)

    return {
        "first_name": session_meta["first"],
        "last_name": session_meta["last"],
        "date": session_meta["date"],
        "time": time,
        "side_text": side_text,
        "side_code": side_code,
        "speed1": sp1,
        "speed2": sp2,
        "program_text": program_text,
        "program_code": program_code
    }

def rewrite(content: str, m: dict) -> str:
    flags = re.MULTILINE

    side_fi = "vasen" if m["side_code"] == 1 else "oikea"

    content = re.sub(
        r"^name\s+.*$",
        f"name\t{side_fi} polven oj/kouk 500 Nm {m['program_text']} {m['speed1']}/{m['speed2']} Mittaus 3 toisto tauko 120s",
        content,
        flags=flags
    )

    repl = [
        (r"^subject name\s*\t.*$",       f"subject name\t{m['last_name']}"),
        (r"^subject name first\s*\t.*$", f"subject name first\t{m['first_name']}"),
        (r"^date \(dd/mm/yyyy\)\s+.*",   f"date (dd/mm/yyyy)\t{m['date']}"),
        (r"^time \(hh/mm/ss\)\s+.*",     f"time (hh/mm/ss)\t{m['time']}"),
        (r"^time\(system\)\s+.*",        f"time(system)\t{m['date']} {m['time']}"),
        (r"^side\s+.*",                  f"side\t{m['side_code']}\t{m['side_text']}"),
        (r"^program\s+\d+\s+.*",         f"program\t{m['program_code']}\t{m['program_text']}"),
        (r"^speed\s+\d+\s+\d+",          f"speed\t{m['speed1']}\t{m['speed2']}")
    ]

    for pattern, repl_val in repl:
        content = re.sub(pattern, repl_val, content, flags=flags)

    return content

def generate(files, sessions, per_session, progress_callback=None):
    example = files[0].read_text(encoding="ISO-8859-1", errors="replace")
    out_dir = Path("generated"); out_dir.mkdir(exist_ok=True)

    processed = 0

    for s in range(1, sessions+1):
        session_meta = make_session_meta(example)

        for i in range(1, per_session+1):
            src = files[(i-1) % len(files)]
            original = src.read_text(encoding="ISO-8859-1", errors="replace")

            meta = per_copy_meta(session_meta, i, original)
            new_content = rewrite(original, meta)

            out_file = out_dir / f"{src.stem}_s{s}_{i}.CTM"
            out_file.write_text(new_content, encoding="ISO-8859-1")

            processed += 1
            if progress_callback:
                progress_callback(processed, out_file.name)

    return processed
