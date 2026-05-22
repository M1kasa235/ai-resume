#!/usr/bin/env python3
"""Generate PDF versions of key knowledge base test data files."""

import os
import sys

# Try importing fpdf2, install if missing
try:
    from fpdf import FPDF
except ImportError:
    print("Installing fpdf2...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
    from fpdf import FPDF


class KnowledgePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, self.title, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def txt_to_pdf(txt_path, pdf_path, title):
    """Convert a text file to a styled PDF."""
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    pdf = KnowledgePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.title = title
    pdf.add_page()

    # Split content into lines and render
    lines = content.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            pdf.ln(4)
            continue

        # Detect headings - lines that are short and end with no punctuation
        # or start with Chinese numbers or 数字.
        is_heading = False
        if len(stripped) < 60 and (
            stripped.startswith(("一", "二", "三", "四", "五", "六", "七", "八", "九", "十"))
            or stripped[0].isdigit()
            or stripped.startswith(("核心", "常", "策", "技", "行", "面", "ST", "IC", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."))
        ):
            is_heading = True

        if is_heading:
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 30, 120)
            pdf.multi_cell(0, 7, stripped)
            pdf.set_text_color(40, 40, 40)
            pdf.ln(2)
        else:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(0, 5.5, stripped)

    pdf.output(pdf_path)
    return os.path.getsize(pdf_path)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Select key files across all three doc_types
    files_to_convert = [
        # interview type (files with "interview" in name)
        ("interview_behavioral_guide.txt", "interview_behavioral_guide.pdf", "行为面试实战指南"),
        ("interview_technical_guide.txt", "interview_technical_guide.pdf", "技术面试通关全攻略"),
        ("interview_case_guide.txt", "interview_case_guide.pdf", "案例面试完全指南"),

        # resume_guide type (files with "resume" in name)
        ("resume_guide.txt", "resume_guide.pdf", "简历优化完全指南"),
        ("resume_english_guide.txt", "resume_english_guide.pdf", "英文简历写作完全指南"),
        ("resume_ATS优化.txt", "resume_ATS优化.pdf", "ATS简历优化指南"),

        # job type (other files)
        ("career_strategy.txt", "career_strategy.pdf", "职业发展战略指南"),
        ("salary_negotiation.txt", "salary_negotiation.pdf", "薪资谈判实战指南"),
        ("industry_internet_tech_career.txt", "industry_internet_tech_career.pdf", "互联网与科技行业职业发展全景指南"),
        ("overseas_career_guide.txt", "overseas_career_guide.pdf", "出海求职与跨国职业发展指南"),
    ]

    success_count = 0
    for txt_name, pdf_name, title in files_to_convert:
        txt_path = os.path.join(base_dir, txt_name)
        pdf_path = os.path.join(base_dir, pdf_name)

        if not os.path.exists(txt_path):
            print(f"SKIP: {txt_name} not found")
            continue

        try:
            size = txt_to_pdf(txt_path, pdf_path, title)
            size_kb = size / 1024
            print(f"OK: {pdf_name} ({size_kb:.1f} KB) - {title}")
            success_count += 1
        except Exception as e:
            print(f"FAIL: {pdf_name} - {e}")

    print(f"\nDone. {success_count}/{len(files_to_convert)} PDFs generated in {base_dir}")


if __name__ == "__main__":
    main()