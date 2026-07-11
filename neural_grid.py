"""
Neural Network Awakening — GitHub Contribution Grid Animator
--------------------------------------------------------------
Turns your GitHub contribution grid into a neural network. A pulse
starts from one corner and fires through synapse-like connections to
every active (contributed) cell, lighting each one up like a neuron
activating, with a glow trail along each synapse. Once the whole
network is "awake" it settles back into your real GitHub green
palette, holds, dims back down, and loops.

Usage:
    GH_USERNAME=<you> GITHUB_TOKEN=<token with read:user> python3 neural_grid.py

If GH_USERNAME/GITHUB_TOKEN are not set, a deterministic synthetic demo
grid is used instead (handy for local previews).
"""

import os
import sys
import json
import math
import random
import urllib.request
from collections import deque

COLS = 52
ROWS = 7
LOOP_SECONDS = 10
K_NEAREST = 2            # synapses per neuron to its nearest active neighbors
MAX_SYNAPSE_DIST = 6.5     # max grid distance for a synapse to form

LEVELS_LIGHT = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
LEVELS_DARK = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
IDLE_LIGHT = "#ebedf0"
IDLE_DARK = "#161b22"
PULSE_COLOR_LIGHT = "#ffffff"
PULSE_COLOR_DARK = "#eafcff"
GLOW_COLOR = "#4fd1ff"     # cyan-blue flash / synapse glow

GITHUB_GRAPHQL = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""

LEVEL_MAP = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def fetch_contribution_levels(username, token):
    req = urllib.request.Request(
        GITHUB_GRAPHQL,
        data=json.dumps({"query": QUERY, "variables": {"login": username}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "neural-contribution-grid",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    grid = [[0] * len(weeks) for _ in range(ROWS)]
    for col, week in enumerate(weeks):
        for row, day in enumerate(week["contributionDays"]):
            grid[row][col] = LEVEL_MAP.get(day["contributionLevel"], 0)
    return grid


def synthetic_demo_grid(seed=42):
    rng = random.Random(seed)
    grid = [[0] * COLS for _ in range(ROWS)]
    for r in range(ROWS):
        for c in range(COLS):
            if rng.random() > 0.72:
                grid[r][c] = rng.choice([1, 1, 2, 2, 3, 4])
    return grid


def build_graph(active_nodes):
    """Connect each active node to its K nearest active neighbors within range."""
    edges = set()
    for a in active_nodes:
        dists = []
        for b in active_nodes:
            if a == b:
                continue
            d = math.hypot(a[0] - b[0], a[1] - b[1])
            if d <= MAX_SYNAPSE_DIST:
                dists.append((d, b))
        dists.sort(key=lambda x: x[0])
        for _, b in dists[:K_NEAREST]:
            edge = tuple(sorted([a, b]))
            edges.add(edge)
    adj = {n: [] for n in active_nodes}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return edges, adj


def bfs_wave(active_nodes, adj):
    """BFS from the top-left-most active node; chain through disconnected
    components so the whole network fires in one continuous sweep."""
    depth = {}
    remaining = set(active_nodes)
    ordered = sorted(active_nodes, key=lambda n: (n[1], n[0]))  # reading order
    depth_offset = 0
    while remaining:
        start = next(n for n in ordered if n in remaining)
        q = deque([start])
        depth[start] = depth_offset
        remaining.discard(start)
        local_max = depth_offset
        while q:
            cur = q.popleft()
            for nxt in adj.get(cur, []):
                if nxt in remaining:
                    depth[nxt] = depth[cur] + 1
                    local_max = max(local_max, depth[nxt])
                    remaining.discard(nxt)
                    q.append(nxt)
        depth_offset = local_max + 1
    return depth


def build_svg(levels_grid, dark=False):
    cell = 11
    gap = 3
    pitch = cell + gap
    pad = 12
    width = pad * 2 + COLS * pitch - gap
    height = pad * 2 + ROWS * pitch - gap

    idle_color = IDLE_DARK if dark else IDLE_LIGHT
    pulse_color = PULSE_COLOR_DARK if dark else PULSE_COLOR_LIGHT
    levels_palette = LEVELS_DARK if dark else LEVELS_LIGHT
    bg = "#0d1117" if dark else "#ffffff"

    active_nodes = [(r, c) for r in range(ROWS) for c in range(COLS) if levels_grid[r][c] > 0]
    edges, adj = build_graph(active_nodes)
    depth = bfs_wave(active_nodes, adj)
    max_depth = max(depth.values()) if depth else 1

    IDLE_END = 5
    FIRE_START = 6
    FIRE_END = 78
    HOLD_END = 92
    LOOP_END = 100

    def fire_pct(d):
        if max_depth == 0:
            return FIRE_START
        return FIRE_START + (FIRE_END - FIRE_START) * (d / max_depth)

    def cx(node):
        r, c = node
        return pad + c * pitch + cell / 2

    def cy(node):
        r, c = node
        return pad + r * pitch + cell / 2

    keyframes = []
    rects = []
    lines = []

    for r in range(ROWS):
        for c in range(COLS):
            if levels_grid[r][c] == 0:
                x = pad + c * pitch
                y = pad + r * pitch
                rects.append(
                    f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" ry="2" fill="{idle_color}" />'
                )

    for i, (a, b) in enumerate(sorted(edges)):
        name = f"syn{i}"
        t = fire_pct(min(depth[a], depth[b]))
        t2 = min(t + 3, FIRE_END)
        stops = [
            (0, idle_color, 0.12),
            (max(0, t - 0.5), idle_color, 0.12),
            (t, GLOW_COLOR, 1.0),
            (t2, levels_palette[2], 0.35),
            (HOLD_END, levels_palette[2], 0.35),
            (LOOP_END, idle_color, 0.12),
        ]
        kf = f"@keyframes {name} {{\n"
        for pct, col, op in stops:
            kf += f"  {pct:.3f}% {{ stroke: {col}; opacity: {op}; }}\n"
        kf += "}"
        keyframes.append(kf)
        lines.append(
            f'<line x1="{cx(a):.1f}" y1="{cy(a):.1f}" x2="{cx(b):.1f}" y2="{cy(b):.1f}" '
            f'stroke-width="1" style="animation: {name} {LOOP_SECONDS}s ease-in-out infinite;" />'
        )

    for node in active_nodes:
        r, c = node
        name = f"n{r}_{c}"
        level = levels_grid[r][c]
        settle_color = levels_palette[level]
        x = pad + c * pitch
        y = pad + r * pitch
        t = fire_pct(depth[node])
        t2 = min(t + 2.2, FIRE_END)

        stops = [
            (0, idle_color, 0, 1.0),
            (max(0, t - 0.6), idle_color, 0, 1.0),
            (t, pulse_color, 10, 1.35),
            (t2, settle_color, 4, 1.0),
            (HOLD_END, settle_color, 4, 1.0),
            (LOOP_END, idle_color, 0, 1.0),
        ]
        kf = f"@keyframes {name} {{\n"
        for pct, col, blur, scale in stops:
            kf += (
                f"  {pct:.3f}% {{ fill: {col}; "
                f"filter: drop-shadow(0 0 {blur}px {GLOW_COLOR}); "
                f"transform: scale({scale}); }}\n"
            )
        kf += "}"
        keyframes.append(kf)

        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" ry="2" '
            f'style="animation: {name} {LOOP_SECONDS}s ease-in-out infinite; '
            f'transform-box: fill-box; transform-origin: center;" />'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
<style>
line {{ stroke-linecap: round; }}
{chr(10).join(keyframes)}
</style>
<rect x="0" y="0" width="{width}" height="{height}" fill="{bg}" />
{chr(10).join(lines)}
{chr(10).join(rects)}
</svg>"""
    return svg

import os

def main():
    username = os.environ.get("GH_USERNAME")
    token = os.environ.get("GITHUB_TOKEN")

    print(username, token)

    if username and token:
        levels_grid = fetch_contribution_levels(username, token)
    else:
        print("No GH_USERNAME/GITHUB_TOKEN found - generating synthetic demo grid.", file=sys.stderr)
        levels_grid = synthetic_demo_grid()

    out_dir = "dist"
    os.makedirs(out_dir, exist_ok=True)

    light_svg = build_svg(levels_grid, dark=False)
    dark_svg = build_svg(levels_grid, dark=True)

    with open(os.path.join(out_dir, "neural-grid-light.svg"), "w") as f:
        f.write(light_svg)
    with open(os.path.join(out_dir, "neural-grid-dark.svg"), "w") as f:
        f.write(dark_svg)

    print("Wrote dist/neural-grid-light.svg and dist/neural-grid-dark.svg")


if __name__ == "__main__":
    main()
