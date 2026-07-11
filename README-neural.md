# neural-network-contribution-grid

Turns your GitHub contribution graph into a neural network. A pulse
starts from one corner and fires through synapse-like connections to
every contribution cell, lighting each one up like a neuron activating.
Once fully "awake" it settles into your real GitHub green colors, holds,
dims back down, and loops.

## Setup (in your existing BhaviBanga repo)

Since you already have `GH_PAT` set up from the Game of Life version,
you just need to add the new script + workflow:

1. Copy `neural_grid.py` into the repo root (alongside `life_grid.py` —
   you can keep both, they don't conflict).
2. Copy `neural-network.yml` into `.github/workflows/`.
3. Push to `main`. The existing `GH_PAT` secret will work for this too.
4. Check the **Actions** tab — once green, switch to the `output`
   branch and confirm `neural-grid-light.svg` / `neural-grid-dark.svg`
   are there.

## Embed in your profile README

```md
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/BhavneeshBanga/BhaviBanga/output/neural-grid-dark.svg" />
  <img alt="neural network contribution grid" src="https://raw.githubusercontent.com/BhavneeshBanga/BhaviBanga/output/neural-grid-light.svg" />
</picture>
```

You can put both animations in the same README, one above the other,
or swap between them — they read from the same `output` branch.

## Tuning

Open `neural_grid.py` and adjust:
- `K_NEAREST` / `MAX_SYNAPSE_DIST` — how densely connected the network looks
- `LOOP_SECONDS` — total loop duration (default 10s)
- `GLOW_COLOR` — the pulse/synapse color, if cyan-blue isn't your thing
