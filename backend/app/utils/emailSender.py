from flask_mail import Message 
from app.extensions import mail
from flask import current_app
import urllib.parse

def send_verification_email(recipient_email, verification_token):
    #safe token parse 
    token_provided = urllib.parse.urlencode({
    "token": verification_token
    })
    verification_url = (
    f"{current_app.config['FRONTEND_ORIGIN']}/verify-email?{token_provided}"
    )
    # Create the email message
    msg = Message(
        subject="Verify your email | Ticketmaster",
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[recipient_email],
        body=(
            "Please verify your email using the link below:\n\n"
            f"{verification_url}\n\n"
            "This link expires in 15 minutes. "
            "If you did not create this account, you can ignore this email."
        )
    )
    # Send the email
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        raise Exception("Unable to send email, please try again") from e
    