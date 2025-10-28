
# 📄 Office to PDF Converter

Convert Microsoft Office documents (Word, PowerPoint) to PDF using either:
- the native Office suite installed on your laptop (via docx2pdf), or
- a headless CLI engine (LibreOffice) that runs without opening any GUI.

## 🎯 Supported Formats

| Type | Extensions | Engine(s) |
|------|-----------|-----------|
| Word | `.docx`, `.doc` | Microsoft Word (docx2pdf) or LibreOffice (headless) |
| PowerPoint | `.pptx`, `.ppt` | Microsoft PowerPoint (docx2pdf) or LibreOffice (headless) |

## ⚙️ How it works

Default engine is `docx2pdf`, which launches the native Office application in the background:
- macOS: AppleScript to control Word/PowerPoint
- Windows: COM automation to control Word/PowerPoint

Headless/CLI mode uses `LibreOffice` (no window opens):
- Cross-platform, requires `soffice`/`libreoffice` available on PATH
- Use the environment variable `OFFICE_TO_PDF_ENGINE=libreoffice` to force headless mode

## 📦 Installation

Minimal:
```bash
pip install docx2pdf
```

Headless (no GUI windows):
- macOS: `brew install --cask libreoffice`
- Debian/Ubuntu: `sudo apt-get update && sudo apt-get install -y libreoffice`
- Windows: Install LibreOffice and ensure `soffice` is on PATH

Then set:
```bash
# macOS/Linux
export OFFICE_TO_PDF_ENGINE=libreoffice

# Windows (PowerShell)
$env:OFFICE_TO_PDF_ENGINE = "libreoffice"
```

## 📋 Operations

### 1. `convert` - Convert Office document to PDF

```json
{
  "tool": "office_to_pdf",
  "params": {
    "operation": "convert",
    "input_path": "docs/office/report.docx",
    "output_path": "docs/pdfs/report.pdf",
    "overwrite": false
  }
}
```

Response:
```json
{
  "success": true,
  "input_path": "docs/office/report.docx",
  "output_path": "docs/pdfs/report.pdf",
  "output_size_bytes": 524288,
  "output_size_kb": 512.0,
  "output_size_mb": 0.5,
  "duration_ms": 4235,
  "engine": "docx2pdf",
  "message": "Conversion successful"
}
```

Notes:
- If `overwrite` is false and the file exists, a suffix `_1`, `_2`, etc. is added automatically.
- To run without opening Office GUIs, install LibreOffice and set `OFFICE_TO_PDF_ENGINE=libreoffice`.

---

### 2. `get_info` - Get file metadata

```json
{
  "tool": "office_to_pdf",
  "params": {
    "operation": "get_info",
    "input_path": "docs/office/presentation.pptx"
  }
}
```

Response (enriched):
```json
{
  "success": true,
  "path": "docs/office/presentation.pptx",
  "name": "presentation.pptx",
  "size_bytes": 1048576,
  "size_mb": 1.0,
  "extension": ".pptx",
  "file_type": "PowerPoint presentation",
  "app_type": "Microsoft PowerPoint",
  "exists": true,
  "page_count": 12,
  "large_images_over_100px": 4,
  "metadata": {
    "title": "Q1 Update",
    "creator": "Alice",
    "company": "Acme Inc.",
    "slides": 12,
    "last_modified_by": "Bob",
    "modified_utc": "2025-10-27T16:45:23Z"
  }
}
```

How page_count is computed:
- PPTX: number of slides from the OOXML package (no conversion required).
- DOCX: prefers Pages from docProps/app.xml; if missing, tries a temporary PDF conversion and counts pages.
- DOC/PPT (legacy): tries OLE properties (if `olefile` installed); else best-effort via temporary PDF conversion.

Image counting (large_images_over_100px):
- DOCX/PPTX: counts embedded images in `word/media/` or `ppt/media/` with width and height >= 100 px (supports PNG/JPEG/GIF).
- DOC/PPT: not supported (returns null).

---

## 📁 Directory Structure

```
docs/
├── office/          # Input files (Word, PowerPoint)
│   ├── report.docx
│   ├── slides.pptx
└── pdfs/            # Output PDFs
    ├── report.pdf
    └── slides.pdf
```

## 🚀 Examples

Convert Word document (default engine):
```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "office_to_pdf",
    "params": {
      "operation": "convert",
      "input_path": "docs/office/monthly_report.docx"
    }
  }'
```

Headless conversion (no GUI windows):
```bash
export OFFICE_TO_PDF_ENGINE=libreoffice
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "office_to_pdf",
    "params": {
      "operation": "convert",
      "input_path": "docs/office/company_presentation.pptx",
      "output_path": "docs/pdfs/presentation_2025.pdf"
    }
  }'
```

Get file info:
```bash
curl -X POST http://127.0.0.1:8000/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "tool": "office_to_pdf",
    "params": {
      "operation": "get_info",
      "input_path": "docs/office/report.docx"
    }
  }'
```

## 🧰 Troubleshooting

- "docx2pdf library not installed": `pip install docx2pdf`
- "PDF file was not created":
  - Ensure Microsoft Office is installed (for docx2pdf) or install LibreOffice (headless)
  - Close Word/PowerPoint if already running; try again
  - Check the input file isn't corrupted
- "LibreOffice conversion failed": ensure `soffice`/`libreoffice` is on PATH
- "Permission error": verify write permissions to `docs/pdfs/`

## 🔐 Security

- Input chroot: files must be under `docs/office/`
- Output chroot: PDFs saved under `docs/pdfs/`
- No network access: conversion is 100% local

## ⚠️ Limitations

- Excel (`.xlsx`, `.xls`) not supported (separate implementation needed)
- docx2pdf requires Office installed (macOS/Windows)
- Conversion time depends on document complexity

