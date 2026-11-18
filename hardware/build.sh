#!/bin/sh
# Regenerate both sensor boards from the scripts and export the review and
# ordering files.  Needs KiCad 9 (kicad-cli and the pcbnew Python module).
#   ./build.sh           regenerate schematics, boards and exports
#   ./build.sh export    only redo the exports from the files as they are
set -e
cd "$(dirname "$0")"
case "$1" in ""|export) ;; *) echo "usage: $0 [export]" >&2; exit 2 ;; esac
for v in ch32v003 ch32v005; do
    p=sensor-$v/sensor-$v
    out=sensor-$v/out
    if [ "$1" != export ]; then
        python3 scripts/gen_sch.py $v $p.kicad_sch
        python3 scripts/gen_pcb.py $v sensor-$v --route
    fi
    mkdir -p $out
    kicad-cli sch erc --severity-all --exit-code-violations -o $out/erc.rpt $p.kicad_sch
    kicad-cli pcb drc --schematic-parity --severity-all --exit-code-violations -o $out/drc.rpt $p.kicad_pcb
    kicad-cli sch export pdf -o $out/schematic.pdf $p.kicad_sch
    kicad-cli sch export bom --exclude-dnp --fields 'Value,Reference,Footprint,LCSC,${QUANTITY}' \
        --labels 'Comment,Designator,Footprint,LCSC,Qty' --group-by 'Value,Footprint,LCSC' -o $out/bom-jlc.csv $p.kicad_sch
    kicad-cli pcb export pos --format csv --units mm --side front --exclude-dnp -o $out/cpl-jlc.csv $p.kicad_pcb
    sed -i '1s/.*/Designator,Val,Package,Mid X,Mid Y,Rotation,Layer/' $out/cpl-jlc.csv
    kicad-cli pcb render --side top --width 2000 --height 800 --zoom 2.4 -o $out/board-top.png $p.kicad_pcb
    kicad-cli pcb render --side bottom --width 2000 --height 800 --zoom 2.4 -o $out/board-bottom.png $p.kicad_pcb
    kicad-cli pcb export gerbers --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,F.SilkS,B.SilkS,Edge.Cuts -o $out/gerbers/ $p.kicad_pcb
    kicad-cli pcb export drill --excellon-separate-th -o $out/gerbers/ $p.kicad_pcb
done
