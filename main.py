import os
import sys
import wave
import shutil
import tempfile
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

APP_NAME = "声文 · 视频转文字"
APP_VERSION = "2.1"

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
        self.root.geometry("1180x820")
        self.root.minsize(1000, 720)
        self.root.configure(bg=BG)
        self.video_path = ""
        self.transcript_segments = []
        self.transcript_text = ""
        self.busy = False
        self.audio_duration = 0.0
        self._style()
        self._build()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        width = min(1180, self.root.winfo_screenwidth() - 80)
        height = min(820, self.root.winfo_screenheight() - 80)
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
            text="本机语音识别 · 实时进度 · 导出 TXT / SRT / MP3 / WAV · 生成带字幕视频",
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

        # Body: settings/action column and transcript column
        body = tk.Frame(outer, bg=BG)
        body.pack(fill="both", expand=True, pady=(14, 0))
        body.grid_columnconfigure(0, weight=4, uniform="body")
        body.grid_columnconfigure(1, weight=6, uniform="body")
        body.grid_rowconfigure(0, weight=1)

        _, left = self._card(body)
        left.master.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        left.pack_propagate(False)
        self._section_title(left, "02", "识别设置")

        tk.Label(left, text="识别语言", bg=CARD, fg=INK, font=(FONT, 10)).pack(anchor="w")
        self.lang_var = tk.StringVar(value="自动检测")
        self.lang_combo = ttk.Combobox(
            left, textvariable=self.lang_var, state="readonly", style="Modern.TCombobox",
            values=["自动检测", "中文", "英语", "日语", "韩语", "法语", "德语", "西班牙语"],
        )
        self.lang_combo.pack(fill="x", pady=(5, 13))

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
        ).pack(anchor="w", pady=(0, 12))

        self.vad_var = tk.BooleanVar(value=False)
        self.vad_check = tk.Checkbutton(
            left, text="跳过长静音（可能漏掉轻声，默认关闭）", variable=self.vad_var,
            bg=CARD, fg=INK, activebackground=CARD, activeforeground=INK,
            selectcolor="#EEF3FF", font=(FONT, 9), anchor="w", padx=0,
        )
        self.vad_check.pack(fill="x", pady=(0, 12))

        tk.Label(left, text="识别提示（可填写人名、专有名词）", bg=CARD, fg=INK, font=(FONT, 10)).pack(anchor="w")
        self.prompt_var = tk.StringVar()
        self.prompt_entry = tk.Entry(
            left, textvariable=self.prompt_var, relief="flat", bd=0, bg="#F7F9FC", fg=INK,
            insertbackground=INK, font=(FONT, 10), highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT
        )
        self.prompt_entry.pack(fill="x", ipady=9, pady=(5, 12))

        self.start_btn = self._button(left, "开始识别语音", self.start_processing, kind="primary")
        self.start_btn.pack(fill="x", pady=(0, 8))
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

        text_wrap = tk.Frame(right, bg=BORDER, padx=1, pady=1)
        text_wrap.pack(fill="both", expand=True)
        self.textbox = ScrolledText(
            text_wrap, wrap="word", relief="flat", bd=0, bg="#FBFCFE", fg=INK,
            insertbackground=INK, font=(FONT, 10), padx=13, pady=12, spacing1=2,
            spacing3=3, undo=True
        )
        self.textbox.pack(fill="both", expand=True)
        self._show_placeholder()

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
        tk.Label(
            outer, text="提示：准确率受录音质量、口音及背景音乐影响；可尝试更大模型或在识别提示中填写专有名词。",
            bg=BG, fg=MUTED, font=(FONT, 9), anchor="w"
        ).pack(fill="x", pady=(12, 0))

    def _show_placeholder(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", "识别文字会在这里实时显示。\n\n建议：\n• 普通视频优先选择「medium（更准确）」\n• 如果后半段漏字，保持「跳过长静音」关闭\n• 人名或专业词可以填写在「识别提示」中")
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
        self.start_btn.configure(state=state)
        self.pick_btn.configure(state=state)
        self.lang_combo.configure(state="disabled" if busy else "readonly")
        self.model_combo.configure(state="disabled" if busy else "readonly")
        self.prompt_entry.configure(state=state)
        self.vad_check.configure(state=state)
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
        self.transcript_text = ""
        self.audio_duration = 0.0
        self.textbox.configure(state="normal", fg="#8390A3")
        self._show_placeholder()
        for button in (self.copy_btn, self.srt_btn, self.txt_btn, self.subtitle_video_btn):
            button.configure(state="disabled")
        size = os.path.getsize(path)
        size_text = f"{size / (1024 * 1024):.1f} MB" if size >= 1024 * 1024 else f"{size / 1024:.0f} KB"
        self.file_label.configure(text=os.path.basename(path), fg=INK)
        self.file_hint.configure(text=f"{size_text}  ·  {os.path.dirname(path)}", fg=MUTED)
        self.mp3_btn.configure(state="normal")
        self.wav_btn.configure(state="normal")
        self.status_var.set("视频已载入。建议使用 medium 模型；为避免漏掉轻声，默认不跳过静音。")
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

    def _make_asr_wav(self, output_path):
        self._ffmpeg_run(
            ["-i", self.video_path, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", output_path],
            "音频准备"
        )

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
        lang_map = {"中文": "zh", "英语": "en", "日语": "ja", "韩语": "ko", "法语": "fr", "德语": "de", "西班牙语": "es"}
        options = {
            "model": model_labels.get(self.model_var.get(), "medium"),
            "language": lang_map.get(self.lang_var.get()),
            "language_label": self.lang_var.get(),
            "vad_filter": bool(self.vad_var.get()),
            "initial_prompt": self.prompt_var.get().strip(),
        }
        self.transcript_segments = []
        self.transcript_text = ""
        self.audio_duration = 0.0
        self._set_busy(True)
        self.txt_btn.configure(state="disabled")
        self.srt_btn.configure(state="disabled")
        self.copy_btn.configure(state="disabled")
        self.subtitle_video_btn.configure(state="disabled")
        self.textbox.configure(state="normal", fg=INK)
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", "正在准备音频……\n")
        self.textbox.see("end")
        self.progress.configure(value=0)
        self.percent_var.set("0%")
        self._set_status("正在准备音频……", 0)
        threading.Thread(target=self._process_worker, args=(options,), daemon=True).start()

    def _process_worker(self, options):
        collected = []
        detected_lang = ""
        duration = 0.0
        temp_dir = None
        failure = None
        try:
            self._set_status("正在提取并整理音频……", 2)
            temp_dir = tempfile.mkdtemp(prefix="shengwen_asr_")
            wav_path = os.path.join(temp_dir, "audio_16k_mono.wav")
            self._make_asr_wav(wav_path)
            with wave.open(wav_path, "rb") as wf:
                duration = wf.getnframes() / max(1, wf.getframerate())
            self.audio_duration = duration
            self._set_status("正在加载识别模型（首次使用可能需要下载）……", 4)
            from faster_whisper import WhisperModel
            model = WhisperModel(options["model"], device="cpu", compute_type="int8")
            self._set_status(f"正在识别 · {options['model']} 模型 · 音频 {format_time(duration)}", 5)

            transcribe_kwargs = dict(
                language=options["language"],
                beam_size=5,
                best_of=5,
                vad_filter=options["vad_filter"],
                condition_on_previous_text=False,
                word_timestamps=False,
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
                compression_ratio_threshold=2.4,
            )
            if options["initial_prompt"]:
                transcribe_kwargs["initial_prompt"] = options["initial_prompt"]
            if options["vad_filter"]:
                # A longer silence threshold and speech padding help preserve quiet/short utterances.
                transcribe_kwargs["vad_parameters"] = {
                    "min_silence_duration_ms": 900,
                    "speech_pad_ms": 400,
                    "min_speech_duration_ms": 100,
                }
            segments, info = model.transcribe(wav_path, **transcribe_kwargs)
            detected_lang = getattr(info, "language", "") or ""
            # Iterate the whole lazy generator. Update both transcript and progress as segments arrive;
            # keep any partial results available if decoding raises partway through a long file.
            for seg in segments:
                text = (seg.text or "").strip()
                if not text:
                    continue
                item = {"start": float(seg.start), "end": float(seg.end), "text": text}
                collected.append(item)
                self.root.after(0, lambda item=item: self._append_segment(item))
                pct = 5 + (min(99.0, max(0.0, item["end"] / duration * 94.0)) if duration else 70)
                self._set_status(f"正在识别 · 已处理到 {format_time(item['end'])} / {format_time(duration)}", pct)
            if not collected:
                raise RuntimeError("没有识别到语音。请检查视频是否有声音，或尝试更大的识别模型。")
        except Exception as exc:
            failure = str(exc)
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            self.root.after(0, lambda data=collected, lang=detected_lang, dur=duration, err=failure: self._finish_processing(data, lang, dur, err))

    def _append_segment(self, item):
        # Called only on the UI thread; stream results so users can see whether later speech is being processed.
        self.textbox.configure(state="normal", fg=INK)
        current = self.textbox.get("1.0", "end-1c")
        if current.strip() == "正在准备音频……":
            self.textbox.delete("1.0", "end")
        self.textbox.insert("end", item["text"] + "\n")
        self.textbox.see("end")

    def _finish_processing(self, segments, lang, duration, error):
        self.transcript_segments = segments
        self.transcript_text = "\n".join(item["text"] for item in segments)
        self._set_busy(False)
        if self.transcript_text:
            self.textbox.configure(state="normal", fg=INK)
            # Rebuild from canonical collected list to guarantee result order and avoid any queue race.
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", self.transcript_text)
            self.textbox.see("1.0")
            self.txt_btn.configure(state="normal")
            self.srt_btn.configure(state="normal")
            self.copy_btn.configure(state="normal")
            self.subtitle_video_btn.configure(state="normal" if self.transcript_segments else "disabled")
            self.progress.configure(value=100 if not error else self.progress["value"])
            self.percent_var.set("100%" if not error else self.percent_var.get())
        else:
            self.textbox.configure(state="normal")
            self.textbox.delete("1.0", "end")
            self.textbox.insert("1.0", "暂未识别到文字。\n\n可以尝试：\n• 选择 medium 或 large-v3 模型\n• 选择正确的语言，而不是自动检测\n• 检查视频中说话声音是否清晰")
            self.textbox.configure(fg="#8390A3")
        if error:
            self._set_status("识别未完整完成；已保留当前已识别文字。", self.progress["value"], DANGER)
            self.root.after(100, lambda e=error: messagebox.showerror("识别未完成", e + ("\n\n已保留识别到的部分文字，可以先导出。" if segments else "")))
            if self.transcript_text:
                self.txt_btn.configure(state="normal")
                self.srt_btn.configure(state="normal")
                self.copy_btn.configure(state="normal")
                self.subtitle_video_btn.configure(state="normal" if self.transcript_segments else "disabled")
        else:
            language_names = {"zh": "中文", "en": "英语", "ja": "日语", "ko": "韩语", "fr": "法语", "de": "德语", "es": "西班牙语"}
            lang_text = language_names.get(lang, lang or "未知")
            self._set_status(f"识别完成 · {lang_text} · {len(segments)} 段 · 音频 {format_time(duration)}", 100, SUCCESS)

    def _ensure_transcript(self):
        if not self.transcript_text:
            messagebox.showinfo("暂无识别结果", "请先完成语音识别。")
            return False
        return True

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
        if not self.transcript_segments:
            messagebox.showinfo("暂无字幕", "请先完成语音识别。")
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

    def export_subtitled_video(self):
        """Render recognized subtitle timings directly into a new MP4 video."""
        if not self._ensure_transcript():
            return
        if not self.video_path or not self.transcript_segments:
            messagebox.showinfo("暂无字幕", "请先选择视频并完成语音识别。")
            return
        base = os.path.splitext(os.path.basename(self.video_path))[0]
        output_path = filedialog.asksaveasfilename(
            title="生成带字幕视频（硬字幕）",
            defaultextension=".mp4",
            initialdir=os.path.dirname(self.video_path),
            initialfile=base + "_带字幕.mp4",
            filetypes=[("MP4 视频", "*.mp4")]
        )
        if not output_path:
            return
        if os.path.normcase(os.path.abspath(output_path)) == os.path.normcase(os.path.abspath(self.video_path)):
            messagebox.showwarning("不能覆盖原视频", "请另存为一个新文件，避免覆盖原视频。")
            return
        # Snapshot the inputs so the worker uses exactly the result displayed to the user.
        video_path = self.video_path
        segments = [dict(item) for item in self.transcript_segments]
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
