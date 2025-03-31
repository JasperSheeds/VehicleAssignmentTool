"""This program uses Calamp API to gather information regarding vehicles that have operated outside operating hours.

Definition Key:
  Event = A snapshot of device properties triggered by various actions performed with device. For this program we're only concerned with IGON or IGOFF actions.
  Trip = An IGON and an IGOFF event, the times those events occurred, and the difference in the odometer between the events
  Type 2 = IGON or Ignition turned on
  Type 3 = IGOFF or Ignition turned off

Change wd_start_hour and wd_start_min to alter start of workday.
Change wd_end_hour and wd_end_min to alter end of workday.
(Time is in 24-hour format)

  Last updated by Jasper Sheeds 3/31/25"""

wd_start_hour = 7
wd_start_min = 0
wd_end_hour = 3
wd_end_min = 30

import json
from datetime import datetime, timedelta, timezone, time
from jsonpath_ng.ext import parse
import requests
import os
from dotenv import load_dotenv
from GetToken import validate_token
from SupportFunctions import print_file, folder_loc, error_log, email_send

load_dotenv()
appkey = os.getenv("APPKEY")
baseurl = os.getenv("base_url_calamp")
cal_account = os.getenv("cal_account")
authtoken = validate_token()
assigned_devices = []
all_devices = []
event_string = []
all_events = []
all_trips = []
unassigned_plain = []
unassigned_driven = []
location_file = []
location_plain = []
holidays = os.getenv("holidays")
iso_time = timedelta(hours=5)
est_time = timezone(timedelta(hours=-5))

def get_week(date):
    """ Calculates a seven-day week that ends the day before the current date. """
    now = date.replace(hour=0,minute=0,second=0)
    start_day = now - timedelta(days=7)
    end_day = now - timedelta(days=1)
    return start_day, end_day

def get_devices(date):
    """ Gets all the devices in the account. Returns a list. """
    url = baseurl + "accounts/" + str(cal_account) + "/subaccounts/devices"
    headers = {
        "accept": "application/json;charset=UTF-8",
        "calamp-services-app": appkey,
        "authorization": "Bearer " + authtoken}
    response = requests.get(url, headers=headers).text
    data_dic = json.loads(response)
    match = parse('$.response.results.[*].device.id').find(data_dic)
    for m in match:
        if m.value not in assigned_devices:
            check_location_history(m.value, date)

def calculate_dates(start, end):
    """ Calculates hours for days given after checking if it is a work day or holiday/weekend."""
    days = []
    temp_day = start
    global search_start
    search_start = "[" + str((temp_day + iso_time).isoformat())+ "Z TO " + str((end.replace(hour=23, minute=59) + iso_time).isoformat()) + "Z]"
    while temp_day <= end:
        if temp_day.weekday() == 5 or temp_day.weekday() == 6 or str(temp_day.date()) in holidays:
            temp_start = (temp_day + iso_time)
            temp_end = (temp_day.replace(hour=23, minute=59) + iso_time)
        else:
            temp_start = (temp_day + iso_time)
            temp_end = (temp_day.replace(hour=wd_start_hour, minute=wd_start_min) + iso_time)
            temp_date = Day(temp_start, temp_end)
            days.append(temp_date)
            temp_start = (temp_day.replace(hour=wd_end_hour, minute=wd_end_min) + iso_time)
            temp_end = (temp_day.replace(hour=23, minute=59) + iso_time)
        temp_date = Day(temp_start, temp_end)
        days.append(temp_date)
        temp_day = temp_day + timedelta(days=1)
    return days

def find_days(date, page, code):
    """ Finds events within a date set in Calamp."""
    url = 'https://connect.calamp.com/connect/results/events/avl/search?v=2.0&pgsize=500&pg=' + str(page)
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "calamp-services-app": appkey,
        "authorization": "Bearer " + authtoken,
        'Connection': 'keep-alive'}
    payload = {"search": {
            "searchTerms": {
                "eventTime": date,
                "accountId": cal_account,
                "eventCode": code
            },
            "maxResults": 999
        }}
    response = requests.post(url, json=payload, headers=headers).text
    try:
        new_response = json.loads(response)
        return new_response
    except:
        return 0

def vehicle_usage(today):
    """ Main method that is called with the current date. """
    current_week = get_week(today)
    start = current_week[0]
    end = current_week[1]
    global date_array
    date_array = calculate_dates(start, end)
    get_all_pages(search_start, 2)
    get_all_pages(search_start, 3)
    device_set = list(set(assigned_devices))
    for d in device_set:
        filtered_events = [event for event in all_events if event.device == d]
        filtered_events.sort(key=lambda x:x.eventTime)
        last = filtered_events.pop()
        while len(filtered_events) >= 2:
            if last.type == 3:
                prev = filtered_events.pop()
                if prev.type == 2:
                    all_trips.append(Trip(prev, last, d,  last.asset))
                    last = filtered_events.pop()
                else:
                    last = prev
            else:
                last = filtered_events.pop()
    all_trips.sort(key=lambda x:x.igon_time)
    if len(all_trips) > 0:
        location_file_loc = r"./WeeklyVehicleAuditLogs/"
        location_name = str(cal_account) + '_' + today.strftime('%Y%m%d%H%M') + '.csv'
        try:
            print_file(location_file_loc, location_name, all_trips, "IGON DATE, IGON ADDRESS, IGOFF DATE, IGOFF ADDRESS, TRIP MILES, ASSET, DEVICE, DRIVER\n")
        except:
            folder_loc(location_file_loc)
            try:
                print_file(location_file_loc, location_name, all_trips,"IGON DATE, IGON ADDRESS, IGOFF DATE, IGOFF ADDRESS, TRIP MILES, ASSET, DEVICE, DRIVER\n")
            except:
                error_log("Error creating Weekly Vehicle Audit file.\n")

    if len(unassigned_driven) > 0:
        event_set = list(set(unassigned_driven))
        event_plain = list(set(unassigned_plain))
        try:
            final_driven = """<style> h1 {font-size:25px; font-family: Arial, sans-serif; text-align: center;} th {font-size:20px; font-family: Arial, sans-serif; text-align: left;} tr {font-size:15px; font-family: Arial, sans-serif; text-align: center;} th,td {padding: 3px;} </style><h1>Vehicles With No Driver Data</h1><style>table, th, td {}</style><body><table style="width:100%"> <tr><th>Asset</th><th>Asset Alias</th><th>Event Date</th></tr>""" + ''.join(str(x) for x in event_set) + "</table></body>"
            final_plain  = "\tAsset, Asset Alias, Event Date\n" + ''.join(str(x) for x in event_plain)
            email_send(final_driven,final_plain, "Vehicles With No Driver Data")
        except:
            error_log("Error creating Weekly Unassigned file.\n")

    get_devices(today.date())
    if len(location_file) > 0:
        try:
            final_location = """<style> h1 {font-size:25px; font-family: Arial, sans-serif; text-align: center;} th {font-size:20px; font-family: Arial, sans-serif; text-align: center;} tr {font-size:15px; font-family: Arial, sans-serif; text-align: center;} th,td {padding: 3px;} </style><h1>Weekly Vehicles with No Location Data</h1><style>table, th, td {}</style><body><table style="width:100%"> <tr><th>Asset</th><th>Last Event</th></tr>""" + ''.join(str(x) for x in location_file) + "</table></body>"
            final_plain = '\tAsset, Last Event\n' + ''.join(str(x) for x in location_file)
            email_send(final_location, final_plain, "Vehicles with No Location Data")
        except:
            error_log("Error creating Weekly Location file.\n")

def check_location_history(asset, date):
    """ Goes through and finds assets latest location event. If the event is older than 7 days the asset is added to record. """
    url = "https://connect.calamp.com/connect/results/events/device/" + str(asset) + "/avl/lastknownposition?idType=DeviceId&v=2.0"
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "calamp-services-app": appkey,
        "authorization": "Bearer " + authtoken
    }
    response = requests.get(url, headers=headers).text
    try:
        data_dic = json.loads(response)
        match = parse('$.response.results.[*].avlEvent').find(data_dic)
        for i in match:
            if (date-datetime.fromisoformat(i.value['eventTime']).date()) > timedelta(days=7):
                location_file.append("<tr><td>" + str(asset) + "</td><td>" + str(datetime.fromisoformat(i.value['eventTime'])) + "</td></tr>")
                location_plain.append(str(asset) + ", " + str(datetime.fromisoformat(i.value['eventTime'])) + "\n")
    except:
        location_file.append("<tr><td>" + str(asset) + "</td><td>NONE</td></tr>")
        location_plain.append(str(asset) + ", NONE\n")

class Day:
    def __init__(self, start, end):
        self.start = start.replace(tzinfo=timezone.utc)
        self.end = end.replace(tzinfo=timezone.utc)

class Event:
    def __init__(self, device, address, eventTime, type, driver, odometer, asset):
        self.device = device
        self.address = address
        self.eventTime = eventTime
        self.type = type
        self.driver = driver
        self.odometer = odometer
        self.asset = asset

class Trip:
    def __init__(self, igon, igoff, device, asset):
        self.igon_time = igon.eventTime
        self.igon_address = igon.address
        self.igoff_time = igoff.eventTime
        self.igoff_address = igoff.address
        self.trip_miles = float(igoff.odometer)-float(igon.odometer)
        self.device = device
        self.asset = asset
        self.driver = igon.driver

    def __str__(self):
        return (str(self.igon_time) + ", " + str(self.igon_address.replace(',', '')) + ", " + str(self.igoff_time) + ", "
                + str(self.igoff_address.replace(',', '')) + ", " + str(self.trip_miles) + ", " + self.asset + ", " + str(self.device) + ", " + self.driver + "\n")

def get_one_page(page):
    """ Get the events from one page. """
    for i in page:
        tempTime = datetime.fromisoformat(i.value['eventTime']).replace(tzinfo=timezone.utc)
        for d in date_array:
            if (tempTime >= d.start and tempTime <= d.end):
                assigned_devices.append(i.value['deviceId'])
                try:
                    driver = i.value['operators'][0]['title'].replace(',', '')
                except:
                    driver = 'No Driver Assigned'
                all_events.append(Event(i.value['deviceId'], str(i.value['address']['label']), (
                    ((datetime.fromisoformat(i.value['eventTime'])).astimezone(timezone.utc)).astimezone(
                        est_time)).strftime('%m-%d-%Y %H:%M%p'), i.value['eventCode'], driver,
                                        i.value['deviceDataConverted']['accumulators'][0]['value'],
                                        i.value['asset']['title']))
            else:
                if tempTime.time() > time(8, 30) and not 'operators' in i.value:
                    unassigned_driven.append("<tr><td>" + str(i.value['asset']['title']) + '</td><td>' + i.value['assetExternalId'] + '</td><td>' + str(tempTime.strftime('%m-%d-%Y')) + '</td></tr>')
                    unassigned_plain.append(str(i.value['asset']['title']) + ' ,' + i.value['assetExternalId'] + ', ' + str(tempTime.strftime('%m-%d-%Y')) + '\n')

def get_all_pages(date, code):
    """ Gets all events on all pages from Calamp pull. """
    data = find_days(date, 1, code)
    events = parse('$.response.results.[*].avlEvent').find(data)
    get_one_page(events)
    match = parse('$.*.last').find(data)
    index = 2
    try:
        while not match[0].value:
            data = find_days(date, index,code)
            events = parse('$.response.results.[*].avlEvent').find(data)
            get_one_page(events)
            match = parse('$.*.last').find(data)
            index = index + 1
    finally:
        return