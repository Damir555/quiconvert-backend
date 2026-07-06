# QuiConvert Roadmap

## Vision

QuiConvert is a modern PDF processing platform focused on speed, simplicity and high-quality document tools.

The goal is to provide users with an intuitive interface for organizing, converting, securing and enhancing PDF documents while building a scalable backend architecture for future AI-powered features.

---

## Backend Status

### PDF Organization

- [x] Merge PDF
- [x] Split PDF
- [x] Compress PDF
- [x] Rotate PDF
- [x] Rearrange Pages
- [x] Delete Pages
- [x] Duplicate Pages
- [x] Reverse Pages

### Graphics

- [x] Text Watermark
- [x] Page Numbers
- [ ] Image Watermark
- [ ] Header
- [ ] Footer

### Security

- [x] Protect PDF
- [x] Unlock PDF
- [ ] Digital Signature

### Conversion

- [x] Image to PDF
- [ ] PDF to Image
- [ ] Word to PDF
- [ ] PDF to Word

### AI

- [ ] OCR
- [ ] PDF Summarization
- [ ] Translation
- [ ] Extract Tables

---

## Current Sprint

### Backend Stabilization v1

- [ ] Standardize download filenames
- [ ] Improve input validation
- [ ] Improve error handling
- [ ] Prepare modular backend structure
- [ ] Document current API endpoints

---

## Future Architecture

```text
services/
├── page_engine.py
├── graphics_engine.py
├── security_engine.py
├── conversion_engine.py
└── ai_engine.py
