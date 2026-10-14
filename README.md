# Tutor Lesson Log Lite

**Two tiny offline scripts that show private tutors what their cancellations cost and who is behind with payment.**

## What it does

- `lesson_summary.py` – reads a plain CSV lesson log and prints, per month and student: lessons taught, late cancels + no-shows, amount billed under *your* cancellation policy, and income missed.
- `overdue_check.py` – reads a plain CSV invoice list and shows every open invoice, sorted by days overdue, with a suggested reminder tone (friendly / second / clear).

Both scripts use only the Python standard library, never touch the network and never change your input files. `lesson_summary.py` writes a file only if you pass `--out`, and it refuses to overwrite an existing file.

Use first names or initials of the adult student or payer. No data about children is needed.

## Quick start

```bash
python lesson_summary.py lessons.sample.csv --rate 45 --student-rate "Tom H.=38" --late-pct 50 --currency EUR
python overdue_check.py invoices.sample.csv --terms 14 --today 2026-10-12
```

Lesson CSV columns: `date,student,minutes,status,note`
Statuses: `Taught`, `Late cancel`, `No-show`, `Cancelled in time`, `Teacher cancelled`, `Trial / free`.

Invoice CSV columns: `invoice,student,issue_date,amount,paid` (`paid` can be empty). Dates: `YYYY-MM-DD`.

Useful options: `--month 2026-09` (one month only), `--out summary.csv` (save a new file), `--noshow-pct 100`.

## Requirements

- Python 3.8 or newer. No packages to install.
- Works on Windows, macOS and Linux.

## Notes

The scripts are organising aids for your own records. They do not replace a tax professional, accountant or lawyer.

Created with AI assistance by an automated system.

## Licence

MIT – see `LICENSE`.

## Full version

This lite version is two command-line scripts. The full **Lessons Taught, Lessons Paid** kit is a ready-made Excel workbook that adds:

- a Dashboard with waiting / overdue money, income earned but not yet invoiced, and a 6-month chart
- linked sheets for lessons, invoices, part payments and students, with drop-downs and checks
- a one-page printable invoice for any invoice number
- a Rate Check sheet that estimates the extra income from a new rate
- ready-to-adapt messages: reminders, a lesson policy for new students, a late-cancellation reply, a rate-increase note
- sample data and a blank copy

Details: https://kontor7-agent.github.io/p/lessons-taught-lessons-paid-lesson-log-invoice-t?s=github
