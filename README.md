<div align="center">

```text
███╗   ███╗██████╗ ██████╗ ███████╗██╗    ██╗██╗███████╗██████╗ ████████╗
████╗ ████║██╔══██╗╚════██╗██╔════╝██║    ██║██║██╔════╝██╔══██╗╚══██╔══╝
██╔████╔██║██████╔╝ █████╔╝███████╗██║ █╗ ██║██║█████╗  ██████╔╝   ██║
██║╚██╔╝██║██╔═══╝  ╚═══██╗╚════██║██║███╗██║██║██╔══╝  ██╔══██╗   ██║
██║ ╚═╝ ██║██║     ██████╔╝███████║╚███╔███╔╝██║███████╗██║  ██║   ██║
╚═╝     ╚═╝╚═╝     ╚═════╝ ╚══════╝ ╚══╝╚══╝ ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝
```

### `A fast, modern YouTube → MP3 downloader for Windows.`

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Project Structure](#project-structure)

</div>

---

## `> OVERVIEW`

**Mp3Swift** is a Windows music downloader designed around speed, simplicity, and batch processing.

Search for a song, download it as an MP3, or process an entire collection at once.

```text
INPUT
  │
  ├── Artist - Song
  ├── Artist - Song
  └── Artist - Song
        │
        ▼
   ┌─────────────┐
   │  Mp3Swift   │
   └──────┬──────┘
          │
          ▼
      SEARCH / MATCH
          │
          ▼
       DOWNLOAD
          │
          ▼
      MP3 OUTPUT
```

Mp3Swift supports **songs available on YouTube** and can process **multiple songs in a single batch**.

---

## `> FEATURES`

```text
[01]  YouTube song search
[02]  Automatic song matching
[03]  MP3 audio downloads
[04]  Batch processing
[05]  Live activity / progress
[06]  Automatic audio conversion
[07]  Windows-focused workflow
```

### Batch Processing

Instead of downloading songs individually:

```text
Artist - Song One
Artist - Song Two
Artist - Song Three
Artist - Song Four
Artist - Song Five
```

Mp3Swift processes the entire list automatically.

---

## `> INSTALLATION`

### Requirements

```text
OS          Windows 10 / 11
Python      3.10+
FFmpeg      Required for audio conversion
```

### 01 — Clone

```bash
git clone https://github.com/PingDealer/Mp3Swift.git
cd Mp3Swift
```

### 02 — Install dependencies

```bash
pip install -r requirements.txt
```

### 03 — Launch

```bash
python app.py
```

---

## `> USAGE`

Create a list of songs using:

```text
Artist - Song Title
Artist - Another Song
Artist - Another Track
```

Then start Mp3Swift and begin the download process.

The application handles searching, matching, downloading, and conversion automatically.

---

## `> PROJECT STRUCTURE`

```text
Mp3Swift/
│
├── app.py
├── batch_processor.py
├── downloader.py
├── youtube_search.py
├── song_parser.py
├── ffmpeg_setup.py
│
├── requirements.txt
├── README.md
│
└── ffmpeg/
```

### Core Components

```text
app.py
    └── Application interface and control flow

youtube_search.py
    └── Song discovery and matching

batch_processor.py
    └── Multi-song processing pipeline

downloader.py
    └── Audio download / conversion

song_parser.py
    └── Artist / title parsing

ffmpeg_setup.py
    └── FFmpeg configuration
```

---

## `> WORKFLOW`

```text
┌──────────┐
│   INPUT  │
└────┬─────┘
     │
     ▼
┌──────────┐
│  PARSER  │
└────┬─────┘
     │
     ▼
┌──────────┐
│  SEARCH  │
└────┬─────┘
     │
     ▼
┌──────────┐
│  MATCH   │
└────┬─────┘
     │
     ▼
┌──────────┐
│ DOWNLOAD │
└────┬─────┘
     │
     ▼
┌──────────┐
│   MP3    │
└──────────┘
```

---

## `> DEVELOPMENT`

Clone the repository:

```bash
git clone https://github.com/PingDealer/Mp3Swift.git
cd Mp3Swift
```

Install the development dependencies:

```bash
pip install -r requirements.txt
```

Run locally:

```bash
python app.py
```

---

## `> NOTES`

Mp3Swift is intended for downloading content that you have permission to download.

Please respect copyright laws and the terms of service of the platforms you use.

---

<div align="center">

```text
────────────────────────────────────────────────────────────

                 MP3SWIFT // WINDOWS
              FAST • SIMPLE • BATCH

────────────────────────────────────────────────────────────
```

**Built for fast, frictionless music downloads.**

</div>
