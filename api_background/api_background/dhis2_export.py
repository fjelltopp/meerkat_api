import requests
import json

from datetime import date

from export_data import __get_keys_from_db
from util import get_db_engine
from meerkat_abacus.model import form_tables


def clear_old_events(program_id, org_unit_id):
    events_id_list = []
    res = requests.get("{}events?program={}&orgUnit={}&skipPaging=true".format(api_url, program_id, org_unit_id), auth=credentials)
    # res = requests.get("{}events?program={}&orgUnit={}&pageSize={}&page={}".format(api_url, program_id, org_unit_id, 100, index), auth=credentials)
    results = res.json()
    for result in results["events"]:
        event_id = result['event']
        events_id_list.append({'event' : event_id})
    delete_json = json.dumps({"events" : events_id_list})
    a_delete = requests.post("{}events?strategy=DELETE".format(api_url), data=delete_json, headers=headers)
    print("Deleted old events with status {}".format(a_delete.status_code))


def update_data_elements(key, headers):
    payload = {}
    payload['name'] = key
    payload['shortName'] = key
    payload['domainType'] = 'TRACKER'
    payload['valueType'] = 'TEXT'
    payload['aggregationType'] = 'NONE'
    json_payload = json.dumps(payload)

    post_res = requests.post("{}dataElements".format(api_url), data=json_payload, headers=headers)
    json_res = post_res.json()
    # print(post_res.status_code)
    # print(post_res.text)
    uid = json_res['response']['uid']
    print("Created data element \"{}\" with uid: {}".format(key, uid))
    return uid


def prepare_data_values(keys, dhis_keys, data):
    data_values = []
    for key in keys:
        # if key in ["vaccination_type", "national"]:
        #     TODO: vaccination & vaccination_type give the same first result!!!
            # continue
        if key in data.keys():
            data_values.append({'dataElement': dhis_keys[key], 'value': data[key]})
    return data_values


def get_dhis2_keys(url, credentials, headers, keys):
    result = {}
    dhis2_data_elements_res = requests.get("{}dataElements".format(url), auth=credentials)
    dhis2_data_elements = dhis2_data_elements_res.json()['dataElements']
    data_elements_ids = []
    data_elements_names = []
    for d in dhis2_data_elements:
        data_elements_ids.append(d['id'])
        data_elements_names.append(d['displayName'])
    data_element_lookup = dict(zip(data_elements_names, data_elements_ids))
    for key in keys:
        if key in data_element_lookup:
            dhis_key_id = data_element_lookup[key]
        else:
            update_data_elements([key], headers)
        result[key] = dhis_key_id
    return result


def send_events_batch(payload_list):
    payload = {}
    payload['events'] = payload_list
    json_event_payload = json.dumps(payload)
    s = requests.session()
    event_res = s.post("{}events".format(api_url), headers=headers, data=json_event_payload)
    print(event_res.status_code)
    print(event_res.text)


if __name__ == "__main__":
    form = "demo_case"
    url = "http://54.76.53.0:8080"
    api_resource = "/api/26/"
    api_url = url + api_resource
    credentials = ('admin', 'district')
    headers = {"Content-Type": "application/json", "Authorization": "Basic YWRtaW46ZGlzdHJpY3Q="}

    db, session = get_db_engine()
    keys = __get_keys_from_db(db, form)
    dhis_keys = get_dhis2_keys(api_url, credentials, headers, keys)

    # TODO: for now only hardocded will be done in a more elegant way
    program_id = 'ZU7Z7ouwbba'
    # program_id = 'T6VaKGprnc5'
    # program_id_req = requests.get("{}programs?query={}".format(api_url, form), auth=credentials)
    # program_id = list(program_id_req.json()['programs'][0].values())[0]
    org_unit_id = 'wZxJHG0MUNz' # TODO: What is orgUnit in DHIS2 in WHO context?
    str_today = date.today().strftime("%Y-%m-%d")
    status = 'COMPLETED'
    stored_by = 'admin'

    clear_old_events(program_id, org_unit_id)

    data_values = []
    results = session.query(form_tables[form].data).all()

    event_payload_list = []
    for counter, result in enumerate(results):
        event_payload = {}
        data_values = prepare_data_values(keys, dhis_keys, result.data)

        event_payload['dataValues'] = data_values
        event_payload['program'] = program_id
        event_payload['orgUnit'] = org_unit_id
        event_payload['eventDate'] = str_today
        event_payload['completedDate'] = str_today
        event_payload['dataValues'] = data_values
        event_payload['status'] = status

        event_payload_list.append(event_payload)
        if counter % 100 == 0:
            send_events_batch(event_payload_list)
            event_payload_list = []
    send_events_batch(event_payload_list)



