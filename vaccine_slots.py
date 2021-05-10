import requests
import datetime
import http.client
import json
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import time
import os

pincodes = {
    os.environ.get("EMAIL_ID2"):['201301','201014'],
    os.environ.get("EMAIL_ID1"):['208001','208017','208002','208004','208011','208007']
}
ages = {
    os.environ.get("EMAIL_ID1"):25,
    os.environ.get("EMAIL_ID2"):24
}
all_ids = {
    os.environ.get("EMAIL_ID1"):[os.environ.get("EMAIL_ID1"),os.environ.get("EMAIL_ID2")],
    os.environ.get("EMAIL_ID2"):[os.environ.get("EMAIL_ID2"),os.environ.get("EMAIL_ID1")]
}

session_ids = set()

def send_mail(found_info,receiver_id):
    if len(found_info)>1:
        for rid in all_ids[receiver_id]:
            df = pd.DataFrame(found_info,columns=['Centre','Pincode','Date','Age','Available Capacity','Vaccine'])
            message = MIMEMultipart()
            message['Subject'] = 'Found slots for {} in requested pincodes!'.format(receiver_id)
            message['From'] = os.environ.get("SENDER_ID")
            message['To'] = rid
            body_content = df.to_html()
            message.attach(MIMEText(body_content, "html"))
            msg_body = message.as_string()
            server = SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(message['From'], os.environ.get("SENDER_PASSWORD"))
            server.sendmail(message['From'], message['To'], msg_body)
            server.quit()

def find_and_mail(pincodes,receiver_id):
    found_info = []
    new_info=0
    for pincode in pincodes[receiver_id]:
        params = {
        'pincode':str(pincode),
        'date':datetime.datetime.now().strftime('%d-%m-%y')
        }
        payload = ''
        for key in params:
            payload += key+'='+params[key]+'&'

        conn = http.client.HTTPSConnection("cdn-api.co-vin.in")
        headers = {}
        conn.request("GET", "/api/v2/appointment/sessions/public/calendarByPin?"+payload[:-1], '', headers)
        res = conn.getresponse()
        data = res.read()
        data = json.loads(data.decode("utf-8"))
        for dt in data['centers']:
            for session in dt['sessions']:
                if session['available_capacity']>0:
                    if session['min_age_limit']<ages[receiver_id]:
                        found_info += [[dt['name'],dt['pincode'],session['date'],str(session['min_age_limit'])+'+',session['available_capacity'],session['vaccine']]]
                        if session['session_id'] not in session_ids:
                            session_ids.add(session['session_id'])
                            new_info=1
    if new_info==1:
        send_mail(found_info,receiver_id)

while(1):
    for eid in [os.environ.get("EMAIL_ID2"),os.environ.get("EMAIL_ID1")]:
        find_and_mail(pincodes,eid)
        time.sleep(15)
