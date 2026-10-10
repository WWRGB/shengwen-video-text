import os
import sys
import wave
import shutil
import tempfile
import threading
import subprocess
import json
import html
import time
import urllib.parse
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

APP_NAME = "声文 · 视频转文字"
APP_VERSION = "5.0"

# Visual system: warm light canvas, white cards, ink typography, and a single blue accent.
BG = "#F3F6FB"
CARD = "#FFFFFF"
INK = "#172033"
MUTED = "#66758B"
BORDER = "#E0E7F0"
ACCENT = "#3563E9"
ACCENT_HOVER = "#274FCE"
SUCCESS = "#14804A"
DANGER = "#B42318"
FONT = "Microsoft YaHei UI"

# Whisper 多语言模型支持的语言代码（与上游 tokenizer 的 99 个语言代码保持一致）。
LANGUAGE_OPTIONS = [
    ("自动检测（逐段识别，适合混合语言）", None),
    ('中文（普通话）', 'zh'),
    ('粤语 / 地方汉语方言（自动检测，提示词辅助）', None),
    ('英语', 'en'),
    ('西班牙语', 'es'),
    ('法语', 'fr'),
    ('德语', 'de'),
    ('日语', 'ja'),
    ('韩语', 'ko'),
    ('葡萄牙语', 'pt'),
    ('俄语', 'ru'),
    ('阿拉伯语', 'ar'),
    ('印地语', 'hi'),
    ('孟加拉语', 'bn'),
    ('旁遮普语', 'pa'),
    ('乌尔都语', 'ur'),
    ('波斯语', 'fa'),
    ('土耳其语', 'tr'),
    ('意大利语', 'it'),
    ('荷兰语', 'nl'),
    ('波兰语', 'pl'),
    ('乌克兰语', 'uk'),
    ('越南语', 'vi'),
    ('泰语', 'th'),
    ('印度尼西亚语', 'id'),
    ('马来语', 'ms'),
    ('菲律宾语 / 他加禄语', 'tl'),
    ('希伯来语', 'he'),
    ('希腊语', 'el'),
    ('捷克语', 'cs'),
    ('瑞典语', 'sv'),
    ('丹麦语', 'da'),
    ('芬兰语', 'fi'),
    ('挪威语', 'no'),
    ('新挪威语（Nynorsk）', 'nn'),
    ('法罗语', 'fo'),
    ('罗马尼亚语', 'ro'),
    ('匈牙利语', 'hu'),
    ('保加利亚语', 'bg'),
    ('克罗地亚语', 'hr'),
    ('塞尔维亚语', 'sr'),
    ('斯洛伐克语', 'sk'),
    ('斯洛文尼亚语', 'sl'),
    ('立陶宛语', 'lt'),
    ('拉脱维亚语', 'lv'),
    ('爱沙尼亚语', 'et'),
    ('加泰罗尼亚语', 'ca'),
    ('巴斯克语', 'eu'),
    ('加利西亚语', 'gl'),
    ('威尔士语', 'cy'),
    ('冰岛语', 'is'),
    ('卢森堡语', 'lb'),
    ('马耳他语', 'mt'),
    ('阿尔巴尼亚语', 'sq'),
    ('亚美尼亚语', 'hy'),
    ('格鲁吉亚语', 'ka'),
    ('阿塞拜疆语', 'az'),
    ('哈萨克语', 'kk'),
    ('乌兹别克语', 'uz'),
    ('蒙古语', 'mn'),
    ('藏语', 'bo'),
    ('缅甸语', 'my'),
    ('高棉语', 'km'),
    ('老挝语', 'lo'),
    ('尼泊尔语', 'ne'),
    ('僧伽罗语', 'si'),
    ('泰米尔语', 'ta'),
    ('泰卢固语', 'te'),
    ('卡纳达语', 'kn'),
    ('马拉雅拉姆语', 'ml'),
    ('马拉地语', 'mr'),
    ('古吉拉特语', 'gu'),
    ('阿萨姆语', 'as'),
    ('梵语', 'sa'),
    ('信德语', 'sd'),
    ('普什图语', 'ps'),
    ('塔吉克语', 'tg'),
    ('土库曼语', 'tk'),
    ('鞑靼语', 'tt'),
    ('巴什基尔语', 'ba'),
    ('白俄罗斯语', 'be'),
    ('波斯尼亚语', 'bs'),
    ('马其顿语', 'mk'),
    ('斯瓦希里语', 'sw'),
    ('豪萨语', 'ha'),
    ('约鲁巴语', 'yo'),
    ('索马里语', 'so'),
    ('阿姆哈拉语', 'am'),
    ('南非荷兰语', 'af'),
    ('修纳语', 'sn'),
    ('林加拉语', 'ln'),
    ('马达加斯加语', 'mg'),
    ('毛利语', 'mi'),
    ('夏威夷语', 'haw'),
    ('爪哇语', 'jw'),
    ('巽他语', 'su'),
    ('拉丁语', 'la'),
    ('布列塔尼语', 'br'),
    ('奥克语', 'oc'),
    ('意第绪语', 'yi'),
    ('海地克里奥尔语', 'ht'),
]
LANGUAGE_CODE_BY_LABEL = {label: code for label, code in LANGUAGE_OPTIONS}
LANGUAGE_NAME_BY_CODE = {code: label for label, code in LANGUAGE_OPTIONS if code}

# MyMemory is used only when the user explicitly clicks Translate and accepts sending text online.
# The provider may not support every source/target pair; the app reports failures rather than silently substituting text.
TARGET_LANGUAGE_OPTIONS = [
    ("简体中文", "zh-CN"), ("英语", "en"), ("日语", "ja"), ("韩语", "ko"),
    ("西班牙语", "es"), ("法语", "fr"), ("德语", "de"), ("葡萄牙语", "pt-PT"),
    ("俄语", "ru"), ("阿拉伯语", "ar"), ("印地语", "hi"), ("孟加拉语", "bn"),
    ("乌尔都语", "ur"), ("波斯语", "fa"), ("土耳其语", "tr"), ("意大利语", "it"),
    ("荷兰语", "nl"), ("波兰语", "pl"), ("乌克兰语", "uk"), ("越南语", "vi"),
    ("泰语", "th"), ("印度尼西亚语", "id"), ("马来语", "ms"), ("菲律宾语", "tl"),
    ("希伯来语", "he"), ("希腊语", "el"), ("捷克语", "cs"), ("瑞典语", "sv"),
    ("丹麦语", "da"), ("芬兰语", "fi"), ("挪威语", "no"), ("罗马尼亚语", "ro"),
    ("匈牙利语", "hu"), ("保加利亚语", "bg"), ("克罗地亚语", "hr"), ("塞尔维亚语", "sr"),
    ("斯洛伐克语", "sk"), ("斯洛文尼亚语", "sl"), ("立陶宛语", "lt"), ("拉脱维亚语", "lv"),
    ("爱沙尼亚语", "et"), ("加泰罗尼亚语", "ca"), ("威尔士语", "cy"), ("冰岛语", "is"),
    ("阿尔巴尼亚语", "sq"), ("亚美尼亚语", "hy"), ("格鲁吉亚语", "ka"), ("阿塞拜疆语", "az"),
    ("哈萨克语", "kk"), ("乌兹别克语", "uz"), ("蒙古语", "mn"), ("尼泊尔语", "ne"),
    ("僧伽罗语", "si"), ("泰米尔语", "ta"), ("泰卢固语", "te"), ("卡纳达语", "kn"),
    ("马拉雅拉姆语", "ml"), ("马拉地语", "mr"), ("古吉拉特语", "gu"), ("阿萨姆语", "as"),
    ("普什图语", "ps"), ("塔吉克语", "tg"), ("土库曼语", "tk"), ("鞑靼语", "tt"),
    ("白俄罗斯语", "be"), ("波斯尼亚语", "bs"), ("马其顿语", "mk"), ("斯瓦希里语", "sw"),
    ("豪萨语", "ha"), ("约鲁巴语", "yo"), ("索马里语", "so"), ("阿姆哈拉语", "am"),
    ("南非荷兰语", "af"), ("修纳语", "sn"), ("林加拉语", "ln"), ("马达加斯加语", "mg"),
]
TARGET_CODE_BY_LABEL = {label: code for label, code in TARGET_LANGUAGE_OPTIONS}
LANGUAGE_CODE_ALIASES = {"zh": "zh-CN", "pt": "pt-PT", "tl": "tl", "jw": "jv", "haw": "haw"}


def resource_path(relative_path):
    """Resolve a bundled or source-relative resource path."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(sys.argv[0])))
    return os.path.join(base, relative_path)


def ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def format_time(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class SpeechTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1240x900")
        self.root.minsize(1000, 720)
        self.root.configure(bg=BG)
        self.video_path = ""
        self.transcript_segments = []          # user-editable source subtitle rows
        self.original_segments = []            # immutable snapshot of the first-pass ASR result
        self.transcript_text = ""
        self.translation_segments = []
        self.translation_complete = False
        self.translation_target_code = ""
        self.translation_target_label = ""
        self.translation_privacy_accepted = False
        self.subtitle_translation_var = tk.BooleanVar(value=True)
        self.busy = False
        self.audio_duration = 0.0
        self.review_report_rows = []
        self.language_summary = ""
        self.last_processing_options = {}
        self._style()
        self._build()
        self._on_mode_change()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        width = min(1240, self.root.winfo_screenwidth() - 40)
        height = min(900, self.root.winfo_screenheight() - 60)
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Modern.TCombobox", padding=(10, 8), font=(FONT, 10),
            fieldbackground="#FFFFFF", background="#FFFFFF", foreground=INK,
            arrowcolor=MUTED, bordercolor=BORDER, lightcolor=BORDER,
            darkcolor=BORDER, insertcolor=INK
        )
        style.map(
            "Modern.TCombobox",
            fieldbackground=[("readonly", "#FFFFFF"), ("disabled", "#F3F5F8")],
            foreground=[("readonly", INK), ("disabled", MUTED)],
            selectbackground=[("readonly", "#FFFFFF")],
            selectforeground=[("readonly", INK)]
        )
        style.configure(
            "Modern.Horizontal.TProgressbar", troughcolor="#E8EDF5",
            background=ACCENT, bordercolor="#E8EDF5", lightcolor=ACCENT,
            darkcolor=ACCENT, thickness=9
        )

    def _button(self, parent, text, command, kind="secondary", state="normal", width=None):
        if kind == "primary":
            bg, fg, active_bg, active_fg = ACCENT, "#FFFFFF", ACCENT_HOVER, "#FFFFFF"
        elif kind == "ghost":
            bg, fg, active_bg, active_fg = CARD, ACCENT, "#EEF3FF", ACCENT_HOVER
        else:
            bg, fg, active_bg, active_fg = "#F7F9FC", INK, "#EDF2F8", INK
        options = dict(
            text=text, command=command, bg=bg, fg=fg, activebackground=active_bg,
            activeforeground=active_fg, disabledforeground="#A4AFBF",
            relief="flat", bd=0, padx=14, pady=10,
            font=(FONT, 10, "bold" if kind == "primary" else "normal"),
            cursor="hand2" if state == "normal" else "arrow", state=state,
            highlightthickness=1, highlightbackground=ACCENT if kind == "primary" else BORDER,
            highlightcolor=ACCENT
        )
        if width is not None:
            options["width"] = width
        return tk.Button(parent, **options)

    def _card(self, parent, **grid_options):
        border = tk.Frame(parent, bg=BORDER, bd=0, highlightthickness=0)
        inner = tk.Frame(border, bg=CARD, padx=18, pady=16)
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        if grid_options:
            border.grid(**grid_options)
        return border, inner

    def _section_title(self, parent, number, title):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", pady=(0, 14))
        badge = tk.Label(row, text=number, bg="#EDF2FF", fg=ACCENT, font=(FONT, 9, "bold"), padx=8, pady=4)
        badge.pack(side="left")
        tk.Label(row, text=title, bg=CARD, fg=INK, font=(FONT, 12, "bold")).pack(side="left", padx=(9, 0))
        return row

    def _build(self):
        # Top brand strip
        topbar = tk.Frame(self.root, bg="#111B2E", height=66)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        brand = tk.Frame(topbar, bg="#111B2E")
        brand.pack(side="left", padx=24, fill="y")
        logo = tk.Label(brand, text="声", bg=ACCENT, fg="#FFFFFF", font=(FONT, 17, "bold"), width=2, height=1)
        logo.pack(side="left", pady=12)
        brand_text = tk.Frame(brand, bg="#111B2E")
        brand_text.pack(side="left", padx=(11, 0), pady=11)
        tk.Label(brand_text, text="声文", bg="#111B2E", fg="#FFFFFF", font=(FONT, 15, "bold")).pack(anchor="w")
        tk.Label(brand_text, text="视频 · 语音 · 字幕成片", bg="#111B2E", fg="#AEBBD0", font=(FONT, 9)).pack(anchor="w")
        self.header_status = tk.Label(topbar, text="●  已就绪", bg="#193B33", fg="#8EE0BA", font=(FONT, 9, "bold"), padx=12, pady=7)
        self.header_status.pack(side="right", padx=24, pady=18)

        outer = tk.Frame(self.root, bg=BG, padx=24, pady=20)
        outer.pack(fill="both", expand=True)

        intro = tk.Frame(outer, bg=BG)
        intro.pack(fill="x", pady=(0, 16))
        tk.Label(intro, text="把视频里的话，变成可编辑的文字", bg=BG, fg=INK, font=(FONT, 21, "bold")).pack(anchor="w")
        tk.Label(
            intro,
            text="多语言语音识别 · 口音提示 · 导出 TXT / SRT / MP3 / WAV · 生成带字幕视频",
            bg=BG, fg=MUTED, font=(FONT, 10)
        ).pack(anchor="w", pady=(5, 0))

        # Source file card
        source_border, source = self._card(outer)
        source_border.pack(fill="x")
        self._section_title(source, "01", "选择视频")
        source_row = tk.Frame(source, bg=CARD)
        source_row.pack(fill="x")
        self.file_icon = tk.Label(source_row, text="▶", bg="#EEF3FF", fg=ACCENT, font=(FONT, 14, "bold"), width=4, pady=11)
        self.file_icon.pack(side="left")
        file_meta = tk.Frame(source_row, bg=CARD)
        file_meta.pack(side="left", fill="x", expand=True, padx=12)
        self.file_label = tk.Label(file_meta, text="还没有选择视频", bg=CARD, fg=INK, font=(FONT, 10, "bold"), anchor="w")
        self.file_label.pack(fill="x", anchor="w")
        self.file_hint = tk.Label(file_meta, text="支持 MP4、MOV、MKV、AVI、WEBM 等常见格式", bg=CARD, fg=MUTED, font=(FONT, 9), anchor="w")
        self.file_hint.pack(fill="x", anchor="w", pady=(4, 0))
        self.pick_btn = self._button(source_row, "选择视频文件", self.pick_video, kind="secondary")
        self.pick_btn.pack(side="right")
        self.start_btn = self._button(source_row, "开始识别语音", self.start_processing, kind="primary", state="disabled")
        self.start_btn.pack(side="right", padx=(0, 8))

        # Body: settings/action column and transcript column
        body = tk.Frame(outer, bg=BG)
        body.pack(fill="both", expand=True, pady=(14, 0))
        body.grid_columnconfigure(0, weight=4, uniform="body")
        body.grid_columnconfigure(1, weight=6, uniform="body")
        body.grid_rowconfigure(0, weight=1)

        # Scrollable settings card: keeps the main action reachable on 720p laptops.
        left_border = tk.Frame(body, bg=BORDER, bd=0, highlightthickness=0)
        left_border.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        left_border.grid_rowconfigure(0, weight=1)
        left_border.grid_columnconfigure(0, weight=1)
        left_canvas = tk.Canvas(left_border, bg=CARD, highlightthickness=0, bd=0)
        left_scrollbar = ttk.Scrollbar(left_border, orient="vertical", command=left_canvas.yview)
        left_canvas.configure(yscrollcommand=left_scrollbar.set)
        left_canvas.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        left_scrollbar.grid(row=0, column=1, sticky="ns", pady=1)
        left = tk.Frame(left_canvas, bg=CARD, padx=18, pady=16)
        left_window = left_canvas.create_window((0, 0), window=left, anchor="nw")
        left.bind("<Configure>", lambda _event: left_canvas.configure(scrollregion=left_canvas.bbox("all")))
        left_canvas.bind("<Configure>", lambda event: left_canvas.itemconfigure(left_window, width=event.width))
        self._section_title(left, "02", "识别设置")

        tk.Label(left, text="操作模式", bg=CARD, fg=INK, font=(FONT, 10)).pack(anchor="w")
        self.mode_var = tk.StringVar(value="简单模式")
        self.mode_combo = ttk.Combobox(
            left, textvariable=self.mode_var, state="readonly", style="Modern.TCombobox",
            values=["简单模式", "专业模式"],
        )
        self.mode_combo.pack(fill="x", pady=(5, 10))
        self.mode_combo.bind("<<ComboboxSelected>>", self._on_mode_change)

        tk.Label(left, text="语音语言（自动逐段检测；也可手动指定）", bg=CARD, fg=INK, font=(FONT, 10)).pack(anchor="w")
        self.lang_var = tk.StringVar(value=LANGUAGE_OPTIONS[0][0])
        self.lang_combo = ttk.Combobox(
            left, textvariable=self.lang_var, state="readonly", style="Modern.TCombobox",
            values=[label for label, _code in LANGUAGE_OPTIONS],
        )
        self.lang_combo.pack(fill="x", pady=(5, 6))
        tk.Label(
            left, text="自动语种检测按约 20 秒重叠片段进行，适合发现视频中的语种切换。方言/口音无法保证被准确分类，请在提示中注明，结果仍需复核。",
            bg=CARD, fg=MUTED, font=(FONT, 9), justify="left", wraplength=390
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(left, text="识别模型", bg=CARD, fg=INK, font=(FONT, 10)).pack(anchor="w")
        self.model_var = tk.StringVar(value="medium（更准确）")
        self.model_combo = ttk.Combobox(
            left, textvariable=self.model_var, state="readonly", style="Modern.TCombobox",
            values=["small（速度较快）", "medium（更准确）", "large-v3（高准确，较慢）"],
        )
        self.model_combo.pack(fill="x", pady=(5, 7))
        tk.Label(
            left, text="模型越大通常越准确，但更慢、占用更多内存，首次使用需下载模型。",
            bg=CARD, fg=MUTED, font=(FONT, 9), justify="left", wraplength=390
        ).pack(anchor="w", pady=(0, 7))

        tk.Label(left, text="译文目标语言（可选；先识别原文，再单独翻译）", bg=CARD, fg=INK, font=(FONT, 10)).pack(anchor="w")
        self.translation_target_var = tk.StringVar(value="简体中文")
        self.translation_target_combo = ttk.Combobox(
            left, textvariable=self.translation_target_var, state="readonly", style="Modern.TCombobox",
            values=[label for label, _code in TARGET_LANGUAGE_OPTIONS],
        )
        self.translation_target_combo.pack(fill="x", pady=(5, 6))
        self.translate_btn = self._button(left, "生成译文（联网）", self.start_translation, kind="secondary", state="disabled")
        self.translate_btn.pack(fill="x", pady=(0, 5))
        tk.Label(
            left, text="翻译会把字幕文字发送到 MyMemory 在线翻译服务（不上传视频/音频）。不同语种组合可能不受支持，并受服务可用性与额度限制；方言语义仍需人工核对。",
            bg=CARD, fg=MUTED, font=(FONT, 8), justify="left", wraplength=390
        ).pack(anchor="w", pady=(0, 8))

        self.enhance_var = tk.BooleanVar(value=True)
        self.enhance_check = tk.Checkbutton(
            left, text="基础人声清理（轻降噪 + 音量均衡，默认开启）", variable=self.enhance_var,
            bg=CARD, fg=INK, activebackground=CARD, activeforeground=INK,
            selectcolor="#EEF3FF", font=(FONT, 9), anchor="w", padx=0,
        )
        self.enhance_check.pack(fill="x", pady=(0, 5))
        self.vad_var = tk.BooleanVar(value=False)
        self.vad_check = tk.Checkbutton(
            left, text="跳过长静音（可能漏掉轻声，默认关闭）", variable=self.vad_var,
            bg=CARD, fg=INK, activebackground=CARD, activeforeground=INK,
            selectcolor="#EEF3FF", font=(FONT, 9), anchor="w", padx=0,
        )
        self.vad_check.pack(fill="x", pady=(0, 12))

        prompt_header = tk.Frame(left, bg=CARD)
        prompt_header.pack(fill="x")
        tk.Label(prompt_header, text="口音 / 方言 / 专有词提示（选填，不代表自动方言分类）", bg=CARD, fg=INK, font=(FONT, 10)).pack(side="left", anchor="w")
        self.prompt_var = tk.StringVar()
        self.prompt_entry = tk.Entry(
            left, textvariable=self.prompt_var, relief="flat", bd=0, bg="#F7F9FC", fg=INK,
            insertbackground=INK, font=(FONT, 10), highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT
        )
        self.prompt_entry.pack(fill="x", ipady=9, pady=(5, 12))
        self.prompt_entry.insert(0, "例如：墨西哥西班牙语口音；粤语口语；术语/人名/地名")
        self.prompt_entry.configure(fg="#8390A3")
        self.prompt_entry.bind("<FocusIn>", self._clear_prompt_placeholder)
        self.prompt_entry.bind("<FocusOut>", self._restore_prompt_placeholder)

        audio_row = tk.Frame(left, bg=CARD)
        audio_row.pack(fill="x")
        self.mp3_btn = self._button(audio_row, "导出 MP3", lambda: self.export_audio("mp3"), kind="secondary", state="disabled")
        self.mp3_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.wav_btn = self._button(audio_row, "导出 WAV", lambda: self.export_audio("wav"), kind="secondary", state="disabled")
        self.wav_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Right transcript card
        _, right = self._card(body)
        right.master.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        right.pack_propagate(False)
        result_header = tk.Frame(right, bg=CARD)
        result_header.pack(fill="x", pady=(0, 10))
        self._section_title(result_header, "03", "识别结果")
        exports = tk.Frame(result_header, bg=CARD)
        exports.pack(side="right", anchor="e", pady=(0, 14))
        self.copy_btn = self._button(exports, "复制", self.copy_text, kind="ghost", state="disabled")
        self.copy_btn.pack(side="left", padx=(0, 5))
        self.srt_btn = self._button(exports, "导出 SRT", self.export_srt, kind="secondary", state="disabled")
        self.srt_btn.pack(side="left", padx=(0, 5))
        self.txt_btn = self._button(exports, "导出 TXT", self.export_txt, kind="secondary", state="disabled")
        self.txt_btn.pack(side="left", padx=(0, 5))
        self.subtitle_video_btn = self._button(
            exports, "生成带字幕视频", self.export_subtitled_video,
            kind="primary", state="disabled"
        )
        self.subtitle_video_btn.pack(side="left")

        self.translation_toolbar = tk.Frame(right, bg=CARD)
        self.translation_toolbar.pack(fill="x", pady=(0, 8))
        self.export_original_btn = self._button(self.translation_toolbar, "导出原始转写", self.export_original_txt, kind="ghost", state="disabled")
        self.export_original_btn.pack(side="left", padx=(0, 6))
        self.export_translated_srt_btn = self._button(self.translation_toolbar, "导出译文 SRT", self.export_translated_srt, kind="ghost", state="disabled")
        self.export_translated_srt_btn.pack(side="left", padx=(0, 6))
        self.export_translated_txt_btn = self._button(self.translation_toolbar, "导出译文 TXT", self.export_translated_txt, kind="ghost", state="disabled")
        self.export_translated_txt_btn.pack(side="left", padx=(0, 8))
        self.use_translation_check = tk.Checkbutton(
            self.translation_toolbar, text="生成视频时使用译文字幕（有译文时）",
            variable=self.subtitle_translation_var, bg=CARD, fg=INK, activebackground=CARD,
            selectcolor="#EEF3FF", font=(FONT, 9), anchor="w", padx=0,
        )
        self.use_translation_check.pack(side="left", fill="x", expand=True)

        text_wrap = tk.Frame(right, bg=BORDER, padx=1, pady=1)
        text_wrap.pack(fill="both", expand=True)
        # Reserve enough room for status/progress below the editor; otherwise a short screen can clip them.
        text_wrap.configure(height=285)
        text_wrap.pack_propagate(False)
        self.text_tabs = ttk.Notebook(text_wrap)
        self.text_tabs.pack(fill="both", expand=True)
        editor_tab = tk.Frame(self.text_tabs, bg=CARD)
        original_tab = tk.Frame(self.text_tabs, bg=CARD)
        translation_tab = tk.Frame(self.text_tabs, bg=CARD)
        self.text_tabs.add(editor_tab, text="编辑稿（每行一条字幕）")
        self.text_tabs.add(original_tab, text="原始转写（保留不改）")
        self.text_tabs.add(translation_tab, text="译文（可编辑）")
        self.textbox = ScrolledText(
            editor_tab, wrap="word", relief="flat", bd=0, bg="#FBFCFE", fg=INK,
            insertbackground=INK, font=(FONT, 10), padx=13, pady=12, spacing1=2,
            spacing3=3, undo=True
        )
        self.textbox.pack(fill="both", expand=True)
        self.original_textbox = ScrolledText(
            original_tab, wrap="word", relief="flat", bd=0, bg="#F6F8FB", fg=INK,
            font=(FONT, 10), padx=13, pady=12, spacing1=2, spacing3=3
        )
        self.original_textbox.pack(fill="both", expand=True)
        self.translation_textbox = ScrolledText(
            translation_tab, wrap="word", relief="flat", bd=0, bg="#FBFCFE", fg=INK,
            insertbackground=INK, font=(FONT, 10), padx=13, pady=12, spacing1=2,
            spacing3=3, undo=True
        )
        self.translation_textbox.pack(fill="both", expand=True)
        self._show_placeholder()
        self.original_textbox.insert("1.0", "原始识别结果会单独保留在这里。")
        self.original_textbox.configure(state="disabled", fg="#8390A3")
        self.translation_textbox.insert("1.0", "识别完成后，可选择目标语言并点击左侧「生成译文」。")
        self.translation_textbox.configure(fg="#8390A3")

        progress_area = tk.Frame(right, bg=CARD)
        progress_area.pack(fill="x", pady=(12, 0))
        status_row = tk.Frame(progress_area, bg=CARD)
        status_row.pack(fill="x", pady=(0, 7))
        self.status_var = tk.StringVar(value="准备就绪。选择视频后，可开始识别或单独导出音频。")
        self.status_label = tk.Label(status_row, textvariable=self.status_var, bg=CARD, fg=MUTED, font=(FONT, 9), anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        self.percent_var = tk.StringVar(value="0%")
        tk.Label(status_row, textvariable=self.percent_var, bg=CARD, fg=ACCENT, font=(FONT, 9, "bold")).pack(side="right")
        self.progress = ttk.Progressbar(progress_area, mode="determinate", maximum=100, value=0, style="Modern.Horizontal.TProgressbar")
        self.progress.pack(fill="x")
        self.review_btn = self._button(progress_area, "导出语言与质量校对表 CSV", self.export_review_report, kind="ghost", state="disabled")
        self.review_btn.pack(anchor="e", pady=(8, 0))
        tk.Label(
            outer, text="默认简单模式：自动逐段识别、基础音频清理、自动复核。方言识别与机器翻译仍可能出错；原始转写会单独保留。",
            bg=BG, fg=MUTED, font=(FONT, 9), anchor="w"
        ).pack(fill="x", pady=(12, 0))

    def _on_mode_change(self, event=None):
        """Simple mode is an actual preset; professional mode unlocks model/VAD choices."""
        simple = self.mode_var.get() == "简单模式"
        if simple:
            self.model_var.set("medium（更准确）")
            self.vad_var.set(False)
        if hasattr(self, "model_combo"):
            self.model_combo.configure(state="disabled" if simple or self.busy else "readonly")
        if hasattr(self, "vad_check"):
            self.vad_check.configure(state="disabled" if simple or self.busy else "normal")
        if hasattr(self, "enhance_check"):
            self.enhance_check.configure(state="disabled" if self.busy else "normal")
        self.status_var.set("简单模式：medium 模型、自动逐段检测语种、轻度音频清理、自动复核。" if simple else "专业模式：可自行调整模型、语种、音频处理和 VAD 选项。")

    def _clear_prompt_placeholder(self, event=None):
        placeholder = "例如：墨西哥西班牙语口音；粤语口语；术语/人名/地名"
        if self.prompt_var.get() == placeholder:
            self.prompt_var.set("")
            self.prompt_entry.configure(fg=INK)

    def _restore_prompt_placeholder(self, event=None):
        if not self.prompt_var.get().strip():
            self.prompt_var.set("例如：墨西哥西班牙语口音；粤语口语；术语/人名/地名")
            self.prompt_entry.configure(fg="#8390A3")

    def _get_prompt_text(self):
        value = self.prompt_var.get().strip()
        placeholder = "例如：墨西哥西班牙语口音；粤语口语；术语/人名/地名"
        return "" if value == placeholder else value

    def _show_placeholder(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", "识别文字会在这里实时显示。\n\n处理流程：\n1. 音频预处理（可关闭）\n2. 按片段识别语种并转写\n3. 对低置信片段二次解码\n4. 标记疑似错词、语种不确定和长间隔\n\n方言/口音不保证自动识别正确，请导出校对表复核。")
        self.textbox.configure(fg="#8390A3")

    def _set_status(self, text, percent=None, color=None):
        def apply():
            self.status_var.set(text)
            if percent is not None:
                self.percent_var.set(f"{int(max(0, min(100, percent)))}%")
                self.progress.configure(value=max(0, min(100, percent)))
            if color:
                self.status_label.configure(fg=color)
        self.root.after(0, apply)

    def _set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.start_btn.configure(state="disabled" if busy or not self.video_path else "normal")
        self.pick_btn.configure(state=state)
        self.lang_combo.configure(state="disabled" if busy else "readonly")
        simple_mode = getattr(self, "mode_var", None) is not None and self.mode_var.get() == "简单模式"
        self.model_combo.configure(state="disabled" if busy or simple_mode else "readonly")
        if hasattr(self, "translation_target_combo"):
            self.translation_target_combo.configure(state="disabled" if busy else "readonly")
        if hasattr(self, "translate_btn"):
            self.translate_btn.configure(state="disabled" if busy or not self.transcript_segments else "normal")
        if hasattr(self, "export_original_btn"):
            self.export_original_btn.configure(state="disabled" if busy or not self.original_segments else "normal")
        if hasattr(self, "export_translated_srt_btn"):
            self.export_translated_srt_btn.configure(state="disabled" if busy or not self.translation_complete else "normal")
        if hasattr(self, "export_translated_txt_btn"):
            self.export_translated_txt_btn.configure(state="disabled" if busy or not self.translation_complete else "normal")
        if hasattr(self, "mode_combo"):
            self.mode_combo.configure(state="disabled" if busy else "readonly")
        self.prompt_entry.configure(state=state)
        self.enhance_check.configure(state=state)
        simple_mode = getattr(self, "mode_var", None) is not None and self.mode_var.get() == "简单模式"
        self.vad_check.configure(state="disabled" if busy or simple_mode else "normal")
        if hasattr(self, "review_btn"):
            self.review_btn.configure(state="disabled" if busy or not self.review_report_rows else "normal")
        self.mp3_btn.configure(state="disabled" if busy or not self.video_path else "normal")
        self.wav_btn.configure(state="disabled" if busy or not self.video_path else "normal")
        has_text = bool(self.transcript_text)
        has_segments = bool(self.transcript_segments)
        for button, available in (
            (self.copy_btn, has_text),
            (self.txt_btn, has_text),
            (self.srt_btn, has_segments),
            (self.subtitle_video_btn, has_segments),
        ):
            button.configure(state="disabled" if busy or not available else "normal")
        self.header_status.configure(
            text="●  正在处理" if busy else "●  已就绪",
            bg="#5B431E" if busy else "#193B33",
            fg="#FFD995" if busy else "#8EE0BA"
        )

    def pick_video(self):
        path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[("视频文件", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.mpeg *.mpg *.wmv *.flv"), ("所有文件", "*.*")]
        )
        if not path:
            return
        self.video_path = path
        # Never leave results from a previous video attached to the newly selected file.
        self.transcript_segments = []
        self.original_segments = []
        self.transcript_text = ""
        self.translation_segments = []
        self.translation_complete = False
        self.translation_target_code = ""
        self.translation_target_label = ""
        self.audio_duration = 0.0
        self.review_report_rows = []
        self.language_summary = ""
        self.review_btn.configure(state="disabled")
        self.textbox.configure(state="normal", fg="#8390A3")
        self._show_placeholder()
        for button in (self.copy_btn, self.srt_btn, self.txt_btn, self.subtitle_video_btn,
                       self.translate_btn, self.export_original_btn, self.export_translated_srt_btn,
                       self.export_translated_txt_btn):
            button.configure(state="disabled")
        self.original_textbox.configure(state="normal")
        self.original_textbox.delete("1.0", "end")
        self.original_textbox.configure(state="disabled", fg="#8390A3")
        self.translation_textbox.configure(state="normal", fg="#8390A3")
        self.translation_textbox.delete("1.0", "end")
        self.translation_textbox.insert("1.0", "识别完成后，可选择目标语言并点击左侧「生成译文」。")
        size = os.path.getsize(path)
        size_text = f"{size / (1024 * 1024):.1f} MB" if size >= 1024 * 1024 else f"{size / 1024:.0f} KB"
        self.file_label.configure(text=os.path.basename(path), fg=INK)
        self.file_hint.configure(text=f"{size_text}  ·  {os.path.dirname(path)}", fg=MUTED)
        self.mp3_btn.configure(state="normal")
        self.wav_btn.configure(state="normal")
        self.start_btn.configure(state="normal")
        self.status_var.set("视频已载入。简单模式默认使用 medium、自动语种检测、轻度清理和自动复核。")
        self.percent_var.set("0%")
        self.progress.configure(value=0)

    def _ffmpeg_run(self, args, task_label, cwd=None):
        cmd = [ffmpeg_path(), "-y", "-hide_banner", "-loglevel", "error"] + args
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), cwd=cwd
        )
        if result.returncode != 0:
            detail = (result.stderr or "").strip()[-1600:]
            raise RuntimeError(f"{task_label}失败。请确认视频包含可读取的音轨。\n\n{detail}")

    def _make_asr_wav(self, output_path, enhance=True):
        args = ["-i", self.video_path, "-vn", "-ac", "1", "-ar", "16000"]
        if enhance:
            # Light-weight speech-oriented filter chain. This cleans noise and evens loudness; it does not separate overlapping sources.
            args += ["-af", "highpass=f=80,lowpass=f=9500,afftdn=nf=-22,dynaudnorm=f=150:g=12"]
        args += ["-c:a", "pcm_s16le", output_path]
        self._ffmpeg_run(args, "音频准备")

    def export_audio(self, audio_format):
        if self.busy or not self.video_path:
            return
        base = os.path.splitext(os.path.basename(self.video_path))[0]
        extension = ".mp3" if audio_format == "mp3" else ".wav"
        out = filedialog.asksaveasfilename(
            title=f"导出 {audio_format.upper()} 音频", defaultextension=extension,
            initialdir=os.path.dirname(self.video_path), initialfile=base + extension,
            filetypes=[(f"{audio_format.upper()} 音频", f"*{extension}")]
        )
        if not out:
            return
        self._set_busy(True)
        self.progress.configure(value=0)
        self.percent_var.set("0%")
        threading.Thread(target=self._audio_worker, args=(out, audio_format), daemon=True).start()

    def _audio_worker(self, out, audio_format):
        try:
            self._set_status(f"正在提取 {audio_format.upper()} 音频……", 15)
            if audio_format == "mp3":
                args = ["-i", self.video_path, "-vn", "-c:a", "libmp3lame", "-b:a", "192k", "-ar", "44100", "-ac", "2", out]
            else:
                args = ["-i", self.video_path, "-vn", "-c:a", "pcm_s16le", out]
            self._ffmpeg_run(args, "音频导出")
            self._set_status(f"{audio_format.upper()} 已导出：{out}", 100, SUCCESS)
            self.root.after(0, lambda: messagebox.showinfo("导出完成", f"音频已保存到：\n{out}"))
        except Exception as exc:
            msg = str(exc)
            self._set_status("音频导出失败，请查看错误提示。", 0, DANGER)
            self.root.after(0, lambda e=msg: messagebox.showerror("导出失败", e))
        finally:
            self.root.after(0, lambda: self._set_busy(False))

    def start_processing(self):
        if self.busy:
            return
        if not self.video_path:
            messagebox.showinfo("先选择视频", "请先点击「选择视频文件」。")
            return
        model_labels = {
            "small（速度较快）": "small",
            "medium（更准确）": "medium",
            "large-v3（高准确，较慢）": "large-v3",
        }
        selected_language = self.lang_var.get()
        language_code = LANGUAGE_CODE_BY_LABEL.get(selected_language)
        # A None language code means identify the language anew for each audio window.
        user_prompt = self._get_prompt_text()
        if selected_language.startswith("粤语 / 地方汉语方言"):
            dialect_hint = "粤语口语及地方汉语词汇。尽量保留原话，不要翻译，不确定内容可按听到的发音转写。"
            user_prompt = (user_prompt + "；" + dialect_hint).strip("；")
        options = {
            "model": model_labels.get(self.model_var.get(), "medium"),
            "language": language_code,
            "language_label": selected_language,
            "task": "transcribe",
            "vad_filter": bool(self.vad_var.get()),
            "enhance_audio": bool(self.enhance_var.get()),
            "initial_prompt": user_prompt,
        }
        self.last_processing_options = dict(options)
        self.transcript_segments = []
        self.original_segments = []
        self.transcript_text = ""
        self.translation_segments = []
        self.translation_complete = False
        self.audio_duration = 0.0
        self.review_report_rows = []
        self.language_summary = ""
        self.review_btn.configure(state="disabled")
        self.original_textbox.configure(state="normal")
        self.original_textbox.delete("1.0", "end")
        self.original_textbox.configure(state="disabled", fg="#8390A3")
        self.translation_textbox.configure(state="normal", fg="#8390A3")
        self.translation_textbox.delete("1.0", "end")
        self.translation_textbox.insert("1.0", "重新识别后，请重新生成译文。")
        self.export_original_btn.configure(state="disabled")
        self.export_translated_srt_btn.configure(state="disabled")
        self.export_translated_txt_btn.configure(state="disabled")
        self._set_busy(True)
        self.txt_btn.configure(state="disabled")
        self.srt_btn.configure(state="disabled")
        self.copy_btn.configure(state="disabled")
        self.subtitle_video_btn.configure(state="disabled")
        self.textbox.configure(state="normal", fg=INK)
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", "第 1/4 步：正在整理音频……\n")
        self.textbox.see("end")
        self.progress.configure(value=0)
        self.percent_var.set("0%")
        self._set_status("第 1/4 步：音频预处理……", 0)
        threading.Thread(target=self._process_worker, args=(options,), daemon=True).start()

    @staticmethod
    def _segment_quality_score(segments):
        if not segments:
            return -99.0
        values = [float(getattr(seg, "avg_logprob", -1.5) or -1.5) for seg in segments]
        return sum(values) / len(values)

    @staticmethod
    def _segment_needs_review(seg):
        reasons = []
        avg_logprob = float(getattr(seg, "avg_logprob", -1.5) or -1.5)
        no_speech_prob = float(getattr(seg, "no_speech_prob", 0.0) or 0.0)
        compression_ratio = float(getattr(seg, "compression_ratio", 0.0) or 0.0)
        if avg_logprob < -0.8:
            reasons.append("模型置信度偏低")
        if no_speech_prob > 0.55:
            reasons.append("疑似静音/背景声混入")
        if compression_ratio > 2.4:
            reasons.append("文本重复或解码异常风险")
        return reasons

    def _process_worker(self, options):
        collected = []
        temp_dir = None
        duration = 0.0
        failure = None
        language_chunks = []
        review_events = []
        try:
            self._set_status("第 1/4 步：提取音频并进行基础清理……", 2)
            temp_dir = tempfile.mkdtemp(prefix="shengwen_asr_")
            wav_path = os.path.join(temp_dir, "audio_16k_mono.wav")
            self._make_asr_wav(wav_path, enhance=options["enhance_audio"])
            with wave.open(wav_path, "rb") as source:
                rate = source.getframerate()
                total_frames = source.getnframes()
                duration = total_frames / max(1, rate)
                params = (source.getnchannels(), source.getsampwidth(), rate, source.getcomptype(), source.getcompname())
                source_frames = total_frames
            self.audio_duration = duration
            if duration <= 0:
                raise RuntimeError("没有从视频中读取到有效音轨。")

            self._set_status("第 2/4 步：加载多语言语音模型……", 4)
            from faster_whisper import WhisperModel
            model = WhisperModel(options["model"], device="cpu", compute_type="int8")

            # Short overlapping windows allow language identification to be revisited across the whole video,
            # rather than inheriting one language guess from the beginning of the file.
            # 16-second windows with a 4-second overlap respond faster to language changes
            # than one long language guess; more windows cost additional processing time.
            chunk_seconds = 16.0
            overlap_seconds = 4.0
            step_seconds = chunk_seconds - overlap_seconds
            starts = [0.0]
            while starts[-1] + chunk_seconds < duration:
                starts.append(starts[-1] + step_seconds)
            chunk_count = len(starts)
            detected_seconds = {}
            detected_probs = {}

            with wave.open(wav_path, "rb") as source:
                for chunk_index, chunk_start in enumerate(starts):
                    chunk_end = min(duration, chunk_start + chunk_seconds)
                    start_frame = min(total_frames, int(round(chunk_start * rate)))
                    end_frame = min(total_frames, int(round(chunk_end * rate)))
                    if end_frame <= start_frame:
                        continue
                    source.setpos(start_frame)
                    frames = source.readframes(end_frame - start_frame)
                    chunk_path = os.path.join(temp_dir, f"chunk_{chunk_index + 1:04d}.wav")
                    with wave.open(chunk_path, "wb") as out_wav:
                        out_wav.setnchannels(params[0])
                        out_wav.setsampwidth(params[1])
                        out_wav.setframerate(params[2])
                        out_wav.setcomptype(params[3], params[4])
                        out_wav.writeframes(frames)

                    transcribe_kwargs = dict(
                        language=options["language"],
                        task=options["task"],
                        beam_size=5,
                        best_of=5,
                        temperature=[0.0, 0.2, 0.4],
                        vad_filter=options["vad_filter"],
                        condition_on_previous_text=True,
                        word_timestamps=False,
                        no_speech_threshold=0.75,
                        log_prob_threshold=-1.0,
                        compression_ratio_threshold=2.4,
                    )
                    if options["initial_prompt"] and options["task"] == "transcribe":
                        transcribe_kwargs["initial_prompt"] = options["initial_prompt"]
                    if options["vad_filter"]:
                        transcribe_kwargs["vad_parameters"] = {
                            "min_silence_duration_ms": 900,
                            "speech_pad_ms": 400,
                            "min_speech_duration_ms": 100,
                        }

                    self._set_status(
                        f"第 3/4 步：识别第 {chunk_index + 1}/{chunk_count} 段，并检测此段语种……",
                        5 + 85 * chunk_index / max(1, chunk_count)
                    )
                    generated, info = model.transcribe(chunk_path, **transcribe_kwargs)
                    decoded = list(generated)  # faster-whisper returns a lazy generator; exhaust it before assessing quality.
                    language = getattr(info, "language", None) or options["language"] or "unknown"
                    language_probability = float(getattr(info, "language_probability", 0.0) or 0.0)
                    chosen = decoded
                    base_score = self._segment_quality_score(decoded)
                    uncertain_chunk = (not decoded) or any(self._segment_needs_review(seg) for seg in decoded) or (options["language"] is None and language_probability < 0.60)

                    # Targeted second decoding for uncertain chunks. Keep the retry only if it scores better and does not collapse the transcript.
                    if uncertain_chunk:
                        retry_kwargs = dict(transcribe_kwargs)
                        retry_kwargs["temperature"] = 0.2
                        retry_kwargs["condition_on_previous_text"] = False
                        retry_kwargs.pop("initial_prompt", None) if options["task"] == "translate" else None
                        try:
                            retry_gen, retry_info = model.transcribe(chunk_path, **retry_kwargs)
                            retried = list(retry_gen)
                            retry_score = self._segment_quality_score(retried)
                            old_chars = sum(len((getattr(seg, "text", "") or "").strip()) for seg in decoded)
                            new_chars = sum(len((getattr(seg, "text", "") or "").strip()) for seg in retried)
                            if retried and (retry_score > base_score + 0.03) and new_chars >= max(1, int(old_chars * 0.85)):
                                chosen = retried
                                language = getattr(retry_info, "language", None) or language
                                language_probability = float(getattr(retry_info, "language_probability", language_probability) or language_probability)
                                review_events.append(f"{format_time(chunk_start)}：低置信片段已进行第二次解码；采用第二次结果。仍建议试听核对。")
                            else:
                                review_events.append(f"{format_time(chunk_start)}：二次解码未显著提高置信度，保留首轮结果并标记复核。")
                        except Exception as retry_exc:
                            review_events.append(f"{format_time(chunk_start)}：二次解码失败，保留首轮结果（{retry_exc}）。")

                    chunk_len = max(0.0, chunk_end - chunk_start)
                    detected_seconds[language] = detected_seconds.get(language, 0.0) + chunk_len
                    detected_probs.setdefault(language, []).append(language_probability)
                    language_chunks.append({
                        "start": chunk_start,
                        "end": chunk_end,
                        "language": language,
                        "language_probability": language_probability,
                        "retried": uncertain_chunk,
                    })

                    # Remove overlap duplicates by accepting each window's segment centers only in its core region.
                    core_start = 0.0 if chunk_index == 0 else chunk_start + overlap_seconds / 2.0
                    core_end = duration if chunk_index == chunk_count - 1 else min(duration, chunk_start + chunk_seconds - overlap_seconds / 2.0)
                    for seg in chosen:
                        text = (getattr(seg, "text", "") or "").strip()
                        if not text:
                            continue
                        local_start = float(seg.start)
                        local_end = float(seg.end)
                        center = chunk_start + (local_start + local_end) / 2.0
                        if center < core_start or center >= core_end:
                            continue
                        reasons = self._segment_needs_review(seg)
                        if options["language"] is None and language_probability < 0.60:
                            reasons.append("本片段语种判定不确定")
                        item = {
                            "start": max(0.0, chunk_start + local_start),
                            "end": min(duration, chunk_start + local_end),
                            "text": text,
                            "language": language,
                            "language_probability": language_probability,
                            "avg_logprob": float(getattr(seg, "avg_logprob", -1.5) or -1.5),
                            "no_speech_prob": float(getattr(seg, "no_speech_prob", 0.0) or 0.0),
                            "compression_ratio": float(getattr(seg, "compression_ratio", 0.0) or 0.0),
                            "review_reasons": reasons,
                        }
                        collected.append(item)
                        self.root.after(0, lambda item=item: self._append_segment(item))
                    pct = 5 + 85 * (chunk_index + 1) / max(1, chunk_count)
                    self._set_status(f"已识别 {chunk_index + 1}/{chunk_count} 段；正在扫描全片语言和疑似错误……", pct)

            collected.sort(key=lambda item: (item["start"], item["end"]))
            if not collected:
                raise RuntimeError("没有识别到语音。请检查视频音轨，或尝试更大的识别模型。")

            # Generate a full-video review sheet: language by window, uncertain segments, and long intervals.
            gap_events = []
            previous_end = 0.0
            for item in collected:
                gap = item["start"] - previous_end
                if gap >= 8.0:
                    gap_events.append(f"{format_time(previous_end)}–{format_time(item['start'])}：有约 {gap:.1f} 秒没有字幕文字；可能是静音，也可能漏识别，请试听。")
                previous_end = max(previous_end, item["end"])
                item["review_flag"] = bool(item["review_reasons"])
            tail_gap = max(0.0, duration - (collected[-1]["end"] if collected else 0.0))
            if tail_gap >= max(6.0, duration * 0.08):
                gap_events.append(f"视频结尾：最后一段文字结束于 {collected[-1]['end']:.1f} 秒，之后约 {tail_gap:.1f} 秒无字幕。可能是静音或漏识别，请试听。")

            lang_parts = []
            for code, seconds in sorted(detected_seconds.items(), key=lambda x: x[1], reverse=True):
                name = LANGUAGE_NAME_BY_CODE.get(code, code if code != "unknown" else "未知语种")
                probs = detected_probs.get(code, [])
                avgp = sum(probs) / len(probs) if probs else 0.0
                lang_parts.append(f"{name}（约 {seconds:.0f} 秒，平均检测概率 {avgp:.0%}）")
            language_summary = "；".join(lang_parts) if lang_parts else "未能确定语种"
            review_count = sum(1 for item in collected if item["review_flag"])
            report_lines = [
                "声文 · 全片语言与质量校对报告",
                f"文件：{os.path.basename(self.video_path)}",
                f"音频时长：{duration:.2f} 秒",
                f"识别模型：{options['model']}",
                "识别模式：保留原语种转写；翻译作为独立、可选步骤执行",
                f"音频预处理：{'开启' if options['enhance_audio'] else '关闭'}（基础滤波，不等于复杂人声分离）",
                f"片段语种概览：{language_summary}",
                f"疑似需复核的文字段数：{review_count}",
                "重要说明：语种按约 30 秒音频窗口估计，短暂的代码切换、极少见语言和方言可能误判；概率不是准确率保证。",
                "地方方言/口音不能由当前本地模型可靠地全面分类；请在识别提示中注明，并对照原视频复核。",
                "",
                "疑似需复核的字幕段：",
            ]
            for item in collected:
                if item["review_flag"]:
                    reason = "、".join(item["review_reasons"]) or "需人工确认"
                    report_lines.append(f"[{item['start']:.2f}-{item['end']:.2f}] [{LANGUAGE_NAME_BY_CODE.get(item['language'], item['language'])}] {item['text']}  → {reason}")
            if not any(item["review_flag"] for item in collected):
                report_lines.append("模型置信指标没有触发明显复核标记；这不等于无错误。")
            if gap_events:
                report_lines.extend(["", "长间隔 / 结尾检查：", *gap_events])
            else:
                report_lines.extend(["", "没有发现超过 8 秒的无文字间隔；这不等于保证没有漏字。"])
            report_lines.extend(["", "逐段记录在导出的 CSV 中；建议先检查低置信段，再进行翻译。"])
            self.review_report_rows = collected
            self.language_summary = language_summary
            self.review_report_text = "\n".join(report_lines)
            self._set_status("第 4/4 步：全片扫描与复核提示已完成。", 98)
        except Exception as exc:
            failure = str(exc)
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            self.root.after(0, lambda data=collected, langs=getattr(self, "language_summary", ""), dur=duration, err=failure: self._finish_processing(data, langs, dur, err))

    def _append_segment(self, item):
        # Streaming output lets the user see whether later speech is still being processed.
        text = str(item.get("text", "")).replace("\r", " ").replace("\n", " ").strip()
        self.textbox.configure(state="normal", fg=INK)
        current = self.textbox.get("1.0", "end-1c")
        if current.strip() == "正在准备音频……":
            self.textbox.delete("1.0", "end")
        if self.textbox.get("1.0", "end-1c").strip():
            self.textbox.insert("end", "\n")
        self.textbox.insert("end", text)
        self.textbox.see("end")
        self.original_textbox.configure(state="normal", fg=INK)
        existing = self.original_textbox.get("1.0", "end-1c").strip()
        if existing in ("原始识别结果会单独保留在这里。", ""):
            self.original_textbox.delete("1.0", "end")
        if self.original_textbox.get("1.0", "end-1c").strip():
            self.original_textbox.insert("end", "\n")
        self.original_textbox.insert("end", text)
        self.original_textbox.configure(state="disabled")
        self.original_textbox.see("end")

    def _finish_processing(self, segments, language_summary, duration, error):
        # Preserve the first-pass result untouched, while edits operate on a separate copy.
        self.original_segments = [dict(item) for item in segments]
        self.transcript_segments = [dict(item) for item in segments]
        self.transcript_text = "\n".join(str(item["text"]).replace("\r", " ").replace("\n", " ").strip() for item in self.transcript_segments)
        self.translation_segments = []
        self.translation_complete = False
        self.audio_duration = duration
        self.language_summary = language_summary or "未能确定语种"
        self._set_busy(False)
        if self.transcript_text:
            self.textbox.configure(state="normal", fg=INK)
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", self.transcript_text)
            self.textbox.see("1.0")
            self.original_textbox.configure(state="normal", fg=INK)
            self.original_textbox.delete("1.0", "end")
            self.original_textbox.insert("1.0", "\n".join(str(item["text"]).replace("\r", " ").replace("\n", " ").strip() for item in self.original_segments))
            self.original_textbox.configure(state="disabled")
            self.txt_btn.configure(state="normal")
            self.srt_btn.configure(state="normal")
            self.copy_btn.configure(state="normal")
            self.subtitle_video_btn.configure(state="normal" if self.transcript_segments else "disabled")
            self.translate_btn.configure(state="normal" if self.transcript_segments else "disabled")
            self.export_original_btn.configure(state="normal" if self.original_segments else "disabled")
            self.export_translated_srt_btn.configure(state="disabled")
            self.review_btn.configure(state="normal" if self.review_report_rows else "disabled")
            self.progress.configure(value=100 if not error else self.progress["value"])
            self.percent_var.set("100%" if not error else self.percent_var.get())
        else:
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", "暂未识别到文字。\n\n可以尝试：\n• 选择 medium 或 large-v3 模型\n• 指定最主要的语种\n• 在提示中注明方言、口音和专有词\n• 检查视频中人声是否被音乐覆盖")
            self.textbox.configure(fg="#8390A3")
        if error:
            self._set_status("识别未完整完成；已保留当前识别到的部分文字。", self.progress["value"], DANGER)
            self.root.after(100, lambda e=error: messagebox.showerror("识别未完成", e + ("\n\n已保留识别到的部分文字，可以先导出。" if segments else "")))
            return

        low_conf = sum(1 for item in segments if item.get("review_flag"))
        last_end = float(segments[-1]["end"]) if segments else 0.0
        tail_gap = max(0.0, float(duration) - last_end)
        task_text = "保留原语种转写"
        status = f"完成 · {task_text} · 语种扫描：{self.language_summary} · {len(segments)} 段 · {low_conf} 段需复核"
        if tail_gap >= max(6.0, duration * 0.08):
            status += f" · 结尾 {tail_gap:.1f}s 无文字，请试听"
        self._set_status(status, 100, "#B7791F" if low_conf or tail_gap >= max(6.0, duration * 0.08) else SUCCESS)
        message = (
            f"已完成整段视频识别与按片段语种扫描。\n\n"
            f"语种估计：{self.language_summary}\n"
            f"标记为疑似需复核：{low_conf} 段\n"
            f"结尾无文字间隔：约 {tail_gap:.1f} 秒\n\n"
            "请点击“导出语言与质量校对表 CSV”，先核对低置信段和长间隔，再用于翻译。\n"
            "这些标记只能帮助发现风险，不能保证模型之外没有错字；方言和口音尤其需要人工听审。"
        )
        self.root.after(250, lambda msg=message: messagebox.showinfo("识别与校对提示完成", msg))

    def export_review_report(self):
        if not self.review_report_rows:
            messagebox.showinfo("暂无校对数据", "请先完成一次识别。")
            return
        base = os.path.splitext(os.path.basename(self.video_path))[0] if self.video_path else "声文校对表"
        path = filedialog.asksaveasfilename(
            title="导出语言与质量校对表", defaultextension=".csv", initialfile=base + "_校对表.csv",
            filetypes=[("CSV 表格", "*.csv")]
        )
        if not path:
            return
        try:
            import csv
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["开始秒", "结束秒", "估计语种", "语种检测概率（窗口级）", "识别文字", "平均对数概率", "无语音概率", "是否需复核", "复核原因"])
                for item in self.review_report_rows:
                    writer.writerow([
                        f"{item['start']:.2f}", f"{item['end']:.2f}",
                        LANGUAGE_NAME_BY_CODE.get(item.get("language", ""), item.get("language", "未知")),
                        f"{float(item.get('language_probability', 0.0)):.3f}", item["text"],
                        f"{float(item.get('avg_logprob', 0.0)):.3f}",
                        f"{float(item.get('no_speech_prob', 0.0)):.3f}",
                        "是" if item.get("review_flag") else "否",
                        "；".join(item.get("review_reasons", [])),
                    ])
            self._set_status(f"校对表已导出：{path}", color=SUCCESS)
            messagebox.showinfo("导出完成", f"校对表已保存：\n{path}\n\n此表保留时间、语种估计和疑似错误标记，可在翻译前用于人工检查。")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    def _sync_editor_to_segments(self, show_warning=True):
        """Apply edited lines to subtitle rows without corrupting timestamps. One line = one row."""
        if not self.transcript_segments:
            if show_warning:
                messagebox.showinfo("暂无识别结果", "请先完成语音识别。")
            return False
        text = self.textbox.get("1.0", "end-1c").replace("\r", "")
        lines = text.split("\n") if text else []
        if len(lines) != len(self.transcript_segments):
            if show_warning:
                messagebox.showwarning(
                    "字幕行数发生变化",
                    f"当前编辑稿有 {len(lines)} 行，但时间轴有 {len(self.transcript_segments)} 条字幕。\n\n"
                    "为避免字幕错位，导出前请恢复成每行对应一条字幕（可修改文字，但暂不支持在这里增删行）。"
                )
            return False
        changed = False
        for item, line in zip(self.transcript_segments, lines):
            cleaned = line.strip()
            if cleaned != str(item.get("text", "")).strip():
                changed = True
            item["text"] = cleaned
        self.transcript_text = "\n".join(item["text"] for item in self.transcript_segments)
        if changed and self.translation_complete:
            self.translation_complete = False
            self.export_translated_srt_btn.configure(state="disabled")
            self.export_translated_txt_btn.configure(state="disabled")
            self.translation_textbox.configure(state="normal", fg="#8390A3")
            self.translation_textbox.delete("1.0", "end")
            self.translation_textbox.insert("1.0", "原文已修改，先前译文已标记为过期。\n\n请点击「生成译文（联网）」重新翻译，以保持原文与译文一致。")
            self.status_var.set("原文已修改：为避免原文与译文不一致，请重新生成译文。")
        return True

    def _sync_translation_to_segments(self, show_warning=True):
        if not self.translation_complete or not self.translation_segments:
            if show_warning:
                messagebox.showinfo("尚无译文", "请先点击「生成译文（联网）」。")
            return False
        text = self.translation_textbox.get("1.0", "end-1c").replace("\r", "")
        lines = text.split("\n") if text else []
        if len(lines) != len(self.translation_segments):
            if show_warning:
                messagebox.showwarning("译文行数发生变化", "请保持每行对应一条字幕，避免时间轴错位。")
            return False
        for item, line in zip(self.translation_segments, lines):
            item["text"] = line.strip()
        return True

    def _ensure_transcript(self):
        if not self.transcript_segments:
            messagebox.showinfo("暂无识别结果", "请先完成语音识别。")
            return False
        return self._sync_editor_to_segments()

    def export_original_txt(self):
        if not self.original_segments:
            messagebox.showinfo("暂无原始转写", "请先完成语音识别。")
            return
        base = os.path.splitext(os.path.basename(self.video_path))[0] if self.video_path else "声文识别结果"
        path = filedialog.asksaveasfilename(
            title="导出原始 TXT", defaultextension=".txt", initialfile=base + "_原始转写.txt",
            filetypes=[("文本文件", "*.txt")]
        )
        if path:
            try:
                original_text = "\n".join(str(item.get("text", "")) for item in self.original_segments)
                with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
                    f.write(original_text)
                self._set_status(f"原始转写已导出：{path}", color=SUCCESS)
            except Exception as exc:
                messagebox.showerror("导出失败", str(exc))

    def export_txt(self):
        if not self._ensure_transcript():
            return
        base = os.path.splitext(os.path.basename(self.video_path))[0] if self.video_path else "声文识别结果"
        path = filedialog.asksaveasfilename(
            title="导出 TXT", defaultextension=".txt", initialfile=base + ".txt",
            filetypes=[("文本文件", "*.txt")]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
                    f.write(self.transcript_text)
                self._set_status(f"TXT 已导出：{path}", color=SUCCESS)
            except Exception as exc:
                messagebox.showerror("导出失败", str(exc))

    @staticmethod
    def _srt_time(seconds):
        ms = int(round(seconds * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    def export_srt(self):
        if not self._ensure_transcript():
            return
        base = os.path.splitext(os.path.basename(self.video_path))[0] if self.video_path else "声文识别结果"
        path = filedialog.asksaveasfilename(
            title="导出 SRT 字幕", defaultextension=".srt", initialfile=base + ".srt",
            filetypes=[("SRT 字幕", "*.srt")]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
                    for i, seg in enumerate(self.transcript_segments, 1):
                        f.write(f"{i}\n{self._srt_time(seg['start'])} --> {self._srt_time(seg['end'])}\n{seg['text']}\n\n")
                self._set_status(f"SRT 已导出：{path}", color=SUCCESS)
            except Exception as exc:
                messagebox.showerror("导出失败", str(exc))

    def export_translated_srt(self):
        if not self._ensure_transcript():
            return
        if not self._sync_translation_to_segments():
            return
        base = os.path.splitext(os.path.basename(self.video_path))[0] if self.video_path else "声文译文"
        default = base + f"_{self.translation_target_label or '译文'}.srt"
        path = filedialog.asksaveasfilename(
            title="导出译文 SRT", defaultextension=".srt", initialfile=default,
            filetypes=[("SRT 字幕", "*.srt")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
                for i, seg in enumerate(self.translation_segments, 1):
                    f.write(f"{i}\n{self._srt_time(seg['start'])} --> {self._srt_time(seg['end'])}\n{seg['text']}\n\n")
            self._set_status(f"译文 SRT 已导出：{path}", color=SUCCESS)
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    def export_subtitled_video(self):
        """Render recognized subtitle timings directly into a new MP4 video."""
        if not self._ensure_transcript():
            return
        if not self.video_path or not self.transcript_segments:
            messagebox.showinfo("暂无字幕", "请先选择视频并完成语音识别。")
            return
        use_translation = bool(self.subtitle_translation_var.get() and self.translation_complete)
        if self.subtitle_translation_var.get() and not self.translation_complete:
            if not messagebox.askyesno("尚未生成译文", "你勾选了使用译文字幕，但目前没有可用译文。\n\n是否改为使用已编辑的原文字幕生成视频？"):
                return
            use_translation = False
        if use_translation and not self._sync_translation_to_segments():
            return
        selected_segments = self.translation_segments if use_translation else self.transcript_segments
        base = os.path.splitext(os.path.basename(self.video_path))[0]
        output_suffix = "_译文字幕.mp4" if use_translation else "_带字幕.mp4"
        output_path = filedialog.asksaveasfilename(
            title="生成带字幕视频（硬字幕）",
            defaultextension=".mp4",
            initialdir=os.path.dirname(self.video_path),
            initialfile=base + output_suffix,
            filetypes=[("MP4 视频", "*.mp4")]
        )
        if not output_path:
            return
        if os.path.normcase(os.path.abspath(output_path)) == os.path.normcase(os.path.abspath(self.video_path)):
            messagebox.showwarning("不能覆盖原视频", "请另存为一个新文件，避免覆盖原视频。")
            return
        # Snapshot the inputs so the worker uses exactly the result displayed to the user.
        video_path = self.video_path
        segments = [dict(item) for item in selected_segments]
        duration = float(self.audio_duration or 0.0)
        self._set_busy(True)
        self.progress.configure(value=0)
        self.percent_var.set("0%")
        self._set_status("正在准备字幕并生成新视频……", 1)
        threading.Thread(
            target=self._subtitled_video_worker,
            args=(video_path, output_path, segments, duration),
            daemon=True
        ).start()

    def _subtitled_video_worker(self, video_path, output_path, segments, duration):
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="shengwen_subtitles_")
            srt_path = os.path.join(temp_dir, "captions.srt")
            with open(srt_path, "w", encoding="utf-8", newline="\n") as f:
                for i, seg in enumerate(segments, 1):
                    start = max(0.0, float(seg.get("start", 0.0)))
                    end = max(start + 0.12, float(seg.get("end", start + 0.12)))
                    text = (str(seg.get("text", "")) or "").strip()
                    if not text:
                        continue
                    f.write(f"{i}\n{self._srt_time(start)} --> {self._srt_time(end)}\n{text}\n\n")
            if not os.path.getsize(srt_path):
                raise RuntimeError("没有可用于生成字幕的文字，请先重新识别视频。")

            # A relative SRT filename avoids drive-colon escaping problems on Windows.
            # libass renders white captions with a black outline near the lower edge.
            subtitle_filter = (
                "subtitles=captions.srt:force_style='"
                "FontName=Microsoft YaHei,FontSize=24,"
                "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                "BorderStyle=1,Outline=2,Shadow=1,Alignment=2,MarginV=34'"
            )
            command = [
                "-i", os.path.abspath(video_path),
                "-vf", subtitle_filter,
                "-map", "0:v:0", "-map", "0:a?",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart",
                "-progress", "pipe:1", "-nostats",
                os.path.abspath(output_path)
            ]
            cmd = [ffmpeg_path(), "-y", "-hide_banner", "-loglevel", "error"] + command
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", cwd=temp_dir,
                creationflags=flags, bufsize=1
            )
            final_pct = 0.0
            # FFmpeg emits out_time progress records. If duration is unknown, show an indeterminate-like steady status.
            if proc.stdout is not None:
                for raw_line in proc.stdout:
                    line = raw_line.strip()
                    if line.startswith("out_time=") and duration > 0:
                        stamp = line.partition("=")[2]
                        try:
                            hh, mm, ss = stamp.split(":")
                            elapsed = int(hh) * 3600 + int(mm) * 60 + float(ss)
                            final_pct = max(final_pct, min(97.0, elapsed / duration * 94.0))
                            self._set_status(
                                f"正在渲染字幕视频 · {format_time(elapsed)} / {format_time(duration)}",
                                3 + final_pct
                            )
                        except (ValueError, TypeError):
                            pass
            return_code = proc.wait()
            stderr_text = proc.stderr.read() if proc.stderr is not None else ""
            if return_code != 0:
                detail = (stderr_text or "").strip()[-1800:]
                if "No such filter: 'subtitles'" in detail or "No such filter: subtitles" in detail:
                    detail += "\n当前 FFmpeg 不支持字幕渲染滤镜，请更新打包使用的 FFmpeg。"
                raise RuntimeError("生成带字幕视频失败。\n\n" + (detail or f"FFmpeg 退出代码：{return_code}"))
            if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                raise RuntimeError("FFmpeg 已结束，但没有生成有效的视频文件。")
            self._set_status(f"带字幕视频已生成：{output_path}", 100, SUCCESS)
            self.root.after(0, lambda out=output_path: messagebox.showinfo("生成完成", f"带字幕的视频已保存到：\n{out}\n\n字幕已直接嵌入画面，分享视频时不需要额外携带 SRT 文件。"))
        except Exception as exc:
            msg = str(exc)
            self._set_status("带字幕视频生成失败，请查看错误提示。", 0, DANGER)
            self.root.after(0, lambda e=msg: messagebox.showerror("生成失败", e))
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            self.root.after(0, lambda: self._set_busy(False))

    def export_translated_txt(self):
        if not self._ensure_transcript():
            return
        if not self._sync_translation_to_segments():
            return
        base = os.path.splitext(os.path.basename(self.video_path))[0] if self.video_path else "声文译文"
        path = filedialog.asksaveasfilename(
            title="导出译文 TXT", defaultextension=".txt",
            initialfile=base + f"_{self.translation_target_label or '译文'}.txt",
            filetypes=[("文本文件", "*.txt")]
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
                f.write("\n".join(item.get("text", "") for item in self.translation_segments))
            self._set_status(f"译文 TXT 已导出：{path}", color=SUCCESS)
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    @staticmethod
    def _translation_lang_code(source_code):
        source_code = str(source_code or "").strip().lower()
        return LANGUAGE_CODE_ALIASES.get(source_code, source_code)

    @staticmethod
    def _call_mymemory(text, source_code, target_code):
        """Translate one caption via MyMemory; sends text only, never the source media."""
        text = str(text or "").strip()
        if not text:
            return ""
        if len(text) > 450:
            # Caption segmentation usually keeps this short; split unusually long rows to fit the provider query limit.
            pieces = []
            rest = text
            while rest:
                if len(rest) <= 450:
                    pieces.append(rest)
                    break
                split_at = max(rest.rfind(" ", 0, 450), rest.rfind("。", 0, 450), rest.rfind(".", 0, 450))
                if split_at < 200:
                    split_at = 450
                pieces.append(rest[:split_at].strip())
                rest = rest[split_at:].strip()
            translated_parts = [SpeechTextApp._call_mymemory(part, source_code, target_code) for part in pieces]
            joiner = "" if target_code.startswith(("zh", "ja", "ko", "th")) else " "
            return joiner.join(translated_parts)
        params = urllib.parse.urlencode({"q": text, "langpair": f"{source_code}|{target_code}"})
        url = "https://api.mymemory.translated.net/get?" + params
        request = urllib.request.Request(url, headers={"User-Agent": f"Shengwen/{APP_VERSION} (desktop subtitle tool)"})
        last_error = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=25) as response:
                    payload = json.loads(response.read().decode("utf-8", errors="replace"))
                status = int(payload.get("responseStatus", 0) or 0)
                result = (payload.get("responseData") or {}).get("translatedText", "")
                if status != 200 or not result:
                    detail = payload.get("responseDetails") or f"翻译服务返回状态 {status}"
                    raise RuntimeError(str(detail))
                return html.unescape(str(result)).replace("\r", " ").replace("\n", " ").strip()
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(0.5 * (attempt + 1))
        raise RuntimeError(str(last_error or "在线翻译失败"))

    def start_translation(self):
        if self.busy:
            return
        if not self._sync_editor_to_segments():
            return
        target_label = self.translation_target_var.get()
        target_code = TARGET_CODE_BY_LABEL.get(target_label)
        if not target_code:
            messagebox.showwarning("请选择目标语言", "请选择译文的目标语言。")
            return
        needs_online = any(
            str(item.get("text", "")).strip()
            and self._translation_lang_code(item.get("language", "")) != target_code
            for item in self.transcript_segments
        )
        if needs_online and not self.translation_privacy_accepted:
            accepted = messagebox.askyesno(
                "在线翻译与隐私提示",
                "为了生成译文，声文会把识别文字（不包含视频或音频文件）发送给 MyMemory 在线翻译服务。\n\n"
                "这会将字幕文本交给第三方处理，服务可能有可用语言、隐私政策和使用额度限制。\n\n"
                "是否同意本次会话使用在线翻译？"
            )
            if not accepted:
                return
            self.translation_privacy_accepted = True
        source_segments = [dict(item) for item in self.transcript_segments]
        if not source_segments:
            messagebox.showinfo("暂无原文", "请先完成语音识别。")
            return
        self.translation_target_code = target_code
        self.translation_target_label = target_label
        self._set_busy(True)
        self._set_status(f"正在逐条翻译为{target_label}；原文与时间轴会保留……", 0)
        self.translation_textbox.configure(state="normal", fg=INK)
        self.translation_textbox.delete("1.0", "end")
        self.translation_textbox.insert("1.0", "正在翻译，请稍候……")
        threading.Thread(
            target=self._translation_worker,
            args=(source_segments, target_code, target_label),
            daemon=True
        ).start()

    def _translation_worker(self, source_segments, target_code, target_label):
        translated = []
        failure = None
        try:
            total = max(1, len(source_segments))
            for idx, seg in enumerate(source_segments):
                source_text = str(seg.get("text", "")).strip()
                source_code = self._translation_lang_code(seg.get("language", ""))
                if not source_text:
                    translated_text = ""
                elif not source_code or source_code == "unknown":
                    raise RuntimeError(
                        f"第 {idx + 1} 条字幕（约 {format_time(seg.get('start', 0))}）没有可靠的语种代码。\n"
                        "请在专业模式中指定该段主要语言后重新识别；为避免错误翻译，程序没有猜测源语言。"
                    )
                elif source_code == target_code or (source_code == "zh" and target_code == "zh-CN"):
                    translated_text = source_text
                else:
                    try:
                        translated_text = self._call_mymemory(source_text, source_code, target_code)
                    except Exception as exc:
                        lang_name = LANGUAGE_NAME_BY_CODE.get(seg.get("language", ""), source_code)
                        raise RuntimeError(
                            f"第 {idx + 1}/{total} 条字幕翻译失败（源语言：{lang_name}，目标语言：{target_label}）。\n"
                            f"服务可能不支持该语言组合、网络中断或达到使用限制。\n\n详细信息：{exc}"
                        ) from exc
                    time.sleep(0.18)  # keep calls gentle to the public translation endpoint
                translated.append({**seg, "text": translated_text, "source_text": source_text})
                pct = 100 * (idx + 1) / total
                self._set_status(f"正在翻译为{target_label} · {idx + 1}/{total} 条字幕", pct)
            self._set_status(f"译文已生成：{target_label}。译文可修改后导出；专有词和方言仍需复核。", 100, SUCCESS)
        except Exception as exc:
            failure = str(exc)
        self.root.after(0, lambda result=translated, err=failure, label=target_label, code=target_code: self._finish_translation(result, err, label, code))

    def _finish_translation(self, translated, error, target_label, target_code):
        self._set_busy(False)
        if error:
            self.translation_complete = False
            self.translation_segments = []
            self.translation_textbox.configure(state="normal", fg=DANGER)
            self.translation_textbox.delete("1.0", "end")
            self.translation_textbox.insert("1.0", "译文未完成。\n\n" + error + "\n\n原始识别和编辑稿未改变。")
            self.export_translated_srt_btn.configure(state="disabled")
            self._set_status("在线翻译未完成；原文保留不变。", color=DANGER)
            messagebox.showerror("翻译失败", error)
            return
        self.translation_segments = translated
        self.translation_complete = True
        self.translation_target_code = target_code
        self.translation_target_label = target_label
        self.translation_textbox.configure(state="normal", fg=INK)
        self.translation_textbox.delete("1.0", "end")
        self.translation_textbox.insert("1.0", "\n".join(item.get("text", "") for item in translated))
        self.translation_textbox.see("1.0")
        self.text_tabs.select(2)
        self.export_translated_srt_btn.configure(state="normal")
        self.export_translated_txt_btn.configure(state="normal")
        self._set_status(f"翻译完成 · {target_label} · {len(translated)} 条。请校对专有词、方言和语义后再导出。", 100, SUCCESS)
        messagebox.showinfo(
            "译文已生成",
            f"已生成 {target_label} 译文并保留每条字幕的时间轴。\n\n"
            "请在“译文”页校对后，可导出译文 SRT，或勾选“生成视频时使用译文字幕”生成带字幕视频。\n"
            "自动翻译可能误解上下文、专有词和方言，不代表已完成人工校验。"
        )

    def copy_text(self):
        if not self._ensure_transcript():
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.transcript_text)
        self._set_status("识别文字已复制到剪贴板。", color=SUCCESS)


def main():
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.0)
    except tk.TclError:
        pass
    SpeechTextApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
