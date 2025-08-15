"""
PDF Generation Module for Smith & Williams Trucking
Generates professional invoices, receipts, and reports with letterhead
"""

import os
from datetime import datetime, date
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.platypus import KeepTogether, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.legends import Legend
import sqlite3
import pandas as pd
from io import BytesIO

class PDFGenerator:
    def __init__(self):
        self.company_name = "Smith & Williams Trucking LLC"
        self.company_address = "4496 Meadow Cliff Dr\nMemphis, TN 38125"
        self.company_phone = "(901) 218-4083"
        self.company_email = "dispatch@swtrucking.com"
        # Use transparent logo (swt_logo.png) for PDFs
        self.logo_path = "swt_logo.png" if os.path.exists("swt_logo.png") else None
        self.db_path = "trailer_moves.db"
        
    def _add_letterhead(self, canvas, doc):
        """Add company letterhead to each page"""
        canvas.saveState()
        
        # Add logo if exists
        if self.logo_path and os.path.exists(self.logo_path):
            canvas.drawImage(self.logo_path, 50, 750, width=60, height=60, preserveAspectRatio=True)
        
        # Company name and info
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(130, 780, self.company_name)
        canvas.setFont("Helvetica", 10)
        canvas.drawString(130, 765, self.company_address.split('\n')[0])
        canvas.drawString(130, 750, self.company_address.split('\n')[1])
        canvas.drawString(130, 735, f"Phone: {self.company_phone} | Email: {self.company_email}")
        
        # Add line separator
        canvas.setStrokeColor(colors.HexColor("#28a745"))
        canvas.setLineWidth(2)
        canvas.line(50, 720, 550, 720)
        
        # Footer
        canvas.setFont("Helvetica", 8)
        canvas.drawString(50, 30, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        canvas.drawRightString(550, 30, f"Page {doc.page}")
        
        canvas.restoreState()
        
    def generate_driver_receipt(self, driver_name, date_from, date_to):
        """Generate driver payment receipt with actual final pay per load"""
        filename = f"driver_receipt_{driver_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=100, bottomMargin=50)
        
        # Container for the 'Flowable' objects
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#28a745'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("DRIVER PAYMENT RECEIPT", title_style))
        elements.append(Spacer(1, 20))
        
        # Driver Information
        info_style = styles['Normal']
        elements.append(Paragraph(f"<b>Driver:</b> {driver_name}", info_style))
        elements.append(Paragraph(f"<b>Period:</b> {date_from} to {date_to}", info_style))
        elements.append(Spacer(1, 20))
        
        # Get driver's moves from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.system_id, m.move_date, 
                   orig.location_title || ' -> ' || dest.location_title as route,
                   m.estimated_miles, m.estimated_earnings, m.payment_status,
                   m.mlbl_number
            FROM moves m
            LEFT JOIN locations orig ON m.origin_location_id = orig.id
            LEFT JOIN locations dest ON m.destination_location_id = dest.id
            WHERE m.driver_name = ? 
            AND m.move_date BETWEEN ? AND ?
            ORDER BY m.move_date DESC
        ''', (driver_name, date_from, date_to))
        
        moves = cursor.fetchall()
        conn.close()
        
        if moves:
            # Create table data
            data = [['System ID', 'Date', 'Route', 'Miles', 'Gross', 'After\nFactoring', 'Status']]
            
            total_gross = 0
            total_net = 0
            
            for move in moves:
                system_id, move_date, route, miles, gross, status, mlbl = move
                after_factoring = gross * 0.97 if gross else 0  # 3% factoring fee
                
                data.append([
                    system_id,
                    move_date,
                    route,
                    f"{miles:,.2f}",
                    f"${gross:,.2f}" if gross else "",
                    f"${after_factoring:,.2f}" if after_factoring else "",
                    status
                ])
                
                if status == 'paid':
                    total_gross += gross if gross else 0
                    total_net += after_factoring
            
            # Add totals row
            data.append(['', '', 'TOTALS:', '', f"${total_gross:,.2f}", f"${total_net:,.2f}", ''])
            
            # Create table
            table = Table(data, colWidths=[80, 70, 180, 60, 70, 70, 60])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 30))
            
            # Add payment breakdown
            elements.append(Paragraph("<b>Payment Breakdown:</b>", styles['Heading3']))
            breakdown_data = [
                ['Description', 'Amount'],
                ['Total Gross Earnings', f"${total_gross:,.2f}"],
                ['Factoring Fee (3%)', f"-${total_gross * 0.03:,.2f}"],
                ['Service Fee (Est.)', f"-$6.00"],
                ['', ''],
                ['NET PAYMENT', f"${total_net - 6:,.2f}"]
            ]
            
            breakdown_table = Table(breakdown_data, colWidths=[300, 150])
            breakdown_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(breakdown_table)
            
        # Build PDF
        doc.build(elements, onFirstPage=self._add_letterhead, onLaterPages=self._add_letterhead)
        return filename
        
    def generate_client_invoice(self, client_name, date_from, date_to):
        """Generate client invoice with professional formatting"""
        filename = f"client_invoice_{client_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=100, bottomMargin=50)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Invoice header
        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#28a745'),
            spaceAfter=10,
            alignment=TA_RIGHT
        )
        elements.append(Paragraph("INVOICE", title_style))
        
        # Invoice details
        invoice_num = f"INV-{datetime.now().strftime('%Y%m%d%H%M')}"
        elements.append(Paragraph(f"<b>Invoice #:</b> {invoice_num}", styles['Normal']))
        elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        elements.append(Paragraph(f"<b>Due Date:</b> Net 30", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Bill To section
        elements.append(Paragraph("<b>BILL TO:</b>", styles['Heading3']))
        elements.append(Paragraph(client_name, styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Get moves for client
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.system_id, m.move_date, m.mlbl_number,
                   orig.location_title || ' -> ' || dest.location_title as route,
                   m.estimated_miles, m.estimated_earnings, m.status
            FROM moves m
            LEFT JOIN locations orig ON m.origin_location_id = orig.id
            LEFT JOIN locations dest ON m.destination_location_id = dest.id
            WHERE m.client = ? 
            AND m.move_date BETWEEN ? AND ?
            AND m.status = 'completed'
            ORDER BY m.move_date DESC
        ''', (client_name, date_from, date_to))
        
        moves = cursor.fetchall()
        conn.close()
        
        if moves:
            # Create invoice line items
            data = [['Date', 'System ID', 'MLBL #', 'Route', 'Miles', 'Amount']]
            
            total_amount = 0
            
            for move in moves:
                system_id, move_date, mlbl, route, miles, amount, status = move
                data.append([
                    move_date,
                    system_id,
                    mlbl or 'Pending',
                    route,
                    f"{miles:,.2f}",
                    f"${amount:,.2f}" if amount else ""
                ])
                total_amount += amount if amount else 0
            
            # Add subtotal and total
            data.append(['', '', '', '', 'Subtotal:', f"${total_amount:,.2f}"])
            data.append(['', '', '', '', 'Tax (0%):', "$0.00"])
            data.append(['', '', '', '', 'TOTAL DUE:', f"${total_amount:,.2f}"])
            
            # Create table
            table = Table(data, colWidths=[70, 90, 80, 180, 60, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 1), (3, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('FONTNAME', (-2, -3), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (-2, -1), (-1, -1), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -4), 1, colors.black),
                ('BOX', (-2, -3), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 30))
            
            # Payment terms
            elements.append(Paragraph("<b>Payment Terms:</b>", styles['Heading3']))
            elements.append(Paragraph("• Payment due within 30 days", styles['Normal']))
            elements.append(Paragraph("• Please reference invoice number with payment", styles['Normal']))
            elements.append(Paragraph("• Wire transfer or check accepted", styles['Normal']))
            
        # Build PDF
        doc.build(elements, onFirstPage=self._add_letterhead, onLaterPages=self._add_letterhead)
        return filename
        
    def generate_status_report(self, date_from, date_to, include_charts=True):
        """Generate comprehensive status report with charts"""
        filename = f"status_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=100, bottomMargin=50)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Report Title
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#28a745'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        elements.append(Paragraph("OPERATIONS STATUS REPORT", title_style))
        elements.append(Paragraph(f"{date_from} to {date_to}", styles['BodyText']))
        elements.append(Spacer(1, 30))
        
        # Get data from database
        conn = sqlite3.connect(self.db_path)
        
        # Summary metrics
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status IN ('active', 'in_transit') THEN 1 END) as in_process,
                COUNT(CASE WHEN status = 'assigned' THEN 1 END) as assigned,
                SUM(CASE WHEN status = 'completed' AND payment_status = 'paid' THEN estimated_earnings ELSE 0 END) as revenue
            FROM moves
            WHERE move_date BETWEEN ? AND ?
        ''', (date_from, date_to))
        
        metrics = cursor.fetchone()
        completed, in_process, assigned, revenue = metrics
        
        # Executive Summary
        elements.append(Paragraph("<b>EXECUTIVE SUMMARY</b>", styles['Heading2']))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Completed Moves', str(completed)],
            ['In Process', str(in_process)],
            ['Assigned (Pending)', str(assigned)],
            ['Total Revenue', f"${revenue:,.2f}" if revenue else "$0.00"]
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 150])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 30))
        
        # Detailed moves by status
        elements.append(Paragraph("<b>COMPLETED MOVES</b>", styles['Heading3']))
        
        cursor.execute('''
            SELECT m.system_id, m.move_date, m.driver_name,
                   orig.location_title || ' -> ' || dest.location_title as route,
                   m.payment_status, m.estimated_earnings
            FROM moves m
            LEFT JOIN locations orig ON m.origin_location_id = orig.id
            LEFT JOIN locations dest ON m.destination_location_id = dest.id
            WHERE m.status = 'completed'
            AND m.move_date BETWEEN ? AND ?
            ORDER BY m.move_date DESC
        ''', (date_from, date_to))
        
        completed_moves = cursor.fetchall()
        
        if completed_moves:
            data = [['System ID', 'Date', 'Driver', 'Route', 'Payment', 'Amount']]
            for move in completed_moves:
                data.append(list(move[:-1]) + [f"${move[-1]:,.2f}" if move[-1] else ""])
            
            table = Table(data, colWidths=[80, 70, 100, 180, 70, 70])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
        
        elements.append(PageBreak())
        
        # In Process Moves
        elements.append(Paragraph("<b>IN PROCESS MOVES</b>", styles['Heading3']))
        
        cursor.execute('''
            SELECT m.system_id, m.move_date, m.driver_name,
                   orig.location_title || ' -> ' || dest.location_title as route,
                   t.trailer_number
            FROM moves m
            LEFT JOIN locations orig ON m.origin_location_id = orig.id
            LEFT JOIN locations dest ON m.destination_location_id = dest.id
            LEFT JOIN trailers t ON m.trailer_id = t.id
            WHERE m.status IN ('active', 'in_transit')
            AND m.move_date BETWEEN ? AND ?
            ORDER BY m.move_date DESC
        ''', (date_from, date_to))
        
        active_moves = cursor.fetchall()
        
        if active_moves:
            data = [['System ID', 'Date', 'Driver', 'Route', 'Trailer']]
            for move in active_moves:
                data.append(list(move))
            
            table = Table(data, colWidths=[80, 70, 100, 200, 80])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
        
        conn.close()
        
        # Build PDF
        doc.build(elements, onFirstPage=self._add_letterhead, onLaterPages=self._add_letterhead)
        return filename

# Make functions available for import
def generate_driver_receipt(driver_name, date_from, date_to):
    generator = PDFGenerator()
    return generator.generate_driver_receipt(driver_name, date_from, date_to)

def generate_client_invoice(client_name, date_from, date_to):
    generator = PDFGenerator()
    return generator.generate_client_invoice(client_name, date_from, date_to)

def generate_status_report(date_from, date_to):
    generator = PDFGenerator()
    return generator.generate_status_report(date_from, date_to)