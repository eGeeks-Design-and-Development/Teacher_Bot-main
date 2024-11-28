from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, HRFlowable, Flowable, KeepTogether
)
from reportlab.lib.units import inch, mm
# Update this line to include TA_RIGHT
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import markdown
import io
from datetime import datetime

class SectionHeader(Flowable):
    """Custom flowable for section headers with background and border"""
    def __init__(self, text, width=500, height=40):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.height = height

    def draw(self):
        # Draw background
        self.canv.setFillColor(colors.HexColor('#F5F8FA'))
        self.canv.setStrokeColor(colors.HexColor('#2D5F8B'))
        self.canv.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=1)
        
        # Draw text
        self.canv.setFillColor(colors.HexColor('#2D5F8B'))
        self.canv.setFont('Helvetica-Bold', 16)
        self.canv.drawString(10, self.height/3, self.text)

class ScoreBox(Flowable):
    """Custom flowable for displaying scores"""
    def __init__(self, score, width=100, height=40):
        Flowable.__init__(self)
        self.score = score
        self.width = width
        self.height = height

    def draw(self):
        # Draw background
        self.canv.setFillColor(colors.HexColor('#2D5F8B'))
        self.canv.setStrokeColor(colors.HexColor('#1B3C59'))
        self.canv.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=1)
        
        # Draw score
        self.canv.setFillColor(colors.white)
        self.canv.setFont('Helvetica-Bold', 14)
        text = f"Score: {self.score}/10"
        text_width = self.canv.stringWidth(text, 'Helvetica-Bold', 14)
        x = (self.width - text_width) / 2
        self.canv.drawString(x, self.height/3, text)

def create_document_styles():
    """Create enhanced document styles"""
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=28,
        spaceAfter=30,
        textColor=colors.HexColor('#1B3C59'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Section styles
    section_style = ParagraphStyle(
        'CustomSection',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=15,
        textColor=colors.HexColor('#2D5F8B'),
        borderPadding=10,
        fontName='Helvetica-Bold'
    )
    
    # Warning style for issues
    warning_style = ParagraphStyle(
        'Warning',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#D32F2F'),
        backColor=colors.HexColor('#FFEBEE'),
        borderPadding=8,
        alignment=TA_JUSTIFY
    )
    
    # Success style for positive points
    success_style = ParagraphStyle(
        'Success',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#1B5E20'),
        backColor=colors.HexColor('#E8F5E9'),
        borderPadding=8,
        alignment=TA_JUSTIFY
    )
    
    # Normal body style
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#333333'),
        alignment=TA_JUSTIFY,
        firstLineIndent=20
    )
    
    # Score style
    score_style = ParagraphStyle(
        'Score',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.white,
        backColor=colors.HexColor('#2D5F8B'),
        borderPadding=10,
        alignment=TA_CENTER
    )
    
    return {
        'title': title_style,
        'section': section_style,
        'warning': warning_style,
        'success': success_style,
        'body': body_style,
        'score': score_style
    }

def create_header_footer(canvas, doc):
    """Enhanced header and footer"""
    canvas.saveState()
    
    # Header with gradient background
    canvas.setFillColorRGB(0.11, 0.24, 0.35)  # Dark blue
    canvas.rect(0, A4[1] - 50, A4[0], 50, fill=1)
    
    # Header text
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 12)
    canvas.drawString(30, A4[1] - 30, "Academic QA Report")
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(
        A4[0] - 30, 
        A4[1] - 30, 
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}"
    )
    
    # Footer with line
    canvas.setStrokeColor(colors.HexColor('#2D5F8B'))
    canvas.setLineWidth(2)
    canvas.line(30, 50, A4[0] - 30, 50)
    
    canvas.setFillColor(colors.HexColor('#2D5F8B'))
    canvas.setFont('Helvetica', 9)
    canvas.drawString(30, 35, "Academic QA Assistant")
    canvas.drawRightString(A4[0] - 30, 35, f"Page {doc.page}")
    
    canvas.restoreState()

def format_content_section(content, styles):
    """Format content sections with appropriate styling"""
    elements = []
    
    # Extract score if present
    score = None
    if 'Score:' in content:
        score_text = content.split('Score:')[1].split('/')[0].strip()
        try:
            score = float(score_text)
            content = content.split('Score:')[0].strip()
        except ValueError:
            pass

    # Split content into sections
    sections = content.split('\n\n')
    
    for section in sections:
        # Remove extra whitespace
        section = section.strip()
        
        if not section:
            continue
            
        # Apply appropriate style based on content
        if any(keyword in section.lower() for keyword in [
            'non-compliance', 'weaknesses', 'issues', 'errors', 
            'lacking', 'missing', 'incorrect'
        ]):
            elements.append(Paragraph(section, styles['warning']))
        elif any(keyword in section.lower() for keyword in [
            'compliance', 'strengths', 'alignment', 'effective',
            'good', 'clear', 'well-structured'
        ]):
            elements.append(Paragraph(section, styles['success']))
        else:
            elements.append(Paragraph(section, styles['body']))
        
        elements.append(Spacer(1, 8))
    
    # Add score if present
    if score is not None:
        elements.append(Spacer(1, 10))
        elements.append(ScoreBox(score))
        elements.append(Spacer(1, 20))
    
    return elements

def create_toc(reports_dict):
    """Create enhanced table of contents"""
    elements = []
    
    # Add TOC header
    elements.append(SectionHeader("Table of Contents"))
    elements.append(Spacer(1, 20))
    
    # Create TOC entries
    toc_data = []
    for i, (title, _) in enumerate(reports_dict.items(), 1):
        toc_data.append([
            Paragraph(f"{i}.", ParagraphStyle(
                'TOCNumber',
                fontSize=12,
                textColor=colors.HexColor('#2D5F8B')
            )),
            Paragraph(title, ParagraphStyle(
                'TOCText',
                fontSize=12,
                textColor=colors.HexColor('#333333')
            )),
            Paragraph(f"Page {i+1}", ParagraphStyle(
                'TOCPage',
                fontSize=12,
                alignment=TA_RIGHT
            ))
        ])
    
    # Create TOC table
    toc = Table(
        toc_data,
        colWidths=[30, 400, 70],
        style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2D5F8B')),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#EEEEEE')),
        ])
    )
    elements.append(toc)
    return elements

def generate_individual_pdf_report(report_title, report_content):
    """Generate enhanced individual PDF report"""
    pdf_bytes = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_bytes,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=60,
        bottomMargin=60
    )
    
    styles = create_document_styles()
    elements = []
    
    # Add title section
    elements.append(Paragraph(report_title, styles['title']))
    elements.append(HRFlowable(
        width="90%",
        thickness=2,
        color=colors.HexColor('#2D5F8B'),
        spaceBefore=10,
        spaceAfter=20
    ))
    
    # Process content
    content_elements = format_content_section(report_content, styles)
    elements.extend(content_elements)
    
    # Build PDF
    doc.build(elements, onFirstPage=create_header_footer, onLaterPages=create_header_footer)
    pdf_bytes.seek(0)
    return pdf_bytes.getvalue()

def generate_compiled_pdf_report(assignment_name, reports_dict):
    """Generate enhanced compiled PDF report"""
    pdf_bytes = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_bytes,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=60,
        bottomMargin=60
    )
    
    styles = create_document_styles()
    elements = []
    
    # Cover page
    elements.append(Paragraph("Academic Quality Assessment", styles['title']))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(f"Assignment: {assignment_name}", styles['section']))
    elements.append(Spacer(1, 50))
    
    # Add table of contents
    elements.extend(create_toc(reports_dict))
    elements.append(PageBreak())
    
    # Add each section
    for report_title, report_content in reports_dict.items():
        # Section header
        elements.append(SectionHeader(report_title))
        elements.append(Spacer(1, 20))
        
        # Process content
        content_elements = format_content_section(report_content, styles)
        elements.extend(content_elements)
        
        # Add section separator
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor('#EEEEEE'),
            spaceBefore=20,
            spaceAfter=20
        ))
        elements.append(PageBreak())
    
    # Build PDF
    doc.build(elements, onFirstPage=create_header_footer, onLaterPages=create_header_footer)
    pdf_bytes.seek(0)
    return pdf_bytes.getvalue()