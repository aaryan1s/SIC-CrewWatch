import os
import io
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from config import REPORTS_DIR, ensure_directories
from logger import logger

def generate_automated_recommendations(compliance_data):
    """
    Generates intelligent, context-aware safety recommendations based on missing PPE items.
    Uses pure ASCII text for ReportLab PDF compatibility.
    """
    workers = compliance_data.get('workers', [])
    recommendations = []
    
    missing_helmets = any(not w['detected_items'].get('helmet', False) for w in workers)
    missing_vests = any(not w['detected_items'].get('vest', False) for w in workers)
    missing_gloves = any(not w['detected_items'].get('glove', False) for w in workers)
    missing_boots = any(not w['detected_items'].get('boots', False) for w in workers)
    
    if missing_helmets:
        recommendations.append("<b>Head Protection (Hardhats):</b> Mandatory hardhat enforcement must be implemented immediately at site access checkpoints. Restrict unequipped workers from entering overhead hazard zones.")
    if missing_vests:
        recommendations.append("<b>High-Visibility Vests:</b> All personnel operating in heavy machinery or vehicular traffic areas must wear class-2 high-vis safety vests to ensure visual conspicuity.")
    if missing_gloves:
        recommendations.append("<b>Hand Protection (Gloves):</b> Issue heavy-duty cut-resistant safety gloves for material handling and tool operation to prevent laceration risks.")
    if missing_boots:
        recommendations.append("<b>Footwear (Steel-Toe Boots):</b> Require certified steel-toe safety footwear with non-slip soles across all active construction zones.")

    if not recommendations:
        recommendations.append("<b>Site Compliance Target Met:</b> Excellent safety adherence! Maintain daily safety toolboxes and routine PPE spot audits to preserve compliance.")

    recommendations.append("<b>General Directive:</b> Conduct mandatory pre-shift safety briefings and maintain automated real-time AI surveillance logging.")
    return recommendations

def generate_fallback_pdf_report(title="CrewWatch Safety Inspection Report", error_msg=None):
    """
    Generates a minimal, fault-tolerant ReportLab PDF if primary PDF generation encounters an unexpected error.
    """
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('FbTitle', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#0F172A'))
        body_style = ParagraphStyle('FbBody', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#334155'), leading=14)
        
        elements = [
            Paragraph(title, title_style),
            Spacer(1, 10),
            Paragraph(f"<b>Inspection Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style),
            Spacer(1, 10),
            Paragraph("<b>System Notice:</b> Safety inspection report generated in minimal compatibility mode.", body_style)
        ]
        if error_msg:
            elements.append(Paragraph(f"<b>Note:</b> {error_msg}", body_style))
            
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
    except Exception as e:
        logger.exception("Fallback PDF generation failed:")
        return b"%PDF-1.4 Minimal Fallback Report"

def generate_pdf_report(
    compliance_data,
    alerts_list=None,
    image_path=None,
    original_image_path=None,
    title="CrewWatch Safety Inspection Report",
    inspection_type="Static Image Audit"
):
    """
    Generates a commercial-grade ReportLab PDF Safety Inspection Report.
    Fully fault tolerant with 100% ASCII font compatibility and exception recovery.
    Returns raw PDF bytes suitable for direct download or file saving.
    """
    try:
        logger.info(f"Generating PDF safety report (Type: '{inspection_type}')")
        
        if alerts_list is None:
            alerts_list = []
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom Corporate Typography & Colors (Helvetica Standard ReportLab Fonts)
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            textColor=colors.HexColor('#0F172A'),
            spaceAfter=4
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=colors.HexColor('#475569'),
            spaceAfter=12
        )
        
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=colors.HexColor('#1E293B'),
            spaceBefore=10,
            spaceAfter=6
        )
        
        body_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            textColor=colors.HexColor('#334155'),
            leading=11
        )

        rec_style = ParagraphStyle(
            'RecTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            textColor=colors.HexColor('#1E293B'),
            leading=12
        )

        elements = []

        # 1. Header Title & Branding Header
        elements.append(Paragraph(title, title_style))
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(
            f"<b>Inspection Date:</b> {now_str} &nbsp;|&nbsp; "
            f"<b>Mode:</b> {inspection_type} &nbsp;|&nbsp; "
            f"<b>Engine:</b> YOLOv8 Industrial AI Guard",
            subtitle_style
        ))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=10))

        # 2. Executive Summary Scorecard
        elements.append(Paragraph("Executive Summary & Site Scorecard", heading_style))
        
        workers = compliance_data.get('total_workers', 0)
        compliant = compliance_data.get('compliant_workers', 0)
        score = compliance_data.get('overall_safety_score', 100.0)
        
        score_hex = '#16A34A' if score >= 85 else ('#D97706' if score >= 60 else '#DC2626')
        
        summary_table_data = [
            [
                Paragraph("<b>Total Personnel</b>", body_style),
                Paragraph("<b>Compliant Workers</b>", body_style),
                Paragraph("<b>Non-Compliant Workers</b>", body_style),
                Paragraph("<b>Overall Safety Index</b>", body_style)
            ],
            [
                Paragraph(f"<font size=11><b>{workers}</b></font>", body_style),
                Paragraph(f"<font size=11 color='#16A34A'><b>{compliant}</b></font>", body_style),
                Paragraph(f"<font size=11 color='#DC2626'><b>{workers - compliant}</b></font>", body_style),
                Paragraph(f"<font size=12 color='{score_hex}'><b>{score:.1f}%</b></font>", body_style)
            ]
        ]
        
        summary_table = Table(summary_table_data, colWidths=[130, 130, 130, 150])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#F8FAFC')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 10))

        # 3. PPE Item Breakdown Table (Plain ASCII without emojis)
        elements.append(Paragraph("PPE Item Compliance Breakdown", heading_style))
        
        item_table_data = [
            [Paragraph("<b>PPE Category</b>", body_style), Paragraph("<b>Compliance Rate (%)</b>", body_style), Paragraph("<b>Status Assessment</b>", body_style)],
            [Paragraph("Helmet / Hardhat", body_style), f"{compliance_data.get('helmet_compliance_pct', 0):.1f}%", "Pass" if compliance_data.get('helmet_compliance_pct', 0) >= 85 else "Action Required"],
            [Paragraph("High-Vis Vest", body_style), f"{compliance_data.get('vest_compliance_pct', 0):.1f}%", "Pass" if compliance_data.get('vest_compliance_pct', 0) >= 85 else "Action Required"],
            [Paragraph("Protective Gloves", body_style), f"{compliance_data.get('glove_compliance_pct', 0):.1f}%", "Pass" if compliance_data.get('glove_compliance_pct', 0) >= 85 else "Action Required"],
            [Paragraph("Safety Boots", body_style), f"{compliance_data.get('boot_compliance_pct', 0):.1f}%", "Pass" if compliance_data.get('boot_compliance_pct', 0) >= 85 else "Action Required"]
        ]
        
        item_table = Table(item_table_data, colWidths=[180, 160, 200])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('PADDING', (0,0), (-1,-1), 5),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ]))
        elements.append(item_table)
        elements.append(Spacer(1, 10))

        # 4. Itemized Worker Violation Log (Plain ASCII)
        worker_list = compliance_data.get('workers', [])
        if worker_list:
            elements.append(Paragraph("Itemized Worker Compliance Log", heading_style))
            worker_rows = [[
                Paragraph("<b>Worker ID</b>", body_style),
                Paragraph("<b>Helmet</b>", body_style),
                Paragraph("<b>Vest</b>", body_style),
                Paragraph("<b>Gloves</b>", body_style),
                Paragraph("<b>Boots</b>", body_style),
                Paragraph("<b>Compliance Status & Violations</b>", body_style)
            ]]
            
            for w in worker_list:
                if w.get('is_fully_compliant', False):
                    status_p = Paragraph("<font color='#16A34A'><b>[COMPLIANT]</b></font>", body_style)
                else:
                    missing_str = ", ".join([m.capitalize() for m in w.get('missing_items', [])])
                    status_p = Paragraph(f"<font color='#DC2626'><b>[VIOLATION]</b> ({missing_str})</font>", body_style)

                worker_rows.append([
                    Paragraph(f"Worker #{w.get('worker_id', 1)}", body_style),
                    "Worn" if w.get('detected_items', {}).get('helmet') else "MISSING",
                    "Worn" if w.get('detected_items', {}).get('vest') else "MISSING",
                    "Worn" if w.get('detected_items', {}).get('glove') else "MISSING",
                    "Worn" if w.get('detected_items', {}).get('boots') else "MISSING",
                    status_p
                ])
                
            worker_table = Table(worker_rows, colWidths=[70, 75, 75, 75, 75, 170])
            worker_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
                ('PADDING', (0,0), (-1,-1), 4),
                ('ALIGN', (1,0), (4,-1), 'CENTER'),
            ]))
            elements.append(worker_table)
            elements.append(Spacer(1, 10))

        # 5. Dual Evidence Inspection Images (Original + Annotated) with Try/Except Safety
        evidence_imgs = []
        if original_image_path:
            try:
                orig_p = Path(original_image_path)
                if orig_p.exists():
                    evidence_imgs.append(RLImage(str(orig_p), width=250, height=140))
            except Exception as e:
                logger.warning(f"Could not load original image into PDF (skipping image): {e}")

        if image_path:
            try:
                ann_p = Path(image_path)
                if ann_p.exists():
                    evidence_imgs.append(RLImage(str(ann_p), width=250, height=140))
            except Exception as e:
                logger.warning(f"Could not load annotated image into PDF (skipping image): {e}")

        if evidence_imgs:
            elements.append(Paragraph("Inspection Evidence Snapshots", heading_style))
            if len(evidence_imgs) == 2:
                img_table_data = [[
                    Paragraph("<b>Raw Ingested Feed</b>", body_style),
                    Paragraph("<b>AI Bounding Overlay Output</b>", body_style)
                ], [evidence_imgs[0], evidence_imgs[1]]]
                img_table = Table(img_table_data, colWidths=[270, 270])
                img_table.setStyle(TableStyle([
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('PADDING', (0,0), (-1,-1), 2),
                ]))
                elements.append(img_table)
            else:
                elements.append(evidence_imgs[0])
            elements.append(Spacer(1, 10))

        # 6. Automated Safety Recommendations & Directives
        elements.append(Paragraph("Automated Safety Recommendations & Directives", heading_style))
        recs = generate_automated_recommendations(compliance_data)
        rec_table_data = []
        for r in recs:
            rec_table_data.append([Paragraph(f"- {r}", rec_style)])
            
        rec_table = Table(rec_table_data, colWidths=[540])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(rec_table)

        # 7. Document Footer
        elements.append(Spacer(1, 15))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=8))
        footer_style = ParagraphStyle(
            'DocFooter',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=colors.HexColor('#1E293B'),
            alignment=1
        )
        footer_sub_style = ParagraphStyle(
            'DocFooterSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=colors.HexColor('#64748B'),
            alignment=1
        )
        elements.append(Paragraph("Generated by CrewWatch", footer_style))
        elements.append(Paragraph("AI-Powered Workforce Safety Monitoring", footer_sub_style))

        # Build PDF Document cleanly
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        logger.info("✔ PDF safety report generated successfully.")
        return pdf_data

    except Exception as e:
        logger.exception("Exception encountered during primary PDF report generation:")
        return generate_fallback_pdf_report(title=title, error_msg=f"Primary PDF rendering bypassed: {str(e)}")

def save_pdf_report_to_disk(pdf_bytes, filename=None):
    """
    Saves generated PDF bytes to the reports/ directory safely using pathlib.Path.
    """
    try:
        ensure_directories()
        if not pdf_bytes:
            logger.warning("Empty PDF bytes passed to save_pdf_report_to_disk.")
            return None

        if filename is None:
            filename = f"ppe_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        file_path = REPORTS_DIR / Path(filename).name
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
            
        logger.info(f"Saved PDF report to disk: {file_path}")
        return str(file_path.resolve())
    except Exception as e:
        logger.exception("Failed to save PDF report to disk:")
        return None
