"""
Professional PDF Letterhead Generator
Creates consistent letterhead for all PDF documents system-wide
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image, PageBreak, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus.doctemplate import BaseDocTemplate
import os
from pathlib import Path
from datetime import datetime

# Company Configuration
COMPANY_INFO = {
    'name': 'Smith & Williams Trucking',
    'address': '7600 N 15th St Suite 150',
    'city_state_zip': 'Phoenix, AZ 85020',
    'phone': '(951) 437-5474',
    'email': 'dispatch@smithwilliamstrucking.com',
    'website': 'www.smithwilliamstrucking.com',
    'dot': 'DOT# 3456789',
    'mc': 'MC# 1234567',
    'ein': 'EIN: 88-1234567',
    'tagline': 'Your cargo. Our mission. Moving forward.'
}

# Brand Colors
COLORS = {
    'primary': colors.HexColor('#1E3A8A'),  # Dark blue
    'secondary': colors.HexColor('#3B82F6'),  # Light blue
    'accent': colors.HexColor('#EF4444'),  # Red
    'dark': colors.HexColor('#1F2937'),  # Dark gray
    'light': colors.HexColor('#F3F4F6'),  # Light gray
    'white': colors.white,
    'black': colors.black
}

class ProfessionalLetterhead:
    """Professional letterhead generator for all PDFs"""
    
    def __init__(self, logo_path=None):
        self.logo_path = logo_path or 'assets/logo.png'
        self.styles = self._create_styles()
        
    def _create_styles(self):
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Company name style
        styles.add(ParagraphStyle(
            name='CompanyName',
            parent=styles['Title'],
            fontSize=24,
            textColor=COLORS['primary'],
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Tagline style
        styles.add(ParagraphStyle(
            name='Tagline',
            parent=styles['Normal'],
            fontSize=12,
            textColor=COLORS['secondary'],
            alignment=TA_CENTER,
            spaceAfter=12,
            fontName='Helvetica-Oblique'
        ))
        
        # Contact info style
        styles.add(ParagraphStyle(
            name='ContactInfo',
            parent=styles['Normal'],
            fontSize=10,
            textColor=COLORS['dark'],
            alignment=TA_CENTER,
            spaceAfter=3
        ))
        
        # Footer style
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=COLORS['dark'],
            alignment=TA_CENTER
        ))
        
        # Document title style
        styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=COLORS['primary'],
            alignment=TA_CENTER,
            spaceAfter=18,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        return styles
    
    def create_header(self, include_logo=True):
        """Create professional letterhead header"""
        elements = []
        
        # Logo and company name section
        if include_logo and os.path.exists(self.logo_path):
            # Create table with logo and company info
            logo = Image(self.logo_path, width=1.5*inch, height=0.6*inch)
            
            company_info = [
                Paragraph(COMPANY_INFO['name'], self.styles['CompanyName']),
                Paragraph(f"<i>{COMPANY_INFO['tagline']}</i>", self.styles['Tagline'])
            ]
            
            # Create table for logo and company name side by side
            header_data = [[logo, company_info]]
            header_table = Table(header_data, colWidths=[2*inch, 4.5*inch])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(header_table)
        else:
            # No logo, just company name and tagline
            elements.append(Paragraph(COMPANY_INFO['name'], self.styles['CompanyName']))
            elements.append(Paragraph(f"<i>{COMPANY_INFO['tagline']}</i>", self.styles['Tagline']))
        
        # Contact information line
        contact_line = f"{COMPANY_INFO['address']} • {COMPANY_INFO['city_state_zip']} • {COMPANY_INFO['phone']}"
        elements.append(Paragraph(contact_line, self.styles['ContactInfo']))
        
        # Email and website line
        digital_line = f"{COMPANY_INFO['email']} • {COMPANY_INFO['website']}"
        elements.append(Paragraph(digital_line, self.styles['ContactInfo']))
        
        # DOT, MC, EIN line
        compliance_line = f"{COMPANY_INFO['dot']} • {COMPANY_INFO['mc']} • {COMPANY_INFO['ein']}"
        elements.append(Paragraph(compliance_line, self.styles['ContactInfo']))
        
        # Add decorative line
        elements.append(Spacer(1, 0.1*inch))
        line_data = [['']]
        line_table = Table(line_data, colWidths=[6.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, COLORS['primary']),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def create_footer(self):
        """Create professional footer"""
        elements = []
        
        # Add decorative line
        line_data = [['']]
        line_table = Table(line_data, colWidths=[6.5*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 1, COLORS['light']),
        ]))
        elements.append(line_table)
        
        # Footer text
        footer_text = f"© {datetime.now().year} {COMPANY_INFO['name']}. All rights reserved."
        elements.append(Paragraph(footer_text, self.styles['Footer']))
        
        # Confidentiality notice
        confidential = "This document contains confidential information and is intended solely for the addressee."
        elements.append(Paragraph(confidential, self.styles['Footer']))
        
        return elements
    
    def add_watermark(self, canvas_obj, doc):
        """Add subtle watermark to page"""
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 60)
        canvas_obj.setFillColor(colors.lightgrey, alpha=0.1)
        canvas_obj.rotate(45)
        canvas_obj.drawString(2*inch, 1*inch, COMPANY_INFO['name'])
        canvas_obj.restoreState()

class ProfessionalPDFDocument(BaseDocTemplate):
    """Custom PDF document class with letterhead on every page"""
    
    def __init__(self, filename, **kwargs):
        self.letterhead = ProfessionalLetterhead()
        BaseDocTemplate.__init__(self, filename, **kwargs)
        self.addPageTemplates([self._create_page_template()])
        
    def _create_page_template(self):
        """Create page template with header and footer"""
        from reportlab.platypus.frames import Frame
        from reportlab.platypus.doctemplate import PageTemplate
        
        def header_footer(canvas_obj, doc):
            """Draw header and footer on each page"""
            canvas_obj.saveState()
            
            # Header
            header_elements = self.letterhead.create_header()
            header_frame = Frame(
                0.75*inch, 9.5*inch, 6.5*inch, 1.5*inch,
                leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0
            )
            header_frame.addFromList(header_elements, canvas_obj)
            
            # Footer
            footer_elements = self.letterhead.create_footer()
            footer_frame = Frame(
                0.75*inch, 0.5*inch, 6.5*inch, 0.75*inch,
                leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0
            )
            footer_frame.addFromList(footer_elements, canvas_obj)
            
            # Page number
            canvas_obj.setFont('Helvetica', 9)
            canvas_obj.setFillColor(COLORS['dark'])
            canvas_obj.drawRightString(
                7.5*inch, 0.5*inch,
                f"Page {doc.page}"
            )
            
            canvas_obj.restoreState()
        
        # Main content frame
        content_frame = Frame(
            0.75*inch, 1.25*inch, 6.5*inch, 8*inch,
            leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0
        )
        
        return PageTemplate(
            id='letterhead',
            frames=[content_frame],
            onPage=header_footer
        )

def generate_sample_pdf():
    """Generate a sample PDF with letterhead"""
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    import io
    
    buffer = io.BytesIO()
    letterhead = ProfessionalLetterhead()
    
    # Create document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Build content
    story = []
    
    # Add header
    story.extend(letterhead.create_header())
    
    # Add document title
    story.append(Paragraph("SAMPLE DOCUMENT", letterhead.styles['DocumentTitle']))
    
    # Add sample content
    sample_text = """
    This is a sample document demonstrating the professional letterhead template 
    for Smith & Williams Trucking. All PDF documents generated by the system will 
    include this consistent, professional header and footer.
    
    The letterhead includes:
    • Company logo (when available)
    • Company name and tagline
    • Complete contact information
    • Regulatory compliance numbers (DOT, MC, EIN)
    • Professional formatting and brand colors
    """
    
    story.append(Paragraph(sample_text, letterhead.styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Add more content to show pagination
    story.append(Paragraph("Additional Information", letterhead.styles['Heading2']))
    story.append(Paragraph("This section demonstrates how content flows with the letterhead design.", 
                          letterhead.styles['Normal']))
    
    # Add footer
    story.extend(letterhead.create_footer())
    
    # Build PDF
    doc.build(story)
    
    return buffer.getvalue()

# Ensure assets directory exists
def ensure_assets_directory():
    """Create assets directory if it doesn't exist"""
    assets_dir = Path('assets')
    assets_dir.mkdir(exist_ok=True)
    
    # Create placeholder for logo if it doesn't exist
    logo_file = assets_dir / 'logo.png'
    if not logo_file.exists():
        placeholder_file = assets_dir / 'logo_placeholder.txt'
        placeholder_file.write_text(
            "Please add your company logo as 'logo.png' in this directory.\n"
            "Recommended specifications:\n"
            "- Size: 300x120 pixels\n"
            "- Format: PNG with transparent background\n"
            "- Resolution: 300 DPI for print quality"
        )

if __name__ == "__main__":
    ensure_assets_directory()
    print("PDF Letterhead system configured!")
    print(f"Company: {COMPANY_INFO['name']}")
    print(f"Address: {COMPANY_INFO['address']}, {COMPANY_INFO['city_state_zip']}")
    print(f"Phone: {COMPANY_INFO['phone']}")
    
    # Generate sample PDF
    sample_pdf = generate_sample_pdf()
    with open("sample_letterhead.pdf", "wb") as f:
        f.write(sample_pdf)
    print("\nSample PDF with letterhead generated: sample_letterhead.pdf")