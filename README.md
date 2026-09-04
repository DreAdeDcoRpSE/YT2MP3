# YouTube to MP3 Converter

A simple Windows application that allows you to paste a YouTube video URL and convert the video's audio to an MP3 file.

## What You Need

Before you can run the converter, you need:

* Windows 10 or Windows 11
* Python 3 installed
* An active Internet connection

You **do not** need to manually install FFmpeg or yt-dlp. The converter will download the components it needs when you first run it.

---

# Step 1 - Install Python

If you already have Python 3 installed, you can skip this step.

Go to the official Python website:

https://www.python.org/downloads/windows/

Download the latest **Python 3** release for Windows.

When the Python installer opens, **IMPORTANT:**

At the bottom of the installer, make sure you check:

**☑ Add python.exe to PATH**

Then click:

**Install Now**

Wait for the installation to finish.

---

# Step 2 - Download the Converter

Go to the GitHub page for this project.

Download the project by clicking:

**Code → Download ZIP**

Save the ZIP file somewhere convenient, such as your Desktop or Downloads folder.

---

# Step 3 - Extract the ZIP File

Windows will download the project as a ZIP file.

Right-click the downloaded ZIP file and select:

**Extract All...**

Choose where you want to keep the converter.

For example:

```text
Desktop
```

Then click:

**Extract**

You should now have a folder containing the converter's Python file.

---

# Step 4 - Run the Converter

Open the extracted folder.

Find:

```text
YouTube_to_MP3_Converter.py
```

Double-click the file.

The converter will start.

---

# Step 5 - First-Time Setup

The first time you run the converter, it will check for the components it needs.

If they are not already present, you will see a message telling you what needs to be downloaded.

For example:

```text
This program needs the following components
to be able to convert YouTube videos to MP3:

  • yt-dlp
  • FFmpeg / FFprobe

These components will be downloaded to the
program's own folder.

Nothing will be installed system-wide.

Would you like to proceed?
```

Select **Yes** if you want to use the converter.

The required components will then be downloaded automatically.

You only need to approve this the first time.

---

# Step 6 - Convert a YouTube Video

Once the converter opens, you will see:

**YouTube to MP3 Converter**

Copy the URL of the YouTube video you want to convert.

Paste the URL into the box.

Click:

**Convert**

The program will retrieve the video information and then ask you where you would like to save the MP3.

Choose the folder and filename you want.

Click:

**Save**

The converter will download the audio and convert it to an MP3 file.

When it is finished, you will receive a confirmation message showing where the MP3 was saved.

The YouTube URL will then be cleared automatically so you can convert another video.

---

# Removing the Components

The converter includes a:

**Remove Installed Components**

button.

If you are finished using the converter and want to remove the components that it downloaded, click this button.

You will be asked to confirm the removal.

Your downloaded MP3 files will **NOT** be deleted.

Only the components used by the converter will be removed.

If you use the converter again after removing the components, you will need to allow the program to download them again.

---

# Where Are the Components Stored?

The converter keeps its required components inside its own folder.

A folder named:

```text
components
```

will be created next to the Python script.

The program does not require you to manually add FFmpeg to your Windows PATH.

---

# Troubleshooting

## The Python file won't open

Make sure Python 3 is installed.

You can test this by opening Command Prompt and entering:

```text
python --version
```

You should see something similar to:

```text
Python 3.x.x
```

If Windows says that Python is not recognized, reinstall Python and make sure:

**Add python.exe to PATH**

is checked during installation.

---

## The converter says it cannot install yt-dlp

Make sure you have an active Internet connection.

The converter needs Internet access to download yt-dlp.

Also make sure Python's `pip` component is available.

You can test it in Command Prompt with:

```text
python -m pip --version
```

---

## The converter says FFmpeg could not be downloaded

Make sure you have an active Internet connection.

FFmpeg is downloaded automatically by the converter, so you do not normally need to install it yourself.

---

# Important

This program is intended for downloading and converting content that you have permission to download.

Please respect YouTube's Terms of Service and the copyright of the content you download.

---

# Quick Start

If Python is already installed:

1. Download the project from GitHub.
2. Extract the ZIP file.
3. Open the extracted folder.
4. Double-click `YouTube_to_MP3_Converter.py`.
5. Approve the required component installation.
6. Paste a YouTube URL.
7. Click **Convert**.
8. Choose where to save the MP3.
9. Enjoy!
