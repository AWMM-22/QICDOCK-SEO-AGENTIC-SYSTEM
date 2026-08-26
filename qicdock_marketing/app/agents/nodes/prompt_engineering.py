"""Professional image-prompt engineering for Qicdock content.

Every prompt is built as a mini AD STORY:
  1. The problem (cable mess, clutter, distraction) - shown visually
  2. The solution (Qicdock docked, clean, hands-free) - the hero moment
  3. The message - headline text rendered in the image

Car-specific topics get car-cabin scenes; general product/educational
topics get modular lifestyle scenes (desk, office, home, wall).
"""
from typing import Optional

# Shared quality floor applied to EVERY prompt (professional consistency)
QUALITY_BASE = (
    "Professional commercial product photography, shot on a full-frame camera, "
    "85mm lens, f/2.8, crisp focus on the product, shallow depth of field. "
    "Premium automotive/tech advertising aesthetic, photorealistic, high dynamic "
    "range, 4K detail. No watermarks; no logos other than the product's own."
)

# Per-content-type framing (variation while staying professional)
TYPE_DIRECTION = {
    "post": (
        "Feed-post composition: strong single-frame story, product clearly the hero, "
        "generous negative space for the headline."
    ),
    "carousel": (
        "Slide-style composition with generous copy space around the product - "
        "designed to pair with feature callouts on the next slides."
    ),
    "reel": (
        "Vertical cinematic opening frame with strong foreground presence and a "
        "sense of motion - built to stop the scroll in the first second."
    ),
    "story": (
        "Vertical candid in-use moment: authentic, spontaneous feel, as if captured "
        "mid-action by the user."
    ),
    "image": "",
}

MOOD_VARIATIONS = [
    "Morning commute mood: golden-hour light through the windshield.",
    "Evening city-drive mood: cool ambient interior glow, city lights bokeh.",
    "Bright daylight road-trip mood: airy cabin, clean neutral tones.",
    "Rainy-day cozy mood: soft diffused light, subtle droplets on windows.",
]

# Problem->solution narrative templates. Each shows the ISSUE first,
# then Qicdock as the resolution - that contrast is the ad.
CAR_PROBLEM_SOLUTION = [
    (
        "Split-scene storytelling in ONE frame: the left third shows the PROBLEM - a dim, "
        "moody view of a cluttered car console with tangled charging cables, loose wires "
        "snaking over the gear lever, a phone lying loose on the passenger seat; a subtle "
        "dark vignette separates it from the right two-thirds which show the SOLUTION - a "
        "bright, spotless centre console with the Qicdock dock installed, phone magnetically "
        "docked and charging cleanly, zero cables anywhere, premium OEM look. The contrast "
        "between chaos and order must be instantly obvious."
    ),
    (
        "Before/after diptych composition: left half 'before' - frustrated driver's hand "
        "untangling a knotted cable in a dim cabin, cable wrapped around the gear stick; "
        "right half 'after' - the same cabin bright and immaculate, hand effortlessly "
        "snapping the phone onto the Qicdock dock with one finger, magnetic click moment "
        "frozen in time, everything else clean and minimal."
    ),
    (
        "Problem-elimination hero shot: in the softly blurred background, faint out-of-focus "
        "silhouette of tangled cables in a bin; in sharp focus in the foreground, the "
        "Qicdock dock installed flush in the centre console with the phone docked at a "
        "confident angle, charging icon glowing on screen, surrounding console area "
        "absolutely pristine - the product visually 'replacing' the mess."
    ),
]

GENERAL_PROBLEM_SOLUTION = [
    (
        "Split-scene storytelling in ONE frame: left third shows the PROBLEM - a desk "
        "corner drowning in tangled charging cables, knotted wires, a phone propped "
        "awkwardly against a mug, dim and chaotic; right two-thirds show the SOLUTION - "
        "the same desk transformed: the Qicdock dock standing clean with the phone "
        "magnetically charging, single clean surface, everything organized, bright and "
        "calm. Chaos-to-order contrast must be instantly readable."
    ),
    (
        "One-hand convenience moment: close-up of a hand effortlessly snapping a phone "
        "onto the Qicdock dock on a work desk - the magnetic alignment mid-click, phone "
        "tilting into perfect position, no cable in sight; background shows a normal "
        "desk with a subtle hint of a coiled old cable pushed aside in shadow."
    ),
    (
        "Modular lifestyle montage feel in one frame: the Qicdock dock shown in a bright "
        "modern workspace charging a phone, with softly blurred hints of its other homes "
        "in the background bokeh - a car console, an AC vent, a wall mount - communicating "
        "one charger that follows you everywhere, zero cable clutter in any scene."
    ),
]

CAR_SCENES = [
    "The dock seamlessly integrated into the car's centre console exactly where it "
    "belongs, looking like a factory-fitted OEM feature.",
    "Close-up of the dock fitted perfectly into the console cavity, precision-fit emphasis.",
    "Driver's point of view: dock in the console, hands on the wheel, clean cabin visible.",
]

GENERAL_SCENES = [
    "Modern minimalist work desk setup with the dock charging a phone, soft daylight.",
    "Stylish office scene: dock on a table charging a phone, clean corporate aesthetic.",
    "Cozy home scene: dock on a bedside table charging a phone, warm lamp light.",
    "AC vent mounted dock charging a phone - universal accessory angle, airy cabin.",
]


def _is_car_specific(topic_text: str) -> bool:
    """Heuristic: does this content target a specific car/model?"""
    t = (topic_text or "").lower()
    car_markers = [
        "swift", "dzire", "baleno", "ertiga", "fronx", "glanza", "taisor",
        "xuv", "3xo", "creta", "nexon", "scorpio", "thar", "grand i10",
        "i20", "venue", "sonet", "seltos", "punch", "altroz", "amaze",
        "city", "slavia", "virtus", "kushaq", "taigun",
        "maruti", "mahindra", "toyota", "hyundai", "tata", "kia", "honda",
        "skoda", "volkswagen", "car model", "your car", "car-specific",
        "centre console", "center console", "console",
    ]
    return any(m in t for m in car_markers)


def build_image_prompt(
    base_prompt: str,
    content_type: str,
    variation_index: int = 0,
    product_name: Optional[str] = None,
    compatibility: Optional[str] = None,
    hook: Optional[str] = None,
    key_message: Optional[str] = None,
) -> str:
    """Compose a professional problem->solution image prompt.

    Structure:
      1. Product fidelity anchor (reference photo)
      2. Problem->solution narrative (the AD idea)
      3. Benefit headline rendered as text overlay
      4. Format direction + mood + quality floor
    """
    base_prompt = (base_prompt or "").strip()
    type_dir = TYPE_DIRECTION.get(content_type, "")
    mood = MOOD_VARIATIONS[variation_index % len(MOOD_VARIATIONS)]

    topic_context = f"{base_prompt} {hook or ''} {key_message or ''}"
    car_specific = _is_car_specific(topic_context)

    # Short punchy overlay text - max ~5 words renders reliably
    overlay_text = (hook or key_message or "").strip().strip(".").strip('"')
    if len(overlay_text) > 42:
        overlay_text = " ".join(overlay_text.split()[:5])

    parts = []

    # 1. Product fidelity anchor
    if product_name:
        parts.append(
            f"PRODUCT (must match the attached reference photo exactly - shape, "
            f"color, materials and finish): {product_name}."
        )

    # 2. The problem->solution narrative - the core ad idea
    if car_specific:
        narrative = CAR_PROBLEM_SOLUTION[variation_index % len(CAR_PROBLEM_SOLUTION)]
        if compatibility and compatibility not in ("All Models",):
            narrative = narrative.replace("car console", f"{compatibility} centre console")
        parts.append(f"AD CONCEPT (problem vs solution): {narrative}")
    else:
        narrative = GENERAL_PROBLEM_SOLUTION[variation_index % len(GENERAL_PROBLEM_SOLUTION)]
        parts.append(f"AD CONCEPT (problem vs solution): {narrative}")

    # Creative angle from the strategy agent, woven in
    if base_prompt:
        parts.append(f"Creative angle to respect: {base_prompt}.")

    # 3. Headline rendered inside the image
    if overlay_text:
        parts.append(
            f'Text overlay: render the headline "{overlay_text}" as bold modern '
            "sans-serif typography, high contrast against the background, positioned "
            "in clean negative space (upper third of the frame), professional "
            "advertisement style, correctly spelled, crisp and legible."
        )

    # 4. Format + mood + quality
    if type_dir:
        parts.append(type_dir)
    parts.append(mood)
    parts.append(QUALITY_BASE)

    return "\n".join(parts)
