#!/usr/bin/env python3
"""lesson_summary.py - monthly lesson summary per student from a simple CSV.

Reads a lessons CSV (columns: date,student,minutes,status,note), works out what
each lesson is worth under your cancellation policy and prints a table per month:
lessons taught, late cancels / no-shows, amount billed and income missed.

Safe by design: standard library only, no network. The input file is only read.
Nothing is written unless you pass --out, and an existing file is never
overwritten.

Example:
    python lesson_summary.py lessons.csv --rate 45 --student-rate "Tom H.=38"
"""
import argparse
import csv
import sys
from collections import OrderedDict
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

# status (lower case) -> share of the lesson that is billed. Override with --late-pct / --noshow-pct.
DEFAULT_PCT = {
    "taught": Decimal("1"),
    "late cancel": Decimal("0.5"),
    "no-show": Decimal("1"),
    "cancelled in time": Decimal("0"),
    "teacher cancelled": Decimal("0"),
    "trial / free": Decimal("0"),
    "trial": Decimal("0"),
}


def money(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def parse_date(text):
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError("unknown date format: %r (use YYYY-MM-DD)" % text)


def parse_args(argv):
    p = argparse.ArgumentParser(description="Monthly lesson summary per student from a CSV.")
    p.add_argument("csv_file", help="lessons CSV: date,student,minutes,status,note")
    p.add_argument("--rate", type=Decimal, default=Decimal("40"), help="standard hourly rate (default 40)")
    p.add_argument("--student-rate", action="append", default=[], metavar="NAME=RATE",
                   help="own hourly rate for one student; repeat as needed")
    p.add_argument("--late-pct", type=Decimal, default=Decimal("50"),
                   help="percent billed for a late cancel (default 50)")
    p.add_argument("--noshow-pct", type=Decimal, default=Decimal("100"),
                   help="percent billed for a no-show (default 100)")
    p.add_argument("--month", help="only this month, e.g. 2026-09")
    p.add_argument("--currency", default="", help="symbol shown after amounts, e.g. EUR")
    p.add_argument("--out", help="also write the summary to this NEW csv file (never overwrites)")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    pct = dict(DEFAULT_PCT)
    pct["late cancel"] = a.late_pct / 100
    pct["no-show"] = a.noshow_pct / 100

    own = {}
    for item in a.student_rate:
        if "=" not in item:
            sys.exit("--student-rate needs NAME=RATE, got %r" % item)
        name, _, val = item.rpartition("=")
        try:
            own[name.strip()] = Decimal(val)
        except Exception:
            sys.exit("bad rate in --student-rate %r" % item)

    path = Path(a.csv_file)
    if not path.is_file():
        sys.exit("file not found: %s" % path)

    rows = OrderedDict()  # (month, student) -> dict
    problems = 0
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        need = {"date", "student", "minutes", "status"}
        if not reader.fieldnames or not need.issubset({f.strip().lower() for f in reader.fieldnames}):
            sys.exit("CSV needs the columns: date,student,minutes,status (note is optional)")
        for n, raw in enumerate(reader, start=2):
            r = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            if not any(r.values()):
                continue
            try:
                day = parse_date(r["date"])
                minutes = Decimal(r["minutes"])
            except Exception as exc:
                print("line %d skipped: %s" % (n, exc), file=sys.stderr)
                problems += 1
                continue
            month = day.strftime("%Y-%m")
            if a.month and month != a.month:
                continue
            status = r["status"].lower()
            if status not in pct:
                print("line %d: unknown status %r counted as 0%% billed" % (n, r["status"]), file=sys.stderr)
                problems += 1
            share = pct.get(status, Decimal("0"))
            rate = own.get(r["student"], a.rate)
            full = money(rate * minutes / 60)
            billed = money(rate * minutes / 60 * share)
            missed = Decimal("0") if status == "taught" else full - billed
            d = rows.setdefault((month, r["student"]), dict(taught=0, cancels=0, billed=Decimal("0"),
                                                             missed=Decimal("0")))
            if status == "taught":
                d["taught"] += 1
            if status in ("late cancel", "no-show"):
                d["cancels"] += 1
            d["billed"] += billed
            if status not in ("trial / free", "trial"):
                d["missed"] += missed

    if not rows:
        print("No lessons found.")
        return 1 if problems else 0

    cur = (" " + a.currency) if a.currency else ""
    head = ("Month", "Student", "Taught", "Late+NoShow", "Billed", "Income missed")
    table = [head]
    for (month, student), d in sorted(rows.items()):
        table.append((month, student, str(d["taught"]), str(d["cancels"]),
                      "%s%s" % (money(d["billed"]), cur), "%s%s" % (money(d["missed"]), cur)))
    w = [max(len(r[i]) for r in table) for i in range(len(head))]
    for i, r in enumerate(table):
        print("  ".join(c.ljust(w[j]) if j < 2 else c.rjust(w[j]) for j, c in enumerate(r)))
        if i == 0:
            print("  ".join("-" * x for x in w))
    total = sum((d["billed"] for d in rows.values()), Decimal("0"))
    print("\nTotal billed: %s%s" % (money(total), cur))

    if a.out:
        out = Path(a.out)
        if out.exists():
            sys.exit("refusing to overwrite existing file: %s" % out)
        with out.open("x", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(head)
            wr.writerows(table[1:])
        print("Written: %s" % out)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
