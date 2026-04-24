# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python web scraper that archives Tilda-based invitation websites into fully self-contained static HTML pages with local assets. The scraper downloads all CSS, JS, images, and fonts, rewrites URLs to point to local copies, and removes anti-bot scripts.

## Setup and Running

```bash
# Activate virtual environment (Python 3.13)
source venv/bin/activate

# Install dependencies (no requirements.txt — install manually)
pip install requests beautifulsoup4

# Run the scraper
python scraper.py
```

The target URL is hardcoded in `scraper.py` as the `URL` constant. Change it before running to scrape a different page.

## How It Works

`scraper.py` is a single-file script with this pipeline:

1. Wipes and recreates `assets/` subdirectories (`css/`, `js/`, `img/`, `fonts/`)
2. Fetches the target Tilda page using a mobile User-Agent
3. Downloads and processes CSS files — rewrites `url()` references inside CSS to point to locally downloaded fonts/images
4. Downloads JS files, images (`<img>`, `<source>`, `data-original` attributes), and inline `style` background URLs
5. Strips Tilda's anti-bot script (the one using `sessionStorage` / `visits`)
6. Writes the final self-contained page to `index.html`

Key detail: `clean_tilda_url()` strips Tilda CDN resize parameters (`/-/resize/NNx/`) so images are always fetched at original resolution. Filenames are made unique via MD5 hash suffix of the source URL.

## File Layout

- `scraper.py` — the scraper script (single entry point)
- `index.html` — generated output (do not edit manually; regenerated on each run)
- `assets/` — downloaded assets (wiped on each run)
- `scratch_gallery.html` — debug page for visually inspecting downloaded images
- `venv/` — Python virtual environment (not committed)
