import os

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, send_file, session, url_for

from llm_service import generate_business_analysis
from pdf_generator import build_pdf

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    business_type = request.form.get("business_type", "").strip()
    if not business_type:
        return redirect(url_for("index"))

    analysis = generate_business_analysis(business_type)

    # Cache so the PDF download can reuse this without a second LLM call
    session["business_type"] = business_type
    session["analysis"] = analysis

    return render_template(
        "analysis.html",
        business_type=business_type,
        data=analysis,
        licenses=[
            {"name": "Udyam Registration", "time": "1-2 Days", "cost": "Free",
             "link": "https://udyamregistration.gov.in/"},
            {"name": "GST Registration", "time": "7-10 Days", "cost": "Free",
             "link": "https://www.gst.gov.in/"},
            {"name": "FSSAI License", "time": "15-30 Days", "cost": "Rs 100 - Rs 7500",
             "link": "https://foscos.fssai.gov.in/"},
            {"name": "Shop & Establishment Act", "time": "5-7 Days", "cost": "Varies by State",
             "link": "#"},
            {"name": "Professional Tax", "time": "3-5 Days", "cost": "Varies", "link": "#"},
        ],
        schemes=[
            {"name": "PMEGP", "benefit": "Up to 35% subsidy on project cost",
             "link": "https://www.kviconline.gov.in/pmegpeportal/"},
            {"name": "CLCSS", "benefit": "15% capital subsidy for tech upgrade",
             "link": "https://dashboard.msme.gov.in/"},
            {"name": "Credit Guarantee Fund", "benefit": "Collateral-free loans up to Rs 2 Cr",
             "link": "https://www.cgtmse.in/"},
        ],
    )


@app.route("/download-pdf")
def download_pdf():
    business_type = request.args.get("business_type") or session.get("business_type")
    if not business_type:
        return redirect(url_for("index"))

    analysis = session.get("analysis")
    if not analysis or session.get("business_type") != business_type:
        analysis = generate_business_analysis(business_type)

    pdf_buffer = build_pdf(business_type, analysis)
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in business_type.lower()) or "report"

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"EaseBiz_AI_Roadmap_{safe_name}.pdf",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
