from __future__ import annotations

import io
import math
import os
from typing import Optional

import asyncio

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageFont

CARD_W, CARD_H = 1280, 400
ART_SIZE = 310
ART_X, ART_Y = 40, 45

GOLD = (255, 200, 60)
DARK_PURPLE = (30, 10, 50)
WHITE = (255, 255, 255)
SOFT_GOLD = (230, 180, 80)
OVERLAY_COLOR = (0, 0, 0, 180)

_font_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "fonts")


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    paths = [
        os.path.join(_font_dir, name),
        f"/usr/share/fonts/truetype/liberation/{name}",
        f"/usr/share/fonts/truetype/dejavu/{name}",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


async def _fetch_image_async(url: str) -> Optional[Image.Image]:
    """Fetch thumbnail without blocking the event loop."""
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        pass
    return None


def _fallback_bg() -> Image.Image:
    img = Image.new("RGBA", (CARD_W, CARD_H))
    draw = ImageDraw.Draw(img)
    for y in range(CARD_H):
        t = y / CARD_H
        r = int(30 + 20 * t)
        g = int(5 + 5 * t)
        b = int(60 + 30 * t)
        draw.line([(0, y), (CARD_W, y)], fill=(r, g, b, 255))
    return img


def _draw_glow(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int) -> None:
    for r in range(radius, 0, -10):
        alpha = int(60 * (1 - r / radius))
        color = (180, 80, 255, alpha)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)


def _draw_progress_ring(
    draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, progress: float
) -> None:
    bbox = [cx - r, cy - r, cx + r, cy + r]
    draw.arc(bbox, start=-90, end=270, fill=(60, 60, 60, 120), width=6)
    if progress > 0:
        end_angle = -90 + 360 * min(progress, 1.0)
        draw.arc(bbox, start=-90, end=end_angle, fill=GOLD + (220,), width=6)


def _round_image(img: Image.Image, radius: int = 24) -> Image.Image:
    img = img.resize((ART_SIZE, ART_SIZE), Image.LANCZOS)
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, ART_SIZE, ART_SIZE], radius=radius, fill=255)
    result = Image.new("RGBA", img.size, (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result


def _truncate(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    original_len = len(text)
    while len(text) > 1:
        bbox = font.getbbox(text + "…")
        if bbox[2] - bbox[0] <= max_w:
            break
        text = text[:-1]
    return text + "…" if len(text) < original_len else text


def _build_card(
    title: str,
    uploader: str,
    thumb: Optional[Image.Image],
    requester: str,
    elapsed: int,
    duration: int,
) -> io.BytesIO:
    """CPU-bound Pillow work — run this in a thread executor."""

    if thumb:
        bg = thumb.resize((CARD_W, CARD_H), Image.LANCZOS).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(radius=20))
        overlay = Image.new("RGBA", bg.size, OVERLAY_COLOR)
        bg = Image.alpha_composite(bg, overlay)
    else:
        bg = _fallback_bg()

    draw = ImageDraw.Draw(bg, "RGBA")

    font_brand = _load_font("Roboto-Bold.ttf", 22)
    font_title = _load_font("Roboto-Bold.ttf", 34)
    font_artist = _load_font("Roboto-Regular.ttf", 22)
    font_small = _load_font("Roboto-Regular.ttf", 18)

    draw.line([(0, 0), (CARD_W, 0)], fill=GOLD, width=3)
    draw.line([(0, CARD_H - 3), (CARD_W, CARD_H - 3)], fill=GOLD, width=3)

    draw.text((16, 10), "JATT MUSIC BOT", font=font_brand, fill=GOLD)

    art_cx = ART_X + ART_SIZE // 2
    art_cy = ART_Y + ART_SIZE // 2

    _draw_glow(draw, art_cx, art_cy, ART_SIZE // 2 + 40)

    progress = elapsed / duration if duration > 0 else 0.0
    _draw_progress_ring(draw, art_cx, art_cy, ART_SIZE // 2 + 18, progress)

    if thumb:
        art = _round_image(thumb.convert("RGBA"), 24)
        bg.paste(art, (ART_X, ART_Y), art)
    else:
        draw.rounded_rectangle(
            [ART_X, ART_Y, ART_X + ART_SIZE, ART_Y + ART_SIZE],
            radius=24,
            fill=(60, 20, 100, 200),
        )
        draw.text(
            (art_cx, art_cy),
            "♪",
            font=_load_font("Roboto-Bold.ttf", 100),
            fill=GOLD,
            anchor="mm",
        )

    text_x = ART_X + ART_SIZE + 40
    text_max_w = CARD_W - text_x - 30

    draw.text(
        (text_x, 55),
        _truncate(title, font_title, text_max_w),
        font=font_title,
        fill=WHITE,
    )
    draw.text(
        (text_x, 100),
        _truncate(uploader, font_artist, text_max_w),
        font=font_artist,
        fill=SOFT_GOLD,
    )

    bar_y = 180
    bar_h = 10
    bar_w = text_max_w
    bar_x = text_x

    draw.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
        radius=5,
        fill=(80, 80, 80, 180),
    )
    filled_w = int(bar_w * progress)
    if filled_w > 0:
        draw.rounded_rectangle(
            [bar_x, bar_y, bar_x + filled_w, bar_y + bar_h],
            radius=5,
            fill=GOLD,
        )
        dot_x = bar_x + filled_w
        draw.ellipse([dot_x - 7, bar_y - 3, dot_x + 7, bar_y + bar_h + 3], fill=GOLD)

    def _fmt(s: int) -> str:
        m, sec = divmod(abs(s), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{sec:02d}"
        return f"{m}:{sec:02d}"

    draw.text((bar_x, bar_y + 18), _fmt(elapsed), font=font_small, fill=SOFT_GOLD)
    dur_text = _fmt(duration) if duration else "Live"
    dur_bbox = font_small.getbbox(dur_text)
    draw.text(
        (bar_x + bar_w - (dur_bbox[2] - dur_bbox[0]), bar_y + 18),
        dur_text,
        font=font_small,
        fill=SOFT_GOLD,
    )

    req_text = f"Requested by {requester}"
    req_box_y = CARD_H - 55
    req_bbox = font_small.getbbox(req_text)
    req_w = req_bbox[2] - req_bbox[0] + 30
    draw.rounded_rectangle(
        [bar_x, req_box_y, bar_x + req_w, req_box_y + 32],
        radius=10,
        fill=(50, 10, 80, 200),
    )
    draw.text((bar_x + 15, req_box_y + 7), req_text, font=font_small, fill=SOFT_GOLD)

    buf = io.BytesIO()
    bg.convert("RGB").save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return buf


async def generate_now_playing_card(
    title: str,
    uploader: str,
    thumbnail_url: str,
    requester: str,
    elapsed: int,
    duration: int,
) -> io.BytesIO:
    """
    Public async entry point.
    - Fetches the thumbnail concurrently (async HTTP).
    - Runs all blocking Pillow work in a thread executor so the event loop
      stays free during card generation.
    """
    thumb = await _fetch_image_async(thumbnail_url)
    loop = asyncio.get_event_loop()
    buf = await loop.run_in_executor(
        None,
        lambda: _build_card(title, uploader, thumb, requester, elapsed, duration),
    )
    return buf
