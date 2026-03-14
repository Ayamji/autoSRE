from typing import Dict
from fpdf import FPDF
import io

def generate_json_report(incident: Dict) -> Dict:
    return {
        "incident_id": incident.get("id"),
        "type": incident.get("type"),
        "severity": incident.get("severity"),
        "root_cause": incident.get("root_cause"),
        "time_detected": incident.get("timestamp"),
        "action_taken": incident.get("action_taken", "None"),
        "recovery_time": "TBD",  # In a real system, you'd calculate start - end
        "status": incident.get("status")
    }

def generate_pdf_report(incident: Dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)
    
    pdf.cell(200, 10, txt="AutoSRE Incident Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Incident ID: {incident.get('id')}", ln=True)
    pdf.cell(200, 10, txt=f"Type: {incident.get('type')}", ln=True)
    pdf.cell(200, 10, txt=f"Severity: {incident.get('severity')}", ln=True)
    pdf.cell(200, 10, txt=f"Time Detected: {incident.get('timestamp')}", ln=True)
    pdf.cell(200, 10, txt=f"Status: {incident.get('status')}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(200, 10, txt="Root Cause Analysis:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=incident.get('root_cause', 'N/A'))
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(200, 10, txt="Suggested Action / Remediation:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=incident.get('action_taken') or incident.get('suggested_action', 'N/A'))

    # Return as bytes
    # pdf.output returns a string if name is provided, but since we want bytes,
    # in fpdf2 .output(dest='S').encode('latin-1') works, or bytes output
    return pdf.output(dest='S').encode('latin-1')

