import argparse
import os
from typing import List, Tuple, Optional

from PIL import Image, ImageDraw, ImageFont


TEMPLATE_PATH_NET = os.path.join("templates", "1080x540 for .NET.png")
TEMPLATE_PATH_JAVA = os.path.join("templates", "1080x540 for Java.png")
TEMPLATE_PATH_PYTHON = os.path.join("templates", "1080x540 for Python.png")
TEMPLATE_PATH_NODEJS = os.path.join("templates", "1080x540 for Node.js.png")
TEMPLATE_PATH_OTHER = os.path.join("templates", "1080x540 for Other.png")

FONTS_DIR = "fonts"
LOGOS_DIR = "logos"


def load_font(preferred_paths: List[str], font_size: int) -> ImageFont.FreeTypeFont:
    for path in preferred_paths:
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, font_size)
            except Exception:
                continue
    # Fallback to default PIL font (not ideal, but ensures the script runs)
    return ImageFont.load_default()


def _set_font_variation_by_name_if_possible(font: ImageFont.FreeTypeFont, name_candidates: List[str]) -> bool:
    try:
        if hasattr(font, "get_variation_names") and hasattr(font, "set_variation_by_name"):
            names = font.get_variation_names() or []
            lowered = {n.lower(): n for n in names}
            for cand in name_candidates:
                cands = [cand, cand.replace(" ", ""), cand.replace(" ", "-")]
                for c in cands:
                    if c.lower() in lowered:
                        font.set_variation_by_name(lowered[c.lower()])
                        return True
    except Exception:
        pass
    return False


def _set_font_weight_axis_if_possible(font: ImageFont.FreeTypeFont, weight_value: Optional[int]) -> bool:
    if weight_value is None:
        return False
    try:
        if hasattr(font, "get_variation_axes") and hasattr(font, "set_variation_by_axes"):
            axes = font.get_variation_axes() or []
            if not axes:
                return False
            values = []
            wght_index = None
            for idx, axis in enumerate(axes):
                # axis is a dict like {"name": "Weight", "tag": "wght", "min": 100, "default": 400, "max": 900}
                tag = axis.get("tag") or axis.get("name")
                if isinstance(tag, str) and tag.lower() == "wght":
                    wght_index = idx
                values.append(axis.get("default", 0))
            if wght_index is None:
                return False
            # Clamp into allowed range
            min_w = axes[wght_index].get("min", weight_value)
            max_w = axes[wght_index].get("max", weight_value)
            clamped = max(min_w, min(max_w, weight_value))
            values[wght_index] = clamped
            font.set_variation_by_axes(values)
            return True
    except Exception:
        pass
    return False


def load_inter_variable_font(font_name: str, font_size: int, instance_name: Optional[str], weight_value: Optional[int]) -> ImageFont.FreeTypeFont:
    inter_path = os.path.join(FONTS_DIR, font_name)
    if os.path.isfile(inter_path):
        try:
            fnt = ImageFont.truetype(inter_path, font_size)
            # Prefer named instance if available
            name_candidates: List[str] = []
            if instance_name:
                name_candidates.append(instance_name)
            # Add some common aliases for robustness
            if instance_name and instance_name.lower() == "extra bold":
                name_candidates += ["ExtraBold", "Extra Bold", "Extrabold", "Extrabold"]
            if instance_name and instance_name.lower() == "bold":
                name_candidates += ["Bold"]

            if name_candidates and _set_font_variation_by_name_if_possible(fnt, name_candidates):
                return fnt

            # Fallback to weight axis if supported
            if _set_font_weight_axis_if_possible(fnt, weight_value):
                return fnt

            return fnt
        except Exception:
            pass
    # Final fallback
    return ImageFont.load_default()


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font, anchor="la")
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    return width, height


def wrap_text_to_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    words = text.split()
    if not words:
        return [""]

    lines: List[str] = []
    current_line: List[str] = []

    for word in words:
        trial = (" ".join(current_line + [word])).strip()
        w, _ = measure_text(draw, trial, font)
        if w <= max_width or not current_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    rect_xywh: Tuple[float, float, float, float],
    font: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    h_align: str = "left",
    v_align: str = "top",
    line_spacing_px: int = 0,
) -> None:
    x, y, width, height = rect_xywh
    x = int(round(x))
    y = int(round(y))
    width = int(round(width))
    height = int(round(height))

    lines = wrap_text_to_width(draw, text, font, width)

    # Compute total text block height
    ascent, descent = font.getmetrics()
    base_line_height = ascent + descent
    if line_spacing_px == 0:
        line_spacing_px = max(2, int(0.2 * base_line_height))
    line_heights = []
    for line in lines:
        _, h = measure_text(draw, line, font)
        line_heights.append(h)
    total_text_height = sum(line_heights) + (len(lines) - 1) * line_spacing_px

    # Vertical alignment
    if v_align.lower() in ("middle", "center", "centre"):
        start_y = y + (height - total_text_height) // 2
    elif v_align.lower() in ("bottom", "right"):  # handle possible spec typo using 'right' for vertical
        start_y = y + height - total_text_height
    else:
        start_y = y

    # Draw each line with horizontal alignment
    current_y = start_y
    for i, line in enumerate(lines):
        line_width, line_height = measure_text(draw, line, font)
        if h_align.lower() in ("center", "centre"):
            line_x = x + (width - line_width) // 2
        elif h_align.lower() in ("right", "bottom"):  # handle possible spec typo using 'top'/'right'
            line_x = x + width - line_width
        else:
            line_x = x
        draw.text((line_x, current_y), line, font=font, fill=fill)
        current_y += line_height + line_spacing_px


def fit_image_into_box(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    w, h = img.size
    if w == 0 or h == 0:
        return img
    scale = min(max_w / w, max_h / h)
    new_size = (int(round(w * scale)), int(round(h * scale)))
    return img.resize(new_size, Image.LANCZOS)


def select_logo_path(product_name: str) -> str:
    # Exact match first
    exact = os.path.join(LOGOS_DIR, f"{product_name}.png")
    if os.path.isfile(exact):
        return exact
    # Try normalized filename variants
    normalized = product_name.replace("/", "-")
    candidate = os.path.join(LOGOS_DIR, f"{normalized}.png")
    if os.path.isfile(candidate):
        return candidate

    # Fallback: default logo
    return os.path.join(LOGOS_DIR, "Generic.png")


def generate_cover_image(product_name: str, product_version: str, title: str, output_path: str) -> None:
    template_path = None

    if "CLI" in product_name or "UI" in product_name:
        template_path = TEMPLATE_PATH_OTHER
    elif "for .NET" in product_name:
        template_path = TEMPLATE_PATH_NET
    elif "for Java" in product_name:
        template_path = TEMPLATE_PATH_JAVA
    elif "for Python" in product_name:
        template_path = TEMPLATE_PATH_PYTHON
    elif "for Node.js" in product_name:
        template_path = TEMPLATE_PATH_NODEJS
    else:
        template_path = TEMPLATE_PATH_OTHER

    template = Image.open(template_path).convert("RGBA")
    canvas = template.copy()
    draw = ImageDraw.Draw(canvas)

    # Calculate font size and rect position based on product_version
    font_version_size = 100
    rect_position_x = 692
    rect_position_y = 264
    rect_width = 370
    rect_height = 116
    if len(product_version) > 4:
        font_version_size = 70
        rect_position_x = 695.49
        rect_position_y = 280.27
        rect_width = 360
        rect_height = 89.1

    # Load variable font (Inter.ttf) and set variations (weights)
    font_product_name = load_inter_variable_font(font_name="Inter-ExtraBold.ttf", font_size=44, instance_name="Extra Bold", weight_value=800)
    font_version = load_inter_variable_font(font_name="Inter-ExtraBold.ttf", font_size=font_version_size, instance_name="Extra Bold", weight_value=800)
    font_title = load_inter_variable_font(font_name="Inter-Bold.ttf", font_size=32, instance_name="Bold", weight_value=700)

    # 1) Logo
    logo_x, logo_y = 61.88, 55.26
    logo_w, logo_h = 78.68, 78.57
    logo_path = select_logo_path(product_name)
    logo = Image.open(logo_path).convert("RGBA")
    logo = fit_image_into_box(logo, int(round(logo_w)), int(round(logo_h)))
    canvas.alpha_composite(logo, (int(round(logo_x)), int(round(logo_y))))

    # Colors
    white = (255, 255, 255)

    # 2) Product name
    pn_x, pn_y = 165.98, 69.26
    pn_w, pn_h = 746.04, 88.32
    draw_text_block(
        draw=draw,
        text=product_name,
        rect_xywh=(pn_x, pn_y, pn_w, pn_h),
        font=font_product_name,
        fill=white,
        h_align="left",
        v_align="top",
    )

    # 3) Product version
    ver_x, ver_y = rect_position_x, rect_position_y
    ver_w, ver_h = rect_width, rect_height
    draw_text_block(
        draw=draw,
        text=product_version,
        rect_xywh=(ver_x, ver_y, ver_w, ver_h),
        font=font_version,
        fill=white,
        h_align="center",
        v_align="top",
    )

    # 4) Title
    title_x, title_y = 269.94, 430.16
    title_w, title_h = 737.04, 88.32
    # The spec lists vertical align "right" and horizontal "top"; interpret as top-right
    draw_text_block(
        draw=draw,
        text=title,
        rect_xywh=(title_x, title_y, title_w, title_h),
        font=font_title,
        fill=white,
        h_align="right",
        v_align="top",
    )

    # When output path is not specified, use product name and title separated by hyphen, replace spaces and dots with hyphen
    output_file_name = f"{product_name}-{product_version}".lower().replace(" ", "-").replace(".", "-").replace("--", "-")
    output_file = f"{output_file_name}.png"
    if output_path == "":
        output_path = os.path.join("output", output_file)

    # Save result (ensure output directory exists)
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    # Preserve transparency by saving with alpha (PNG)
    canvas.save(output_path, format="PNG")

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate cover image for blog post")
    parser.add_argument("--product", default="GroupDocs.Total for Java", help="Product name, e.g. 'GroupDocs.Total for Java'")
    parser.add_argument("--version", default="25.8", help="Product version, e.g. '25.8'")
    parser.add_argument("--title", default="August 2025 release", help="Cover title, e.g. 'August 2025 release'")
    parser.add_argument("--output", default="", help="Output file path (PNG)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = generate_cover_image(args.product, args.version, args.title, args.output)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()

