# Read Me
A tool to update Vehicle Assignments on Cityworks and Calamp. Also sends out unassigned employees, issues found in daily vehicle inspections, and vehicles that operated outside of business hours.

*SQL queries, keys, and account numbers removed for security purposes.*

To run, daily and undaily tasks should be called in a scheduler. Daily should be triggered once a day before undaily. Undaily should be triggered multiple times on a regular basis; for example once every fifteen minutes.

Operating hours, reset hours, days run can be updated for the files. Look for information within the files to find more information on what to change. 

### A list of what is inside the .env file:
-APPKEY = Calamp application key
-USERINFO = username=CALAMPUSERNAME&password=CALAMPPASSWORD
-cw_username=Cityworks Username
-cw_password=Cityworks Password
-email_from= email address that the emails are sent from
-email_to= email address that the emails are sent to
-email_pass= email password for the email address that the emails are sent from (I used an application password with gmail)
-base_url_calamp=calamp base url
-base_url_cw=cityworks base url
-cal_account= calamp account id
-holidays = list of holidays outside of business hours format ex.-('2024-01-01', '2024-01-15', '2024-03-29', '2024-04-27')
-cw_connection= connection string for cityworks sql server
-daily_concerns_sql= SQL Query that grabs an EntityUID, and a response to each of the vehicle concerns from a pre-trip inspection. 
-get_pairs_sql =-SQL Query that grabs an EntityUID and an EmployeeId from pretrip inspections based on filters that narrow employees down to employees that are not currently assigned to the Entity listed in their pre-trip inspection. 
-create_driver_sql = SQL Query that grabs workgroup, first name, and last name from cityworks filtered by added employee id 
-daily_reset_sql=SQL Query that grabs employee id filtered by employees that have vehicles assigned to it
-daily_assignments_sql = SQL Query that grabs EntityUID, EmployeeSID, filtered by employees where current assigned vehicle does not include current entity in pretrip inspection. 
-daily_unassigned_sql= SQL Query that grabs Employee ID, Employee Name, Employee Workgroup Filtered by employees without vehicle assigned to them


For assistance writing SQL queries for the program visit [BeamAndStream](beamandstream.com) for a quote.
