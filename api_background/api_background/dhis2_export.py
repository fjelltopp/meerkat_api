import requests
import json
from time import sleep

from datetime import date

from export_data import __get_keys_from_db
from util import get_db_engine
from meerkat_abacus.model import form_tables

if __name__ == "__main__":
    form = "demo_case"
    db, session = get_db_engine()
    keys = __get_keys_from_db(db, form)
    url = "http://54.76.53.0:8080"
    api_resource = "/api/26/"
    api_url = url + api_resource
    credentials = ('admin', 'district')
    headers = {"Content-Type": "application/json", "Authorization": "Basic YWRtaW46ZGlzdHJpY3Q="}

    # TODO: for now only hardocded will be done in a more elegant way
    program_id = 'ZU7Z7ouwbba'
    # program_id_req = requests.get("{}programs?query={}".format(api_url, form), auth=credentials)
    # program_id = list(program_id_req.json()['programs'][0].values())[0]
    org_unit_id = 'wZxJHG0MUNz' # TODO: What is orgUnit in DHIS2 in WHO context?

    # removing previously stored events
    res = requests.get("{}events?program={}&orgUnit={}".format(api_url, program_id, org_unit_id), auth=credentials)
    results = res.json()
    for result in results["events"]:
        event_id = result['event']
        a_delete = requests.delete("{}events/{}".format(api_url, event_id), auth=credentials)
        print("Deleted event {} with status {}".format(event_id, a_delete.status_code))
    for key in keys:
        continue
        res = requests.get("{}dataElements?query={}".format(api_url, key), auth=credentials)
        json_body = json.loads(res.text)
        if int(json_body['pager']['total']) == 0:
            payload = {}
            payload['name'] = key
            payload['shortName'] = key
            payload['domainType'] = 'TRACKER'
            payload['valueType'] = 'TEXT'
            payload['aggregationType'] = 'NONE'
            json_payload = json.dumps(payload)

            post_res = requests.post("{}dataElements".format(api_url), data=json_payload, headers=headers)
            print(post_res.status_code)
            print(post_res.text)

    data_values = []
    results = session.query(form_tables[form].data).all()

    event_payload_list = []
    for counter, result in enumerate(results):
        event_payload = {}
        data_values = []
        data = result.data
        s2 = requests.session()
        print("Preparing event {}".format(str(counter)))
        for key in keys:
            if key in ["vaccination_type", "national"]:
                continue
            key_dhis_id_req = s2.get("{}dataElements?query={}".format(api_url, key), auth=credentials)
            dhis_key_id = key_dhis_id_req.json()['dataElements'][0]['id']
            _temp = {}
            if key in data.keys():
                # data_values.append({'dataElement' : dhis_key_id, 'value' : key + "_" + str(counter)})
                data_values.append({'dataElement' : dhis_key_id, 'value' : data[key]})
        event_payload['dataValues'] = data_values
        str_today = date.today().strftime("%Y-%m-%d")
        status = 'COMPLETED'
        stored_by = 'admin'

        event_payload['program'] = program_id
        event_payload['orgUnit'] = org_unit_id
        event_payload['eventDate'] = str_today
        event_payload['completedDate'] = str_today
        event_payload['dataValues'] = data_values
        event_payload['status'] = status

        event_payload_list.append(event_payload)

    payload = {}
    payload['events'] = event_payload_list
    json_event_payload = json.dumps(payload)

    s = requests.session()
    event_res = s.post("{}events".format(api_url), headers=headers, data=json_event_payload)
    print(event_res.status_code)
    print(event_res.text)







    # res = requests.get("%s%sdataElements" % (url, api_resource), auth=credentials)
    # print(res.status_code)
    # print(res.text)
