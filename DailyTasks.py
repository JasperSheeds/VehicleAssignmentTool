"""Tasks to initiate daily.

Day of week to number
    Monday = 0
    Tuesday = 1
    Wednesday = 2
    Thursday = 3
    Friday = 4
    Saturday = 5
    Sunday = 6

Change veh_audit_day to alter day of week the vehicle audit is pulled.
  Last updated by Jasper Sheeds 3/31/25"""

veh_audit_day = 2

from VehicleReset import daily_reset
from UpdateDrivers import get_assigned_vehicles, get_pairs, remove_operators
from WeeklyAudit import vehicle_usage
import datetime
from SupportFunctions import get_errors, return_token, cw_connections, email_send, error_log

today = datetime.datetime.now()
error_file = []
cw_token = None
cw_cursor = None

try:
    cw_token = return_token()
    cw_cursor = cw_connections()
except:
    error_log("Error: Connection could not be made to Cityworks.")

# reset operators and start first round of assigning
if cw_token is not None and cw_cursor is not None:
    daily_reset(today, cw_token, cw_cursor)
    remove_operators(get_assigned_vehicles())
    get_pairs([])

# if desired day, pull vehicles that have been driven outside operating hours
if today.weekday() == veh_audit_day:
    vehicle_usage(today)

# Any errors captured are sent in an email
if len(get_errors()) > 0:
    final_error = ''.join(str(x) for x in get_errors())
    email_send(final_error, final_error, "Vehicle Function Error")