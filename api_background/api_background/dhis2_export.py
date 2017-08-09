import requests
import json
import logging

from datetime import date

from _populate_locations import populate_row_locations, set_empty_locations
from export_data import __get_keys_from_db
from util import get_db_engine, all_location_data, is_child
from meerkat_abacus.model import form_tables
from meerkat_abacus.config import dhis2_config

codes_to_ids = {}
#TODO: id_list = "http://54.76.53.0:8080/api/26/system/id.json?limit=100"

def get_dhis2_ids(n=100):
    result = requests.get("{}system/id.json?limit={}".format(api_url, n)).json().get('codes', [])
    if not result:
        logging.error("Could not get ids from DHIS2.")
    return result

def clear_old_events(program_id, org_unit_id):
    events_id_list = []
    res = requests.get("{}events?program={}&orgUnit={}&skipPaging=true".format(api_url, program_id, org_unit_id),
                       auth=credentials)
    results = res.json()
    for result in results["events"]:
        event_id = result['event']
        events_id_list.append({'event': event_id})
    delete_json = json.dumps({"events": events_id_list})
    a_delete = requests.post("{}events?strategy=DELETE".format(api_url), data=delete_json, headers=headers)
    print("Deleted old events with status {}".format(a_delete.status_code))


def update_data_elements(key, headers):
    payload = {'name': key, 'shortName': key, 'domainType': 'TRACKER', 'valueType': 'TEXT', 'aggregationType': 'NONE'}
    json_payload = json.dumps(payload)
    post_res = requests.post("{}dataElements".format(api_url), data=json_payload, headers=headers)
    json_res = post_res.json()
    uid = json_res['response']['uid']
    print("Created data element \"{}\" with uid: {}".format(key, uid))
    return uid


def prepare_data_values(keys, dhis_keys, data, form_config):
    data_values = []
    organisation_code = None
    # Add the location data if it has been requested and exists.
    for key in keys:
        if 'deviceid' in data:
            clinic_id = locs_by_deviceid.get(data["deviceid"], None)
            populate_row_locations(data, keys, clinic_id, location_data, use_integer_keys=False)
            organisation_code = locations[clinic_id].country_location_id

        else:
            set_empty_locations(keys, data_values)
        if key in data.keys():
            data_values.append({'dataElement': dhis_keys[key], 'value': data[key]})
    str_today = date.today().strftime("%Y-%m-%d")
    eventDate = data.get(form_config['event_date'], str_today)
    completedDate = data.get(form_config['completed_date'], str_today)
    return data_values, eventDate, completedDate, organisation_code


def get_dhis2_keys(url, credentials, headers, keys):
    result = {}
    dhis2_data_elements_res = requests.get("{}dataElements?skipPaging=True".format(url), auth=credentials)
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
            dhis_key_id = update_data_elements([key], headers)
        result[key] = dhis_key_id
    return result


def send_events_batch(payload_list):
    payload = {}
    payload['events'] = payload_list
    json_event_payload = json.dumps(payload)
    s = requests.session()
    event_res = s.post("{}events".format(api_url), headers=headers, data=json_event_payload)
    logging.info("Send batch of events with status: %d", event_res.status_code)
    logging.info(event_res.text)


def get_dhis2_organisations():
    result = {}
    dhis2_organisations_res = requests.get("{}organisationUnits?skipPaging=True".format(api_url), auth=credentials)
    dhis2_organisations = dhis2_organisations_res.json()['organisationUnits']
    for d in dhis2_organisations:
        res = requests.get("{}organisationUnits/{}".format(api_url, d['id']), auth=credentials)
        organisation_code = res.json().get('code', None)
        result[organisation_code] = d['id']
    return result


def populate_dhis2_locations(locations, zones, regions, districts):
    dhis2_organisations_res = requests.get("{}organisationUnits".format(api_url), auth=credentials)
    organisation_units = dhis2_organisations_res.json()['organisationUnits']
    organisation_ids = []
    organisation_names = []
    organisation_codes = []
    for d in organisation_units:
        organisation_ids.append(d['id'])
        organisation_names.append(d['displayName'])

        res = requests.get("{}organisationUnits/{}".format(api_url, d['id']), auth=credentials)
        organisation_code = res.json().get('code', None)
        organisation_codes.append(organisation_code)

    # http://54.76.53.0:8080/api/26/organisationUnits?filter=code:eq:unique_code
    for zone_index in zones:
        create_dhis2_organisation(locations[zone_index])

    for district_index in districts:
        create_dhis2_organisation(locations[district_index])

    for region_index in regions:
        create_dhis2_organisation(locations[region_index])

    for location in locations.values():
        if location.level == 'clinic':
            create_dhis2_organisation(location)


def create_dhis2_organisation(_location):
    if _location.start_date:
        opening_date = _location.start_date.strftime("%Y-%m-%d")
    else:
        opening_date = "1970-01-01"
    name = _location.name
    organisation_code = _location.country_location_id
    json_res = requests.get("{}organisationUnits?filter=code:eq:{}".format(api_url, organisation_code), auth=credentials).json()
    if not json_res['organisationUnits']:
        json_string = {
            "name": name,
            "shortName": name,
            "code": organisation_code,
            "openingDate": opening_date,
            # "parent": {"id": "parent_uid"}
        }
        payload = json.dumps(json_string)
        response = requests.post("{}organisationUnits".format(api_url), headers=headers, data=payload)
        logging.info("Created location %s with response %d", name, response.status_code)
        logging.info(response.text)
    else:
        logging.info("Organisation %s with code %s already exists", name, organisation_code)
        codes_to_ids[organisation_code] = uid


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Using config:\n {}".format(json.dumps(dhis2_config, indent=4)))
    form_config = dhis2_config['forms'][0]
    form = form_config['name']
    url = dhis2_config['url']
    api_resource = dhis2_config['api_resource']
    api_url = url + api_resource
    credentials = dhis2_config['credentials']
    headers = dhis2_config['headers']

    db, session = get_db_engine()

    location_data = all_location_data(session)
    (locations, locs_by_deviceid, zones, regions, districts, devices) = location_data

    populate_dhis2_locations(locations, zones, regions, districts)
    dhis2_organisations = get_dhis2_organisations()

    exit(0)
    keys = __get_keys_from_db(db, form)
    dhis_keys = get_dhis2_keys(api_url, credentials, headers, keys)

    # TODO: for now only hardocded will be done in a more elegant way
    program_id = form_config['program_id']
    # program_id = 'T6VaKGprnc5' # demo_case


    status = form_config['status']
    stored_by = form_config['stored_by']

    for organisation_id in dhis2_organisations.values():
        clear_old_events(program_id, organisation_id)

    data_values = []
    results = session.query(form_tables[form].data).all()

    event_payload_list = []
    for counter, result in enumerate(results):

        data_values, event_date, completed_date, organisation_code = prepare_data_values(keys, dhis_keys, result.data, form_config)
        event_payload = {
            'program': program_id,
            'orgUnit': dhis2_organisations[organisation_code],
            'eventDate': event_date,
            'completedDate': completed_date,
            'dataValues': data_values,
            'status': status
        }
        event_payload_list.append(event_payload)
        if counter % 100 == 0:
            send_events_batch(event_payload_list)
            event_payload_list = []
    send_events_batch(event_payload_list)
