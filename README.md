# Delivery Note Parser

This folder has been upgraded into a **standalone real GUI project**.

Run the project GUI:

```bash
./run_gui.sh
```

Windows:

```powershell
.\run_gui_windows.ps1
```

Default local URL: `http://127.0.0.1:9116`

This project includes its own FastAPI backend, browser GUI, provider settings, local/cloud LLM routing, encrypted API-key storage, file uploads, job history, exports, and a project-specific plugin configuration.

See `PROJECT_IMPLEMENTATION.md` and `project_config.json` for the applied project-specific features and customization controls.

---

## Original README

# delivery-note-parser

> **Delivery note photo or PDF → structured goods received note.** Matches received vs ordered quantities, flags short shipments and damaged goods, auto-generates GRN draft.

[![PyPI](https://img.shields.io/pypi/v/delivery-note-parser?style=flat)](https://pypi.org/project/delivery-note-parser/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Quickstart

```bash
pip install delivery-note-parser
python -m delivery_note_parser delivery_note.pdf
python -m delivery_note_parser delivery_photo.jpg --json
```

Accepts: PDF, JPEG, PNG (photos), plain text. Handles multi-page documents.
