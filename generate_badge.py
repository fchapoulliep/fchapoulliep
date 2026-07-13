#!/usr/bin/env python3
"""
Generates a GitHub-readme-stats-style SVG badge from Root-Me profile data,
using the OFFICIAL Root-Me API (https://api.www.root-me.org/).

Requirements:
    - A Root-Me API key, generated from https://www.root-me.org/?page=preferences
      Passed via the ROOTME_API_KEY environment variable (set as a GitHub secret).
    - Your Root-Me numeric id_auteur, passed via ROOTME_ID env var
      (found in your profile URL, e.g. root-me.org/fchapoul-12345 -> 12345)

Usage:
    ROOTME_API_KEY=xxx ROOTME_ID=12345 python3 generate_badge.py
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.www.root-me.org"


def fetch_profile(user_id: str, api_key: str) -> dict:
    """Call the official /auteurs/<id> endpoint."""
    resp = requests.get(
        f"{API_BASE}/auteurs/{user_id}",
        cookies={"api_key": api_key},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Root-Me API error: HTTP {resp.status_code}")
    return resp.json()


ICONS = {
    "score": '<path d="M12 2l2.9 6.26L22 9.27l-5 4.87L18.18 21 12 17.27 5.82 21 7 14.14l-5-4.87 7.1-1.01L12 2z"/>',
    "position": '<path d="M4 21V10M10 21V4M16 21v-7M22 21H2"/>',
    "validated": '<path d="M20 6L9 17l-5-5"/>',
    "rang": '<path d="M12 15a6 6 0 100-12 6 6 0 000 12z"/><path d="M8.5 14L7 22l5-3 5 3-1.5-8"/>',
}


def build_svg(
    nom: str, score: str, position: str, nb_challenges: int, rang: str = ""
) -> str:
    """Render a polished, github-readme-stats-inspired dark SVG card."""

    width = 460

    stats = [
        ("score", "Score", f"{score} pts"),
        ("position", "Rank", f"#{position}"),
        ("validated", "Challenges solved", str(nb_challenges)),
    ]
    if rang:
        stats.append(("rang", "Title", rang.capitalize()))

    header_h = 64
    row_h = 40
    pad_bottom = 22
    height = header_h + row_h * len(stats) + pad_bottom

    rows_svg = ""
    for i, (key, label, value) in enumerate(stats):
        y = header_h + i * row_h + row_h / 2
        sep = (
            f'<line x1="26" y1="{header_h + (i + 1) * row_h}" '
            f'x2="{width - 26}" y2="{header_h + (i + 1) * row_h}" stroke="#21262d" stroke-width="1"/>'
            if i < len(stats) - 1
            else ""
        )
        rows_svg += f"""
    <g transform="translate(0,{y})">
      <g transform="translate(30,-9) scale(0.75)" stroke="#3ddc97" stroke-width="2" fill="none"
         stroke-linecap="round" stroke-linejoin="round">
        {ICONS[key]}
      </g>
      <text x="60" y="5" class="stat-label">{label}</text>
      <rect x="{width - 130}" y="-14" width="104" height="28" rx="14" class="pill"/>
      <text x="{width - 78}" y="5" class="stat-value" text-anchor="middle">{value}</text>
    </g>
    {sep}"""

    svg = f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Root-Me stats for {nom}">
  <style>
    .bg {{ fill:#0d1117; }}
    .border {{ fill:none; stroke:#21262d; stroke-width:1; }}
    .accent {{ fill:#3ddc97; }}
    .brand {{ font: 600 13px 'Segoe UI', Ubuntu, Sans-Serif; letter-spacing: 1.5px; fill:#3ddc97; }}
    .username {{ font: 600 20px 'Segoe UI', Ubuntu, Sans-Serif; fill:#e6edf3; }}
    .stat-label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill:#8b949e; }}
    .stat-value {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill:#e6edf3; }}
    .pill {{ fill:#161b22; stroke:#30363d; stroke-width:1; }}
  </style>

  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" class="bg border"/>
  <rect x="0.5" y="0.5" width="6" height="{height - 1}" rx="3" class="accent"/>

  <text x="30" y="28" class="brand">ROOT-ME</text>
  <text x="30" y="52" class="username">{nom}</text>

  <line x1="26" y1="{header_h}" x2="{width - 26}" y2="{header_h}" stroke="#21262d" stroke-width="1"/>

  {rows_svg}
</svg>"""
    return svg


def main():
    api_key = os.environ.get("ROOTME_API_KEY")
    user_id = os.environ.get("ROOTME_ID")
    out_path = os.environ.get("OUT_PATH", "rootme-badge.svg")

    if not api_key or not user_id:
        print(
            "ERROR: ROOTME_API_KEY and ROOTME_ID env vars are required.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        data = fetch_profile(user_id, api_key)
    except Exception as exc:
        print(f"ERROR fetching Root-Me profile: {exc}", file=sys.stderr)
        sys.exit(1)

    nom = data.get("nom", "unknown")
    score = data.get("score", "?")
    position = data.get("position", "?")
    validations = data.get("validations", [])
    if isinstance(validations, (list, dict)):
        nb_challenges = len(validations)
    else:
        nb_challenges = 0

    rang = data.get("rang", "")

    svg = build_svg(nom, score, position, nb_challenges, rang)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(
        f"Badge written to {out_path} ({nom}, score={score}, position=#{position}, rang={rang}, validations={nb_challenges})"
    )


if __name__ == "__main__":
    main()
