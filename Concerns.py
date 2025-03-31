""" Program runs a SQL query on inspections and finds concerns to report
 Changes last made by Jasper Sheeds 3/28/25 """

from SupportFunctions import email_send, error_log
from dotenv import load_dotenv
import os

global insp_text
global plain_text
insp_text = []
plain_text = []
load_dotenv()
daily_concerns_sql = os.getenv("daily_concerns_sql")

def daily_concerns(cursor):
    """ Gets concerns daily. """
    cw_cursor = cursor
    try:
        cw_cursor.execute(daily_concerns_sql)
        inspections = cw_cursor.fetchall()
        insp_text.append("""<style> h1 {font-size:25px; font-family: Arial, sans-serif; text-align: center;} th {font-size:20px; font-family: Arial, sans-serif; text-align: left;} tr {font-size:15px; font-family: Arial, sans-serif; text-align: center;} tr:hover {background-color: #e0f1ff;}th,td {padding: 3px;} </style><h1>Vehicle Concerns</h1><style>table, th, td {}</style><body><table style="width:100%"> <tr><th>Truck</th><th>Concern</th></tr>""")
        plain_text.append("Truck\tConcern\n")
        for truck in inspections:
            text_line = """<tr><td>""" + str(truck[0]) + "</td><td>"
            insp_text.append(text_line)
            plain_text.append(str(truck[0]) + "\t")
            insp = truck[1].split(', ')
            for x, issue in enumerate(insp):
                if x == len(insp)-1:
                    insp_text.append(issue + "</td></tr>")
                    plain_text.append(issue + "\n")
                else:
                    insp_text.append(issue + "<br>")
                    plain_text.append(issue + ", ")

        insp_text.append("</table></body>")
        final_string = ''.join(str(x) for x in insp_text)
        final_plain = ''.join(str(x) for x in plain_text)
        email_send(final_string, final_plain, "Vehicle Concerns")
    except:
        error_log("Error getting daily vehicle concerns.")