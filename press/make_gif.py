"""Figure 5: animated sidebar badge (GIF) - savings ticking up while calls land."""
from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFilter

import figlib as F

OUT = r"F:\EngineeringProject\dsh-token-saver\press"

W, H = 1040, 600
FRAMES_RAMP = 34
FRAMES_HOLD = 10
DURATION = 110  # ms per frame


def money_of(p: float, total: float) -> str:
    return F.money(total * p)


def draw_frame(p: float, pulse: float) -> Image.Image:
    img = F.canvas(W, H, F.PAPER)

    # ---- left: mock conversation sidebar
    left = (32, 40, 372, 560)
    F.card(img, left, 18)
    F.text(img, (56, 62), "DeepSeek Harness", 14, F.INK, bold=True)
    F.text(img, (56, 84), "桌面端 · 左侧栏", 12, F.FAINT)
    F.line(img, (56, 108, 348, 108), F.LINE)

    rows = [("省 token 插件怎么装", "今天"), ("报表合并那个任务", "昨天"), ("知乎推文配图", "周一")]
    y = 124
    for i, (name, when) in enumerate(rows):
        fill = "#F1F4F7" if i else "#FFFFFF"
        F.rrect(img, (52, y, 352, y + 44), 10, fill=fill, outline=F.LINE)
        F.text(img, (68, y + 12), name, 13, F.INK_SOFT)
        F.text(img, (68, y + 30), when, 11, F.FAINT)
        y += 52

    # footer action with the badge
    F.line(img, (56, 300, 348, 300), F.LINE)
    F.text(img, (56, 306), "会话底部 · 插件入口", 11, F.FAINT)

    by0, by1 = 344, 400
    # pulsing halo
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.rounded_rectangle((48 * F.S, (by0 - 8) * F.S, 356 * F.S, (by1 + 8) * F.S), radius=18 * F.S,
                         fill=(31, 143, 106, int(30 + 55 * pulse)))
    halo = halo.filter(ImageFilter.GaussianBlur(9 * F.S))
    img.paste(Image.alpha_composite(img.convert("RGBA"), halo).convert("RGB"), (0, 0))

    F.rrect(img, (52, by0, 352, by1), 14, fill=F.BRAND_SOFT, outline=None)
    F.badge_icon(img, 76, (by0 + by1) / 2, 12)
    F.text(img, (98, by0 + 12), "本次 " + money_of(p, 2.39), 15, F.BRAND_DEEP, bold=True)
    F.text(img, (98, by0 + 32), "累计 " + money_of(p, 34.00), 13, F.BRAND_DEEP)

    # rail variant below (56px)
    F.text(img, (56, 420), "窄侧栏时只留金额", 11, F.FAINT)
    F.rrect(img, (52, 442, 108, 520), 14, fill=F.BRAND_SOFT, outline=None)
    F.badge_icon(img, 80, 462, 11)
    F.text(img, (80, 492), money_of(p, 2.39), 12, F.BRAND_DEEP, bold=True, anchor="mm")
    F.text(img, (80, 508), "本次", 10, F.MUTED, anchor="mm")

    # ---- right: hover tooltip detail
    right = (388, 40, 1008, 560)
    F.card(img, right, 18)
    F.text(img, (412, 62), "点开 / 悬停的明细", 14, F.INK, bold=True)
    F.text(img, (412, 84), "全部数字来自本地会话事件，不联网", 12, F.FAINT)
    F.line(img, (412, 108, 984, 108), F.LINE)

    calls = int(round(225 * p))
    rows2 = [
        ("本次会话", f"{max(1, int(99 * p))} 次调用 · 命中 {97.8 * p:.1f}%"),
        ("累计省", F.money(34.00 * p)),
        ("开启前 → 开启后", f"{F.money(38.98 * p)} → {F.money(4.98 * p)}"),
        ("累计命中", f"{18.89 * p:.2f}M / {19.31 * p:.2f}M 输入 token"),
        ("调用次数", f"{calls} 次"),
        ("缓存前缀重建", f"{int(3 * p)} 次"),
        ("指令瘦身", f"{1 if p > 0.55 else 0} 条 · {int(64 * p)} token"),
    ]
    y = 124
    for label, value in rows2:
        F.text(img, (412, y), label, 13, F.MUTED)
        F.text(img, (984, y), value, 14, F.INK, bold=True, anchor="ra")
        y += 34

    # ---- bars: before vs after
    F.line(img, (412, 386, 984, 386), F.LINE)
    F.text(img, (412, 400), "同一批 token，按两个价码算", 12, F.FAINT)

    bar_x0, bar_x1 = 412, 984
    bar_w = bar_x1 - bar_x0
    F.text(img, (412, 428), "全部未命中", 12, F.MUTED)
    F.text(img, (984, 428), F.money(38.98 * p), 13, "#8A939F", bold=True, anchor="ra")
    F.rrect(img, (412, 448, bar_x1, 472), 12, fill="#EDF0F3", outline=None)
    F.rrect(img, (412, 448, bar_x0 + max(12, bar_w * p), 472), 12, fill="#C7CFD8", outline=None)

    F.text(img, (412, 488), "实付", 12, F.MUTED)
    F.text(img, (984, 488), F.money(4.98 * p), 13, F.BRAND_DEEP, bold=True, anchor="ra")
    F.rrect(img, (412, 508, bar_x1, 532), 12, fill="#EDF0F3", outline=None)
    F.rrect(img, (412, 508, bar_x0 + max(12, bar_w * 0.128 * p), 532), 12, fill=F.BRAND, outline=None)

    # corner note
    F.text(img, (412, 544), "省下的那一段 = 缓存命中带来的差价", 11, F.FAINT)

    # top-left demo label
    F.text(img, (32, 20), "动图示意：每次调用后，左侧栏的钱往上走", 12, F.FAINT)
    return img


def main() -> None:
    frames: list[Image.Image] = []
    total = FRAMES_RAMP + FRAMES_HOLD
    steps = 16
    for i in range(total):
        if i < FRAMES_RAMP:
            raw = i / (FRAMES_RAMP - 1)
            # stepped tick: money jumps once per call, then settles
            step = min(steps - 1, int(raw * steps))
            frac = min(1.0, raw * steps - step)
            p = (step + F.ease_out(frac) * 0.85) / steps
            pulse = 0.5 + 0.5 * math.sin(raw * math.pi)
        else:
            p = 1.0
            t = (i - FRAMES_RAMP) / max(1, FRAMES_HOLD - 1)
            pulse = 0.35 + 0.65 * abs(math.sin(t * math.pi))
        big = draw_frame(p, pulse)
        frames.append(big.resize((W, H), Image.LANCZOS))

    quant = [f.convert("P", palette=Image.ADAPTIVE, colors=128) for f in frames]
    path = OUT + r"\fig5-badge.gif"
    quant[0].save(path, save_all=True, append_images=quant[1:], duration=DURATION,
                  loop=0, optimize=True, disposal=2)
    print("gif frames", len(quant), "->", path)


if __name__ == "__main__":
    main()
