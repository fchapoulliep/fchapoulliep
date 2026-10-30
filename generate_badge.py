#!/usr/bin/env python3
"""
Generates the Root-Me stats card of my GitHub profile, from the OFFICIAL
Root-Me API (https://api.www.root-me.org/).

The card follows my personal design system: monochrome with no accent color,
Comfortaa for the name, Nunito for the figures, Lucide icons and the FC
monogram as a watermark. It is written once per GitHub theme
(rootme-badge-dark.svg and rootme-badge-light.svg), and the profile README
picks the right one with a <picture> element.

GitHub shows README images through an <img> tag, where an SVG cannot load
anything external: both fonts are embedded as base64 from fonts/ (Latin
subsets from Fontsource, SIL Open Font License).

Requirements:
    - A Root-Me API key, generated from https://www.root-me.org/?page=preferences
      Passed via the ROOTME_API_KEY environment variable (set as a GitHub secret).
    - Your Root-Me numeric id_auteur, passed via ROOTME_ID env var
      (found in your profile URL, e.g. root-me.org/fchapoul-12345 -> 12345)

Usage:
    ROOTME_API_KEY=xxx ROOTME_ID=12345 python3 generate_badge.py
    python3 generate_badge.py --demo    # sample data into demo/, no API call
"""

import base64
import os
import sys
from html import escape
from pathlib import Path

API_BASE = "https://api.www.root-me.org"
FONTS_DIR = Path(__file__).resolve().parent / "fonts"

DEMO_PROFILE = {
    "nom": "fchapoul",
    "score": "670",
    "position": 25834,
    "rang": "trainee",
    "validations": [{}] * 50,
}

# Design system tokens (card, border, border-strong, foreground,
# muted-foreground), one set per GitHub theme.
THEMES = {
    "dark": {
        "card": "#1a1a1a",
        "border": "#2a2a2a",
        "border_strong": "#3a3a3a",
        "ink": "#f5f5f5",
        "muted": "#a3a3a3",
    },
    "light": {
        "card": "#ffffff",
        "border": "#e6e6e6",
        "border_strong": "#d4d4d4",
        "ink": "#171717",
        "muted": "#666666",
    },
}
WATERMARK_OPACITY = 0.05

# Lucide icons (lucide-static 1.65.0, ISC license), on a 24 x 24 grid.
ICONS = {
    "trophy": (
        '<path d="M10 14.66V17a1 1 0 0 1-1 1 2 2 0 0 0-2 2v2"/>'
        '<path d="M14 14.66V17a1 1 0 0 0 1 1 2 2 0 0 1 2 2v2"/>'
        '<path d="M17.916 10H19.5A2.5 2.5 0 0 0 22 7.5V5a1 1 0 0 0-1-1h-3"/>'
        '<path d="M4 22h16"/>'
        '<path d="M6 9a6 6 0 0 0 12 0V3a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1z"/>'
        '<path d="M6.084 10H4.5A2.5 2.5 0 0 1 2 7.5V5a1 1 0 0 1 1-1h3"/>'
    ),
    "globe": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>'
        '<path d="M2 12h20"/>'
    ),
    "flag": (
        '<path d="M4 22V4a1 1 0 0 1 .4-.8A6 6 0 0 1 8 2c3 0 5 2 7.333 2q2 0 3.067-.8'
        'A1 1 0 0 1 20 4v10a1 1 0 0 1-.4.8A6 6 0 0 1 16 16c-3 0-5-2-8-2a6 6 0 0 0-4 1.528"/>'
    ),
}

# The FC monogram (the stroked "Reference"), and the box it is drawn in.
MONOGRAM_PATH = (
    "M 102.30 31.86 A 50 50 0 1 0 102.30 96.14 M 50 50 V 92 M 50 50 H 112 M 50 70 H 84"
)
MONOGRAM_BOX = (10, 10, 106, 108)  # x, y, width, height


def fetch_profile(user_id: str, api_key: str) -> dict:
    """Call the official /auteurs/<id> endpoint."""
    import requests

    resp = requests.get(
        f"{API_BASE}/auteurs/{user_id}",
        cookies={"api_key": api_key},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Root-Me API error: HTTP {resp.status_code}")
    return resp.json()


def font_faces() -> str:
    """Embed the two fonts, since an SVG shown through <img> loads nothing external."""
    faces = ""
    for family, weight, file in (
        ("Comfortaa", 700, "comfortaa-latin-700-normal.woff2"),
        ("Nunito", 600, "nunito-latin-600-normal.woff2"),
    ):
        data = base64.b64encode((FONTS_DIR / file).read_bytes()).decode("ascii")
        faces += (
            f"    @font-face {{ font-family:'{family}'; font-weight:{weight}; "
            f"src:url(data:font/woff2;base64,{data}) format('woff2'); }}\n"
        )
    return faces


def format_number(value) -> str:
    """25834 -> '25,834'; anything that is not a number is kept as is."""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def build_svg(
    theme: str, nom: str, score: str, position: str, nb_challenges: int, rang: str = ""
) -> str:
    """Render the card for one theme ("dark" or "light")."""

    c = THEMES[theme]
    width, height, pad = 495, 184, 28

    stats = [
        ("trophy", "Points", "", format_number(score)),
        ("globe", "Global rank", "#", format_number(position)),
        ("flag", "Challenges solved", "", str(nb_challenges)),
    ]

    # Three columns under the name, split by thin vertical rules.
    col_w = (width - 2 * pad) / 3
    columns_svg = ""
    for i, (icon, label, prefix, value) in enumerate(stats):
        x = pad + i * col_w
        if i:
            columns_svg += (
                f'\n  <line x1="{x - 18:.1f}" y1="112" x2="{x - 18:.1f}" y2="160" class="rule"/>'
            )
        prefix_svg = f'<tspan class="dim">{prefix}</tspan>' if prefix else ""
        columns_svg += f"""
  <g class="rise" style="animation-delay:{120 + i * 80}ms">
    <g transform="translate({x:.1f},112) scale({16 / 24:.4f})" class="icon">{ICONS[icon]}</g>
    <text x="{x + 22:.1f}" y="124.5" class="label">{label}</text>
    <text x="{x:.1f}" y="158" class="value">{prefix_svg}{escape(value)}</text>
  </g>"""

    # The Root-Me title as a pill, right-aligned on the name's line. Its width
    # follows the text length (Nunito 600 at 12 px is about 7 px per letter).
    pill_svg = ""
    if rang:
        pill_w = 26 + 7 * len(rang)
        pill_x = width - pad - pill_w
        pill_svg = f"""
    <rect x="{pill_x}" y="51" width="{pill_w}" height="26" rx="13" class="pill"/>
    <text x="{pill_x + pill_w / 2}" y="68.2" class="pill-text" text-anchor="middle">{escape(rang.capitalize())}</text>"""

    # The watermark: the monogram at 120 % of the card height, overflowing on
    # the right, painted in one piece (opacity on the group, not the stroke).
    bx, by, bw, bh = MONOGRAM_BOX
    scale = height * 1.2 / bh
    wm_x = width - bw * scale * 0.72 - bx * scale
    wm_y = (height - bh * scale) / 2 - by * scale

    summary = (
        f"Root-Me stats for {nom}: {format_number(score)} points, "
        f"global rank #{format_number(position)}, {nb_challenges} challenges solved"
    )

    return f"""<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(summary)}">
  <title>{escape(summary)}</title>
  <style>
{font_faces()}    .card {{ fill:{c["card"]}; stroke:{c["border"]}; stroke-width:1; }}
    .rule {{ stroke:{c["border"]}; stroke-width:1; }}
    .brand {{ font:600 12px 'Nunito', ui-rounded, system-ui, sans-serif; letter-spacing:1.68px; fill:{c["muted"]}; }}
    .name {{ font:700 24px 'Comfortaa', ui-rounded, system-ui, sans-serif; letter-spacing:-0.48px; fill:{c["ink"]}; }}
    .pill {{ fill:none; stroke:{c["border_strong"]}; stroke-width:1; }}
    .pill-text, .label {{ font:600 12px 'Nunito', ui-rounded, system-ui, sans-serif; fill:{c["muted"]}; }}
    .value {{ font:600 28px 'Nunito', ui-rounded, system-ui, sans-serif; font-variant-numeric:tabular-nums; fill:{c["ink"]}; }}
    .dim {{ fill:{c["muted"]}; }}
    .icon {{ fill:none; stroke:{c["muted"]}; stroke-width:1.75; stroke-linecap:round; stroke-linejoin:round; }}
    .rise {{ animation:rise 400ms cubic-bezier(0.2, 0, 0, 1) backwards; }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(8px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .rise {{ animation:none; }} }}
  </style>
  <clipPath id="card-shape">
    <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12"/>
  </clipPath>

  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" class="card"/>
  <g clip-path="url(#card-shape)" aria-hidden="true">
    <g opacity="{WATERMARK_OPACITY}" transform="translate({wm_x:.1f},{wm_y:.1f}) scale({scale:.4f})">
      <path d="{MONOGRAM_PATH}" fill="none" stroke="{c["ink"]}" stroke-width="7"
            stroke-linecap="round" stroke-linejoin="round"/>
    </g>
  </g>

  <g class="rise">
    <text x="{pad}" y="38" class="brand">ROOT-ME</text>
    <text x="{pad}" y="72" class="name">{escape(nom)}</text>{pill_svg}
  </g>
  <line x1="{pad}" y1="94" x2="{width - pad}" y2="94" class="rule"/>
{columns_svg}
</svg>
"""


def main():
    demo = "--demo" in sys.argv[1:]

    if demo:
        data = DEMO_PROFILE
        out_dir = Path(os.environ.get("OUT_DIR", "demo"))
    else:
        from dotenv import load_dotenv

        load_dotenv()
        api_key = os.environ.get("ROOTME_API_KEY")
        user_id = os.environ.get("ROOTME_ID")
        out_dir = Path(os.environ.get("OUT_DIR", "."))

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

    out_dir.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        out_path = out_dir / f"rootme-badge-{theme}.svg"
        out_path.write_text(
            build_svg(theme, nom, score, position, nb_challenges, rang),
            encoding="utf-8",
        )

    print(
        f"Badges written to {out_dir}/rootme-badge-{{dark,light}}.svg "
        f"({nom}, score={score}, position=#{position}, rang={rang}, validations={nb_challenges})"
    )


if __name__ == "__main__":
    main()
