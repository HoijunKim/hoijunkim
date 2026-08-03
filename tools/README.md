# tools

Asset pipeline for the profile artwork.

```sh
python tools/build.py
```

Regenerates `assets/hero.svg` from code. Deterministic (fixed seeds) - same
input, byte-identical output. The SVG is self-contained and animates with pure
SMIL / CSS (no JavaScript, no external references), which is what lets it
animate when GitHub serves it through its image proxy.

Edit colors, text, or waveforms at the top of `build.py`, re-run, and commit
the regenerated `assets/`.

- `hero.svg` - EMG oscilloscope: 3 forearm EMG channels (FDS / EDC / APB) + a
  video pose channel, a sweeping scan bar, and a prosthetic gripper that flexes
  on each burst (muscle signal -> motion).

Two rules keep the artwork honest:

- **Only identity goes in the picture.** Lists and tables (the stack, the
  project index) live in markdown, where they stay selectable, searchable, and
  theme-aware. A previous `stack.svg` drew the stack as a probe bank; it was a
  table pretending to be an image and was dropped.
- **Size for the real column.** The README renders at roughly 780px wide, so an
  SVG is scaled by `780 / viewBox width`. Keep design font sizes above
  `11 * (viewBox width / 780)` or the labels turn into texture.

Preview locally by opening the SVG in a browser (animations play), or render a
still frame with headless Chrome.
