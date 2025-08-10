from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from typing import Dict, Any, List
import io

def render_pdf(reading: Dict[str,Any]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    margin = 0.75 * inch
    x = margin
    y = height - margin

    def wrap(text: str, width_chars: int) -> List[str]:
        words = text.split()
        lines, cur = [], ""
        for w in words:
            if len(cur)+len(w)+1 > width_chars:
                lines.append(cur); cur = w
            else:
                cur = w if not cur else cur + " " + w
        if cur: lines.append(cur)
        return lines

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, f"{reading.get('meta',{}).get('name','Your')} Skyprint")
    y -= 0.35*inch

    c.setFont("Helvetica", 11)
    c.drawString(x, y, "Signature: " + ", ".join(reading.get("signature", [])))
    y -= 0.25*inch

    for sec in reading.get("sections", []):
        if y < margin + 1*inch: c.showPage(); y = height - margin
        c.setFont("Helvetica-Bold", 13); c.drawString(x, y, sec.get("title","")); y -= 0.22*inch
        c.setFont("Helvetica", 11)
        for line in wrap(sec.get("short",""), 95):
            if y < margin + 0.75*inch: c.showPage(); y = height - margin
            c.drawString(x, y, line); y -= 0.18*inch
        for line in wrap(sec.get("long",""), 95):
            if y < margin + 0.75*inch: c.showPage(); y = height - margin
            c.drawString(x, y, line); y -= 0.18*inch
        acts = sec.get("actions", [])
        if acts:
            if y < margin + 0.9*inch: c.showPage(); y = height - margin
            c.setFont("Helvetica-Oblique", 11); c.drawString(x, y, "Try this:"); y -= 0.18*inch
            c.setFont("Helvetica", 11)
            for a in acts:
                for line in wrap("• " + a, 92):
                    if y < margin + 0.75*inch: c.showPage(); y = height - margin
                    c.drawString(x, y, line); y -= 0.18*inch
        y -= 0.12*inch
    c.save()
    return buf.getvalue()
