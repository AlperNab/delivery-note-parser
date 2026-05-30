#!/usr/bin/env python3
"""
delivery-note-parser — delivery note photo or PDF → structured receipt
Matches received vs ordered quantities, flags discrepancies, damaged goods,
short shipments, generates goods received note (GRN)
"""
import anthropic, base64, json, re, sys
from datetime import datetime, timezone
from pathlib import Path

SYSTEM = """You are a warehouse manager and logistics specialist.
Parse this delivery note and identify every discrepancy between what was ordered and received.

Return ONLY valid JSON — no markdown, no explanation.

{
  "document_type": "delivery_note|packing_list|goods_received_note|waybill|combined",
  "delivery_info": {
    "delivery_note_number": "string or null",
    "delivery_date": "YYYY-MM-DD or null",
    "po_reference": "string or null",
    "supplier": "string or null",
    "carrier": "string or null",
    "vehicle_ref": "string or null",
    "delivery_address": "string or null",
    "received_by": "string or null"
  },
  "line_items": [
    {
      "line_number": number,
      "sku": "string or null",
      "description": "product description",
      "ordered_qty": number_or_null,
      "delivered_qty": number,
      "unit": "units|kg|boxes|pallets|liters|...",
      "unit_price": number_or_null,
      "currency": "string or null",
      "batch_number": "string or null",
      "expiry_date": "YYYY-MM-DD or null",
      "condition": "good|damaged|suspect|missing",
      "discrepancy": true_or_false,
      "discrepancy_type": "short_delivery|over_delivery|damaged|wrong_item|substitution|null",
      "discrepancy_qty": number_or_null,
      "notes": "string or null"
    }
  ],
  "summary": {
    "total_lines": number,
    "lines_with_discrepancies": number,
    "total_ordered_units": number_or_null,
    "total_delivered_units": number,
    "short_delivery_lines": number,
    "damaged_lines": number,
    "over_delivery_lines": number
  },
  "grn_status": "fully_received|partially_received|rejected|pending_inspection",
  "action_required": [
    {
      "action": "description",
      "priority": "urgent|normal|low",
      "responsible": "warehouse|procurement|supplier|finance"
    }
  ],
  "financial_impact": {
    "value_ordered": number_or_null,
    "value_received": number_or_null,
    "discrepancy_value": number_or_null,
    "currency": "string or null"
  },
  "grn_draft": {
    "grn_number": "GRN-{date}-001",
    "ready_to_issue": true_or_false,
    "blocking_issues": ["list"]
  },
  "confidence": 0.0
}"""

def parse(source: str) -> dict:
    client = anthropic.Anthropic()
    path = Path(source)
    if path.exists():
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
            content = [
                {"type":"document","source":{"type":"base64","media_type":"application/pdf","data":data}},
                {"type":"text","text":"Parse this delivery note and identify all discrepancies."}
            ]
        elif suffix in (".jpg",".jpeg",".png",".webp"):
            mt = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","webp":"image/webp"}[suffix.lstrip(".")]
            data = base64.standard_b64encode(path.read_bytes()).decode("ascii")
            content = [
                {"type":"image","source":{"type":"base64","media_type":mt,"data":data}},
                {"type":"text","text":"Parse this delivery note and identify all discrepancies."}
            ]
        else:
            text = path.read_text(encoding="utf-8",errors="replace")[:30000]
            content = [{"type":"text","text":f"Parse this delivery note:\n\n{text}"}]
    else:
        content = [{"type":"text","text":f"Parse this delivery note:\n\n{source[:30000]}"}]

    resp = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=3000, system=SYSTEM,
        messages=[{"role":"user","content":content}]
    )
    raw = re.sub(r'^```(?:json)?\s*','',resp.content[0].text.strip(),flags=re.MULTILINE)
    raw = re.sub(r'\s*```$','',raw,flags=re.MULTILINE)
    return json.loads(raw)

COND_ICON = {"good":"✅","damaged":"🔴","suspect":"🟠","missing":"⬛"}
DISC_ICON = {"short_delivery":"📉","over_delivery":"📈","damaged":"💥","wrong_item":"❌","substitution":"🔄"}
STATUS_ICON = {"fully_received":"✅","partially_received":"⚠️","rejected":"🚫","pending_inspection":"🔍"}

def print_report(r: dict):
    info = r.get("delivery_info",{})
    summary = r.get("summary",{})
    fin = r.get("financial_impact",{})
    grn = r.get("grn_draft",{})
    status = r.get("grn_status","pending_inspection")

    print(f"\n{'═'*60}")
    print(f"  DELIVERY NOTE PARSER")
    print(f"  {STATUS_ICON.get(status,'')} {status.upper().replace('_',' ')}")
    print(f"{'═'*60}")

    if info.get("delivery_note_number"): print(f"\n  DN#: {info['delivery_note_number']}")
    if info.get("delivery_date"): print(f"  Date: {info['delivery_date']}")
    if info.get("po_reference"): print(f"  PO: {info['po_reference']}")
    if info.get("supplier"): print(f"  Supplier: {info['supplier']}")

    disc = summary.get("lines_with_discrepancies",0)
    total = summary.get("total_lines",0)
    print(f"\n  Lines: {total} | Discrepancies: {disc}")
    if summary.get("short_delivery_lines"): print(f"  Short: {summary['short_delivery_lines']} lines")
    if summary.get("damaged_lines"): print(f"  Damaged: {summary['damaged_lines']} lines")

    items = r.get("line_items",[])
    print(f"\n  LINE ITEMS")
    for item in items:
        cond = item.get("condition","good")
        icon = COND_ICON.get(cond,"•")
        disc_flag = ""
        if item.get("discrepancy"):
            dt = item.get("discrepancy_type","")
            dq = item.get("discrepancy_qty",0)
            disc_flag = f" ⚠ {DISC_ICON.get(dt,'')} {dt.replace('_',' ')} ({dq:+.0f})" if dq else f" ⚠ {dt.replace('_','')}"
        print(f"\n  {icon} {item.get('description','?')}")
        ordered = item.get("ordered_qty")
        delivered = item.get("delivered_qty",0)
        if ordered: print(f"     Ordered: {ordered} | Received: {delivered} {item.get('unit','')}{disc_flag}")
        else: print(f"     Received: {delivered} {item.get('unit','')}{disc_flag}")
        if item.get("batch_number"): print(f"     Batch: {item['batch_number']}", end="")
        if item.get("expiry_date"): print(f" | Expiry: {item['expiry_date']}", end="")
        if item.get("batch_number") or item.get("expiry_date"): print()
        if item.get("notes"): print(f"     Note: {item['notes']}")

    if fin.get("discrepancy_value"):
        print(f"\n  Financial impact: {fin.get('currency','')}{abs(fin.get('discrepancy_value',0)):,.2f}")

    actions = r.get("action_required",[])
    if actions:
        print(f"\n  ACTIONS REQUIRED")
        for a in actions:
            pri_icon = {"urgent":"🚨","normal":"📋","low":"📝"}.get(a.get("priority","normal"),"•")
            print(f"  {pri_icon} [{a.get('responsible','?').upper()}] {a.get('action','')}")

    print(f"\n  GRN Ready: {'✅' if grn.get('ready_to_issue') else '❌'}")
    for bl in grn.get("blocking_issues",[]): print(f"  ! {bl}")
    print(f"  Confidence: {int(r.get('confidence',0)*100)}%")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    if len(sys.argv)<2: print("Usage: python -m delivery_note_parser <note.pdf|.jpg|.txt> [--json]"); sys.exit(0)
    src = sys.argv[1]
    r = parse(src if src!="-" else sys.stdin.read())
    if "--json" in sys.argv: print(json.dumps(r,indent=2,ensure_ascii=False))
    else: print_report(r)
