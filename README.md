# Stripe Invoice Sender

A Python tool for sending custom Stripe invoice emails using Resend bc Stripe emails look good
but offer very little by the way of customization. 

## Usage

Basic usage example:

```python
from stripe_invoice_sender import StripeInvoiceSender

sender = StripeInvoiceSender(
    invoice_id="in_1234567890",
    business_name="Your Business", #optional
    business_email="invoices@yourbusiness.com" #optional
    attach_invoice_pdf=False, #will not attach invoice pdf
    attach_receipt_pdf=False, #will not attach receipt pdf
)

sender.send_invoice()
```

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

## License

[MIT License](LICENSE)