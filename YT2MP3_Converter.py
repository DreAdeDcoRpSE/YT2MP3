# YouTube to MP3 Converter
# Created by coRpSE
#
# The program asks permission before installing any required components.
# Components are kept locally with this program.
# The Remove Components button removes everything this program installed/downloaded.

import importlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_NAME = 'YouTube to MP3 Converter'
BG = '#1e1e1e'
FG = '#f0f0f0'
MUTED = '#aaaaaa'
ENTRY = '#2b2b2b'
BUTTON = '#333333'
GREEN = '#00ff00'
BASE = Path(__file__).resolve().parent
COMPONENTS = BASE / 'components'
YTDLP_DIR = COMPONENTS / 'yt-dlp'
FFMPEG_BIN = COMPONENTS / 'ffmpeg' / 'bin'
FFMPEG_EXE = FFMPEG_BIN / 'ffmpeg.exe'
FFPROBE_EXE = FFMPEG_BIN / 'ffprobe.exe'
FFMPEG_URL = 'https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/ffmpeg-master-latest-win64-gpl.zip'


class Cancelled(Exception):
    pass


def local_ytdlp():
    """Import the bundled package only; never mistake a global install for a local one."""
    if not (YTDLP_DIR / 'yt_dlp' / '__init__.py').is_file():
        return None
    if str(YTDLP_DIR) not in sys.path:
        sys.path.insert(0, str(YTDLP_DIR))
    importlib.invalidate_caches()
    try:
        return importlib.import_module('yt_dlp')
    except (ImportError, OSError):
        return None


def installed():
    return local_ytdlp() is not None and FFMPEG_EXE.is_file() and FFPROBE_EXE.is_file()


def valid_youtube_url(value):
    try:
        parsed = urllib.parse.urlsplit(value)
        host = (parsed.hostname or '').lower().rstrip('.')
        return parsed.scheme in ('https', 'http') and host in (
            'youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com',
            'youtube-nocookie.com', 'www.youtube-nocookie.com', 'youtu.be', 'www.youtu.be'
        ) and bool(parsed.path.strip('/'))
    except ValueError:
        return False


def safe_filename(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', name).rstrip(' .').strip()
    name = name[:170].rstrip(' .') or 'YouTube Audio'
    stem = name.split('.')[0].upper()
    if stem in {'CON', 'PRN', 'AUX', 'NUL'} or re.fullmatch(r'(COM|LPT)[1-9]', stem):
        name = '_' + name
    return name


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.configure(bg=BG)
        self.root.geometry('740x495')
        self.root.minsize(680, 465)
        self.running = False
        self.cancel_event = threading.Event()
        self.ytdlp = None
        self.worker = None
        self.save_path = None
        self.temp_prefix = None
        self.progress_value = tk.DoubleVar(value=0)
        self.quality = tk.StringVar(value='192')
        self.artwork = tk.BooleanVar(value=True)
        self.last_folder = str(Path.home() / 'Music') if (Path.home() / 'Music').is_dir() else str(Path.home())
        self._build()
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.root.after(100, self.check_components)

    def _build(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass
        style.configure('Green.Horizontal.TProgressbar', troughcolor='#292929', background=GREEN,
                        bordercolor='#292929', lightcolor=GREEN, darkcolor=GREEN)
        style.configure('Dark.TCombobox', fieldbackground=ENTRY, background=BUTTON, foreground=FG,
                        arrowcolor=FG, selectbackground=ENTRY, selectforeground=FG)
        style.configure('Dark.TCheckbutton', background=BG, foreground=FG)
        style.map('Dark.TCheckbutton', background=[('active', BG)], foreground=[('active', FG)])
        border = tk.Frame(self.root, bg=GREEN, padx=2, pady=2)
        border.pack(fill='both', expand=True, padx=12, pady=12)
        body = tk.Frame(border, bg=BG, padx=23, pady=16)
        body.pack(fill='both', expand=True)
        tk.Label(body, text=APP_NAME, font=('Segoe UI', 26, 'bold'), bg=BG, fg=FG).pack()
        tk.Label(body, text='Paste a YouTube video URL to convert its audio to MP3.',
                 font=('Segoe UI', 11), bg=BG, fg=MUTED).pack(pady=(2, 16))
        url_row = tk.Frame(body, bg=BG)
        url_row.pack(fill='x')
        self.url_entry = tk.Entry(url_row, font=('Segoe UI', 12), bg=ENTRY, fg=FG,
                                  insertbackground=FG, relief='flat', highlightthickness=1,
                                  highlightbackground=GREEN, highlightcolor=GREEN)
        self.url_entry.pack(side='left', fill='x', expand=True, ipady=8)
        self.convert_btn = self.button(url_row, 'Convert', self.start_conversion, 12)
        self.convert_btn.pack(side='left', padx=(10, 0))
        self.url_entry.bind('<Return>', lambda _event: self.start_conversion())
        self.setup_url_context_menu()

        settings = tk.Frame(body, bg=BG)
        settings.pack(fill='x', pady=(15, 5))
        tk.Label(settings, text='MP3 quality:', bg=BG, fg=FG, font=('Segoe UI', 10)).pack(side='left')
        self.quality_box = ttk.Combobox(settings, textvariable=self.quality, state='readonly',
                                         values=('128', '192', '256', '320'), width=6,
                                         style='Dark.TCombobox')
        self.quality_box.pack(side='left', padx=(8, 5))
        tk.Label(settings, text='kbps', bg=BG, fg=MUTED).pack(side='left')
        self.artwork_check = ttk.Checkbutton(settings, text='Embed title, artist and thumbnail',
                                              variable=self.artwork, style='Dark.TCheckbutton')
        self.artwork_check.pack(side='right')
        tk.Label(body, text='Higher MP3 bitrates do not improve the original audio quality.',
                 font=('Segoe UI', 9), bg=BG, fg=MUTED).pack(anchor='w', pady=(0, 12))

        self.status_label = tk.Label(body, text='Ready', font=('Segoe UI', 11), bg=BG, fg=GREEN)
        self.status_label.pack(pady=(5, 5))
        self.progress = ttk.Progressbar(body, variable=self.progress_value, maximum=100,
                                         mode='determinate', style='Green.Horizontal.TProgressbar')
        self.progress.pack(fill='x', pady=(0, 6))
        self.detail_label = tk.Label(body, text='', font=('Segoe UI', 9), bg=BG, fg=MUTED)
        self.detail_label.pack(pady=(0, 12))
        actions = tk.Frame(body, bg=BG)
        actions.pack(fill='x')
        self.cancel_btn = self.button(actions, 'Cancel', self.cancel_conversion)
        self.cancel_btn.pack(side='left')
        self.cancel_btn.config(state='disabled')
        self.open_btn = self.button(actions, 'Open Save Folder', self.open_folder)
        self.open_btn.pack(side='left', padx=(10, 0))
        self.open_btn.config(state='disabled')
        self.manage_btn = self.button(actions, 'Manage Components', self.manage_components)
        self.manage_btn.pack(side='right')
        self.components_label = tk.Label(body, text='Checking components...', bg=BG, fg=MUTED,
                                          font=('Segoe UI', 9))
        self.components_label.pack(side='bottom', pady=(12, 0))
        self.url_entry.focus_set()

    def setup_url_context_menu(self):
        """Readable right-click menu with consistent hover colors."""
        menu = tk.Menu(
            self.root, tearoff=False, font=('Segoe UI', 11),
            bg=ENTRY, fg=FG, activebackground='#444444',
            activeforeground='#FFFFFF', disabledforeground='#999999',
            selectcolor=GREEN, borderwidth=1, relief='solid',
            activeborderwidth=0,
        )

        def edit(action):
            # Leave menu entries enabled so every item has the same hover
            # styling. An unavailable action simply does nothing.
            entry = self.url_entry
            if action == 'select_all':
                entry.select_range(0, tk.END)
                entry.icursor(tk.END)
                entry.focus_set()
            elif action in ('cut', 'copy'):
                if entry.selection_present():
                    entry.event_generate('<<Cut>>' if action == 'cut' else '<<Copy>>')
            elif action == 'paste':
                try:
                    entry.clipboard_get()
                except tk.TclError:
                    return
                entry.event_generate('<<Paste>>')

        menu.add_command(label='Cut', command=lambda: edit('cut'))
        menu.add_command(label='Copy', command=lambda: edit('copy'))
        menu.add_command(label='Paste', command=lambda: edit('paste'))
        menu.add_separator()
        menu.add_command(label='Select All', command=lambda: edit('select_all'))
        self.url_context_menu = menu

        def show_menu(event):
            if str(self.url_entry.cget('state')) == 'disabled':
                return 'break'
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
            return 'break'

        self.url_entry.bind('<Button-3>', show_menu)
        self.url_entry.bind('<Control-a>', lambda _event: (self.url_entry.select_range(0, tk.END), 'break')[1])

    def button(self, parent, text, command, font_size=10):
        return tk.Button(parent, text=text, command=command, font=('Segoe UI', font_size),
                         bg=BUTTON, fg=FG, activebackground='#444444', activeforeground=FG,
                         relief='flat', padx=12, pady=7, cursor='hand2')

    def ui(self, fn):
        # All UI callbacks are executed by the Tk main loop.
        self.root.after(0, fn)

    def status(self, message, detail=None, percent=None):
        def apply():
            self.status_label.config(text=message)
            if detail is not None:
                self.detail_label.config(text=detail)
            if percent is not None:
                self.progress_value.set(max(0, min(100, percent)))
        self.ui(apply)

    def set_busy(self, busy):
        self.running = busy
        state = 'disabled' if busy else 'normal'
        self.convert_btn.config(state=state)
        self.url_entry.config(state=state)
        self.manage_btn.config(state=state)
        self.quality_box.config(state='disabled' if busy else 'readonly')
        self.artwork_check.config(state=state)
        self.cancel_btn.config(state='normal' if busy else 'disabled')

    def check_components(self):
        self.ytdlp = local_ytdlp()
        ready = self.ytdlp is not None and FFMPEG_EXE.is_file() and FFPROBE_EXE.is_file()
        self.components_label.config(text='yt-dlp / FFmpeg: Installed' if ready else 'Components: Not installed')
        if not ready:
            if messagebox.askyesno('Components Required',
                    'This program needs yt-dlp, FFmpeg and FFprobe.\n\n'
                    'They will be downloaded into the program\'s components folder only.\n'
                    'No system-wide installation is performed.\n\nDownload now?'):
                self.install_dependencies()
            else:
                self.status_label.config(text='Components required before converting.')

    def start_worker(self, function, *args):
        self.cancel_event.clear()
        self.set_busy(True)
        self.worker = threading.Thread(target=function, args=args, daemon=True)
        self.worker.start()

    def finish_worker(self, message, detail='', error=None):
        def done():
            self.set_busy(False)
            self.status_label.config(text=message)
            self.detail_label.config(text=detail)
            if error:
                messagebox.showerror(APP_NAME, str(error))
        self.ui(done)

    def download_file(self, url, destination):
        request = urllib.request.Request(url, headers={'User-Agent': 'YT2MP3-Converter/2.0'})
        with urllib.request.urlopen(request, timeout=45) as response, open(destination, 'wb') as out:
            total = int(response.headers.get('Content-Length') or 0)
            count = 0
            while True:
                if self.cancel_event.is_set():
                    raise Cancelled()
                block = response.read(1024 * 512)
                if not block:
                    break
                out.write(block)
                count += len(block)
                if total:
                    self.status('Downloading FFmpeg...', f'{count / 1048576:.1f} / {total / 1048576:.1f} MB', 100 * count / total)
                else:
                    self.status('Downloading FFmpeg...', f'{count / 1048576:.1f} MB')

    def install_dependencies(self, update=False):
        if self.running:
            return
        self.progress_value.set(0)
        self.start_worker(self._install_worker, update)

    def _install_worker(self, update):
        try:
            COMPONENTS.mkdir(parents=True, exist_ok=True)
            if update or local_ytdlp() is None:
                self.status('Downloading yt-dlp...', 'This may take a moment.', 0)
                with tempfile.TemporaryDirectory(dir=str(COMPONENTS)) as tmp:
                    command = [sys.executable, '-m', 'pip', 'download', '--disable-pip-version-check',
                               '--no-deps', '--only-binary=:all:', '-d', tmp, 'yt-dlp']
                    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
                    if result.returncode:
                        raise RuntimeError('yt-dlp download failed.\n' + (result.stderr or result.stdout)[-1000:])
                    wheels = list(Path(tmp).glob('*.whl'))
                    if not wheels:
                        raise RuntimeError('yt-dlp wheel not found after download.')
                    stage = Path(tmp) / 'unpacked'
                    stage.mkdir()
                    with zipfile.ZipFile(wheels[0]) as archive:
                        # Only yt_dlp package files, and reject unsafe paths.
                        for item in archive.infolist():
                            parts = Path(item.filename).parts
                            if not parts or parts[0] != 'yt_dlp' or '..' in parts or item.is_dir():
                                continue
                            target = stage.joinpath(*parts)
                            target.parent.mkdir(parents=True, exist_ok=True)
                            with archive.open(item) as src, open(target, 'wb') as dst:
                                shutil.copyfileobj(src, dst)
                    source = stage / 'yt_dlp'
                    if not (source / '__init__.py').exists():
                        raise RuntimeError('Downloaded yt-dlp package is incomplete.')
                    target = YTDLP_DIR / 'yt_dlp'
                    YTDLP_DIR.mkdir(parents=True, exist_ok=True)
                    # Keep the old version until the new download has succeeded.
                    backup = YTDLP_DIR / 'yt_dlp_backup'
                    if backup.exists():
                        shutil.rmtree(backup)
                    if target.exists():
                        target.rename(backup)
                    try:
                        shutil.copytree(source, target)
                    except Exception:
                        if target.exists():
                            shutil.rmtree(target)
                        if backup.exists():
                            backup.rename(target)
                        raise
                    if backup.exists():
                        shutil.rmtree(backup)
            if self.cancel_event.is_set():
                raise Cancelled()
            if not FFMPEG_EXE.is_file() or not FFPROBE_EXE.is_file():
                self.status('Downloading FFmpeg...', 'Downloading portable Windows binaries...', 0)
                with tempfile.TemporaryDirectory(dir=str(COMPONENTS)) as tmp:
                    archive_path = Path(tmp) / 'ffmpeg.zip'
                    self.download_file(FFMPEG_URL, archive_path)
                    with zipfile.ZipFile(archive_path) as archive:
                        candidates = {}
                        for item in archive.infolist():
                            basename = Path(item.filename).name.lower()
                            if basename in ('ffmpeg.exe', 'ffprobe.exe') and not item.is_dir():
                                candidates[basename] = item
                        if len(candidates) != 2:
                            raise RuntimeError('FFmpeg archive does not contain both required executables.')
                        FFMPEG_BIN.mkdir(parents=True, exist_ok=True)
                        for name, item in candidates.items():
                            if self.cancel_event.is_set():
                                raise Cancelled()
                            target = FFMPEG_BIN / name
                            staged = Path(tmp) / name
                            with archive.open(item) as src, open(staged, 'wb') as dst:
                                shutil.copyfileobj(src, dst)
                            os.replace(staged, target)
            if self.cancel_event.is_set():
                raise Cancelled()
            self.ui(self._installation_success)
        except Cancelled:
            self.finish_worker('Installation cancelled.')
        except Exception as exc:
            self.finish_worker('Component installation failed.', error=exc)

    def _installation_success(self):
        self.ytdlp = local_ytdlp()
        if self.ytdlp is None or not FFMPEG_EXE.is_file() or not FFPROBE_EXE.is_file():
            self.set_busy(False)
            messagebox.showerror(APP_NAME, 'Components could not be verified. Restart and try again.')
            return
        self.set_busy(False)
        self.progress_value.set(0)
        self.status_label.config(text='Ready')
        self.detail_label.config(text='')
        self.components_label.config(text='yt-dlp / FFmpeg: Installed')
        messagebox.showinfo(APP_NAME, 'Components are ready to use.')

    def start_conversion(self):
        if self.running:
            return
        url = self.url_entry.get().strip()
        if not valid_youtube_url(url):
            messagebox.showerror(APP_NAME, 'Please enter a valid YouTube video URL.')
            return
        if not installed():
            messagebox.showerror(APP_NAME, 'Required components are missing. Use Manage Components to install them.')
            return
        self.progress_value.set(0)
        self.detail_label.config(text='')
        self.start_worker(self._fetch_info, url)

    def _fetch_info(self, url):
        try:
            self.status('Getting video information...')
            with self.ytdlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'noplaylist': True,
                                       'socket_timeout': 25, 'retries': 2}) as ydl:
                info = ydl.extract_info(url, download=False)
            if self.cancel_event.is_set():
                raise Cancelled()
            if not info:
                raise RuntimeError('No video information returned.')
            title = safe_filename(info.get('title') or 'YouTube Audio')
            self.ui(lambda: self.choose_save_path(url, title))
        except Cancelled:
            self.finish_worker('Cancelled.')
        except Exception as exc:
            self.finish_worker('Unable to get video information.', error=exc)

    def choose_save_path(self, url, title):
        self.status_label.config(text='Choose where to save the MP3...')
        destination = filedialog.asksaveasfilename(title='Save MP3 File', defaultextension='.mp3',
                    initialdir=self.last_folder, initialfile=title + '.mp3',
                    filetypes=[('MP3 Audio', '*.mp3')])
        if not destination:
            self.set_busy(False)
            self.status_label.config(text='Cancelled.')
            return
        destination = str(Path(destination).with_suffix('.mp3'))
        if os.path.exists(destination) and not messagebox.askyesno('Overwrite existing file?',
                f'This file already exists:\n\n{destination}\n\nReplace it?'):
            self.set_busy(False)
            self.status_label.config(text='Cancelled.')
            return
        self.last_folder = str(Path(destination).parent)
        self.save_path = destination
        self.progress_value.set(0)
        self.status_label.config(text='Downloading audio...')
        self.cancel_event.clear()
        quality = self.quality.get()
        embed_artwork = self.artwork.get()
        self.worker = threading.Thread(target=self._convert_worker, args=(url, destination, quality, embed_artwork), daemon=True)
        self.worker.start()

    def _convert_worker(self, url, destination, quality, embed_artwork):
        # Download into a temporary directory to avoid overwriting the target on failure.
        try:
            with tempfile.TemporaryDirectory(prefix='yt2mp3-', dir=str(Path(destination).parent)) as tmp:
                output = str(Path(tmp) / 'audio.%(ext)s')
                def hook(data):
                    if self.cancel_event.is_set():
                        raise Cancelled()
                    state = data.get('status')
                    if state == 'downloading':
                        current = data.get('downloaded_bytes', 0)
                        total = data.get('total_bytes') or data.get('total_bytes_estimate')
                        speed = data.get('speed')
                        eta = data.get('eta')
                        detail = f'{current / 1048576:.1f} MB'
                        if total:
                            detail += f' / {total / 1048576:.1f} MB'
                        if speed:
                            detail += f'  •  {speed / 1048576:.2f} MB/s'
                        if eta is not None:
                            detail += f'  •  {int(eta)}s remaining'
                        self.status('Downloading audio...', detail, current * 100 / total if total else None)
                    elif state == 'finished':
                        self.status('Converting to MP3...', 'Encoding audio; please wait.', 100)
                def post_hook(data):
                    if self.cancel_event.is_set():
                        raise Cancelled()
                    if data.get('status') == 'started':
                        self.status('Converting to MP3...', 'Encoding audio; please wait.', 100)
                opts = {
                    'format': 'bestaudio/best', 'outtmpl': output, 'noplaylist': True,
                    'ffmpeg_location': str(FFMPEG_BIN), 'quiet': True, 'no_warnings': True,
                    'overwrites': False, 'socket_timeout': 30, 'retries': 3,
                    'progress_hooks': [hook], 'postprocessor_hooks': [post_hook],
                    'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',
                                        'preferredquality': quality}],
                }
                if embed_artwork:
                    opts['writethumbnail'] = True
                    opts['postprocessors'] += [
                        {'key': 'FFmpegMetadata', 'add_metadata': True},
                        {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
                    ]
                with self.ytdlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                if self.cancel_event.is_set():
                    raise Cancelled()
                converted = Path(tmp) / 'audio.mp3'
                if not converted.is_file():
                    raise RuntimeError('The converted MP3 could not be found.')
                # Atomic replacement on the same volume; existing target survives failed conversion.
                os.replace(converted, destination)
            self.ui(lambda: self.conversion_success(destination))
        except Cancelled:
            self.finish_worker('Conversion cancelled.', 'Temporary download files removed.')
        except Exception as exc:
            self.finish_worker('Conversion failed.', error=exc)

    def conversion_success(self, destination):
        self.set_busy(False)
        self.progress_value.set(100)
        self.status_label.config(text='Conversion complete!')
        self.detail_label.config(text=destination)
        self.url_entry.delete(0, tk.END)
        self.open_btn.config(state='normal')
        messagebox.showinfo('Success', f'MP3 created successfully!\n\nSaved to:\n{destination}')

    def cancel_conversion(self):
        if self.running:
            self.cancel_event.set()
            self.status_label.config(text='Cancelling...')
            self.cancel_btn.config(state='disabled')

    def open_folder(self):
        if self.save_path and os.path.isdir(os.path.dirname(self.save_path)):
            os.startfile(os.path.dirname(self.save_path))

    def manage_components(self):
        if self.running:
            return
        dlg = tk.Toplevel(self.root)
        dlg.title('Manage Components')
        dlg.configure(bg=BG)
        dlg.geometry('410x240')
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()
        version = getattr(getattr(self.ytdlp, 'version', None), '__version__', 'Not installed')
        tk.Label(dlg, text='Component Manager', font=('Segoe UI', 17, 'bold'),
                 bg=BG, fg=FG).pack(pady=(15, 8))
        tk.Label(dlg, text=f'yt-dlp: {version}\nFFmpeg: {"Installed" if FFMPEG_EXE.is_file() else "Missing"}\n'
                           f'FFprobe: {"Installed" if FFPROBE_EXE.is_file() else "Missing"}',
                 bg=BG, fg=MUTED, justify='left').pack()
        buttons = tk.Frame(dlg, bg=BG)
        buttons.pack(pady=12)
        def do_update():
            dlg.destroy()
            self.install_dependencies(update=True)
        def do_remove():
            dlg.destroy()
            self.remove_components()
        self.button(buttons, 'Install / Update yt-dlp', do_update).pack(side='left', padx=5)
        self.button(buttons, 'Remove Components', do_remove).pack(side='left', padx=5)
        tk.Label(dlg, text='Updates require internet access and may take a moment.',
                 bg=BG, fg=MUTED, font=('Segoe UI', 9)).pack()

    def remove_components(self):
        if self.running:
            return
        if not messagebox.askyesno('Remove Components',
                'Remove locally downloaded yt-dlp, FFmpeg and FFprobe?\n\nYour MP3 files will not be deleted.'):
            return
        try:
            if COMPONENTS.exists():
                shutil.rmtree(COMPONENTS)
            self.ytdlp = None
            self.components_label.config(text='Components: Not installed')
            self.status_label.config(text='Components removed. Restart or use Manage Components to reinstall.')
            messagebox.showinfo(APP_NAME, 'Components removed. Restart the program before reinstalling yt-dlp.')
        except OSError as exc:
            messagebox.showerror(APP_NAME, f'Unable to remove components:\n{exc}')

    def on_close(self):
        if self.running:
            if not messagebox.askyesno(APP_NAME, 'A task is still running. Cancel it and close?'):
                return
            self.cancel_event.set()
        self.root.destroy()



def main():
    if os.name != 'nt':
        print('This portable build requires Windows (FFmpeg Windows binaries).')
        return
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
