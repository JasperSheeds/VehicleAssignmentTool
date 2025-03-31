"""This program uses Calamp API and Cityworks to gather driver assignments based on pretrip inspections done and then assigns them in Calamp.
 Last updated by Jasper Sheeds 3/31/25"""

import json
from jsonpath_ng.ext import parse
import requests
import os
from dotenv import load_dotenv
from GetToken import validate_token
from SupportFunctions import cw_connections, error_log, email_send

load_dotenv()
appkey = os.getenv("APPKEY")
account = os.getenv("cal_account")
baseurl = os.getenv("base_url_calamp")
new_vehicle_file = []
new_vehicle_plain = []
global authtoken
authtoken = validate_token()

def get_pairs(currentList):
    """ This function uses Cityworks to establish a list of vehicles and the drivers currently assigned to them from pre-trip inspections. """
    global cursor
    cursor = cw_connections()
    if cursor != 0:
        cursor.execute(os.getenv("get_pairs_sql"))
        try:
            current_assigned = [str(match.value) for match in currentList]
        except:
            current_assigned = []
        for row in cursor:
            try:
                driver = str(get_driver_id(str(row[1])))
                asset = str(get_asset_id(str(row[0])))

                if asset == "0":
                    new_vehicle_file.append(str(row[0]) + "<br>")
                    new_vehicle_plain.append(str(row[0]) + "\n")
                elif asset != "1" and asset not in current_assigned:
                    assign_driver(driver, asset)
            except:
                error_log(
                    "There was an issue getting id from the driver: " + str(row[1]) + " or from the asset: " + str(
                        row[0]) + ",\n")
        if len(new_vehicle_file) > 0:
            final_new = "<h2>Vehicle(s) not found in Calamp</h2><ul><p>" + ''.join(str(x) for x in new_vehicle_file)
            final_plain = "Vehicles(s) not found in Calamp\n"
            email_send(final_new, final_plain, "Vehicles Not Found")


def get_driver_id(cwid):
    """ Uses EmployeeID to find the Employees Calamp ID. Creates employee if one is not found. """
    url = baseurl + "operators/search"
    payload = {"search": {"searchTerms": {"badgeNumber": cwid,
                                          "account": account}}}
    headers = {
    "accept": "*/*",
    "content-type": "application/json",
    "calamp-services-app": appkey,
    "authorization": "Bearer " + authtoken}
    response = requests.post(url, json=payload, headers=headers).text
    data_dic = json.loads(response)
    match = parse("$.response.results.[*].operator.id").find(data_dic)
    try:
        return match[0].value
    except:
        return create_driver(cwid)

def assign_driver(driver, asset):
    """ Assigns driver in Calamp to vehicle from pretrip inspection. """
    tempdriver = driver.split(',')
    for driver in tempdriver:
        try:
            url = baseurl + "assets/" + asset + "/operators"
            payload = {"operator": [{"href": baseurl + "operators/" + driver, "rel": "operator", "status": "Enabled"}]}
            headers = {
                "accept": "*/*",
                "content-type": "application/json",
                "calamp-services-app": appkey,
                "authorization": "Bearer " + authtoken}
            response = requests.post(url, json=payload, headers=headers).status_code
            if response != 200:
                error_log("Unsuccessful in adding " + driver + " to " + asset + ",\n")
        except:
            error_log("Unsuccessful in adding " + driver + " to " + asset + ",\n")

def get_asset_id(asset):
    """ Uses CW asset id to find the Calamp id for a vehicle. "0" returned if vehicle does not exist. """
    url = baseurl + "assets/search"
    payload = {"search": {
        "searchTerms": {"name": asset,
                        "account": account},
        "sort": ["+lastModifiedOn"],
        "maxResults": 1
    }}
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "calamp-services-app": appkey,
        "authorization": "Bearer " + authtoken}
    response = requests.post(url, json=payload, headers=headers).text
    data_dic = json.loads(response)
    try:
        typeName = parse("$.response.results.[*].asset.assetType").find(data_dic)
        if typeName[0].value == 'Vehicle':
            match = parse("$.response.results.[*].asset.id").find(data_dic)
            try:
                return match[0].value
            except:
                return "0"
        else:
            return "1"
    except:
        return "0"

def get_assigned_vehicles():
    """ Goes through Calamp and finds all the assets with operators currently assigned to them. """
    url = baseurl + "accounts/" + str(account) + "/subaccounts/assets"
    headers = {
        "accept": "application/json;charset=UTF-8",
        "calamp-services-app": appkey,
        "authorization": "Bearer " + authtoken}
    response = requests.get(url, headers=headers).text
    data_dic = json.loads(response)
    match = parse("$.response.results[?(asset.operators[0])].asset.id").find(data_dic)
    return match

def remove_operators(assets):
    """ Removes operators from vehicles from the previous day. """
    for asset in assets:
        try:
            url = baseurl + "assets/" + str(asset.value) + "/operators"
            headers = {
                "accept": "application/json;charset=UTF-8",
                "calamp-services-app": appkey,
                "authorization": "Bearer " + authtoken}
            response = requests.delete(url, headers=headers)
            if response.status_code != 200:
                error_log("There's been an issue removing operators from " + str(asset.value['id']) + ".\n")
        except:
            error_log("Error removing operator from " + str(asset.value['id']))


def create_driver(driver):
    """ Uses information from Cityworks to create a driver in Calamp. """
    cursor.execute(os.getenv("create_driver_sql_1") + driver + os.getenv("create_driver_sql_2"))
    values = cursor.fetchall()[0]
    try:
        url = baseurl + "operators"
        payload = {"operator": {
            "account": {
                "rel": "account",
                "href": baseurl + "accounts/" + str(account)
            },
            "version": 0,
            "lastName": str(values[2]).title(),
            "firstName": str(values[1]).title(),
            "badgeNumber": driver
        }}
        headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "calamp-services-app": appkey,
            "authorization": "Bearer " + authtoken
        }
        response = requests.post(url, json=payload, headers=headers).status_code
        if response != 200:
            return get_driver_id(driver)
    except:
        error_log("There's been an issue creating this driver " + str(driver) + ".\n")