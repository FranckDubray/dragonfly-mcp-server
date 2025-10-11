# 📄 Office to PDF Converter

Convert Microsoft Office documents (Word, PowerPoint) to PDF using the **native Office suite installed on your laptop**.

## 🎯 Supported Formats

| Type | Extensions | App Used |
|------|-----------|----------|
| Word | `.docx`, `.doc` | Microsoft Word |
| PowerPoint | `.pptx`, `.ppt` | Microsoft PowerPoint |

## ⚙️ How it works

Uses **docx2pdf** library which launches the native Office application in the background:
- **macOS**: Uses AppleScript to control Word/PowerPoint
- **Windows**: Uses COM automation to control Word/PowerPoint

**Requires Microsoft Office installed on your laptop.**

## 📦 Installation

```bash
pip install docx2pdf
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

**Parameters:**
- `input_path` (required): Path to Office file (must be under `docs/office/`)
- `output_path` (optional): Path to output PDF (auto-generated if not provided)
- `overwrite` (optional): Overwrite existing file (default: false)

**Response:**
```json
{
  "success": true,
  "input_path": "docs/office/report.docx",
  "output_path": "docs/pdfs/report.pdf",
  "output_size_bytes": 524288,
  "output_size_kb": 512.0,
  "output_size_mb": 0.5,
  "message": "Conversion successful"
}
```

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

**Response:**
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
  "exists": true
}
```

---

## 📁 Directory Structure

```
docs/
├── office/          # Input files (Word, PowerPoint)
│   ├── report.docx
│   ├── budget.xlsx  # ⚠️ Not supported (use Excel separately)
│   └── slides.pptx
└── pdfs/            # Output PDFs
    ├── report.pdf
    └── slides.pdf
```

## 🚀 Examples

### Convert Word document
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

### Convert PowerPoint presentation
```bash
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

### Get file info
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

## 🔧 Troubleshooting

### Error: "docx2pdf library not installed"
```bash
pip install docx2pdf
```

### Error: "PDF file was not created"
- ✅ Check if Microsoft Office (Word/PowerPoint) is installed
- ✅ Try opening the file manually in Word/PowerPoint first
- ✅ Close Word/PowerPoint if already running
- ✅ Check file isn't corrupted

### Error: "Office application error"
- ⚠️ Close all Office applications and retry
- ⚠️ Check Office isn't running in protected mode
- ⚠️ Verify Office license is active

### Error: "Permission error"
- Check file isn't read-only
- Verify you have write permissions to `docs/pdfs/`

## ⚡ Performance

| Document Size | Conversion Time |
|---------------|-----------------|
| Small (< 1MB) | 2-5 seconds |
| Medium (1-5MB) | 5-15 seconds |
| Large (> 5MB) | 15-30 seconds |

*Conversion time depends on document complexity and Office performance*

## 🔒 Security

- **Chroot**: Input files must be under `docs/office/`
- **Output chroot**: PDFs saved under `docs/pdfs/`
- **No network access**: Conversion is 100% local
- **Native Office**: Uses your Office installation (trusted app)

## ⚠️ Limitations

- ❌ **Excel not supported** (`.xlsx`, `.xls`) - need separate implementation
- ❌ **Requires Office installed** - won't work without Word/PowerPoint
- ⚠️ **Synchronous** - blocks during conversion (can take 5-30s)
- ⚠️ **One file at a time** - no batch processing yet

## 🎯 Future Enhancements

- [ ] Batch conversion (multiple files at once)
- [ ] Excel support (`.xlsx` → PDF)
- [ ] Progress feedback (for large files)
- [ ] LibreOffice fallback (for Linux/systems without Office)
- [ ] Async conversion (non-blocking)
