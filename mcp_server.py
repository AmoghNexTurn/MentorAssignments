from datetime import datetime
import os
import json
import sys
import config
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import psycopg2
import hashlib

load_dotenv()

# Create an MCP server
mcp = FastMCP("MCP Server")

def get_db_connection():
    conn = psycopg2.connect(
        host='db',
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    return conn

def slot_not_inside(slots1, slots2):
    for i in range(7):
        if slots1[i][0] == -1 and slots1[i][1] == -1:
            continue
        if not (slots2[i][0] <= slots1[i][0] <= slots1[i][1] <= slots2[i][1]):
            return True
    return False

def slot_overlap(slots1, slots2):
    for i in range(7):
        if (slots1[i][0] == -1 and slots1[i][1] == -1) or (slots2[i][0] == -1 and slots2[i][1] == -1):
            continue
        if (slots2[i][0] <= slots1[i][0] <= slots2[i][1]) or (slots2[i][0] <= slots1[i][1] <= slots2[i][1]):
            return True
    return False

def date_overlap(start_date1, end_date1, start_date2, end_date2):
    return start_date1 <= end_date2 and start_date2 <= end_date1

def conflict(StartDate: str, EndDate: str, HoursBooked: list, WorkerName: str) -> bool:
    """Function to check for conflicts in bookings"""
    for h in range(len(HoursBooked)):
        if len(HoursBooked[h]) == 0:
            HoursBooked[h] = [-1, -1]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("Select AvailableHours from availability where WorkerName = %s;", (WorkerName,))
    availability = cur.fetchone()[0]
    if len(availability) != 0:
        if slot_not_inside(HoursBooked, availability):
            return True
    cur.execute("SELECT StartDate, EndDate, HoursBooked from bookings where WorkerName = %s;", (WorkerName,))
    bookings = cur.fetchall()
    if len(bookings) != 0:
        StartDate = datetime.strptime(StartDate, '%Y%m%d').date()
        EndDate = datetime.strptime(EndDate, '%Y%m%d').date()
        for b in bookings:
            if date_overlap(StartDate, EndDate, b[0], b[1]) and slot_overlap(HoursBooked, b[2]):
                print("Conflict with booking:", b, StartDate, EndDate, HoursBooked)
                return True
    return False

@mcp.tool()
def get_info(table: str):
    '''
    Get info from a table
    '''
    conn = get_db_connection()
    cur = conn.cursor()
    if table != "users": 
        cur.execute("SELECT * FROM %s;" % (table,))
    else:
        cur.execute("SELECT UserID, UserName, UserType, Classification from users;")
    rows = cur.fetchall()
    if len(rows) == 0:
        return f'No data in table {table}'
    cur.close()
    conn.close()
    # for r in rows:
    #     for d in r:
    #         if isinstance(d, datetime):
    #             d = d.strftime("%Y%m%d")
    return json.dumps(rows, indent=4, default=str)

@mcp.tool()
def add_user(UserName: str, UserPassword: str, UserType: str, Classification: str) -> str:
    '''
    Function to add a user to the users table
    '''
    encoded_string = UserPassword.encode('utf-8')
    sha256_hash = hashlib.sha256()
    sha256_hash.update(encoded_string)
    UserPassword_hashed = sha256_hash.hexdigest()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (UserName, UserPassword, UserType, Classification) VALUES (%s, %s, %s, %s);", (UserName, UserPassword_hashed, UserType, Classification))
    conn.commit()
    cur.close()
    conn.close()
    return 'User added successfully'

@mcp.tool()
def add_booking(BidderName: str, WorkerName: str, StartDate: str, EndDate: str, HoursBooked: list, HourlyRate: str) -> str:
    '''
    Function to add a booking to the bookings table.
    StartDate and EndDate should be in YYYYMMDD format.
    HoursBooked should be a 7x2 list of integers. For example, [[9,17], [], [], [], [], [10,16], []] means monday 9am to 5pm and and saturday 10 am to 4pm.
    '''
    for h in range(len(HoursBooked)):
        if len(HoursBooked[h]) == 0:
            HoursBooked[h] = [-1, -1]
    conn = get_db_connection()
    cur = conn.cursor()
    if conflict(StartDate, EndDate, HoursBooked, WorkerName):
        return 'Booking conflict detected'
    cur.execute("INSERT INTO bookings (BidderName, WorkerName, StartDate, EndDate, HoursBooked, HourlyRate) VALUES (%s, %s, %s, %s, %s, %s);", (BidderName, WorkerName, StartDate, EndDate, HoursBooked, HourlyRate))
    conn.commit()
    cur.close()
    conn.close()
    return 'Booking added successfully'

@mcp.tool()
def add_bid(BidderName: str, WorkerName: str, StartDate: str, EndDate: str, HoursBooked: list, HourlyRate: str) -> str:
    '''
    Function to add a bid to the bids table.
    StartDate and EndDate should be in YYYYMMDD format. If it is not, do it yourself.
    HoursBooked should be a 7x2 list of integers. For example, [[9,17], [], [], [], [], [10,16], []] means monday 9am to 5pm and and saturday 10 am to 4pm.
    '''
    for h in range(len(HoursBooked)):
        if len(HoursBooked[h]) == 0:
            HoursBooked[h] = [-1, -1]
    conn = get_db_connection()
    cur = conn.cursor()
    if conflict(StartDate, EndDate, HoursBooked, WorkerName):
        return 'Booking conflict detected'
    cur.execute("INSERT INTO bids (BidderName, WorkerName, StartDate, EndDate, HoursBooked, HourlyRate) VALUES (%s, %s, %s, %s, %s, %s);", (BidderName, WorkerName, StartDate, EndDate, HoursBooked, HourlyRate))
    conn.commit()
    cur.close()
    conn.close()
    return 'Bid added successfully'

@mcp.tool()
def add_availability(WorkerName: str, AvailableHours: list) -> str:
    '''
    This function is called alongside add_user when a worker type user is added. It doesn't need to be called explicitly.
    Function to add availability to the availability table when a worker type user adds their available hours.
    AvailableHours should be a 7x2 list of integers. For example, [[9,17], [], [], [], [], [10,16], []] means monday 9am to 5pm and and saturday 10 am to 4pm.
    '''
    for h in range(len(AvailableHours)):
        if len(AvailableHours[h]) == 0:
            AvailableHours[h] = [-1, -1]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO availability (WorkerName, AvailableHours) VALUES (%s, %s);", (WorkerName, AvailableHours))
    conn.commit()
    cur.close()
    conn.close()
    return 'Availability added successfully'

@mcp.tool()
def check_availability(classification: str, StartDate: str, EndDate: str, HoursBooked: list) -> str:
    '''
    Function to check availability of workers based on Classification and HourBooked.
    StartDate and EndDate should be in YYYYMMDD format.
    HoursBooked should be a 7x2 list of integers. For example, [[9,17], [], [], [], [], [10,16], []] means monday 9am to 5pm and and saturday 10 am to 4pm.
    '''
    for h in range(len(HoursBooked)):
        if len(HoursBooked[h]) == 0:
            HoursBooked[h] = [-1, -1]
        else:
            HoursBooked[h] = [int(HoursBooked[h][0]), int(HoursBooked[h][1])]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT UserName from users where usertype='worker' and classification = %s;", (classification,))
    workers = cur.fetchall()
    for w in workers:
        name = w[0]
        if conflict(StartDate, EndDate, HoursBooked, name):
            workers.remove(w)
    conn.commit()
    cur.close()
    conn.close()
    if len(workers) == 0:
        return 'No workers available'
    return json.dumps(workers)

@mcp.tool()
def choose_bid(WorkerName: str) -> str:
    '''
    Function to accept the highest bid of a user and to add to the bookings table.
    '''
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bids where workername = %s order by hourlyrate desc;", (WorkerName,))
    bid = cur.fetchone()
    if not bid:
        return f'There are no bids for user {WorkerName}'
    BidderName = bid[1]
    StartDate = bid[3].strftime("%Y%m%d")
    EndDate = bid[4].strftime("%Y%m%d")
    HoursBooked = bid[5]
    HourlyRate = bid[6]
    cur.execute("INSERT INTO bookings (BidderName, WorkerName, StartDate, EndDate, HoursBooked, HourlyRate) VALUES (%s, %s, %s, %s, %s, %s);", (BidderName, WorkerName, StartDate, EndDate, HoursBooked, HourlyRate))
    cur.execute("DELETE FROM BIDS where workername = %s;", (WorkerName,))
    conn.commit()
    cur.close()
    conn.close()
    return str(bid)

@mcp.tool()
def hourly_bid_accept() -> str:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username from users where usertype='worker';")
    workers = cur.fetchall()
    for w in workers:
        choose_bid(w[0])
    return "Processed all bids"

if __name__ == "__main__":
    mcp.run(transport="stdio")