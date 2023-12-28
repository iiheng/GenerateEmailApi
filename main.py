from http.client import HTTPException

from fastapi import FastAPI
import imaplib
import email
import re

from pydantic import BaseModel

# Constants for IMAP server and credentials
IMAP_SERVER = 'imap.qq.com'
IMAP_PORT = 993
class EmailCredentials(BaseModel):
    username: str
    password: str

app = FastAPI()

def get_html_part(email_message):
    """Extracts HTML part from an email message."""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == 'text/html':
                return part.get_payload(decode=True)
    elif email_message.get_content_type() == 'text/html':
        return email_message.get_payload(decode=True)

def getAddress(html_content):
    """Extracts URL from the 'Verify email address' link in HTML content."""
    pattern = r'<a href="(http[^"]+)"[^>]*>\s*Verify email address\s*</a>'
    match = re.search(pattern, html_content)
    return match.group(1) if match else None

def read_latest_email(username, password):
    """Reads the latest email and extracts the verification link address."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(username, password)
        mail.select('inbox')

        status, data = mail.search(None, 'ALL')
        latest_email_id = int(data[0].split()[-1])
        status, data = mail.fetch(str(latest_email_id), '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)
        html_content = get_html_part(email_message)

        mail.logout()

        if html_content:
            if isinstance(html_content, bytes):
                html_content = html_content.decode()
            return getAddress(html_content)
        return None
    except imaplib.IMAP4.error:
        raise HTTPException(status_code=401, detail="Authentication failed")

@app.post("/get_verification_link")
async def get_verification_link(credentials: EmailCredentials):
    address = read_latest_email(credentials.username, credentials.password)
    return {"verification_link": address}

# To run the application, use the following command in your terminal:
# uvicorn yourfilename:app --reload
