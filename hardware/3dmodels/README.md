# 3D models

The few models the renders need, so `kicad-cli pcb render` works without
KiCad's full model library.

- `*.step` are copied unchanged from the KiCad packages3D library (tag 9.0.6),
  licensed CC-BY-SA 4.0 with the KiCad library exception. Each file carries its
  own notice.
- `*.wrl` are simple block models written by `../scripts/gen_models.py`, for
  the two packages the KiCad library has no model for.
