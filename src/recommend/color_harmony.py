"""
StyleMind — color harmony scoring.

Scores how well two garments' dominant colors pair together, using
hue relationships on the color wheel (complementary/analogous/triadic).
Neutrals (black/white/grey) are treated as compatible with anything,
since hue comparison is meaningless for them.
"""

import colorsys

NEUTRAL_SATURATION_THRESHOLD = 0.15  # below this, treat as neutral regardless of hue
NEUTRAL_LIGHTNESS_HIGH = 0.90        # near-white
NEUTRAL_LIGHTNESS_LOW = 0.10         # near-black


def hex_to_hsl(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = [int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l  # hue in degrees, saturation, lightness


def is_neutral(hex_color):
    _, s, l = hex_to_hsl(hex_color)
    return s < NEUTRAL_SATURATION_THRESHOLD or l > NEUTRAL_LIGHTNESS_HIGH or l < NEUTRAL_LIGHTNESS_LOW


def hue_distance(h1, h2):
    """Shortest distance between two hues on a 360-degree wheel."""
    diff = abs(h1 - h2) % 360
    return min(diff, 360 - diff)


def score_hue_pair(h1, h2):
    """
    Scores two hues based on classic color-wheel relationships.
    Returns 0-1, higher = more harmonious.
      - Complementary (~180 deg apart): high score
      - Triadic (~120 deg apart): high score
      - Analogous (~0-30 deg apart): high score
      - Everything else: scaled down
    """
    dist = hue_distance(h1, h2)

    if dist <= 30:          # analogous / near-identical
        return 1.0 - (dist / 30) * 0.2       # 1.0 -> 0.8
    if 150 <= dist <= 180:  # complementary
        return 1.0 - abs(dist - 180) / 30 * 0.2
    if 105 <= dist <= 135:  # triadic
        return 0.85 - abs(dist - 120) / 15 * 0.15
    # awkward in-between hues (e.g. ~60-90 deg apart)
    return 0.4


def score_color_pair(hex1, hex2):
    """
    Main entry point. Scores one color from item A against one color
    from item B. Returns 0-1, higher = more harmonious.
    """
    if is_neutral(hex1) or is_neutral(hex2):
        return 0.9  # neutrals pair well with almost anything

    h1, _, _ = hex_to_hsl(hex1)
    h2, _, _ = hex_to_hsl(hex2)
    return score_hue_pair(h1, h2)


def score_item_pair(colors_a, colors_b):
    """
    Scores two items' full dominant_colors lists (each a list of hex
    strings) against each other. Uses the BEST-scoring pair of colors
    across both lists -- i.e. if any color from item A harmonizes well
    with any color from item B, that's the pairing score, since a
    dominant_colors list contains the item's main colors and only one
    strong match is needed to call the pairing harmonious.
    """
    best = 0.0
    for ca in colors_a:
        for cb in colors_b:
            s = score_color_pair(ca, cb)
            if s > best:
                best = s
    return round(best, 4)