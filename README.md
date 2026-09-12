<div align="center">

```text
                                       
 _____ _____ ___ _____       _ ___ _   
|     |  _  |_  |   __|_ _ _|_|  _| |_ 
| | | |   __|_  |__   | | | | |  _|  _|
|_|_|_|__|  |___|_____|_____|_|_| |_|  
                                       
                                                                                                           
```
[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Workflow](#workflow) • [Development](#development) • [Notes](#notes)
### `A fast, modern YouTube → MP3 downloader for Windows.`



</div>

---

## OVERVIEW

**Mp3Swift** is a Windows music downloader designed around speed, simplicity, and batch processing.

## FEATURES

```text
[01]  YouTube song search
[02]  Automatic song matching
[03]  MP3 audio downloads
[04]  Batch processing
[05]  Live activity / progress
```



## INSTALLATION

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

## USAGE

Create a txt list of songs, like:

```text
Song - Artist
Song2-Artist
Song3 - Artist
tip: add the songs u like to spo0tify playlist and use playlist to txt tools
```

Then start Mp3Swift and choose the txt file and click search once it finds a matching video for each of it click download and wait.

The application handles searching, matching, downloading, and conversion automatically.

---



## WORKFLOW

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

## DEVELOPMENT

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

## NOTES

Mp3Swift is intended for downloading content that you have permission to download.

Please respect copyright laws and the terms of service of the platforms you use.

---

<div align="center">

```text
────────────────────────────────────────────────────────────

                 MP3SWIFT // WINDOWS
                Made by PingDealer -PDOSP

────────────────────────────────────────────────────────────
```

</div>
