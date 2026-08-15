"""
StyleMind — color harmony scoring.

Scores how well two garments' dominant colors pair together, using two
INDEPENDENT signals for chromatic+chromatic pairs, combined into one score:

  1. Hue relationship (monochromatic/analogous/triadic/complementary)
     — do the two hues sit in a pleasing relationship on the color wheel?
     This is the DOMINANT signal (75% weight) — it's the primary driver
     of what "safe" vs "bold" styling actually means in color theory.
  2. Saturation profile (muted vs vivid)
     — are the colors toned-down or eye-catching? A secondary, reinforcing
     signal (25% weight) that nudges borderline cases without overriding
     a clear hue-based styling identity.

Neutral-involving pairs skip hue/saturation math entirely and use flat,
style-dependent scores.

Style mode ("safe" or "bold") shapes EVERY pairing type:
  - "safe": rewards low-risk, universally appealing combos — neutral+neutral
    scores highest, subtle hue schemas (monochromatic/analogous) and LOW
    saturation are preferred.
  - "bold": rewards high-impact combos — neutral+neutral is deprioritized,
    high-contrast hue schemas (complementary/triadic) and HIGH saturation
    are preferred.

Hue scoring uses smooth interpolation between named schemas rather than a
flat penalty in the "in-between" zones (~45-105 deg, ~135-150 deg) — a pair
just past "analogous" is still reasonably close to analogous-harmonious,
not suddenly clashy.
"""

import colorsys

NEUTRAL_SATURATION_THRESHOLD = 0.15  # below this, treat as neutral regardless of hue
NEUTRAL_LIGHTNESS_HIGH = 0.90        # near-white
NEUTRAL_LIGHTNESS_LOW = 0.10         # near-black

# How much weight the final chromatic+chromatic score gives to hue
# schema vs. saturation profile. Hue is dominant; saturation is a nudge.
HUE_WEIGHT = 0.75
SATURATION_WEIGHT = 0.25

# Score at the most clashy hue midpoints (~75 deg, ~142.5 deg) in the
# smooth transition zones between named schemas.
AWKWARD_FLOOR = 0.45


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


# Neutral-involving pairs, by style mode.
# Safe: neutrals are the "universally appealing" safe bet -> scored high.
# Bold: neutrals are the "boring" outcome bold mode avoids -> scored low.
NEUTRAL_SCORES = {
    "safe": {
        "neutral_neutral": 0.95,
        "neutral_chromatic": 0.90,
    },
    "bold": {
        "neutral_neutral": 0.50,
        "neutral_chromatic": 0.65,
    },
}

# Chromatic+chromatic HUE schema scores, by style mode.
# Safe:  monochromatic > analogous > complementary > triadic
# Bold:  complementary > triadic > analogous > monochromatic
SCHEMA_BASE_SCORES = {
    "safe": {
        "monochromatic": 0.90,
        "analogous": 0.85,
        "complementary": 0.75,
        "triadic": 0.60,
    },
    "bold": {
        "monochromatic": 0.55,
        "analogous": 0.70,
        "triadic": 0.90,
        "complementary": 0.95,
    },
}


def score_hue_pair(h1, h2, style="safe"):
    """
    Scores two CHROMATIC hues based on color-wheel relationships alone
    (saturation is NOT considered here — see score_saturation_pair).
    Returns 0-1, higher = more harmonious for the given style.

    Named schemas:
      - Monochromatic (~0-15 deg apart)
      - Analogous (~15-45 deg apart)
      - Triadic (~105-135 deg apart)
      - Complementary (~150-180 deg apart)

    Between named schemas (~45-105 deg, ~135-150 deg), the score
    smoothly interpolates rather than dropping to a flat penalty.
    """
    dist = hue_distance(h1, h2)
    scores = SCHEMA_BASE_SCORES.get(style, SCHEMA_BASE_SCORES["safe"])

    if dist <= 15:  # monochromatic
        return scores["monochromatic"] - (dist / 15) * 0.1

    if 15 < dist <= 45:  # analogous
        return scores["analogous"] - (abs(dist - 30) / 15) * 0.1

    if 105 <= dist <= 135:  # triadic
        return scores["triadic"] - (abs(dist - 120) / 15) * 0.1

    if 150 <= dist <= 180:  # complementary
        return scores["complementary"] - (abs(dist - 180) / 30) * 0.1

    if 45 < dist < 105:  # smooth transition: analogous -> triadic
        analogous_edge = scores["analogous"] - (30 / 15) * 0.1  # score at dist=45
        triadic_edge = scores["triadic"] - (15 / 15) * 0.1      # score at dist=105
        mid = 75
        if dist <= mid:
            t = (dist - 45) / (mid - 45)
            return analogous_edge + (AWKWARD_FLOOR - analogous_edge) * t
        else:
            t = (dist - mid) / (105 - mid)
            return AWKWARD_FLOOR + (triadic_edge - AWKWARD_FLOOR) * t

    if 135 < dist < 150:  # smooth transition: triadic -> complementary
        triadic_edge = scores["triadic"] - (15 / 15) * 0.1
        complementary_edge = scores["complementary"] - (30 / 30) * 0.1
        t = (dist - 135) / (150 - 135)
        return triadic_edge + (complementary_edge - triadic_edge) * t


def score_saturation_pair(s1, s2, style="safe"):
    """
    Scores two CHROMATIC colors based on their saturation profile alone
    (hue relationship is NOT considered here — see score_hue_pair).
    Returns 0-1, higher = better fit for the given style.

    Uses the average saturation of the two colors, normalized against
    the chromatic range (NEUTRAL_SATURATION_THRESHOLD to 1.0):
      - "safe":  low average saturation -> high score (muted/toned-down)
      - "bold":  high average saturation -> high score (vivid/eye-catching)
    """
    avg_sat = (s1 + s2) / 2

    span = 1.0 - NEUTRAL_SATURATION_THRESHOLD
    normalized = (avg_sat - NEUTRAL_SATURATION_THRESHOLD) / span
    normalized = max(0.0, min(1.0, normalized))  # clamp

    if style == "bold":
        return 0.5 + normalized * 0.5   # ranges 0.5 -> 1.0
    else:
        return 0.5 + (1.0 - normalized) * 0.5   # ranges 0.5 -> 1.0


def score_color_pair(hex1, hex2, style="safe"):
    """
    Main entry point. Scores one color from item A against one color
    from item B. Returns 0-1, higher = more harmonious for the chosen
    style ("safe" or "bold"). Style shapes every pairing type.

    For chromatic+chromatic pairs, combines hue-schema score and
    saturation score using HUE_WEIGHT / SATURATION_WEIGHT (75/25 —
    hue is the dominant signal, saturation a secondary nudge).
    """
    neutral1 = is_neutral(hex1)
    neutral2 = is_neutral(hex2)
    neutral_scores = NEUTRAL_SCORES.get(style, NEUTRAL_SCORES["safe"])

    if neutral1 and neutral2:
        return neutral_scores["neutral_neutral"]
    if neutral1 or neutral2:
        return neutral_scores["neutral_chromatic"]

    h1, s1, _ = hex_to_hsl(hex1)
    h2, s2, _ = hex_to_hsl(hex2)

    hue_score = score_hue_pair(h1, h2, style=style)
    sat_score = score_saturation_pair(s1, s2, style=style)

    return (hue_score * HUE_WEIGHT) + (sat_score * SATURATION_WEIGHT)


def score_item_pair(colors_a, colors_b, style="safe"):
    """
    Scores two items using their PRIMARY dominant color only
    (index 0 = most prevalent from K-Means), not best-of-all-combos.
    This stops a minor background/edge-artifact neutral shade from
    always winning over genuine hue matches.
    """
    if not colors_a or not colors_b:
        # No color data — fall back to the style's neutral+chromatic score
        # as a moderate, non-extreme default.
        return NEUTRAL_SCORES.get(style, NEUTRAL_SCORES["safe"])["neutral_chromatic"]
    return score_color_pair(colors_a[0], colors_b[0], style=style)