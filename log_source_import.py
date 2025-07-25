import time
from contextlib import nullcontext
from time import sleep
import datetime
import os
import pandas as pd
import requests
import json
import base64
from functools import lru_cache
import urllib3
from urllib3.exceptions import InsecureRequestWarning, HTTPError

urllib3.disable_warnings(InsecureRequestWarning)
# QRadar API auth

USERNAME = ''
PASSWORD = ''
BASE_URL = ''  # replace QRadar  API URL
LOG = "import_logSource_log.txt"






def getcredentials():
    userpass = USERNAME.strip() + ':' + PASSWORD.strip()
    encoded_credentials = b'Basic ' + base64.b64encode(userpass.encode('ascii'))
    # print(encoded_credentials)
    return encoded_credentials

def add_log(message: str):
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, LOG)
    with open(log_file, "a") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log = f"[*] {timestamp} - {message}\n"
        f.write(log)





def createLogSource():
    file_path = './log_sources.xlsx'  # replace your excel file path
    df = pd.read_excel(file_path)
    success_count = 0
    fail_count = 0
    headers = {
        'Accept': 'application/json',
        'Authorization': getcredentials(),
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Content-Type':'application/json'
    }


    targetUrl = BASE_URL+'/api/config/event_sources/log_source_management/log_sources'

    for index, row in df.iterrows():
        if pd.isna(row['Description']) or len(row['Description']) == 0:
            description = str(f"IP : {row['IP']}")
        else:
            description = row['Description']

        log_source = {
                "group_ids": [get_log_source_groups_id(row['Device Group'])],
                "coalesce_events": False,
                "language_id": 1,
                "name": row['Log Source Name'],  # Log Source name
                "description": description,
                "type_id": get_log_source_type_id(row['Log Source Type']),
                "protocol_parameters": [
                    {
                        "name": "identifier",
                        "id": 0,
                        "value": row["Log Source Identifier"]
                    }
                ],
                "enabled": False,
                "protocol_type_id": 0,
            }





        sendData = requests.post(targetUrl, headers=headers,json=log_source,verify=False)

        if sendData.status_code == 201:
            print(f"Log Source '{log_source['name']}' Import Successfully.")

            add_log(f"Log Source '{log_source['name']}' Import Successfully.")
            success_count += 1

            # print("wait for 3 second ! ")
            sleep(3)

            # if success_count == 10:
            #     break
        else:

            print(f"[+] Log Source '{log_source['name']}' Import Error，Status: {sendData.status_code}, Error: {sendData.text}")
            add_log(f"[+] Log Source '{log_source['name']}' Import Error，Status: {sendData.status_code}, Error: {sendData.text}")
            fail_count += 1
            sleep(3)


    print(f'import success : {success_count}')
    print(f'import fail : {fail_count}')
    add_log(f"Import Success {success_count} records")
    add_log(f"Import Fail {fail_count} records")

def get_log_source_types():
    url = (
        BASE_URL
        + "/api/config/event_sources/log_source_management/log_source_types?fields=id,name"
    )
    headers = {"Accept": "application/json", "Authorization": getcredentials()}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == 200:
        add_log("Getting Log Source Types Metadata...")

        with open("log_source_types.json", "w", encoding="utf-8") as file:
            json.dump(resp.json(), file, indent=4, ensure_ascii=False)

        return resp.json()
    else:
        add_log(
            f"Status Code: {resp.status_code}, Failed to Get Log Source Types Metadata."
        )

def get_log_source_type_id(type_name):

    df = pd.read_json("./log_source_types.json")

    for name, id in zip(df['name'], df['id']):
        if name == type_name:

            return id

def get_log_source_groups():

    url = BASE_URL  + "/api/config/event_sources/log_source_management/log_source_groups?fields=name,id,child_group_ids"
    headers = {"Accept": "application/json", "Authorization": getcredentials()}
    resp = requests.get(url, headers=headers, verify=False)
    print(resp.json())
    with open("log_source_groups.json", "w", encoding="utf-8") as file:
        json.dump(resp.json(), file, indent=4, ensure_ascii=False)

    return resp.json()

def get_log_source_groups_id(group_name):

    df = pd.read_json("./log_source_groups.json")
    for name, id in zip(df['name'], df['id']):
        # if name == group_name and  child_group_ids is not None:
        if name == group_name:

            return id

def patchData():
    file_path = 'log_sources.xlsx'  # replace Excel file path
    df = pd.read_excel(file_path)
    success_count = 0
    fail_count = 0

    headers = {
        'Accept': 'text/plain',
        'Authorization': getcredentials(),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Content-Type': 'application/json'
    }
    for index, row in df.iterrows():
        log_source = [{

            # "description": row["status description"],
            "id": row["ID"],
            "description": row["Description"],
            "name": row["name"],
            # "protocol_parameters": [
            #         {
            #             "name": "identifier",
            #             "id": 0,
            #             "value": row["Log Source Identifier"]
            #         }
            #     ]
        }]
        print(log_source)
        targetUrl = BASE_URL + '/api/config/event_sources/log_source_management/log_sources'

        searchLogPart = requests.patch(targetUrl, headers=headers, json=log_source, verify=False)

        if searchLogPart.status_code == 202:
            print(f"Log Source 'log_source['name']' 修改成功！")
            sleep(2)
            # add_log("Log Source '{log_source['name']}' 修改成功！")
            success_count += 1

            # if success_count == 1:
            #     break
        else:

            print(
                f"Log Source 'log_source['name']' 修改失败，状态码: {searchLogPart.status_code}, 错误信息: {searchLogPart.text}")
            # if fail_count == 1:
            #     break
            # add_log("Log Source '{log_source['name']}' 修改失败，状态码: {sendData.status_code}, 错误信息: {sendData.text}")
            fail_count += 1
            # if fail_count == 1:
            #     break
    print(f"成功修改{success_count}条记录")
    print(f"修改失败{fail_count}条")

def main():
    if not os.path.exists("./log_source_types.json"):
        print(f"[*] No source_type file found and start to get source_type")
        get_log_source_types()
    if not os.path.exists("./log_source_groups.json"):
        print(f"[*] No source_groups file found and start to get source_type")
        get_log_source_groups()
    createLogSource()


# @lru_cache(maxsize=None)
# def get_id_by_name_with_cache(name):
#     with open("./log_source_groups.json", "r", encoding="utf-8") as file:
#         data = json.load(file)
#     for item in data:
#         if item['name'] == name:
#             return item['id']
#     return None



if __name__ == '__main__':
    # main()
    patchData()


