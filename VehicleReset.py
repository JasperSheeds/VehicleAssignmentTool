""" Program runs a SQL query on inspections and assigns vehicles based on results
 Changes last made by Jasper Sheeds 3/28/25 """

import json
import requests
import os
from dotenv import load_dotenv
import numpy as np
import string
from SupportFunctions import error_log, email_send

load_dotenv()
baseurl = os.getenv("base_url_cw")
cw_username = os.getenv("cw_username")
cw_password = os.getenv("cw_password")

def remove_vehicles(emp_sids):
    """ Resets Vehicle value to '' for every employee in provided list. """
    url = baseurl + ('Ams/Employee/Update?data={"EmployeeSids": [' + ', '.join(str(x.EMPLOYEESID) for x in emp_sids) + '], "CustomFieldValues":{193610:""}}&token=' + cw_token)
    response = requests.post(url).text
    try:
        json.loads(response)
    except:
        error_log("Error: removing vehicles from " + ', '.join(str(x.EMPLOYEESID) for x in emp_sids) + " failed\n")
        return 0

def daily_reset(date, token, cursor):
    """ Main function that is called and calls rest of the functions. """
    global file_date
    global cw_cursor
    global cw_token
    cw_token = token
    cw_cursor = cursor
    file_date = date.strftime('%Y%m%d')
    cw_cursor.execute(os.getenv("daily_reset_sql"))
    empsids = cw_cursor.fetchall()
    if len(empsids) > 0:
        try:
            remove_vehicles(empsids)
        except:
            error_log("Error removing vehicle from Cityworks Employee: " + str(empsids))
    daily_assignments(cursor, token)

def add_vehicle(emp_sid, veh_id, cw_token):
    """ Assigns a vehicle to a user in Cityworks. """
    url = baseurl +  ('Ams/Employee/Update?data={"EmployeeSids": [' + emp_sid + '], "CustomFieldValues":{193610:"' + veh_id + '"}}&token=' + cw_token)
    response = requests.post(url).text
    try:
        json.loads(response)
    except:
        error_log("Error: Adding " + veh_id + " to " + emp_sid + " failed\n")
        return 0

def daily_assignments(cursor, token):
    """ Uses SQL to find the daily vehicle assignments. """
    cw_cursor = cursor
    try:
        cw_cursor.execute(os.getenv("daily_assignments_sql"))
        insp_list = cw_cursor.fetchall()

        for insp in insp_list:
            if insp[2] != '':
                add_vehicle(str(insp[1]), str(insp[0] + ', ' + insp[2]), token)
            else:
                add_vehicle(str(insp[1]), insp[0], token)
    except:
        error_log("Error: Daily Assignment Failed\n")

def daily_unassigned(cw_cursor):
    """ Uses SQL to find workgroup employees not assigned to a vehicle. """
    cw_cursor.execute(os.getenv("daily_unassigned_sql"))
    query = cw_cursor.fetchall()
    emp_list = np.array(query)
    wg_list = sorted(set(emp_list[:, 2]))
    emp_string = []
    emp_plain = []
    for wg in wg_list:
        emp_string.append('<h2>' + wg + '</h2><ul><p>')
        emp_plain.append("\t" + wg + "\n\n")
        wg_emp = emp_list[emp_list[:, 2] == wg]
        for emp in wg_emp:
            emp_string.append(emp[0] + " " + string.capwords(emp[1]) + '<br>')
            emp_plain.append(emp[0] + " " + string.capwords(emp[1]) + "\n")
        emp_string.append("</p></ul>")
        emp_plain.append("\n")

    if len(emp_string) > 0:
        try:
            final_plain = ''.join(str(x) for x in emp_plain)
            final_string = ''.join(str(x) for x in emp_string)
            email_send(final_string, final_plain, "Daily Unassigned")
        except:
            error_log("Issue saving file with errors.\n")