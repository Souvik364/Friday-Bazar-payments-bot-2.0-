from io import BytesIO
import qrcode


def generate_payment_qr(plan_name: str, amount: int) -> BytesIO:
    """
    Generate a fake/test QR code for payment.
    
    TO REPLACE WITH REAL PAYMENT QR:
    1. Replace the qr_data string with your actual UPI payment string:
       Example: f"upi://pay?pa=yourUPI@bank&pn=YourName&am={amount}&cu=INR&tn=Premium Plan {plan_name}"
    2. Or integrate with your payment gateway API to get dynamic QR data
    3. Keep the rest of the function unchanged
    
    Args:
        plan_name: Name of the plan (e.g., "1 Month", "3 Months")
        amount: Payment amount in rupees
        
    Returns:
        BytesIO: QR code image buffer ready to send via Telegram
    """
    qr_data = f"TEST_PAYMENT|Plan:{plan_name}|Amount:{amount}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer
