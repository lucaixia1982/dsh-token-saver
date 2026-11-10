"""Figure 1 (mechanism) and Figure 2 (before/after slimming)."""
from __future__ import annotations

import sys

from PIL import Image, ImageDraw

import figlib as F

OUT = r"F:\EngineeringProject\dsh-token-saver\press"


def fig1() -> None:
    W, H = 1200, 660
    img = F.canvas(W, H, F.PAPER)

    a = (32, 36, 348, 320)
    b = (434, 36, 768, 320)
    c = (852, 36, 1168, 320)
    for box in (a, b, c):
        F.card(img, box, 18)

    # ---- card A: the raw instruction
    F.text(img, (56, 60), "你打的字", 15, F.MUTED, bold=True)
    F.text(img, (56, 82), "自然语言，随你写", 12, F.FAINT)
    lines = [
        "把这个目录下 11 月的报表合并，",
        "字段留代码/名称/收盘价/成交量，",
        "按代码升序。",
        "",
        "注意：不要动原始文件。",
        "注意：不要动原始文件。",
        "弄完跟我说一声，谢谢！",
    ]
    y = 112
    for i, ln in enumerate(lines):
        if ln == "":
            y += 14
            continue
        if i in (5,):
            F.rrect(img, (52, y - 3, 328, y + 22), 6, fill=F.RED_SOFT, outline=None)
        if "谢谢" in ln:
            w = F.width_of(ln, 14)
            F.rrect(img, (56 + w - 46, y + 14, 56 + w, y + 21), 3, fill=F.RED_SOFT, outline=None)
        F.text(img, (56, y), ln, 14, F.INK_SOFT if i != 5 else F.RED)
        y += 25
    F.chip(img, (52, 272), "188 tok", size=13, fg=F.RED, bg=F.RED_SOFT)

    # ---- card B: the slimmer
    F.text(img, (458, 60), "瘦身器", 15, F.MUTED, bold=True)
    F.text(img, (458, 82), "在模型看见之前，只删零信息量字符", 12, F.FAINT)
    rules = [
        "行尾空格、连续空格",
        "连续空行（3 行以上压成 1 行）",
        "重复的行",
        "重复的段落（≥ 60 字才判重）",
        "结尾寒暄：谢谢 / 辛苦了 / thanks",
    ]
    y = 116
    for r in rules:
        d = ImageDraw.Draw(img)
        d.ellipse((460 * F.S, (y + 8) * F.S, 466 * F.S, (y + 14) * F.S), fill=F.BRAND)
        F.text(img, (476, y), r, 13, F.INK_SOFT)
        y += 27
    F.line(img, (458, 254, 744, 254), F.LINE)
    F.text(img, (458, 264), "代码块整段跳过，一个字不动。", 12, F.MUTED)
    F.text(img, (458, 284), "省得不够就不改：<15 tok 或 <4% 留原文。", 12, F.MUTED)

    # ---- card C: what the model gets
    F.text(img, (876, 60), "进模型的指令", 15, F.MUTED, bold=True)
    F.text(img, (876, 82), "少 64 个 token，意思一点没少", 12, F.FAINT)
    F.text(img, (876, 110), "124", 44, F.INK, bold=True)
    F.text(img, (876 + F.width_of("124", 44, bold=True) + 8, 134), "tok", 16, F.MUTED, bold=True)
    F.chip(img, (876, 186), "省 64 tok · 34%", size=13)
    F.line(img, (876, 232, 1144, 232), F.LINE)
    F.text(img, (876, 244), "历史前缀不变 →", 12, F.MUTED)
    F.text(img, (876, 264), "提示词缓存照常命中。", 12, F.MUTED)

    # ---- arrows
    F.arrow(img, (356, 178), (426, 178), fill="#BAC3CC", width=2)
    F.arrow(img, (776, 178), (844, 178), fill="#BAC3CC", width=2)

    # ---- bottom: accounting -> badge
    left = (32, 348, 700, 560)
    right = (716, 348, 1168, 560)
    F.card(img, left, 18)
    F.card(img, right, 18)

    F.text(img, (56, 370), "每次调用只记三个数", 15, F.MUTED, bold=True)
    cols = [
        ("未命中输入", "¥2 / M", F.RED, F.RED_SOFT),
        ("命中输入", "¥0.2 / M", F.ACCENT, F.ACCENT_SOFT),
        ("输出", "¥3 / M", F.AMBER, F.AMBER_SOFT),
    ]
    x = 56
    for name, price, fg, bg in cols:
        F.rrect(img, (x, 400, x + 190, 470), 12, fill=bg, outline=None)
        F.text(img, (x + 18, 414), name, 13, F.MUTED)
        F.text(img, (x + 18, 434), price, 20, fg, bold=True)
        x += 206
    F.text(img, (56, 490), "DeepSeek 官方口径：命中的输入比未命中便宜 10 倍。", 13, F.INK_SOFT)
    F.text(img, (56, 514), "插件的每一分「省」，都按这三个价码换算成钱。", 13, F.MUTED)

    F.text(img, (740, 370), "左侧栏", 15, F.MUTED, bold=True)
    F.text(img, (740, 392), "会话底部，扫一眼就知道省了多少", 12, F.FAINT)
    # badge mock
    bx0, by0, bx1, by1 = 740, 420, 1144, 468
    F.rrect(img, (bx0, by0, bx1, by1), 12, fill=F.BRAND_SOFT, outline=None)
    F.badge_icon(img, bx0 + 24, (by0 + by1) / 2, 12)
    F.text(img, (bx0 + 44, (by0 + by1) / 2), "本次 ¥2.39 · 累计 ¥34.00", 16,
           F.BRAND_DEEP, bold=True, anchor="lm")
    F.text(img, (740, 486), "点开：命中率 97.8% · 225 次调用 · 缓存前缀重建 3 次", 12, F.MUTED)
    F.text(img, (740, 510), "数据只写本地 ~/.dsh/dsh-token-saver.json，不联网。", 12, F.MUTED)

    F.text(img, (32, 588), "价格默认按 DeepSeek 目录价（未命中 ¥2 / 命中 ¥0.2 / 输出 ¥3，每百万 token），可在 config 里改成你实际网关的价。",
           13, F.MUTED)
    F.text(img, (32, 614), "瘦身带来的直接节省是零头；真正的大头是「命中 vs 未命中」这 10 倍差价 —— 插件把这件事第一次算成了钱。",
           13, F.INK_SOFT)

    F.save(img, OUT + r"\fig1-mechanism.png", (W, H))


def fig2() -> None:
    W, H = 1200, 760
    img = F.canvas(W, H, F.PAPER)

    left = (32, 36, 592, 636)
    right = (608, 36, 1168, 636)
    F.card(img, left, 18)
    F.card(img, right, 18)

    F.text(img, (56, 60), "原始指令", 16, F.INK, bold=True)
    F.chip(img, (452, 58), "188 tok", size=13, fg=F.RED, bg=F.RED_SOFT)
    F.text(img, (56, 88), "模型原本要读这些", 12, F.FAINT)

    F.text(img, (632, 60), "进模型的指令", 16, F.INK, bold=True)
    F.chip(img, (1028, 58), "124 tok", size=13)
    F.text(img, (632, 88), "同一件事，同样的约束", 12, F.FAINT)

    rows = [
        ("把这个目录下 11 月的报表合并，", "keep"),
        ("字段留代码/名称/收盘价/成交量，", "keep"),
        ("按代码升序。", "keep"),
        ("", "blank"),
        ("注意：不要动原始文件。", "dup"),
        ("注意：不要动原始文件。", "dup2"),
        ("弄完跟我说一声，谢谢！", "filler"),
    ]
    y = 124
    for txt, kind in rows:
        if kind == "blank":
            y += 16
            continue
        if kind in ("dup", "dup2"):
            F.rrect(img, (48, y - 4, 576, y + 30), 7, fill=F.RED_SOFT, outline=None)
            F.text(img, (56, y), txt, 17, F.RED)
            if kind == "dup2":
                F.text(img, (470, y + 6), "重复", 12, F.RED)
        elif kind == "filler":
            F.text(img, (56, y), txt, 17, F.INK_SOFT)
            w = F.width_of(txt, 17)
            F.rrect(img, (56 + w - 56, y + 18, 56 + w, y + 26), 3, fill=F.RED_SOFT, outline=None)
            F.text(img, (470, y + 6), "寒暄", 12, F.RED)
        else:
            F.text(img, (56, y), txt, 17, F.INK_SOFT)
        y += 36

    F.text(img, (56, 386), "删掉了什么", 13, F.MUTED, bold=True)
    F.text(img, (56, 410), "重复段落 ×1　·　结尾寒暄 ×1（谢谢！）", 14, F.INK_SOFT)
    F.text(img, (56, 434), "空行 ×1 —— 这 64 个 token 的全部来源", 14, F.INK_SOFT)
    F.text(img, (56, 466), "红色 = 删掉的部分；字段、条件、边界一个字没动。", 13, F.MUTED)
    F.text(img, (56, 488), "指令本身的意思、约束、顺序全部保留。", 13, F.MUTED)
    F.dashed(img, (48, 526, 576, 600), 10, fill="#CBD3DB")
    F.text(img, (64, 544), "代码块 / 运行时上下文：完全不动", 13, F.MUTED)
    F.text(img, (64, 566), "（围栏里的内容整段跳过，不做任何处理）", 12, F.FAINT)

    # right side result
    y = 124
    kept = [
        "把这个目录下 11 月的报表合并，",
        "字段留代码/名称/收盘价/成交量，",
        "按代码升序。",
        "注意：不要动原始文件。",
        "弄完跟我说一声",
    ]
    for txt in kept:
        F.text(img, (632, y), txt, 17, F.INK_SOFT)
        y += 36

    F.line(img, (632, 330, 1144, 330), F.LINE)
    F.text(img, (632, 348), "结果", 13, F.MUTED, bold=True)
    stats = [("188 → 124 tok", "−64"), ("−34%", ""), ("代码块 0 字改动", "")]
    x = 632
    x, _ = F.chip(img, (x, 372), "188 → 124 tok", size=14)
    x, _ = F.chip(img, (x + 10, 372), "−64 tok", size=14)
    x, _ = F.chip(img, (x + 10, 372), "−34%", size=14)
    F.text(img, (632, 420), "省下的 64 个 token 只值 ¥0.0001 量级。", 14, F.INK_SOFT)
    F.text(img, (632, 444), "所以它只是配菜。主菜是下面那张图：", 14, F.INK_SOFT)
    F.text(img, (632, 468), "同样的输入，命中缓存比不命中便宜 10 倍。", 14, F.INK_SOFT)

    F.rrect(img, (632, 506, 1144, 612), 12, fill=F.BRAND_SOFT, outline=None)
    F.text(img, (652, 522), "保守开关", 13, F.BRAND_DEEP, bold=True)
    F.text(img, (652, 546), "省不到 15 tok，或不到原文字数 4%，", 13, F.INK_SOFT)
    F.text(img, (652, 568), "插件就原样放行，不改你的话。", 13, F.INK_SOFT)

    F.text(img, (32, 668), "样本：一条真实的「合并报表」指令。瘦身只做字符级的无损清理，不重写、不总结、不压缩语义。",
           13, F.MUTED)
    F.text(img, (32, 700), "改写发生在 agent/pre-step：模型收到的是瘦身后的文本，而会话记录里留的也是它 —— 你随时能回看。",
           13, F.MUTED)

    F.save(img, OUT + r"\fig2-slimming.png", (W, H))


if __name__ == "__main__":
    fig1()
    fig2()
    print("fig1/fig2 ok")
