from io import BytesIO
from typing import List, Tuple
from render import Renderer
import resend
import base64
import stripe
from load_dotenv import load_dotenv
import os


load_dotenv()
stripe.api_key = os.environ.get("STRIPE_KEY")


class StripeInvoiceSender:
    
    def __init__(
        self,
        invoice_id,
        business_name=None,
        business_email=None,
        attach_invoice_pdf=True,
        attach_receipt_pdf=True,
        subject_line=None,
        from_email=None
        ):
        self.invoice_id = invoice_id
        self.customer = self.get_customer_from_invoice()
        if not self.customer:   raise ValueError("This invoice does not have an associated customer.")
        
        self.business_name = business_name
        self.business_email = business_email
        self.renderer = Renderer(
            invoice_id=self.invoice_id,
            business_name=self.business_name,
            business_email=self.business_email
        )
        
        self.attach_invoice_pdf = attach_invoice_pdf
        self.attach_receipt_pdf = attach_receipt_pdf
        self.invoice_pdf = None
        self.receipt_pdf = None
        self.subject_line = subject_line
        self.from_email = from_email
        
        
        
    def send_invoice(self):
        rendered_html = self.renderer.generate_receipt_html()
        attachments = []

        
        if self.attach_invoice_pdf:
            self.invoice_pdf = self.renderer.get_pdf_invoice()
            attachments.append(("Invoice.pdf", self.invoice_pdf))
            
        if self.attach_receipt_pdf:
            self.receipt_pdf = self.renderer.get_pdf_receipt()
            attachments.append(("Receipt.pdf", self.receipt_pdf))
              
        self._send_email(
            subject=self.subject_line,
            to_email=self.customer.name,
            message=rendered_html,
            attachments=attachments
        )
           
         
         
           
    def _get_customer_from_invoice(
       self
    ):
        invoice = stripe.Invoice.retrieve(self.invoice_id)
        customer = invoice.customer
        if not customer:
            return None
        return stripe.Customer.retrieve(customer)
                
            
    def _send_email(
        self,
        subject: str,
        to_email: str,
        message: str,
        attachments: List[Tuple[str, BytesIO]] = None
    ):
        try:
            params = {
                "from": self.from_email,
                "to": to_email,
                "subject": subject,
                "html": message,
            }

            if attachments:
                params["attachments"] = []
                for name, content in attachments:
                    encoded_content = base64.b64encode(content.getvalue()).decode('utf-8')

                    params["attachments"].append({
                        "filename": name,
                        "content":encoded_content,
                        "type": "application/pdf"
                    })

            response = resend.Emails.send(params)
            print(f"Email sent successfully! ID: {response['id']}")
        except Exception as e:
            print(f"Failed to send email: {e}")
        
        
        
        
        
        
    

        
