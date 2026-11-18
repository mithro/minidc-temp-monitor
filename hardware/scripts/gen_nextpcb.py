#!/usr/bin/env python3
"""Write the files NextPCB's assembly quote page takes, from the JLC outputs.

NextPCB matches parts by manufacturer part number, wants one board's parts
list (it multiplies by the board count itself) and takes the placement file
only as a spreadsheet. For each board this writes, in sensor-*/out/nextpcb/:
  bom.xlsx       one board's parts, in NextPCB's template columns
  centroid.xlsx  the panel placement file (out/panel/cpl-jlc.csv) as a sheet
The panel gerbers are uploaded as they are (out/panel/gerbers.zip).
Needs openpyxl.
"""
import csv
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent.parent

# LCSC number: manufacturer part number, as listed in the JLCPCB catalogue
MPN = {
    'C5346354': 'CH32V003J4M6',
    'C49006243': 'CH32V005D6U6',
    'C7430446': 'ZX-SH1.0-4PWT',
    'C6807762': 'SDNT1005X104F3950FTF',
    'C52923': 'CL05A105KA5NQNC',
    'C1525': 'CL05B104KO5NNNC',
    'C2286': 'KT-0603R',
    'C25741': '0402WGF1003TCE',
    'C11702': '0402WGF1001TCE',
    'C23162': '0603WAF4701T5E',
}


def write(name):
    out = HERE / name / 'out'
    (out / 'nextpcb').mkdir(exist_ok=True)

    parts = {}                          # one part can span several BOM rows
    with open(out / 'bom-jlc.csv') as f:
        for r in csv.DictReader(f):
            refs, _ = parts.setdefault(r['LCSC'], ([], r['Comment']))
            refs += r['Designator'].split(',')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['S/N', 'Designator', 'Quantity', 'Manufacturer Part Number',
               'Procurement Type', 'Customer Note'])
    for n, (lcsc, (refs, comment)) in enumerate(parts.items(), 1):
        ws.append([n, ','.join(refs), len(refs), MPN[lcsc], '', comment])
    wb.save(out / 'nextpcb' / 'bom.xlsx')

    wb = openpyxl.Workbook()
    ws = wb.active
    with open(out / 'panel' / 'cpl-jlc.csv') as f:
        rows = csv.reader(f)
        ws.append(next(rows))
        for r in rows:
            ws.append(r[:3] + [float(x) for x in r[3:6]] + r[6:])
    wb.save(out / 'nextpcb' / 'centroid.xlsx')


if __name__ == '__main__':
    for board in ('sensor-ch32v003', 'sensor-ch32v005'):
        write(board)
