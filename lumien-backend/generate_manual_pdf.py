from fpdf import FPDF

class ManualPDF(FPDF):
    def header(self):
        self.set_fill_color(12, 74, 110) # Slate 900
        self.rect(0, 0, 210, 30, 'F')
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, 'FIDUCIA | SSBD (CFCFRMS) User Manual', ln=True, align='L')
        self.set_font('Helvetica', 'I', 10)
        self.cell(0, 5, 'Bank HQ Integration & Case Handling Guidelines v1.1', ln=True, align='L')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Confidential Intellectual Property of FIDUCIA', 0, 0, 'C')

def create_pdf():
    pdf = ManualPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    sections = [
        ("1. Executive Summary", "The FIDUCIA Platform is a state-of-the-art intermediary intelligence system designed to sit between the I4C (Indian Cybercrime Coordination Centre) portal and dedicated Bank Nodal HQs. This manual provides the operational protocols for Bank HQ Integration Users to handle fraud intelligence signals, execute reactive holds, and maintain regulatory compliance within the 24-hour SLA window."),
        ("2. Authentication & Security", "Access to the FIDUCIA node is strictly controlled via Role-Based Access Control (RBAC).\n\n2.1 Nodal Credentials\nEach bank is assigned a unique nodal branch credential.\n- Access URL: http://localhost:3000\n- Session Duration: 24 hours (Stateful JWT)\n\n2.2 Data Isolation Policy\nBank users are in a siloed environment. You will only see intelligence signals identified as RELATED to your bank via your specific IFSC or VPA prefixes."),
        ("3. The Nodal Command Center", "Upon login, the Case Inbox acts as your primary triage center.\n\n3.1 Case Status Indicators\n- ROUTED: New intelligence signal received from FIDUCIA. Clock is active.\n- BANK_CONFIRMED: Nodal user has verified the account relationship.\n- HOLD_INITIATED: Temporary lean/freeze has been placed on the beneficiary account.\n- NOT_RELATED: Intelligence disputed. Case sent back for re-analysis."),
        ("4. Intelligence-Driven Case Analysis", "Every case in your inbox has been auto-enriched by the FIDUCIA Intelligence Engine.\n\n4.1 Routing Signals\n- IFSC Signal: The detected branch identifier (e.g., SBIN0001234).\n- Confidence Score: The certainty level (usually 100%) that the funds moved into your ecosystem.\n- Nodal Branch HQ: The identified target within your bank's infrastructure responsible for the action."),
        ("5. The Bank Action Playbook", "When you open a case, you are presented with the Bank Action Playbook.\n\nStep 1: Confirm Related\nVerify account in CBS. Click Confirm Related.\n\nStep 2: Initiate Hold/Freeze\nIf funds available, click Initiate Hold/Freeze. Enter remarks (e.g., Full amount Rs.12,000 Kept on lien).\n\nStep 3: Mark Not Related\nIf account invalid or wrong bank, click Mark Not Related with justification."),
        ("6. SLA Compliance & Deadlines", "Regulatory frameworks require bank responses within 24 hours of intelligence routing.\n\n- SLA Monitor: Visible via administrative node.\n- Breach Protocol: Cases exceeding 24h are flagged as BREACHED and reported in compliance analytics."),
        ("7. Audit & Evidence", "Every action taken - every button click and every remark - is timestamped and logged with User ID and IP Address. These logs are tamper-proof and accessible by Compliance Officers.")
    ]

    for title, content in sections:
        # Title
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(12, 74, 110)
        clean_title = title.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 10, clean_title, ln=True)
        pdf.ln(2)
        
        # Content
        pdf.set_font("Helvetica", size=10)
        pdf.set_text_color(0, 0, 0)
        clean_content = content.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, clean_content)
        pdf.ln(10)

    pdf.output("c:/Users/sapra/.gemini/antigravity/scratch/ssbd-simulator/SSBD_I4C_CFCFRMS_Bank_User_Manual_v1.1.pdf")
    print("PDF Generated Successfully.")

if __name__ == "__main__":
    create_pdf()
