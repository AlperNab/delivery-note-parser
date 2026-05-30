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
