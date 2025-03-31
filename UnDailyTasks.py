"""Tasks to initiate multiple times a day.

Inspection time cap is used to note vehicles that have not received an inspection for
the day, as well as to pull a daily list of concerns found in vehicle inspections.
Change insp_cap_hour and insp_cap_min to alter time inspection cap is.

  Last updated by Jasper Sheeds 3/28/25"""

insp_cap_hour = 8
insp_cap_min = 45

from datetime import datetime
from Concerns import daily_concerns
from SupportFunctions import return_token, cw_connections, get_errors, email_send
from UpdateDrivers import get_assigned_vehicles, get_pairs
from VehicleReset import daily_assignments, daily_unassigned

today = datetime.now()
insp_time_cap = today.replace(hour=insp_cap_hour, minute=insp_cap_min)
error_file = []
cw_token = None
cw_cursor = None

if today.weekday() < 5:
    cw_token = return_token()
    cw_cursor = cw_connections()

# Assigns vehicles
if today.weekday() < 5 and today <= insp_time_cap and cw_token is not None and cw_cursor is not None:
    daily_assignments(cw_cursor, cw_token)
    get_pairs(get_assigned_vehicles())

# Assigns vehicles, tracks unassigned vehicles, and vehicle concerns
elif today.weekday() < 5 and today > insp_time_cap and cw_token is not None and cw_cursor is not None:
    daily_assignments(cw_cursor, cw_token)
    get_pairs(get_assigned_vehicles())
    daily_unassigned(cw_cursor)
    daily_concerns(cw_cursor)

# Any errors captured are sent in an email
if len(get_errors()) > 0:
    final_error = ''.join(str(x) for x in get_errors())
    email_send(final_error, final_error, "Vehicle Function Error")