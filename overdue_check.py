#!/usr/bin/env python3
"""overdue_check.py - who is behind with payment? Reads an invoices CSV.

CSV columns: invoice,student,issue_date,amount,paid   (paid may be empty = 0)

Prints every invoice with an open balance, sorted by days overdue, with a
suggested tone for the reminder. Read-only: standard library only, no network,
no files are written or changed.

Example:
    python overdue_check.py invoices.csv --terms 14 --today 2026-10-12
"""
import argparse
import csv
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path


def parse_date(text):
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError("unknown date format: %r (use YYYY-MM-DD)" % text)


def tone(days):
    if days <= 0:
        return "not due yet"
    if days < 10:
        return "friendly reminder"
    if days < 21:
        return "second reminder"
    return "clear final reminder"


def main(argv=None):
    p = argparse.ArgumentParser(description="List open and overdue invoices from a CSV.")
    p.add_argument("csv_file")
    p.add_argument("--terms", type=int, default=14, help="payment terms in days after issue date (default 14)")
    p.add_argument("--today", help="pretend today is YYYY-MM-DD (default: real date)")
    a = p.parse_args(argv)

    path = Path(a.csv_file)
    if not path.is_file():
        sys.exit("file not found: %s" % path)
    today = parse_date(a.today) if a.today else date.today()

    out, problems = [], 0
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        need = {"invoice", "student", "issue_date", "amount"}
        if not reader.fieldnames or not need.issubset({f.strip().lower() for f in reader.fieldnames}):
            sys.exit("CSV needs the columns: invoice,student,issue_date,amount,paid")
        for n, raw in enumerate(reader, start=2):
            r = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            if not any(r.values()):
                continue
            try:
                due = parse_date(r["issue_date"]) + timedelta(days=a.terms)
                amount = Decimal(r["amount"])
                paid = Decimal(r.get("paid") or "0")
            except Exception as exc:
                print("line %d skipped: %s" % (n, exc), file=sys.stderr)
                problems += 1
                continue
            bal = amount - paid
            if bal > Decimal("0.004"):
                out.append(((today - due).days, r["invoice"], r["student"], due, bal))

    if not out:
        print("Nothing open. All invoices are paid.")
        return 1 if problems else 0

    out.sort(key=lambda x: (-x[0], x[1]))
    print("As of %s (terms: %d days)\n" % (today.isoformat(), a.terms))
    print("%-16s %-18s %-11s %10s %8s  %s" % ("Invoice", "Student", "Due", "Balance", "Overdue", "Suggested"))
    for days, inv, stu, due, bal in out:
        print("%-16s %-18s %-11s %10s %8s  %s" % (inv, stu, due.isoformat(), "%.2f" % bal,
                                                  ("%dd" % days) if days > 0 else "-", tone(days)))
    over = sum((o[4] for o in out if o[0] > 0), Decimal("0"))
    print("\nWaiting: %.2f   of which overdue: %.2f" % (sum((o[4] for o in out), Decimal("0")), over))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
