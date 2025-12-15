# PDF N-in-1 Imposer & Merger

A tiny Python CLI tool that  
1. converts every **N** pages of each PDF into **1** imposed A4 sheet (3 × 5 by default, no margins, portrait),  
2. outputs one lightweight PDF per source file, and  
3. automatically merges those outputs into ≈ 20 MB chunks.

## Features
- Fully customizable grid (cols × rows)  
- 300 dpi rasterisation → crisp print quality  
- Skip already-processed files (idempotent)  
- Cross-platform (Windows / macOS / Linux)

## Requirements
```bash
pip install -r requirements.txt
```
`requirements.txt`  
```
PyMuPDF>=1.23
Pillow>=10.0
```

## Quick Start
1. Put your PDFs into the `./pdf` folder.  
2. Tune constants in the script head if needed:
   ```python
   COLS  = 4          # columns
   ROWS  = 5          # rows
   DPI   = 300        # resolution
   TARGET_MB = 20     # max size per merged file
   ```
3. Run:
   ```bash
   python pdf_n_in1.py
   ```
4. Results:
   - `./20in1_out/` – one imposed PDF per source  
   - `./merged/` – final volumes (`merged_part000.pdf`, …)

