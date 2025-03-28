""" Housekeeping functions used in other files.
 Changes last made by Jasper Sheeds 3/28/25 """

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pyodbc
import os
import requests
from dotenv import load_dotenv
load_dotenv()
global error_log_file
error_log_file = []

def cw_connections():
    """ Creates and returns a Cityworks connection. """
    connection = pyodbc.connect(os.getenv('cw_connection'))
    return connection.cursor()

def folder_loc(path):
    """ Checks if folder exists, and creates it if it does not."""
    if not os.path.exists(path):
        os.makedirs(path)

def print_file(path, file_name, file, opening):
    """ Writes a string array to a file in a given location. """
    event_file_loc = path + file_name
    event_logging = open(event_file_loc, "w+")
    event_final_string = ''.join(str(x) for x in file)
    event_logging.write(opening + event_final_string)
    event_logging.close()

def error_log(error):
    """ Writes error to list. """
    error_log_file.append(error)

def get_errors():
    """ Returns errors in list. """
    return error_log_file

def email_send(html, plain, subject):
    """ Sends email. """
    email_from = os.getenv('email_from')
    email_to = os.getenv('email_to')
    email_pass = os.getenv('email_pass')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = email_from
    msg['To'] = email_to

    part1 = MIMEText(plain, 'plain')
    part2 = MIMEText(html, 'html')

    msg.attach(part1)
    msg.attach(part2)

    mail = smtplib.SMTP('smtp.gmail.com', 587)
    mail.ehlo()
    mail.starttls()
    mail.login(email_from, email_pass)
    mail.sendmail(email_from,email_to, msg.as_string())
    mail.quit()

def return_token():
    """ Returns Cityworks AuthToken. Returns 0 if failure has occurred."""
    url = os.getenv("base_url_cw") +  'General/Authentication/Authenticate?data={"LoginName":"' + os.getenv("cw_username") + '","Password":"' + os.getenv("cw_password") + '"}'
    try:
        response = json.loads(requests.request("GET", url).text)
        if response['Status'] == 0:
            return response['Value']['Token']
        else:
            return 0
    except:
        return 0

print(return_token())