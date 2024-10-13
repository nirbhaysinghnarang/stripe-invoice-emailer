import stripe
from load_dotenv import load_dotenv
import os
from datetime import datetime
import random
import threading
import requests
from io import BytesIO
import resend



load_dotenv()
stripe.api_key = os.environ.get("STRIPE_KEY")
resend.api_key = os.environ.get("RESEND_API_KEY")


class Renderer:
    def __init__(
        self,
        invoice_id,
        business_name=None,
        business_email=None
    ):
        self.invoice_id = invoice_id
        self.business_name = business_name
        self.business_email = business_email
        
       
        self.invoice = stripe.Invoice.retrieve(invoice_id, expand=["discounts"])
        self.customer = stripe.Customer.retrieve(self.invoice.customer)
        self.charge = stripe.Charge.retrieve(self.invoice.charge)
        self.intent = stripe.PaymentIntent.retrieve(self.invoice.payment_intent)
        self.payment_method = stripe.PaymentMethod.retrieve(self.intent.payment_method)        
        
    def _get_card_details(self):
        assert(
            self.payment_method.type == 'card'
        )    
        card_details = self.payment_method.card
        return card_details.brand, card_details.last4
    
    
    def _render_conditionally(
        self,
        payload,
        prop
    ):
        return f'''{payload}''' if prop else ''
        
        
    def generate_receipt_html(self):
        print("Generating html.")

        receipt_data = self._prepare_receipt_data()
        html = f"""
       <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {self._render_conditionally("<title>Receipt from {receipt_data['business_name']}</title>", receipt_data["business_name"])}
        </head>
        <body style="font-family:-apple-system,BlinkMacSystemFont,&quot;Segoe UI&quot;,Roboto,&quot;Helvetica Neue&quot;,Ubuntu,sans-serif;text-decoration:none; margin: 0; padding: 0; background-color: #000;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #000; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                <div style="background-color: transparent; padding: 20px; text-align: center; border-bottom: 1px solid #d6d5ca;">
                {self._render_conditionally(f'<h2 style="margin: 0; color: #d6d5ca;">{receipt_data['business_name']}</h2>', receipt_data['business_name'])}
               
                </div>
                
                <div style="padding: 20px;">
                    <!-- Receipt Card -->
                    <div style="background-color: #1e1e1e; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td style="vertical-align: top; padding-right: 20px;">
                                    <h3 style="margin: 0 0 10px; color: #d6d5ca;">${receipt_data['business_name']}</h3>
                                    <h1 style="margin: 0 0 10px; font-size: 36px; color: #d6d5ca;">${receipt_data['total_amount']}</h1>
                                    <p style="margin: 0 0 20px; color: #fff;">Paid {receipt_data['paid_date']}</p>
                                    
                                <div style="margin-bottom: 20px;">
                                        <a href="{receipt_data['invoice_link']}" style="display: inline-block; padding: 10px 15px; background-color: #000; color: #d6d5ca; text-decoration: none; border-radius: 5px; margin-right: 20px; margin-bottom: 10px;">↓ Download invoice</a>
                                        <a href="{receipt_data['receipt_link']}" style="display: inline-block; padding: 10px 15px; background-color: #000; color: #d6d5ca; text-decoration: none; border-radius: 5px; margin-bottom: 10px;">↓ Download receipt</a>
                                    </div>
                            
                                    <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                                        <tr>
                                            <td width="50%" style="color: #d6d5ca; padding: 5px 0;">Payment method</td>
                                            <td width="50%" style="color:#d6d5ca; text-align: right; padding: 5px 0;"><strong>{receipt_data['payment_method']}</strong></td>
                                        </tr>
                                    </table>
                                </td>
                                <td style="vertical-align: top; width: 200px;">
                                    <img src="https://ci3.googleusercontent.com/meips/ADKq_Nb0PIKp4BW7Q9dGZWAbhhehqH1C7jSJqPrktJ2lzqT_ZKhZb3k_OE2EHw4d-X52LFFEkrtG1wxOZCHxAtGyrjX1yDzocuLEuaTPZySKYYjONkOVyakKaNjTutQUWWCz6ZcbCwWN=s0-d-e1-ft#https://stripe-images.s3.amazonaws.com/emails/invoices_invoice_illustration.png" alt="Receipt Illustration" style="width: 100%; max-width: 200px;">
                                </td>
                            </tr>
                        </table>
                    </div>
                    
                    <!-- Line Items Card -->
                    <div style="background-color: #1e1e1e; border-radius: 8px; padding: 20px;">
                        <h3 style="color: #d6d5ca;">Receipt</h3>
                        
                        {self._generate_item_rows(receipt_data['items'])}
                            
                        <table width="100%" cellpadding="0" cellspacing="0" style="border-top: 1px solid #333; border-bottom: 1px solid #333; padding: 10px 0; margin-top: 20px;">
                            <tr>
                                <td style="color: #fff; padding: 5px 0;">Subtotal</td>
                                <td style="text-align: right; padding: 5px 0; color: #d6d5ca;"><strong>${receipt_data['subtotal']}</strong></td>
                            </tr>
                            
                            <tr>
                                <td style="color: #fff; padding: 5px 0;">Tax</td>
                                <td style="text-align: right; padding: 5px 0; color: #d6d5ca;"><strong>${receipt_data['tax']}</strong></td>
                            </tr>
                        {f'''
                            <tr>
                                <td style="color: #fff; padding: 5px 0;">{receipt_data['discount_description']}</td>
                                <td style="text-align: right; color: #d6d5ca; padding: 5px 0;">-${receipt_data['discount_amount']}</td>
                            </tr>
                            ''' if receipt_data['discount_description'] else ''}
                            <tr>
                                <td style="color: #fff; padding: 5px 0;">Total</td>
                                <td style="text-align: right; padding: 5px 0; color: #d6d5ca;"><strong>${receipt_data['total_amount']}</strong></td>
                            </tr>
                            <tr>
                                <td style="color: #fff; padding: 5px 0;">Amount paid</td>
                                <td style="text-align: right; padding: 5px 0; color: #d6d5ca;"><strong>${receipt_data['total_amount']}</strong></td>
                            </tr>
                        </table>
                    </div>
                    
                    {self._render_conditionally("""
                        <p style="text-align: center; color: #fff; margin-top: 20px;">
                        Questions? Contact us at <a href="mailto:{receipt_data['business_email']}" style="color: #0000FF;">{receipt_data['business_email']}</a>.
                        </p>
                        """, receipt_data["business_name"])
                    }
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    
    def _generate_item_rows(self, items):
        rows = '<table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">'
        for item in items:
            rows += f"""
            <tr style="margin-bottom: 10px;">
                <td style="padding-bottom: 10px;">
                    <p style="margin: 0; color: #d6d5ca;">{item['name']}</p>
                    <p style="margin: 0; color: #fff;">Qty {item['quantity']}</p>
                </td>
                <td style="text-align: right; padding-bottom: 10px;">
                    <strong style="color: #d6d5ca;">${item['price']}</strong>
                </td>
            </tr>
            """
        rows += '</table>'
        return rows
    
    
    def _generate_and_mutate_receipt_number(self):
        if self.charge.receipt_number is not None and self.charge.receipt_number!="":            
            return
        random_number = f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        self.charge.receipt_number = random_number
         
    
    def _prepare_receipt_data(self):
        def _get_payment_method_repr():
            if self.payment_method.type == 'card':
                card_brand, card_last_4 = self._get_card_details()
                return f"{card_brand.upper()} - {card_last_4}"
            return f"{self.payment_method.type.replace('_', ' ').title()}"

        def _get_discount_info():
            if self.invoice.discount:
                coupon = self.invoice.discount.coupon
                if coupon.percent_off:
                    discount_description = f"{coupon.percent_off}% off"
                elif coupon.amount_off:
                    discount_description = f"${coupon.amount_off / 100:.2f} off"
                else:
                    discount_description = "Discount applied"
                
                return {
                    "discount_description": coupon.name or discount_description,
                    "discount_amount": f"{self.invoice.total_discount_amounts[0].amount / 100:.2f}",
                    "discount_code": self.invoice.discount.promotion_code if self.invoice.discount.promotion_code else None
                }
            return {
                "discount_description": "",
                "discount_amount": "0.00",
                "discount_code": None
            }

        try:
            self._generate_and_mutate_receipt_number() 
            discount_info = _get_discount_info()
            return {
                'total_amount': f"{self.invoice.total / 100:.2f}",
                'paid_date': datetime.fromtimestamp(self.invoice.status_transitions.paid_at).strftime("%B %d, %Y"),
                'invoice_link': self.invoice.invoice_pdf,
                'receipt_number': self.charge.receipt_number,
                'receipt_link': self.charge.receipt_url,
                'payment_method': _get_payment_method_repr(),
                'tax': f"{self.invoice.tax / 100:.2f}",
                'items': [
                    {
                        'name': item.description,
                        'quantity': item.quantity,
                        'price': f"{item.amount / 100:.2f}"
                    } for item in self.invoice.lines.data
                ],
                'subtotal': f"{self.invoice.subtotal / 100:.2f}",
                'discount_description': discount_info['discount_description'],
                'discount_amount': discount_info['discount_amount'],
                'discount_code': discount_info['discount_code'],
                'business_name':self.business_name,
                'business_email':self.business_email
            }
        except Exception as e:
            print(f"Caught {str(e)}, raising {str(e)}")
            raise e
    
    
    def get_pdf_receipt(self):
        
        def _get_pdf_link(url):
            base_url, _, query_string = url.partition('?')
            modified_base_url = base_url.rstrip('/') + '/pdf'
            modified_receipt_link = modified_base_url + ('?' + query_string if query_string else '')            
            return modified_receipt_link
        receipt_link = _get_pdf_link(self.charge.receipt_url)
        response = requests.get(receipt_link)
        receipt_pdf = BytesIO(response.content)
        return receipt_pdf
              
    
    def get_pdf_invoice(self):
        invoice_pdf = self.invoice.invoice_pdf
        response = requests.get(invoice_pdf)
        invoice_pdf = BytesIO(response.content)
        return invoice_pdf