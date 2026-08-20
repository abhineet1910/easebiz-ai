"""
Server-side re-implementation of the original pdfGenerator.ts (jsPDF) report,
using reportlab instead. Visual structure, colors, and sections match the original;
the narrative sections (market analysis, expert advice, competition) now pull from
the LLM-generated `data` dict instead of being hardcoded.

Note: unlike the original (which showed the same final page-count on every page's
footer due to how jsPDF's page loop worked), this version correctly shows
"Page X of Y" on every page.
"""

import io

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

LICENSES = [
    {"name": "Udyam MSME Registration", "time": "1-2 Days", "cost": "Free",
     "link": "https://udyamregistration.gov.in/"},
    {"name": "GSTIN Entity Registration", "time": "7-10 Days", "cost": "Free",
     "link": "https://www.gst.gov.in/"},
    {"name": "FSSAI Food Safety License", "time": "15-30 Days", "cost": "Rs 100 - Rs 7500",
     "link": "https://foscos.fssai.gov.in/"},
    {"name": "Shop & Establishments Filing", "time": "5-7 Days", "cost": "State Dependent",
     "link": "https://easebizai.com/"},
    {"name": "Import Export Code (IEC)", "time": "3-5 Days", "cost": "Rs 500 Fees",
     "link": "https://www.dgft.gov.in/"},
]

SCHEMES = [
    {"name": "PMEGP Funding Subsidy", "benefit": "Up to 35% subsidy on structural project cost outlays.",
     "link": "https://www.kviconline.gov.in/pmegpeportal/"},
    {"name": "CLCSS Tech Upgrade Initiative", "benefit": "15% direct financial subsidy on tech/infrastructure updates.",
     "link": "https://dashboard.msme.gov.in/"},
    {"name": "Credit Guarantee Fund Trust", "benefit": "Collateral-free credit accessibility of up to Rs 2 Crores.",
     "link": "https://www.cgtmse.in/"},
]

SLATE_900 = HexColor("#0f172a")
SLATE_700 = HexColor("#334155")
SLATE_600 = HexColor("#475569")
SLATE_500 = HexColor("#64748b")
SLATE_200 = HexColor("#e2e8f0")
SLATE_50 = HexColor("#f8fafc")
EMERALD_50 = HexColor("#f0fdf4")
EMERALD_200 = HexColor("#bbf7d0")
EMERALD_500 = HexColor("#22c55e")
EMERALD_700 = HexColor("#15803d")
EMERALD_800 = HexColor("#166534")
SKY_600 = HexColor("#0284c7")
WHITE = HexColor("#ffffff")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - MARGIN * 2


class FooterCanvas(canvas.Canvas):
    """Buffers every page so we can stamp an accurate 'Page X of Y' footer on all of
    them once the total page count is known (mirrors, and fixes, the original's
    end-of-generation header/footer redraw loop)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        # The last page drawn is still "open" (no explicit showPage() was called
        # for it) -- capture it too, or its content silently gets dropped.
        self._saved_page_states.append(dict(self.__dict__))
        total_pages = len(self._saved_page_states)
        for page_num, state in enumerate(self._saved_page_states, start=1):
            self.__dict__.update(state)
            self._draw_header_footer(page_num, total_pages)
            super().showPage()
        super().save()

    def _draw_header_footer(self, page_num, total_pages):
        self.setStrokeColor(SLATE_200)
        self.setLineWidth(0.5)
        self.line(MARGIN, PAGE_H - 12 * mm, PAGE_W - MARGIN, PAGE_H - 12 * mm)

        self.setFont("Helvetica", 8)
        self.setFillColor(SLATE_500)
        self.drawString(MARGIN, PAGE_H - 10 * mm, "EASEBIZ AI BUSINESS REPORT & ROADMAP")
        self.drawRightString(PAGE_W - MARGIN, 10 * mm, f"CONFIDENTIAL | Page {page_num} of {total_pages}")
        self.drawString(MARGIN, 10 * mm, "easebizai.com")


def _wrap(c, text, font, size, max_width):
    c.setFont(font, size)
    words = text.split()
    lines, current = [], ""
    for w in words:
        trial = f"{current} {w}".strip()
        if c.stringWidth(trial, font, size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [""]


def build_pdf(business_type: str, data: dict) -> io.BytesIO:
    buf = io.BytesIO()
    c = FooterCanvas(buf, pagesize=A4)

    y = [MARGIN]  # "distance from top" cursor, mutable via closure

    def Y(offset):
        return PAGE_H - offset

    def check_page_break(needed):
        if y[0] + needed > PAGE_H - MARGIN:
            c.showPage()
            y[0] = MARGIN

    def draw_wrapped(text, font, size, color, x, width, line_height=5 * mm):
        lines = _wrap(c, text, font, size, width)
        c.setFont(font, size)
        c.setFillColor(color)
        for line in lines:
            c.drawString(x, Y(y[0]), line)
            y[0] += line_height
        return len(lines)

    # --- COVER HEADER BLOCK ---
    c.setFillColor(SLATE_900)
    c.rect(MARGIN, Y(y[0] + 50 * mm), CONTENT_W, 50 * mm, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(EMERALD_500)
    c.drawString(MARGIN + 10 * mm, Y(y[0] + 15 * mm), "COMPREHENSIVE AI REPORT & ROADMAP")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(WHITE)
    title_lines = _wrap(c, business_type.upper(), "Helvetica-Bold", 22, CONTENT_W - 20 * mm)
    for i, line in enumerate(title_lines[:2]):
        c.drawString(MARGIN + 10 * mm, Y(y[0] + 27 * mm + i * 8 * mm), line)

    y[0] += 58 * mm

    # --- CONFIDENCE BADGE ---
    c.setFillColor(SLATE_50)
    c.setStrokeColor(SLATE_200)
    c.rect(MARGIN, Y(y[0] + 18 * mm), CONTENT_W, 18 * mm, fill=1, stroke=1)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(SLATE_900)
    c.drawString(MARGIN + 8 * mm, Y(y[0] + 11 * mm), "AI Engine Confidence Score: 96%")
    c.setFont("Helvetica", 10)
    c.setFillColor(SLATE_600)
    c.drawRightString(PAGE_W - MARGIN - 8 * mm, Y(y[0] + 11 * mm), "Generated by EaseBiz AI")

    y[0] += 28 * mm

    # --- SECTION 1: MARKET ANALYSIS ---
    check_page_break(50 * mm)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(SLATE_900)
    c.drawString(MARGIN, Y(y[0]), "1. Market Size & Sentiment Analysis")
    c.setStrokeColor(EMERALD_500)
    c.setLineWidth(1)
    c.line(MARGIN, Y(y[0] + 2 * mm), MARGIN + 30 * mm, Y(y[0] + 2 * mm))
    y[0] += 10 * mm

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(SLATE_900)
    c.drawString(MARGIN, Y(y[0]), "Market Potential & CAGR Range:")
    y[0] += 6 * mm
    draw_wrapped(data["market_size"], "Helvetica", 10, SLATE_700, MARGIN, CONTENT_W)
    y[0] += 6 * mm

    check_page_break(40 * mm)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(SLATE_900)
    c.drawString(MARGIN, Y(y[0]), "Consumer Behaviors & Adoption Priorities:")
    y[0] += 6 * mm
    draw_wrapped(data["consumer_behavior"], "Helvetica", 10, SLATE_700, MARGIN, CONTENT_W)
    y[0] += 6 * mm

    check_page_break(30 * mm)
    c.setFillColor(EMERALD_50)
    c.setStrokeColor(EMERALD_200)
    c.rect(MARGIN, Y(y[0] + 22 * mm), CONTENT_W, 22 * mm, fill=1, stroke=1)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(EMERALD_700)
    c.drawString(MARGIN + 6 * mm, Y(y[0] + 8 * mm), "AI STRATEGIC INSIGHT FOR STARTUPS:")
    c.setFont("Helvetica", 9.5)
    c.setFillColor(EMERALD_800)
    insight_lines = _wrap(c, data["ai_insight"], "Helvetica", 9.5, CONTENT_W - 12 * mm)
    for i, line in enumerate(insight_lines[:2]):
        c.drawString(MARGIN + 6 * mm, Y(y[0] + 14 * mm + i * 4.5 * mm), line)
    y[0] += 32 * mm

    # --- SECTION 2: EXPERT STRATEGIES ---
    check_page_break(60 * mm)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(SLATE_900)
    c.drawString(MARGIN, Y(y[0]), "2. Multi-Disciplinary Expert Advice")
    c.setStrokeColor(EMERALD_500)
    c.line(MARGIN, Y(y[0] + 2 * mm), MARGIN + 30 * mm, Y(y[0] + 2 * mm))
    y[0] += 10 * mm

    c.setFont("Helvetica-Oblique", 9.5)
    c.setFillColor(SLATE_600)
    quote_lines = _wrap(c, f'"{data["expert_quote"]}"', "Helvetica-Oblique", 9.5, CONTENT_W)
    for line in quote_lines:
        c.drawString(MARGIN, Y(y[0]), line)
        y[0] += 5 * mm
    y[0] += 4 * mm

    advisories = [
        ("Financial Prudence", data["financial_advice"]),
        ("Operations & Tech Adoption", data["operational_advice"]),
        ("Defensible IP & Compliance Setup", data["legal_advice"]),
    ]
    for title, text in advisories:
        check_page_break(25 * mm)
        c.setFont("Helvetica-Bold", 10.5)
        c.setFillColor(SLATE_900)
        c.drawString(MARGIN, Y(y[0]), f"* {title}:")
        y[0] += 5 * mm
        draw_wrapped(text, "Helvetica", 10, SLATE_700, MARGIN + 4 * mm, CONTENT_W - 5 * mm)
        y[0] += 6 * mm

    y[0] += 4 * mm

    # --- SECTION 3: LICENSING ROADMAP ---
    check_page_break(80 * mm)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(SLATE_900)
    c.drawString(MARGIN, Y(y[0]), "3. Licensing & Compliance Roadmap")
    c.setStrokeColor(EMERALD_500)
    c.line(MARGIN, Y(y[0] + 2 * mm), MARGIN + 30 * mm, Y(y[0] + 2 * mm))
    y[0] += 10 * mm

    c.setFillColor(SLATE_900)
    c.rect(MARGIN, Y(y[0] + 8 * mm), CONTENT_W, 8 * mm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(WHITE)
    c.drawString(MARGIN + 3 * mm, Y(y[0] + 5.5 * mm), "Regulatory Clearance Required")
    c.drawString(MARGIN + 65 * mm, Y(y[0] + 5.5 * mm), "Timeline")
    c.drawString(MARGIN + 92 * mm, Y(y[0] + 5.5 * mm), "Govt Cost")
    c.drawString(MARGIN + 125 * mm, Y(y[0] + 5.5 * mm), "Action Portal Link")
    y[0] += 8 * mm

    for lic in LICENSES:
        check_page_break(12 * mm)
        c.setFillColor(SLATE_50)
        c.rect(MARGIN, Y(y[0] + 8 * mm), CONTENT_W, 8 * mm, fill=1, stroke=0)

        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(SLATE_900)
        c.drawString(MARGIN + 3 * mm, Y(y[0] + 5.5 * mm), lic["name"])

        c.setFont("Helvetica", 8.5)
        c.setFillColor(SLATE_700)
        c.drawString(MARGIN + 65 * mm, Y(y[0] + 5.5 * mm), lic["time"])
        c.drawString(MARGIN + 92 * mm, Y(y[0] + 5.5 * mm), lic["cost"])

        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(SKY_600)
        link_x, link_y = MARGIN + 125 * mm, Y(y[0] + 5.5 * mm)
        c.drawString(link_x, link_y, "Access Portal")
        c.linkURL(lic["link"], (link_x, link_y - 2, link_x + 28 * mm, link_y + 4 * mm), relative=0)

        y[0] += 8.5 * mm

    y[0] += 8 * mm

    # --- SECTION 4: GOVERNMENT SCHEMES ---
    check_page_break(65 * mm)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(SLATE_900)
    c.drawString(MARGIN, Y(y[0]), "4. Financial & Assistance Schemes")
    c.setStrokeColor(EMERALD_500)
    c.line(MARGIN, Y(y[0] + 2 * mm), MARGIN + 30 * mm, Y(y[0] + 2 * mm))
    y[0] += 10 * mm

    for sh in SCHEMES:
        check_page_break(25 * mm)
        c.setFont("Helvetica-Bold", 10.5)
        c.setFillColor(SLATE_900)
        c.drawString(MARGIN, Y(y[0]), sh["name"])
        y[0] += 5 * mm

        draw_wrapped(sh["benefit"], "Helvetica", 9.5, SLATE_700, MARGIN + 4 * mm, CONTENT_W - 10 * mm)
        y[0] += 1 * mm

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(SKY_600)
        link_x, link_y = MARGIN + 4 * mm, Y(y[0] + 4 * mm)
        c.drawString(link_x, link_y, "Apply / Verify Eligibility")
        c.linkURL(sh["link"], (link_x, link_y - 2, link_x + 42 * mm, link_y + 4 * mm), relative=0)
        y[0] += 9 * mm

    y[0] += 5 * mm

    # --- SECTION 5: COMPETITIVE LANDSCAPE ---
    check_page_break(60 * mm)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(SLATE_900)
    c.drawString(MARGIN, Y(y[0]), "5. Global & Indian Competitive Positioning")
    c.setStrokeColor(EMERALD_500)
    c.line(MARGIN, Y(y[0] + 2 * mm), MARGIN + 30 * mm, Y(y[0] + 2 * mm))
    y[0] += 10 * mm

    col_w = (CONTENT_W - 6 * mm) / 2
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(SLATE_900)
    c.drawString(MARGIN, Y(y[0]), "Domestic/Indian Market Moat")
    c.drawString(MARGIN + col_w + 6 * mm, Y(y[0]), "Global Ecosystem Standards")
    y[0] += 6 * mm

    local_lines = _wrap(c, data["local_competitors"], "Helvetica", 9.5, col_w)
    global_lines = _wrap(c, data["global_competitors"], "Helvetica", 9.5, col_w)
    max_lines = max(len(local_lines), len(global_lines))

    c.setFont("Helvetica", 9.5)
    c.setFillColor(SLATE_700)
    for i in range(max_lines):
        if i < len(local_lines):
            c.drawString(MARGIN, Y(y[0] + i * 4.5 * mm), local_lines[i])
        if i < len(global_lines):
            c.drawString(MARGIN + col_w + 6 * mm, Y(y[0] + i * 4.5 * mm), global_lines[i])

    y[0] += max_lines * 4.5 * mm + 10 * mm

    # --- FOOTER DISCLAIMER ---
    check_page_break(25 * mm)
    c.setStrokeColor(SLATE_200)
    c.setLineWidth(0.5)
    c.line(MARGIN, Y(y[0]), PAGE_W - MARGIN, Y(y[0]))
    y[0] += 6 * mm

    disclaimer = (
        "Legal Disclaimer: This AI-generated report is provided solely for educational and "
        "introductory roadmapping purposes. Consult with licensed legal and business "
        "professionals in India for final regulatory submissions and audits."
    )
    c.setFont("Helvetica-Oblique", 8.5)
    c.setFillColor(SLATE_500)
    draw_wrapped(disclaimer, "Helvetica-Oblique", 8.5, SLATE_500, MARGIN, CONTENT_W, line_height=4 * mm)

    c.save()
    buf.seek(0)
    return buf
