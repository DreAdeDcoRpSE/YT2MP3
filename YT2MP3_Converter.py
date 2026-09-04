###################################################
# YouTube to MP3 Converter
# Created by coRpSE
#
# The program asks permission before installing
# any required components.
#
# Components are kept locally with this program.
# The Remove Components button removes everything
# this program installed/downloaded.
###################################################

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import urllib.request
import zipfile
import shutil
import re
import importlib.util


###################################################
# SETTINGS
###################################################

APP_NAME = "YouTube to MP3 Converter"

# Dark mode colors
BG_COLOR = "#1e1e1e"
FG_COLOR = "#f0f0f0"
ENTRY_BG = "#2b2b2b"
BUTTON_BG = "#333333"
BUTTON_ACTIVE = "#444444"
STATUS_COLOR = "#00FF00"
BORDER_COLOR = "#00FF00"
PROGRESS_BG = "#333333"
PROGRESS_TROUGH = "#252525"

BASE_FOLDER = os.path.dirname(
    os.path.abspath(__file__)
)

COMPONENTS_FOLDER = os.path.join(
    BASE_FOLDER,
    "components"
)

YTDLP_FOLDER = os.path.join(
    COMPONENTS_FOLDER,
    "yt-dlp"
)

FFMPEG_FOLDER = os.path.join(
    COMPONENTS_FOLDER,
    "ffmpeg"
)

FFMPEG_BIN = os.path.join(
    FFMPEG_FOLDER,
    "bin"
)

FFMPEG_EXE = os.path.join(
    FFMPEG_BIN,
    "ffmpeg.exe"
)

FFPROBE_EXE = os.path.join(
    FFMPEG_BIN,
    "ffprobe.exe"
)


###################################################
# LOCAL YT-DLP IMPORT
###################################################

def find_ytdlp():

    ###################################################
    # Check our local component folder first
    ###################################################

    if os.path.isdir(YTDLP_FOLDER):

        for root, dirs, files in os.walk(
            YTDLP_FOLDER
        ):

            if "__init__.py" in files:

                if root not in sys.path:

                    sys.path.insert(
                        0,
                        root
                    )

                try:

                    import yt_dlp

                    return yt_dlp

                except ImportError:

                    pass

    ###################################################
    # Check normal Python installation
    ###################################################

    try:

        import yt_dlp

        return yt_dlp

    except ImportError:

        return None


###################################################
# DOWNLOAD YT-DLP LOCALLY
###################################################

def download_ytdlp():

    os.makedirs(
        YTDLP_FOLDER,
        exist_ok=True
    )

    ###################################################
    # Download yt-dlp as a ZIP from PyPI
    ###################################################

    zip_path = os.path.join(
        COMPONENTS_FOLDER,
        "yt-dlp.zip"
    )

    download_url = (
        "https://files.pythonhosted.org/packages/"
        "source/y/yt-dlp/yt_dlp-latest.tar.gz"
    )

    ###################################################
    # PyPI source URL can change, so use pip to
    # download the package without installing it.
    ###################################################

    try:

        os.makedirs(
            COMPONENTS_FOLDER,
            exist_ok=True
        )

        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "download",
            "--no-deps",
            "--only-binary=:all:",
            "-d",
            YTDLP_FOLDER,
            "yt-dlp"
        ])

        ###################################################
        # Find downloaded wheel
        ###################################################

        wheel = None

        for file in os.listdir(
            YTDLP_FOLDER
        ):

            if file.lower().endswith(
                ".whl"
            ):

                wheel = os.path.join(
                    YTDLP_FOLDER,
                    file
                )

                break

        if not wheel:

            raise Exception(
                "Could not download the yt-dlp package."
            )

        ###################################################
        # Extract wheel
        ###################################################

        extract_folder = os.path.join(
            YTDLP_FOLDER,
            "package"
        )

        os.makedirs(
            extract_folder,
            exist_ok=True
        )

        with zipfile.ZipFile(
            wheel,
            "r"
        ) as archive:

            archive.extractall(
                extract_folder
            )

        ###################################################
        # Remove wheel
        ###################################################

        try:

            os.remove(
                wheel
            )

        except Exception:
            pass

        ###################################################
        # Locate yt_dlp package
        ###################################################

        package_location = None

        for root, dirs, files in os.walk(
            extract_folder
        ):

            if (
                os.path.basename(root) == "yt_dlp"
                and
                "__init__.py" in files
            ):

                package_location = root

                break

        if not package_location:

            raise Exception(
                "Could not locate yt-dlp after downloading it."
            )

        ###################################################
        # Move yt_dlp into component folder
        ###################################################

        final_package = os.path.join(
            YTDLP_FOLDER,
            "yt_dlp"
        )

        if os.path.exists(
            final_package
        ):

            shutil.rmtree(
                final_package
            )

        shutil.copytree(
            package_location,
            final_package
        )

        ###################################################
        # Remove temporary extraction
        ###################################################

        try:

            shutil.rmtree(
                extract_folder
            )

        except Exception:
            pass

        ###################################################
        # Add local folder to Python path
        ###################################################

        if YTDLP_FOLDER not in sys.path:

            sys.path.insert(
                0,
                YTDLP_FOLDER
            )

        ###################################################
        # Import
        ###################################################

        import yt_dlp

        return yt_dlp

    except Exception as e:

        raise Exception(
            "Unable to download yt-dlp.\n\n"
            + str(e)
        )


###################################################
# DOWNLOAD PORTABLE FFMPEG
###################################################

def download_ffmpeg():

    os.makedirs(
        FFMPEG_FOLDER,
        exist_ok=True
    )

    os.makedirs(
        FFMPEG_BIN,
        exist_ok=True
    )

    zip_path = os.path.join(
        FFMPEG_FOLDER,
        "ffmpeg.zip"
    )

    ###################################################
    # Portable Windows FFmpeg build
    ###################################################

    download_url = (
        "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/"
        "ffmpeg-master-latest-win64-gpl.zip"
    )

    try:

        urllib.request.urlretrieve(
            download_url,
            zip_path
        )

        ###################################################
        # Extract archive
        ###################################################

        with zipfile.ZipFile(
            zip_path,
            "r"
        ) as archive:

            archive.extractall(
                FFMPEG_FOLDER
            )

        ###################################################
        # Locate both executables
        ###################################################

        found_ffmpeg = None
        found_ffprobe = None

        for current_root, dirs, files in os.walk(
            FFMPEG_FOLDER
        ):

            if "ffmpeg.exe" in files:

                found_ffmpeg = os.path.join(
                    current_root,
                    "ffmpeg.exe"
                )

            if "ffprobe.exe" in files:

                found_ffprobe = os.path.join(
                    current_root,
                    "ffprobe.exe"
                )

            if found_ffmpeg and found_ffprobe:

                break

        ###################################################
        # Verify
        ###################################################

        if not found_ffmpeg:

            raise Exception(
                "ffmpeg.exe could not be found."
            )

        if not found_ffprobe:

            raise Exception(
                "ffprobe.exe could not be found."
            )

        ###################################################
        # Copy to permanent bin folder
        ###################################################

        shutil.copy2(
            found_ffmpeg,
            FFMPEG_EXE
        )

        shutil.copy2(
            found_ffprobe,
            FFPROBE_EXE
        )

        ###################################################
        # Remove downloaded archive
        ###################################################

        try:

            os.remove(
                zip_path
            )

        except Exception:
            pass

        ###################################################
        # Remove extracted FFmpeg folders/files
        ###################################################

        for item in os.listdir(
            FFMPEG_FOLDER
        ):

            item_path = os.path.join(
                FFMPEG_FOLDER,
                item
            )

            if os.path.abspath(
                item_path
            ) == os.path.abspath(
                FFMPEG_BIN
            ):

                continue

            try:

                if os.path.isdir(
                    item_path
                ):

                    shutil.rmtree(
                        item_path
                    )

                else:

                    os.remove(
                        item_path
                    )

            except Exception:
                pass

        ###################################################
        # Final verification
        ###################################################

        if (
            os.path.isfile(FFMPEG_EXE)
            and
            os.path.isfile(FFPROBE_EXE)
        ):

            return True

        raise Exception(
            "FFmpeg installation could not be verified."
        )

    except Exception as e:

        try:

            if os.path.exists(
                zip_path
            ):

                os.remove(
                    zip_path
                )

        except Exception:
            pass

        raise e


###################################################
# COMPONENT CHECK
###################################################

def components_available():

    ytdlp = find_ytdlp()

    ffmpeg_ready = (
        os.path.isfile(FFMPEG_EXE)
        and
        os.path.isfile(FFPROBE_EXE)
    )

    return (
        ytdlp is not None
        and
        ffmpeg_ready
    )


###################################################
# INSTALL COMPONENTS WITH USER PERMISSION
###################################################

def install_components():

    ###################################################
    # Check what is missing
    ###################################################

    ytdlp_missing = (
        find_ytdlp() is None
    )

    ffmpeg_missing = not (
        os.path.isfile(FFMPEG_EXE)
        and
        os.path.isfile(FFPROBE_EXE)
    )

    ###################################################
    # Nothing missing
    ###################################################

    if (
        not ytdlp_missing
        and
        not ffmpeg_missing
    ):

        return find_ytdlp()


    ###################################################
    # Build consent message
    ###################################################

    components = []

    if ytdlp_missing:

        components.append(
            "yt-dlp"
        )

    if ffmpeg_missing:

        components.append(
            "FFmpeg / FFprobe"
        )

    component_text = "\n".join(
        "  • " + item
        for item in components
    )

    ###################################################
    # Ask permission
    ###################################################

    answer = messagebox.askyesno(
        "Components Required",
        "This program needs the following components "
        "to be able to convert YouTube videos to MP3:\n\n"
        f"{component_text}\n\n"
        "These components will be downloaded to the "
        "program's own folder.\n\n"
        "Nothing will be installed system-wide.\n\n"
        "Would you like to proceed?"
    )

    ###################################################
    # User said NO
    ###################################################

    if not answer:

        messagebox.showinfo(
            APP_NAME,
            "No components were installed.\n\n"
            "The converter cannot be used until the "
            "required components are installed."
        )

        return None


    ###################################################
    # User said YES
    ###################################################

    try:

        if ytdlp_missing:

            status_window(
                "Installing yt-dlp..."
            )

            ytdlp = download_ytdlp()

        else:

            ytdlp = find_ytdlp()


        if ffmpeg_missing:

            status_window(
                "Downloading FFmpeg..."
            )

            download_ffmpeg()


        ###################################################
        # Final verification
        ###################################################

        ytdlp = find_ytdlp()

        if ytdlp is None:

            raise Exception(
                "yt-dlp could not be installed."
            )

        if not (
            os.path.isfile(FFMPEG_EXE)
            and
            os.path.isfile(FFPROBE_EXE)
        ):

            raise Exception(
                "FFmpeg and FFprobe could not be installed."
            )


        close_status_window()

        messagebox.showinfo(
            APP_NAME,
            "All required components have been installed.\n\n"
            "You are ready to use the converter."
        )

        return ytdlp


    except Exception as e:

        close_status_window()

        messagebox.showerror(
            "Installation Error",
            "The required components could not be installed.\n\n"
            + str(e)
        )

        return None


###################################################
# INSTALLATION STATUS WINDOW
###################################################

installation_window = None
installation_label = None


def status_window(text):

    global installation_window
    global installation_label

    if installation_window is None:

        installation_window = tk.Toplevel()

        installation_window.configure(
            bg=BG_COLOR
        )

        installation_window.title(
            APP_NAME
        )

        installation_window.geometry(
            "400x130"
        )

        installation_window.resizable(
            False,
            False
        )

        installation_window.transient()

        installation_window.grab_set()

        installation_label = tk.Label(
            installation_window,
            text=text,
            font=("Segoe UI", 12),
            wraplength=350,
            bg=BG_COLOR,
            fg=FG_COLOR
        )

        installation_label.pack(
            expand=True
        )

    else:

        installation_label.config(
            text=text
        )

    installation_window.update()


def close_status_window():

    global installation_window

    if installation_window:

        try:

            installation_window.grab_release()

        except Exception:
            pass

        installation_window.destroy()

        installation_window = None


###################################################
# MAIN APPLICATION
###################################################

class YouTubeToMP3:

    def __init__(
        self,
        root,
        ytdlp
    ):

        self.root = root

        self.ytdlp = ytdlp

        self.root.title(
            APP_NAME
        )

        # Dark mode
        self.root.configure(
            bg=BG_COLOR
        )

        style = ttk.Style()

        try:

            style.theme_use(
                "clam"
            )

        except tk.TclError:

            pass

        style.configure(
            "Dark.Horizontal.TProgressbar",
            troughcolor=PROGRESS_TROUGH,
            background=FG_COLOR,
            bordercolor=PROGRESS_BG,
            lightcolor=FG_COLOR,
            darkcolor=FG_COLOR
        )

        self.root.geometry(
            "700x400"
        )

        self.root.resizable(
            False,
            False
        )

        self.center_window()


        ###################################################
        # OUTER BORDER / MAIN FRAME
        ###################################################

        # The outer frame creates a visible border around
        # the entire converter interface.
        outer_frame = tk.Frame(
            self.root,
            bg=BORDER_COLOR,
            padx=2,
            pady=2
        )

        outer_frame.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        main_frame = tk.Frame(
            outer_frame,
            padx=25,
            pady=20,
            bg=BG_COLOR
        )

        main_frame.pack(
            fill="both",
            expand=True
        )


        ###################################################
        # TITLE
        ###################################################

        title = tk.Label(
            main_frame,
            text="YouTube to MP3 Converter",
            font=("Segoe UI", 32, "bold"),
            bg=BG_COLOR,
            fg=FG_COLOR
        )

        title.pack(
            pady=(0, 8)
        )


        ###################################################
        # DESCRIPTION
        ###################################################

        description = tk.Label(
            main_frame,
            text="Just paste the URL of the YouTube video to\nconvert it to a .mp3 file. ",
            font=("Segoe UI", 14),
            bg=BG_COLOR,
            fg=FG_COLOR
        )

        description.pack()


        ###################################################
        # SIGNATURE
        ###################################################

        signature = tk.Label(
            main_frame,
            text="Enjoy...      -coRpSE",
            font=("Segoe UI", 12),
            bg=BG_COLOR,
            fg=FG_COLOR
        )

        signature.pack(
            pady=(2, 20)
        )


        ###################################################
        # URL FRAME
        ###################################################

        url_frame = tk.Frame(
            main_frame,
            bg=BG_COLOR
        )

        url_frame.pack(
            fill="x"
        )


        ###################################################
        # URL ENTRY
        ###################################################

        self.url_entry = tk.Entry(
            url_frame,
            font=("Segoe UI", 14),
            bg=ENTRY_BG,
            fg=FG_COLOR,
            insertbackground=FG_COLOR,
            selectbackground=BUTTON_ACTIVE,
            selectforeground=FG_COLOR,
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=FG_COLOR
        )

        self.url_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=7
        )


        ###################################################
        # CONVERT BUTTON
        ###################################################

        self.convert_button = tk.Button(
            url_frame,
            text="Convert",
            font=("Segoe UI", 14, "bold"),
            padx=22,
            pady=5,
            command=self.start_conversion,
            bg=BUTTON_BG,
            fg=FG_COLOR,
            activebackground=BUTTON_ACTIVE,
            activeforeground=FG_COLOR,
            relief="flat",
            bd=0,
            cursor="hand2"
        )

        self.convert_button.pack(
            side="left",
            padx=(10, 0)
        )


        ###################################################
        # STATUS
        ###################################################

        self.status_label = tk.Label(
            main_frame,
            text="Ready",
            font=("Segoe UI", 11),
            bg=BG_COLOR,
            fg=STATUS_COLOR
        )

        self.status_label.pack(
            pady=(20, 5)
        )


        ###################################################
        # PROGRESS BAR
        ###################################################

        self.progress = ttk.Progressbar(
            main_frame,
            mode="indeterminate",
            style="Dark.Horizontal.TProgressbar"
        )

        self.progress.pack(
            fill="x",
            pady=(0, 15)
        )


        ###################################################
        # REMOVE COMPONENTS BUTTON
        ###################################################

        self.remove_button = tk.Button(
            main_frame,
            text="Remove Installed Components",
            font=("Segoe UI", 10),
            command=self.remove_components,
            bg=BUTTON_BG,
            fg=FG_COLOR,
            activebackground=BUTTON_ACTIVE,
            activeforeground=FG_COLOR,
            relief="flat",
            bd=0,
            cursor="hand2"
        )

        self.remove_button.pack()


        ###################################################
        # ENTER KEY
        ###################################################

        self.url_entry.bind(
            "<Return>",
            lambda event: self.start_conversion()
        )

        self.url_entry.focus_set()


    ###################################################
    # CENTER WINDOW
    ###################################################

    def center_window(self):

        self.root.update_idletasks()

        width = self.root.winfo_width()

        height = self.root.winfo_height()

        screen_width = (
            self.root.winfo_screenwidth()
        )

        screen_height = (
            self.root.winfo_screenheight()
        )

        x = int(
            (screen_width - width) / 2
        )

        y = int(
            (screen_height - height) / 2
        )

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )


    ###################################################
    # START CONVERSION
    ###################################################

    def start_conversion(self):

        url = self.url_entry.get().strip()

        if not url:

            messagebox.showerror(
                APP_NAME,
                "Please paste a YouTube URL first."
            )

            self.url_entry.focus_set()

            return


        ###################################################
        # Basic URL validation
        ###################################################

        if (
            "youtube.com" not in url
            and
            "youtu.be" not in url
        ):

            messagebox.showerror(
                APP_NAME,
                "Please enter a valid YouTube URL."
            )

            self.url_entry.focus_set()

            return


        ###################################################
        # Disable controls
        ###################################################

        self.convert_button.config(
            state="disabled"
        )

        self.url_entry.config(
            state="disabled"
        )

        self.remove_button.config(
            state="disabled"
        )

        self.status_label.config(
            text="Getting video information..."
        )

        self.progress.start(10)


        ###################################################
        # Background thread
        ###################################################

        thread = threading.Thread(
            target=self.prepare_conversion,
            args=(url,),
            daemon=True
        )

        thread.start()


    ###################################################
    # PREPARE CONVERSION
    ###################################################

    def prepare_conversion(
        self,
        url
    ):

        try:

            self.update_status(
                "Getting video information..."
            )

            options = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True
            }

            with self.ytdlp.YoutubeDL(
                options
            ) as ydl:

                info = ydl.extract_info(
                    url,
                    download=False
                )

            title = info.get(
                "title",
                "YouTube Audio"
            )

            title = self.clean_filename(
                title
            )

            self.root.after(
                0,
                lambda: self.ask_save_location(
                    url,
                    title
                )
            )


        except Exception as e:

            self.show_error(
                "Error",
                str(e)
            )

            self.root.after(
                0,
                self.reset_gui
            )


    ###################################################
    # ASK SAVE LOCATION
    ###################################################

    def ask_save_location(
        self,
        url,
        title
    ):

        self.progress.stop()

        save_location = filedialog.asksaveasfilename(
            title="Save MP3 File",
            defaultextension=".mp3",
            initialfile=title + ".mp3",
            filetypes=[
                (
                    "MP3 Audio",
                    "*.mp3"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )


        if not save_location:

            self.reset_gui()

            return


        self.progress.start(10)

        self.status_label.config(
            text="Downloading audio..."
        )


        thread = threading.Thread(
            target=self.convert_video,
            args=(
                url,
                save_location
            ),
            daemon=True
        )

        thread.start()


    ###################################################
    # CONVERT VIDEO
    ###################################################

    def convert_video(
        self,
        url,
        save_location
    ):

        try:

            output_directory = os.path.dirname(
                save_location
            )

            filename = os.path.splitext(
                os.path.basename(
                    save_location
                )
            )[0]

            output_template = os.path.join(
                output_directory,
                filename + ".%(ext)s"
            )


            ###################################################
            # yt-dlp options
            ###################################################

            options = {

                "format": "bestaudio/best",

                "outtmpl": output_template,

                "noplaylist": True,

                "ffmpeg_location": FFMPEG_BIN,

                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192"
                    }
                ],

                "progress_hooks": [
                    self.progress_hook
                ],

                "quiet": True,

                "no_warnings": True
            }


            ###################################################
            # Download
            ###################################################

            with self.ytdlp.YoutubeDL(
                options
            ) as ydl:

                ydl.download(
                    [url]
                )


            ###################################################
            # Verify MP3
            ###################################################

            final_file = os.path.join(
                output_directory,
                filename + ".mp3"
            )

            if not os.path.isfile(
                final_file
            ):

                raise Exception(
                    "The MP3 file could not be found "
                    "after conversion."
                )


            ###################################################
            # Success
            ###################################################

            self.update_status(
                "Conversion complete!"
            )

            self.root.after(
                0,
                lambda: self.show_success_and_clear(
                    final_file
                )
            )


        except Exception as e:

            self.update_status(
                "Conversion failed."
            )

            self.show_error(
                "Conversion Error",
                str(e)
            )


        finally:

            self.root.after(
                0,
                self.reset_gui
            )


    ###################################################
    # SUCCESS MESSAGE + CLEAR URL
    ###################################################

    def show_success_and_clear(
        self,
        final_file
    ):

        messagebox.showinfo(
            "Success",
            "The MP3 was successfully created!\n\n"
            f"Saved to:\n{final_file}"
        )

        ###################################################
        # Clear the URL after the success message
        # has been dismissed.
        ###################################################

        self.url_entry.delete(
            0,
            tk.END
        )

        self.status_label.config(
            text="Ready"
        )


    ###################################################
    # PROGRESS
    ###################################################

    def progress_hook(
        self,
        data
    ):

        status = data.get(
            "status"
        )

        if status == "downloading":

            downloaded = data.get(
                "downloaded_bytes",
                0
            )

            total = data.get(
                "total_bytes"
            )

            if total:

                percent = (
                    downloaded / total
                ) * 100

                self.update_status(
                    f"Downloading... {percent:.1f}%"
                )

            else:

                self.update_status(
                    "Downloading..."
                )


        elif status == "finished":

            self.update_status(
                "Download complete. "
                "Converting to MP3..."
            )


    ###################################################
    # REMOVE COMPONENTS
    ###################################################

    def remove_components(self):

        answer = messagebox.askyesno(
            "Remove Installed Components",
            "This will remove the components installed "
            "by this program:\n\n"
            "  • yt-dlp\n"
            "  • FFmpeg\n"
            "  • FFprobe\n\n"
            "Your MP3 files will NOT be deleted.\n\n"
            "Are you sure you want to remove them?"
        )


        if not answer:

            return


        ###################################################
        # Remove component folder
        ###################################################

        try:

            if os.path.exists(
                COMPONENTS_FOLDER
            ):

                shutil.rmtree(
                    COMPONENTS_FOLDER
                )


            messagebox.showinfo(
                "Components Removed",
                "The installed components have been removed."
            )


            ###################################################
            # Disable converter because dependencies
            # are no longer available.
            ###################################################

            self.convert_button.config(
                state="disabled"
            )

            self.remove_button.config(
                state="disabled"
            )

            self.status_label.config(
                text="Components removed.\n"
                     "You need to restart program to "
                     "rininstall components."
            )


        except Exception as e:

            messagebox.showerror(
                "Removal Error",
                "The components could not be completely removed.\n\n"
                + str(e)
            )


    ###################################################
    # CLEAN WINDOWS FILENAME
    ###################################################

    def clean_filename(
        self,
        filename
    ):

        filename = re.sub(
            r'[<>:"/\\|?*]',
            "",
            filename
        )

        filename = re.sub(
            r"[\x00-\x1f]",
            "",
            filename
        )

        filename = filename.rstrip(
            ". "
        )

        if not filename:

            filename = "YouTube Audio"


        reserved = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9"
        }


        if filename.upper() in reserved:

            filename = "_" + filename


        return filename


    ###################################################
    # UPDATE STATUS
    ###################################################

    def update_status(
        self,
        text
    ):

        self.root.after(
            0,
            lambda: self.status_label.config(
                text=text
            )
        )


    ###################################################
    # SHOW ERROR
    ###################################################

    def show_error(
        self,
        title,
        message
    ):

        self.root.after(
            0,
            lambda: messagebox.showerror(
                title,
                message
            )
        )


    ###################################################
    # RESET GUI
    ###################################################

    def reset_gui(
        self
    ):

        self.progress.stop()

        self.convert_button.config(
            state="normal"
        )

        self.remove_button.config(
            state="normal"
        )

        self.url_entry.config(
            state="normal"
        )

        self.url_entry.focus_set()


###################################################
# MAIN
###################################################

def main():

    global installation_window

    root = tk.Tk()

    ###################################################
    # Hide window while checking components
    ###################################################

    root.withdraw()

    ###################################################
    # Check/install required components
    ###################################################

    ytdlp = install_components()

    ###################################################
    # User declined or installation failed
    ###################################################

    if ytdlp is None:

        root.destroy()

        return

    ###################################################
    # Show converter
    ###################################################

    root.deiconify()

    app = YouTubeToMP3(
        root,
        ytdlp
    )

    root.mainloop()


###################################################
# START
###################################################

if __name__ == "__main__":

    main()
