"""This program uses retrieves a Calamp token if the current one has expired.
  Changes last made by Jasper Sheeds 1/14/25"""

import requests
import datetime
import calendar
from dotenv import load_dotenv
import os

load_dotenv()
APPKEY = os.getenv("APPKEY")
USERINFO = os.getenv("USERINFO")
today = datetime.datetime.now(datetime.timezone.utc)
todayformatted = calendar.timegm(today.timetuple())

def new_token():
    """ Makes call to get a new token. """
    url = "https://connect.calamp.com/connect/services/login?useAuthToken=true"
    payload= USERINFO
    headers = {
       'calamp-services-app': APPKEY,
       'Content-Type': 'application/x-www-form-urlencoded',
       'Accept': '*/*',
       'Host': 'connect.calamp.com',
       'Connection': 'keep-alive'
    }
    response = str(requests.request("POST", url, headers=headers, data=payload).headers)
    authtoken = ((response.split("'Set-Cookie': '")[1]).split("; Path=")[0])
    f = open("AuthToken.txt", "w")
    f.write(authtoken)
    authfile = authtoken.split(";")
    temp_authtoken = (authfile[0])[10:]
    return temp_authtoken

def validate_token():
    """ Reads text file with previous authtoken and checks if the expiration date has passed.
    If token is expired new_token is called. If no file exists, one is created and populated."""
    try:
        f = open("AuthToken.txt", "r")
        authfile = f.read().split(";")
        expdate = calendar.timegm((datetime.datetime.strptime(((authfile[1].split(", ")[1]).split(" GMT")[0]),
                                                              "%d-%b-%Y %H:%M:%S")).timetuple())
        if expdate > todayformatted:
            authtoken = (authfile[0])[10:]
            return authtoken
        else:
            return new_token()
    except:
        open("AuthToken.txt", "w+")
        return new_token()

validate_token()