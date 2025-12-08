import time
from fastapi.responses import JSONResponse
import psycopg2
import os
import json
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from typing import Literal
from pydantic import BaseModel
load_dotenv()


def get_db_connection():
    conn = psycopg2.connect(
        host='localhost',
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    return conn


def get_info_indexed(parameter: str, value: str):
    '''
    Get info from indexed table
    '''
    conn = get_db_connection()
    cur = conn.cursor()
    start_time = time.time()
    cur.execute("SELECT * FROM big_data where %s = %s;" % (parameter, value,))
    rows = cur.fetchall()
    end_time = time.time()
    if len(rows) == 0:
        return f'No data in table big_data'
    if len(rows) > 5:
        rows = rows[:5] + [('...and more rows not displayed...',)]
    cur.close()
    conn.close()
    rows = list(rows)
    rows.append(f'Query time: {end_time - start_time} seconds')  # type: ignore
    return json.dumps(rows)


def get_info_non_indexed(parameter: str, value: str):
    '''
    Get info from the non-indexed table
    '''
    conn = get_db_connection()
    cur = conn.cursor()
    start_time = time.time()
    cur.execute("SELECT * FROM big_data_2 where %s = %s;" %
                (parameter, value,))
    rows = cur.fetchall()
    end_time = time.time()
    if len(rows) == 0:
        return f'No data in table big_data_2'
    if len(rows) > 5:
        rows = rows[:5] + [('...and more rows not displayed...',)]
    cur.close()
    conn.close()
    rows = list(rows)
    rows.append(f'Query time: {end_time - start_time} seconds')  # type: ignore
    return json.dumps(rows)


def get_info_indexed_multiple(parameter1: str, value1: str, parameter2: str, value2: str):
    '''
    Get info from indexed table with multiple conditions
    '''
    conn = get_db_connection()
    cur = conn.cursor()
    start_time = time.time()
    cur.execute("SELECT * FROM big_data where %s = %s AND %s = %s;" %
                (parameter1, value1, parameter2, value2,))
    rows = cur.fetchall()
    end_time = time.time()
    if len(rows) == 0:
        return f'No data in table big_data'
    if len(rows) > 5:
        rows = rows[:5] + [('...and more rows not displayed...',)]
    cur.close()
    conn.close()
    rows = list(rows)
    rows.append(f'Query time: {end_time - start_time} seconds')  # type: ignore
    return json.dumps(rows)


def get_info_non_indexed_multiple(parameter1: str, value1: str, parameter2: str, value2: str):
    '''
    Get info from non-indexed table with multiple conditions
    '''
    conn = get_db_connection()
    cur = conn.cursor()
    start_time = time.time()
    cur.execute("SELECT * FROM big_data_2 where %s = %s AND %s = %s;" %
                (parameter1, value1, parameter2, value2,))
    rows = cur.fetchall()
    end_time = time.time()
    if len(rows) == 0:
        return f'No data in table big_data_2'
    if len(rows) > 5:
        rows = rows[:5] + [('...and more rows not displayed...',)]
    cur.close()
    conn.close()
    rows = list(rows)
    rows.append(f'Query time: {end_time - start_time} seconds')  # type: ignore
    return json.dumps(rows)


class DBQuery(BaseModel):
    parameter: str
    value: str


class DBQueryMultiple(BaseModel):
    parameter1: str
    value1: str
    parameter2: str
    value2: str


class Message(BaseModel):
    message: str


app = FastAPI(title="Database API", description="Database API")


@app.post("/api/single/{name}", responses={404: {"model": Message}}, tags=["Database API"])
def call_tool(
    name: Literal["indexed", "non_indexed"],
    input: DBQuery  # Pydantic model will parse request JSON body
):
    tool_map = {
        "indexed": globals().get("get_info_indexed"),
        "non_indexed": globals().get("get_info_non_indexed"),
    }
    fn = tool_map.get(name)
    if fn is None:
        return JSONResponse(status_code=404, content={"message": f"{name} is not enabled"})
    return JSONResponse(status_code=200, content=fn(input.parameter, input.value))


@app.post("/api/multiple/{name}", responses={404: {"model": Message}}, tags=["Database API"])
def call_tool_multiple(
    name: Literal["indexed", "non_indexed"],
    input: DBQueryMultiple  # Pydantic model will parse request JSON body
):
    tool_map = {
        "indexed": globals().get("get_info_indexed_multiple"),
        "non_indexed": globals().get("get_info_non_indexed_multiple"),
    }
    fn = tool_map.get(name)
    if fn is None:
        return JSONResponse(status_code=404, content={"message": f"{name} is not enabled"})
    return JSONResponse(status_code=200, content=fn(input.parameter1, input.value1, input.parameter2, input.value2))
