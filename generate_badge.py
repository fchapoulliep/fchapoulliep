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

API_BASE = "https://api.www.root-me.org"

from dotenv import load_dotenv

load_dotenv()

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


def build_svg(nom: str, score: str, position: str, nb_challenges: int, rang: str = "") -> str:
    """Render a dark, github-readme-stats-inspired SVG card."""

    width = 420

    rows = [
        ("Score", f"{score} pts"),
        ("Position", f"#{position}"),
        ("Challenges validés", str(nb_challenges)),
    ]
    if rang:
        rows.append(("Rang", rang.capitalize()))

    row_y_start = 78
    row_gap = 28
    height = row_y_start + row_gap * len(rows) + 20

    row_svg = ""
    for i, (label, value) in enumerate(rows):
        y = row_y_start + i * row_gap
        row_svg += f'''
        <g transform="translate(30,{y})">
            <circle cx="4" cy="-5" r="4" fill="#3ddc97"/>
            <text x="20" y="0" class="stat-label">{label}:</text>
            <text x="260" y="0" class="stat-value" text-anchor="end">{value}</text>
        </g>'''

    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Root-Me stats for {nom}">
  <style>
    .card {{ fill:#0d1117; stroke:#30363d; stroke-width:1; rx:8; }}
    .title {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill:#3ddc97; }}
    .subtitle {{ font: 400 12px 'Segoe UI', Ubuntu, Sans-Serif; fill:#8b949e; }}
    .stat-label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill:#c9d1d9; }}
    .stat-value {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill:#ffffff; }}
  </style>

  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" class="card"/>

  <g transform="translate(30,35)">
    <text class="title">Root-Me Stats</text>
    <text class="subtitle" y="20">{nom}</text>
  </g>

  {row_svg}
</svg>'''
    return svg


def main():
    api_key = os.environ.get("ROOTME_API_KEY")
    user_id = os.environ.get("ROOTME_ID")
    out_path = os.environ.get("OUT_PATH", "rootme-badge.svg")

    if not api_key or not user_id:
        print("ERROR: ROOTME_API_KEY and ROOTME_ID env vars are required.", file=sys.stderr)
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

    print(f"Badge written to {out_path} ({nom}, score={score}, position=#{position}, rang={rang}, validations={nb_challenges})")


if __name__ == "__main__":
    main()