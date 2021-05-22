"""
TrueConf PRTG Monitoring sensor [v1.0]
    Ivan T (https://www.sys-admin.su)

Docs:
https://developers.trueconf.ru/api/server/
https://www.paessler.com/manuals/prtg/custom_sensors
"""

import json
import requests
import urllib3
import datetime
import re
from sys import argv


def make_request(path, params):
    """
    Pass request to API
    """
    url = api_server + path
    header = {'Content-Type': 'application/json'}
    param = {'access_token': api_token}
    if params:
        param = {**param, **params}
    try:
        r = requests.get(url, headers=header, params=param, verify=False)
    except Exception as err:
        return_error("Python runtime error. Message: {}".format(err.args[0]))
    else:
        if r.status_code == 200:
            return {'error': False, 'data': r}
        else:
            return_error("HTTP Request error. Error message {}".format(r.text))


def get_users():
    """
    Get user list
    https://developers.trueconf.ru/api/server/#api-Users-GetUserList
    """
    req = make_request("users", None)
    data = json.loads(req['data'].text)
    users = data['users']
    while data['next_page_id'] != -1:
        data = json.loads(req['data'].text)
        req = make_request("users", {"page_id": data['next_page_id']})
        users = users + json.loads(req['data'].text)['users']
    users_offline = []
    users_online = []
    for user in users:
        if user['status'] == 0:
            # 0: OFFLINE
            users_offline.append(user)
        if user['status'] == 1 or user['status'] == 2 or user['status'] == 5:
            # 1: ONLINE; 2: BUSY; 5: MULTIHOST
            users_online.append(user)
    return {'error': False,
            'users_offline': len(users_offline),
            'users_online': len(users_online)}


def get_conferences(raw):
    """
    Get active conferences list
    https://developers.trueconf.ru/api/server/#api-Conferences-GetConferenceList
    """
    param = {'page_size': 300}
    req = make_request("conferences", param)
    data = json.loads(req['data'].text)
    conferences = data['conferences']
    page = 1
    while len(conferences) < data['cnt']:
        page += 1
        param = {"page_id": page, 'page_size': 300}
        req = make_request("conferences", param)
        conferences = conferences + json.loads(req['data'].text)['conferences']
    conferences_stopped = []
    conferences_running = []
    for conference in conferences:
        if conference['state'] == "running":
            conferences_running.append(conference)
        if conference['state'] == "stopped":
            conferences_stopped.append(conference)
    if raw:
        return {'error': False,
                'conferences_total': len(conferences),
                'conferences_running': len(conferences_running),
                'conferences_stopped': len(conferences_stopped)}
    if not raw:
        return {'error': False,
                'conferences_total': conferences,
                'conferences_running': conferences_running,
                'conferences_stopped': conferences_stopped}


def get_conf_users():
    """
    Get total guests list
    https://developers.trueconf.ru/api/server/#api-Conferences_Participants-GetParticipantList
    """
    conferences = get_conferences(raw=False)
    guests = []
    users = []
    if len(conferences['conferences_running']) > 0:
        for conf in conferences['conferences_running']:
            req = make_request("conferences/{}/participants".format(conf['id']), None)
            participants = json.loads(req['data'].text)['participants']
            for participant in participants:
                # also can check for conf['allow_guests']
                if re.match(r'#guest.*@', participant['id']):
                    guests.append(participant)
                else:
                    users.append(participant)
    return {'error': False,
            'total_users': len(guests) + len(users),
            'users': len(users),
            'guests': len(guests)}


def get_eventlog(time_min):
    """
    Get event log
    https://developers.trueconf.ru/api/server/#api-Logs-GetEventList

    notes:
    - 1000 is maximum page size
    - default page is 1, not 0
    """
    dt_now = datetime.datetime.now().strftime("%Y-%d-%m %H:%M:%S")
    dt_target = (datetime.datetime.now() - datetime.timedelta(minutes=time_min)).strftime("%Y-%m-%d %H:%M:%S")

    # Get total log (can take a long time)
    param = {'date_from': dt_target,
             'date_to': dt_now,
             'timezone': 180,
             'page_size': 1000}
    req = make_request("logs/events", param)
    data = json.loads(req['data'].text)
    log_events = data['list']
    page = 1
    while len(log_events) < data['cnt']:
        page += 1
        param = {'date_from': dt_target,
                 'date_to': dt_now,
                 'timezone': 180,
                 'page_size': 1000,
                 "page_id": page}
        req = make_request("logs/events", param)
        log_events = log_events + json.loads(req['data'].text)['list']
    user_login_errors = []
    admin_login_errors = []
    if len(log_events) > 0:
        for event in log_events:
            if event['event_type'] == "login":
                if event['object_type'] == "admin" and not event['payload']['result'] == "0":
                    admin_login_errors.append(event)
                if event['object_type'] == "user":
                    if 'error' in event['payload']:
                        user_login_errors.append(event)
    return {'error': False,
            'admin_login_errors': len(admin_login_errors),
            'user_login_errors': len(user_login_errors)}


def return_error(msg):
    """
    Returns JSON encoded error to PRTG backend
    """
    prtg_dict = {"prtg": {"error": 1, "text": msg}}
    print(json.dumps(prtg_dict))
    exit()


def main():
    """
    Main loop
    """
    prtg_dict = {"prtg": {"result": []}}
    # Online, offline and total users
    users = get_users()
    if not users['error']:
        prtg_dict["prtg"]["result"].append({"channel": "Пользователей онлайн",
                                                "value": users['users_online'],
                                                "float": 0,
                                                "limitmode": 1})
        prtg_dict["prtg"]["result"].append({"channel": "Пользователей офлайн",
                                                "value": users['users_offline'],
                                                "float": 0,
                                                "limitmode": 1})

    # Conferences - list and active/not active
    conferences = get_conferences(raw=True)
    if not conferences['error']:
        prtg_dict["prtg"]["result"].append({"channel": "Конференций всего",
                                                "value": conferences['conferences_total'],
                                                "float": 0,
                                                "limitmode": 1})
        prtg_dict["prtg"]["result"].append({"channel": "Конференций запущено",
                                            "value": conferences['conferences_running'],
                                            "float": 0,
                                            "limitmode": 1})
        prtg_dict["prtg"]["result"].append({"channel": "Конференций остановлено",
                                            "value": conferences['conferences_stopped'],
                                            "float": 0,
                                            "limitmode": 1})

    # Users and guests in conferences
    conference_users = get_conf_users()
    if not conference_users['error']:
        prtg_dict["prtg"]["result"].append({"channel": "Участников в конференциях всего",
                                                "value": conference_users['total_users'],
                                                "float": 0,
                                                "limitmode": 1})
        prtg_dict["prtg"]["result"].append({"channel": "Пользователей в конференциях",
                                            "value": conference_users['users'],
                                            "float": 0,
                                            "limitmode": 1})
        prtg_dict["prtg"]["result"].append({"channel": "Гостей в конференциях",
                                            "value": conference_users['guests'],
                                            "float": 0,
                                            "limitmode": 1})

    # Errors in 5 min
    log_errors = get_eventlog(5)
    if not log_errors['error']:
        prtg_dict["prtg"]["result"].append({"channel": "Ошибок авторизации в пользовательской части, за 5 минут",
                                                "value": log_errors['user_login_errors'],
                                                "float": 0,
                                                "limitmode": 1})
        prtg_dict["prtg"]["result"].append({"channel": "Ошибок авторизации в панели администратора, за 5 минут",
                                            "value": log_errors['admin_login_errors'],
                                            "float": 0,
                                            "limitmode": 1})
    # Errors in 1 min
    log_errors = get_eventlog(1)
    if not log_errors['error']:
        prtg_dict["prtg"]["result"].append({"channel": "Ошибок авторизации в пользовательской части, за 1 минуту",
                                                "value": log_errors['user_login_errors'],
                                                "float": 0,
                                                "limitmode": 1})
        prtg_dict["prtg"]["result"].append({"channel": "Ошибок авторизации в панели администратора, за 1 минуту",
                                            "value": log_errors['admin_login_errors'],
                                            "float": 0,
                                            "limitmode": 1})

    return prtg_dict


if __name__ == '__main__':
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)     # disable certificate related warnings
    try:
        if len(argv) == 5:
            api_token = argv[1]
            api_server = 'https://{}:{}/api/v{}/'.format(argv[2], argv[3], argv[4])
        else:
            return_error("Argument error")
    except Exception as e:
        return_error("Python runtime error. Message: {}".format(e.args[0]))
    else:
        print(json.dumps(main()))
    finally:
        pass
