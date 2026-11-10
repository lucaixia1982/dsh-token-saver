"""Figure 3 (cost bars), Figure 4 (install steps), Figure 0 (Zhihu cover)."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

import figlib as F

OUT = r"F:\EngineeringProject\dsh-token-saver\press"


def fig3_cost() -> None:
    W, H = 1200, 580
    img = F.canvas(W, H, F.PAPER)

    left = (32, 36, 792, 520)
    F.card(img, left, 18)

    F.text(img, (56, 58), "同样这 225 次调用，钱差在哪", 15, F.MUTED, bold=True)
    F.text(img, (56, 82), "插件把每一批 token 用两个价码各算一遍：「全部未命中」与「实际」", 12, F.FAINT)

    bx0, bx1 = 56, 768
    span = bx1 - bx0

    # before bar
    F.text(img, (bx0, 122), "如果全部未命中", 13, F.MUTED)
    F.text(img, (bx1, 116), "¥38.98", 20, "#8A939F", bold=True, anchor="ra")
    F.rrect(img, (bx0, 146, bx1, 190), 22, fill="#EDF0F3", outline=None)
    F.rrect(img, (bx0, 146, bx1, 190), 22, fill="#C7CFD8", outline=None)

    # after bar
    F.text(img, (bx0, 216), "实际支付", 13, F.MUTED)
    F.text(img, (bx1, 210), "¥4.98", 20, F.BRAND_DEEP, bold=True, anchor="ra")
    F.rrect(img, (bx0, 240, bx1, 284), 22, fill="#EDF0F3", outline=None)
    after_w = int(span * 0.128)
    F.rrect(img, (bx0, 240, bx0 + after_w, 284), 22, fill=F.BRAND, outline=None)

    # saving bracket
    top_y, bot_y = 190, 240
    mid_y = (top_y + bot_y) / 2
    x_edge = bx0 + after_w
    F.line(img, (bx0 + 6, 310, bx1, 310), F.LINE)
    F.text(img, (bx0, 322), "两段之差", 13, F.MUTED)
    F.text(img, (bx0, 344), "¥34.00", 34, F.BRAND_DEEP, bold=True)
    F.text(img, (bx0 + 128, 356), "省掉 87%", 15, F.BRAND_DEEP, bold=True)
    F.text(img, (bx0 + 232, 358), "（225 次调用累计，插件实测）", 12, F.MUTED)

    F.text(img, (bx0, 402), "其中：输入命中 18.89M token 按 ¥0.2/M 计价，", 13, F.INK_SOFT)
    F.text(img, (bx0, 424), "输入未命中只有 0.42M token 按 ¥2/M 计价 —— 差价全在这一行。", 13, F.INK_SOFT)
    F.text(img, (bx0, 456), "指令瘦身单独算：1 条，64 token，约 ¥0.00001。零头。", 13, F.MUTED)
    F.text(img, (bx0, 480), "所以别信「压缩提示词能省一半」：真正省钱的是缓存命中，以及把它算清楚。", 12, F.FAINT)

    # right cards
    right = (808, 36, 1168, 520)
    F.card(img, right, 18)
    F.text(img, (832, 58), "同一时刻的其它数字", 15, F.MUTED, bold=True)

    stats = [
        ("缓存命中率", "97.8%", "命中 18.89M / 输入 19.31M"),
        ("调用次数", "225", "启动插件后累计"),
        ("本次会话", "¥2.39", "99 次调用，命中 97.8%"),
        ("瘦身条数", "1", "省 64 token（保守开关）"),
    ]
    y = 96
    for name, value, note in stats:
        F.text(img, (832, y), name, 12, F.MUTED)
        F.text(img, (1144, y - 10), value, 26, F.INK, bold=True, anchor="ra")
        F.text(img, (832, y + 30), note, 11, F.FAINT)
        F.line(img, (832, y + 58, 1144, y + 58), F.LINE)
        y += 78

    F.text(img, (832, 452), "价格可在 config 改：", 11, F.FAINT)
    F.text(img, (832, 472), "priceInputMiss / priceInputHit / priceOutput", 11, F.FAINT, mono=True)

    F.save(img, OUT + r"\fig3-cost.png", (W, H))


def fig4_install() -> None:
    W, H = 1200, 560
    img = F.canvas(W, H, F.PAPER)

    card = (32, 36, 1168, 512)
    F.card(img, card, 18)

    F.text(img, (56, 58), "三步装上，不用改 DSH 源码", 15, F.MUTED, bold=True)

    steps = [
        ("1", "装包", "市场里搜 @acmepoyen/dsh-token-saver，点安装；\n或手边有终端：npm i @acmepoyen/dsh-token-saver"),
        ("2", "挂载", "把包目录交给 plugin_manager 的 install_bundle；\n或自己在 cordis.patch.yml 里加一行 insert"),
        ("3", "生效", "重启 DSH 桌面端，左侧栏出现徽章；\n下一次模型调用后开始记账。"),
    ]
    x = 56
    for num, title, body in steps:
        d = ImageDraw.Draw(img)
        d.ellipse((x * F.S, 100 * F.S, (x + 30) * F.S, 130 * F.S), fill=F.BRAND)
        F.text(img, (x + 15, 115), num, 15, "#FFFFFF", bold=True, anchor="mm")
        F.text(img, (x + 42, 100), title, 17, F.INK, bold=True)
        yy = 138
        for ln in body.split("\n"):
            F.text(img, (x + 42, yy), ln, 13, F.INK_SOFT)
            yy += 22
        x += 372

    F.line(img, (56, 214, 1144, 214), F.LINE)

    F.text(img, (56, 232), "要挂的那一行长这样", 13, F.MUTED, bold=True)
    F.rrect(img, (56, 258, 640, 380), 12, fill="#14181F", outline=None)
    code = [
        ("- insert:", "#D7E0E8"),
        ("    - id: dsh-token-saver", "#8FE3C4"),
        ("      name: '@acmepoyen/dsh-token-saver'", "#8FE3C4"),
    ]
    y = 274
    for ln, color in code:
        F.text(img, (76, y), ln, 14, color, mono=True)
        y += 28

    F.text(img, (672, 232), "卸载", 13, F.MUTED, bold=True)
    F.text(img, (672, 258), "删掉那一行、重启即可。", 13, F.INK_SOFT)
    F.text(img, (672, 282), "宿主机上不写任何全局状态，", 13, F.INK_SOFT)
    F.text(img, (672, 306), "数据只在 ~/.dsh/dsh-token-saver.json。", 13, F.INK_SOFT)
    F.text(img, (672, 338), "客户端只读它自己的 /plugins/…/stats 路由，", 12, F.MUTED)
    F.text(img, (672, 360), "不碰你的会话内容。", 12, F.MUTED)

    F.rrect(img, (56, 400, 1144, 484), 12, fill=F.BRAND_SOFT, outline=None)
    F.text(img, (76, 418), "兼容性", 12, F.BRAND_DEEP, bold=True)
    F.text(img, (76, 440), "DSH 0.2.x（本机 0.2.2-rc.1 实测）；纯 JS，无构建、无第三方运行时依赖；", 13, F.INK_SOFT)
    F.text(img, (76, 462), "只用了 agent/pre-step、session/event、webServer.register 与 sidebar.footer.action 四个公开扩展点。", 13, F.INK_SOFT)

    F.save(img, OUT + r"\fig4-install.png", (W, H))


def cover() -> None:
    W, H = 1200, 675
    img = Image.new("RGB", (W * F.S, H * F.S), "#0E1A17")
    d = ImageDraw.Draw(img)

    # diagonal gradient wash
    for i in range(0, H * F.S, 4):
        t = i / (H * F.S)
        r = int(14 + 10 * t)
        g = int(26 + 26 * t)
        b = int(23 + 18 * t)
        d.rectangle((0, i, W * F.S, i + 4), fill=(r, g, b))

    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((760 * F.S, -140 * F.S, 1420 * F.S, 520 * F.S), fill=(31, 143, 106, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(120 * F.S))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")

    F.text(img, (72, 66), "DeepSeek Harness · dshfind 插件", 15, "#7FCFB2")
    F.text(img, (72, 112), "给 AI 装个「省钱表」", 54, "#FFFFFF", bold=True)
    F.text(img, (72, 196), "指令先瘦身，再把缓存差价算成钱", 24, "#C9D8D3")
    F.text(img, (72, 236), "左侧栏实时显示：本次省多少、累计省多少", 24, "#C9D8D3")

    # badge mock
    bx0, by0, bx1, by1 = 72, 316, 636, 392
    d.rounded_rectangle((bx0 * F.S, by0 * F.S, bx1 * F.S, by1 * F.S), radius=18 * F.S,
                        fill=(234, 246, 241, 26), outline=(143, 227, 196, 120), width=2 * F.S)
    d.ellipse((100 * F.S, 342 * F.S, 140 * F.S, 382 * F.S), fill="#1F8F6A")
    F.text(img, (120, 362), "¥", 22, "#FFFFFF", bold=True, anchor="mm")
    F.text(img, (158, 340), "本次 ¥2.39 · 累计 ¥34.00", 25, "#9FE7C9", bold=True)
    F.text(img, (158, 372), "命中 97.8% · 225 次调用", 13, "#8FAFA5")

    # stat row
    stats = [("¥34.00", "累计省下"), ("97.8%", "缓存命中"), ("−64 tok", "单条指令瘦身")]
    x = 72
    for value, label in stats:
        F.text(img, (x, 452), value, 34, "#FFFFFF", bold=True)
        F.text(img, (x, 496), label, 14, "#8FAFA5")
        x += 250

    F.rrect(img, (72, 556, 706, 612), 12, fill="#12241F", outline="#1E3A32")
    F.text(img, (92, 570), "npm i @acmepoyen/dsh-token-saver", 15, "#8FE3C4", mono=True)
    F.text(img, (92, 592), "market: dshfind.com · repo: lucaixia1982/dsh-token-saver", 11, "#7D968E")

    F.text(img, (860, 452), "本地计算 · 不联网", 14, "#7FCFB2")
    F.text(img, (860, 480), "不写任何全局状态", 14, "#7FCFB2")
    F.text(img, (860, 508), "三个价格都能改", 14, "#7FCFB2")
    F.text(img, (860, 552), "MIT · 纯 JS 无构建", 12, "#6D8C82")

    F.save(img, OUT + r"\fig0-cover.png", (W, H))


if __name__ == "__main__":
    fig3_cost()
    fig4_install()
    cover()
    print("fig0/fig3/fig4 ok")
