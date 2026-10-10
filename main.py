import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "声文 · 视频转文字"

def app_data_dir():
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def ffmpeg_path():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

class SpeechTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("900x650")
        self.root.minsize(760, 560)
        self.root.configure(bg="#F5F7FA")
        self.video_path = ""
        self.audio_path = ""
        self.transcript_segments = []
        self.transcript_text = ""
        self.busy = False
        self._style()
        self._build()

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#F5F7FA")
        style.configure("Card.TFrame", background="#FFFFFF")
        style.configure("TLabel", background="#F5F7FA", foreground="#202939", font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 22, "bold"), foreground="#172033", background="#F5F7FA")
        style.configure("Sub.TLabel", font=("Microsoft YaHei UI", 10), foreground="#687386", background="#F5F7FA")
        style.configure("CardTitle.TLabel", font=("Microsoft YaHei UI", 12, "bold"), background="#FFFFFF", foreground="#202939")
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=(14, 10), background="#3867F4", foreground="#FFFFFF")
        style.map("Accent.TButton", background=[("active", "#2855D9"), ("disabled", "#A9B8F4")])
        style.configure("TButton", font=("Microsoft YaHei UI", 10), padding=(10, 8))
        style.configure("TCombobox", padding=5)
        style.configure("Horizontal.TProgressbar", troughcolor="#E8ECF3", background="#3867F4")

    def _build(self):
        outer = ttk.Frame(self.root, padding=(28, 22))
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 18))
        ttk.Label(header, text="声文", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="VIDEO  →  SPEECH  →  TEXT", style="Sub.TLabel").pack(side="left", padx=(14, 0), pady=(9, 0))
        ttk.Label(outer, text="提取视频音频，自动识别语音，一键导出文字与字幕。", style="Sub.TLabel").pack(anchor="w", pady=(0, 18))

        card = ttk.Frame(outer, style="Card.TFrame", padding=20)
        card.pack(fill="x", pady=(0, 14))
        ttk.Label(card, text="01  选择视频", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 12))
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x")
        self.file_label = tk.Label(row, text="还没有选择视频文件", bg="#F5F7FB", fg="#7B8494",
                                   anchor="w", padx=12, pady=13, font=("Microsoft YaHei UI", 10))
        self.file_label.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.pick_btn = ttk.Button(row, text="浏览文件", command=self.pick_video)
        self.pick_btn.pack(side="right")
        ttk.Label(card, text="支持 MP4、MOV、MKV、AVI、WEBM 等常见格式", background="#FFFFFF",
                  foreground="#8A93A3", font=("Microsoft YaHei UI", 9)).pack(anchor="w", pady=(9, 0))

        opts = ttk.Frame(outer)
        opts.pack(fill="x", pady=(0, 14))
        card2 = ttk.Frame(opts, style="Card.TFrame", padding=18)
        card2.pack(side="left", fill="both", expand=True, padx=(0, 7))
        ttk.Label(card2, text="02  识别设置", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 12))
        line = ttk.Frame(card2, style="Card.TFrame")
        line.pack(fill="x")
        ttk.Label(line, text="识别语言", background="#FFFFFF").pack(side="left")
        self.lang_var = tk.StringVar(value="自动检测")
        self.lang_combo = ttk.Combobox(line, textvariable=self.lang_var, state="readonly", width=13,
            values=["自动检测", "中文", "英语", "日语", "韩语", "法语", "德语", "西班牙语"])
        self.lang_combo.pack(side="right")
        line2 = ttk.Frame(card2, style="Card.TFrame")
        line2.pack(fill="x", pady=(12, 0))
        ttk.Label(line2, text="识别模型", background="#FFFFFF").pack(side="left")
        self.model_var = tk.StringVar(value="small")
        ttk.Combobox(line2, textvariable=self.model_var, state="readonly", width=13,
                     values=["tiny", "base", "small", "medium"]).pack(side="right")
        ttk.Label(card2, text="模型越大通常越准确，也会更慢。首次使用会下载模型。", background="#FFFFFF",
                  foreground="#8A93A3", font=("Microsoft YaHei UI", 9), wraplength=310).pack(anchor="w", pady=(10, 0))

        card3 = ttk.Frame(opts, style="Card.TFrame", padding=18)
        card3.pack(side="left", fill="both", expand=True, padx=(7, 0))
        ttk.Label(card3, text="03  开始处理", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 12))
        self.start_btn = ttk.Button(card3, text="提取音频并识别语音", style="Accent.TButton", command=self.start_processing)
        self.start_btn.pack(fill="x")
        self.audio_btn = ttk.Button(card3, text="仅提取音频（MP3）", command=self.extract_audio_only)
        self.audio_btn.pack(fill="x", pady=(8, 0))
        self.progress = ttk.Progressbar(card3, mode="indeterminate", style="Horizontal.TProgressbar")
        self.progress.pack(fill="x", pady=(12, 6))
        self.status_var = tk.StringVar(value="准备就绪")
        ttk.Label(card3, textvariable=self.status_var, background="#FFFFFF", foreground="#687386",
                  font=("Microsoft YaHei UI", 9), wraplength=300).pack(anchor="w")

        result = ttk.Frame(outer, style="Card.TFrame", padding=18)
        result.pack(fill="both", expand=True)
        top = ttk.Frame(result, style="Card.TFrame")
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="识别结果", style="CardTitle.TLabel").pack(side="left")
        self.txt_btn = ttk.Button(top, text="导出 TXT", command=self.export_txt, state="disabled")
        self.txt_btn.pack(side="right", padx=(8, 0))
        self.srt_btn = ttk.Button(top, text="导出 SRT 字幕", command=self.export_srt, state="disabled")
        self.srt_btn.pack(side="right")
        self.textbox = tk.Text(result, height=8, wrap="word", relief="flat", bg="#F7F8FB", fg="#273244",
                               font=("Microsoft YaHei UI", 10), padx=12, pady=10, insertbackground="#273244")
        self.textbox.pack(fill="both", expand=True)
        self.textbox.insert("1.0", "识别完成后，文字会显示在这里。\n\n提示：首次运行需要联网下载语音识别模型；之后可在本机进行识别。")
        self.textbox.configure(state="disabled")

    def set_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

    def set_busy(self, busy):
        self.busy = busy
        def update():
            state = "disabled" if busy else "normal"
            self.start_btn.configure(state=state)
            self.audio_btn.configure(state=state)
            self.pick_btn.configure(state=state)
            if busy:
                self.progress.start(10)
            else:
                self.progress.stop()
        self.root.after(0, update)

    def pick_video(self):
        path = filedialog.askopenfilename(title="选择视频文件", filetypes=[
            ("视频文件", "*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.mpeg *.mpg"),
            ("所有文件", "*.*")])
        if path:
            self.video_path = path
            self.file_label.configure(text=os.path.basename(path), fg="#202939")
            self.status_var.set("已选择视频，可以开始处理。")

    def _output_dir(self):
        if self.video_path:
            folder = os.path.join(os.path.dirname(self.video_path), "声文导出")
        else:
            folder = os.path.join(os.path.expanduser("~"), "声文导出")
        os.makedirs(folder, exist_ok=True)
        return folder

    def _extract_audio(self, output_path):
        cmd = [ffmpeg_path(), "-y", "-i", self.video_path, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "192k", output_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode != 0:
            raise RuntimeError("音频提取失败。请确认视频文件可正常播放。\n" + result.stderr[-900:])

    def extract_audio_only(self):
        if self.busy:
            return
        if not self.video_path:
            messagebox.showinfo("先选择视频", "请先点击“浏览文件”选择一个视频。")
            return
        self.set_busy(True)
        threading.Thread(target=self._audio_worker, daemon=True).start()

    def _audio_worker(self):
        try:
            out = os.path.join(self._output_dir(), os.path.splitext(os.path.basename(self.video_path))[0] + ".mp3")
            self.set_status("正在提取音频……")
            self._extract_audio(out)
            self.audio_path = out
            self.root.after(0, lambda: messagebox.showinfo("完成", "音频已导出：\n" + out))
            self.set_status("音频导出完成")
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("处理失败", str(e)))
            self.set_status("处理失败，请查看提示")
        finally:
            self.set_busy(False)

    def start_processing(self):
        if self.busy:
            return
        if not self.video_path:
            messagebox.showinfo("先选择视频", "请先点击“浏览文件”选择一个视频。")
            return
        self.set_busy(True)
        self.txt_btn.configure(state="disabled")
        self.srt_btn.configure(state="disabled")
        threading.Thread(target=self._process_worker, daemon=True).start()

    def _process_worker(self):
        try:
            folder = self._output_dir()
            stem = os.path.splitext(os.path.basename(self.video_path))[0]
            self.audio_path = os.path.join(folder, stem + ".wav")
            self.set_status("正在提取音频……")
            self._extract_audio(self.audio_path)
            self.set_status("正在加载语音识别模型（首次使用会下载）……")
            from faster_whisper import WhisperModel
            model_name = self.model_var.get()
            model = WhisperModel(model_name, device="cpu", compute_type="int8")
            lang_map = {"中文": "zh", "英语": "en", "日语": "ja", "韩语": "ko",
                        "法语": "fr", "德语": "de", "西班牙语": "es"}
            lang = lang_map.get(self.lang_var.get())
            self.set_status("正在识别语音，请稍候……")
            segments, info = model.transcribe(self.audio_path, language=lang, vad_filter=True, beam_size=5)
            collected = []
            for seg in segments:
                collected.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
            if not collected:
                raise RuntimeError("没有识别到语音。视频可能没有声音，或声音太轻。")
            self.transcript_segments = collected
            self.transcript_text = "\n".join(s["text"] for s in collected)
            self.root.after(0, self._show_results)
            self.set_status("识别完成 · 共 " + str(len(collected)) + " 段")
        except Exception as e:
            err = str(e)
            self.root.after(0, lambda msg=err: messagebox.showerror("处理失败", msg + "\n\n如果提示缺少模块，请先运行 run.bat。"))
            self.set_status("处理失败，请查看提示")
        finally:
            self.set_busy(False)

    def _show_results(self):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", self.transcript_text)
        self.textbox.configure(state="normal")
        self.txt_btn.configure(state="normal")
        self.srt_btn.configure(state="normal")
        self.status_var.set("识别完成，可以导出 TXT 或 SRT。")

    def export_txt(self):
        if not self.transcript_text:
            return
        path = filedialog.asksaveasfilename(title="导出 TXT", defaultextension=".txt",
            initialfile=os.path.splitext(os.path.basename(self.video_path))[0] + ".txt",
            filetypes=[("文本文件", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8-sig") as f:
                f.write(self.transcript_text)
            self.status_var.set("TXT 已导出")

    @staticmethod
    def _srt_time(seconds):
        ms = int(round(seconds * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    def export_srt(self):
        if not self.transcript_segments:
            return
        path = filedialog.asksaveasfilename(title="导出 SRT", defaultextension=".srt",
            initialfile=os.path.splitext(os.path.basename(self.video_path))[0] + ".srt",
            filetypes=[("SRT 字幕", "*.srt")])
        if path:
            with open(path, "w", encoding="utf-8-sig") as f:
                for i, seg in enumerate(self.transcript_segments, 1):
                    f.write(f"{i}\n{self._srt_time(seg['start'])} --> {self._srt_time(seg['end'])}\n{seg['text']}\n\n")
            self.status_var.set("SRT 字幕已导出")

def main():
    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.15)
    except tk.TclError:
        pass
    SpeechTextApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
