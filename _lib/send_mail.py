import logging
import os
import azure.functions as func
import typing
import json
import smtplib
from email.mime.text import MIMEText
from sendgrid import SendGridAPIClient
from _lib.queue_service import put_queue

def from_plain_text(plain_text):
    rows = plain_text.split("\n")
    text = ""
    for r in rows:
        text += "<div>" + r + "</div>"
    return top + text + bottom

DEFAULT_EMAIL_SENDER = os.environ["EmailSender"]
DEFAULT_SENDER_PWD = os.environ["EmailSenderPwe"]


top = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html data-editor-version="2" class="sg-campaigns" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=1" /><!--[if !mso]><!-->
<meta http-equiv="X-UA-Compatible" content="IE=Edge" /><!--<![endif]-->
<!--[if (gte mso 9)|(IE)]>
<xml>
<o:OfficeDocumentSettings>
<o:AllowPNG/>
<o:PixelsPerInch>96</o:PixelsPerInch>
</o:OfficeDocumentSettings>
</xml>
<![endif]-->
<!--[if (gte mso 9)|(IE)]>
<style type="text/css">
body {width: 600px;margin: 0 auto;}
table {border-collapse: collapse;}
table, td {mso-table-lspace: 0pt;mso-table-rspace: 0pt;}
img {-ms-interpolation-mode: bicubic;}
</style>
<![endif]-->

<style type="text/css">
body, p, div {
font-family: trebuchet ms,helvetica,sans-serif;
font-size: 16px;
margin-bottom: 10px;
}
</style>
<!--user entered Head Start-->

<!--End Head user entered-->
</head>
<body>
"""

bottom = """
</body>
</html>
"""



def BuildMail(from_email, to_emails: typing.List[str], subject, html_content):
    return {"from_email": from_email, "to_emails": to_emails, "subject": subject, "html_content": html_content}


def SendMail(mail):
    logging.info("Pushing email to queue")
    json_mail = json.dumps(mail)
    logging.info(json_mail)
    put_queue("emails",json_mail)
    logging.info("Mail was pushed to queue")



def send_email_with_sendgrid(msg: str) -> None:
    logging.info(msg)
    body = json.loads(msg)
    logging.info("Received email to send.")
    logging.info(body)
#    if os.environ.get("ENV") != "prod":
#        body["to_emails"] = ["gustav.eiman@bdo.se", "tobias.hultman@bdo.se"]
    if "txt_content" in body:
        body["html_content"] = from_plain_text(body["txt_content"])
    message = BuildMail(
        from_email=body["from_email"],
        to_emails=body["to_emails"],
        subject=body["subject"],
        html_content=body["html_content"],
    )
    try:
        logging.info(str(message))
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        logging.info("Sendgrid call was sucessfull.")
        logging.info(response.status_code)
        logging.info(response.body)
        logging.info(response.headers)
    except Exception as e:
        logging.error("Could not send email(s) from %s", body["from_email"])
        logging.error(str(e))
        try:
            send_email_with_office365(msg)
        except Exception as e:
            logging.error("Could not send email(s) from %s", DEFAULT_EMAIL_SENDER)
            logging.error(str(e))
            raise


def send_email_with_office365(message: str):
    logging.info(message)
    body = json.loads(message)
    logging.info("Received email to send.")
    if "txt_content" in body:
        body["html_content"] = from_plain_text(body["txt_content"])

    if "<" in DEFAULT_EMAIL_SENDER:
        i=DEFAULT_EMAIL_SENDER.index("<")
        user_id=DEFAULT_EMAIL_SENDER[i+1:-1]
    else:
        user_id = DEFAULT_EMAIL_SENDER
    logging.info("user_id=%s", user_id)
    s = smtplib.SMTP('smtp.office365.com', 587)
    s.ehlo()
    s.starttls()
    s.login(user=user_id, password=DEFAULT_SENDER_PWD)
    s.set_debuglevel(1)
    msg = MIMEText(body["html_content"],"html")
    msg['Subject'] = body["subject"]
    msg['From'] = DEFAULT_EMAIL_SENDER
    msg['To'] = ", ".join(body["to_emails"])
    s.sendmail(DEFAULT_EMAIL_SENDER, body["to_emails"], msg.as_string())
