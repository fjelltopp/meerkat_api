import json
import logging
from datetime import date

import requests

from api_background._populate_locations import populate_row_locations, set_empty_locations
from api_background.export_data import __get_keys_from_db
from meerkat_abacus.config import dhis2_config
from meerkat_abacus.model import form_tables
from meerkat_abacus.util import get_db_engine, all_location_data

codes_to_ids = {}


class NewIdsProvider:
    def __init__(self, dhis2_api_url, credentials):
        self.dhis2_api_url = dhis2_api_url
        self.credentials = credentials
        self.ids = []

    def pop(self):
        if not self.ids:
            self.ids = self.__get_dhis2_ids()
        return self.ids.pop()

    def __get_dhis2_ids(self, n=100):
        response = requests.get("{}system/id.json?limit={}".format(self.dhis2_api_url, n), auth=self.credentials).json()
        result = response.get('codes', [])
        if not result:
            logging.error("Could not get ids from DHIS2.")
        return result


def update_program(a_program_id):
    payload = {
        "name": form_name,
        "shortName": form_name,
        "programType": "WITHOUT_REGISTRATION",
    }
    organisation_ids = [{"id": x} for x in get_dhis2_organisations().values()]
    if a_program_id is None:
        response = requests.get("{}programs?filter=shortName:eq:{}".format(api_url, form_name), auth=credentials)
        try:
            id_ = response.json().get("programs")[0].get("id")
        except IndexError:
            id_ = None
        if id_:
            a_program_id = id_
            __update_existing_program_with_organisations(a_program_id, organisation_ids, payload)
        else:
            a_program_id = ids.pop()

            payload["id"] = a_program_id
            payload["organisationUnits"] = organisation_ids
            json_payload = json.dumps(payload)
            req = requests.post("{}programs".format(api_url), data=json_payload, headers=headers)
            logging.info("Created program %s with status %d", payload["id"], req.status_code)

            data_element_keys = [{"dataElement": {"id": key}} for key in dhis_keys.values()]
            stage_payload = {
                "name": a_program_id,
                "program": {
                    "id": a_program_id
                },
                "programStageDataElements": data_element_keys
            }
            json_stage_payload = json.dumps(stage_payload)
            res = requests.post("{}programStages".format(api_url), data=json_stage_payload, headers=headers)
            logging.info("Created stage for program %s with status %d", a_program_id, res.status_code)
    else:
        __update_existing_program_with_organisations(a_program_id, organisation_ids, payload)

    return a_program_id


def __update_existing_program_with_organisations(a_program_id, organisation_ids, payload):
    req = requests.get("{}programs/{}".format(api_url, a_program_id), auth=credentials)
    old_organisation_ids = req.json().get('organistaionUnits', [])
    req = requests.put("{}programs/{}".format(api_url, a_program_id), data=payload, auth=credentials)
    payload["organisationUnits"] = organisation_ids + old_organisation_ids
    logging.info("Updated program %s with status %d", a_program_id, req.status_code)


def clear_old_events(program_id, org_unit_id):
    events_id_list = []
    res = requests.get("{}events?program={}&orgUnit={}&skipPaging=true".format(api_url, program_id, org_unit_id),
                       auth=credentials)
    results = res.json()
    for result in results.get("events", []):
        event_id = result['event']
        events_id_list.append({'event': event_id})
    delete_json = json.dumps({"events": events_id_list})
    a_delete = requests.post("{}events?strategy=DELETE".format(api_url), data=delete_json, headers=headers)
    print("Deleted old events for program {} and organisation {}  with status {}\n{!r}".format(program_id,
                                                                                               organisation_id,
                                                                                               a_delete.status_code,
                                                                                               a_delete.json().get(
                                                                                                   "message")))


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
            dhis_key_id = update_data_elements(key, headers)
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
    dhis2_organisations_res = requests.get("{}organisationUnits?skipPaging=True&pageSize=2000".format(api_url),
                                           auth=credentials)
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

    for zone_index in zones:
        create_dhis2_organisation(locations[zone_index])

    for region_index in regions:
        create_dhis2_organisation(locations[region_index])

    for district_index in districts:
        create_dhis2_organisation(locations[district_index])

    for location in locations.values():
        if location.level == 'clinic':
            create_dhis2_organisation(location)


def create_dhis2_organisation(_location):
    organisation_code = _location.country_location_id
    if organisation_code is None:
        return
    if _location.start_date:
        opening_date = _location.start_date.strftime("%Y-%m-%d")
    else:
        opening_date = "1970-01-01"
    name = _location.name
    json_res = requests.get("{}organisationUnits?filter=code:eq:{}".format(api_url, organisation_code),
                            auth=credentials).json()
    if not json_res['organisationUnits']:
        uid = ids.pop()
        parent_location_id = _location.parent_location
        if parent_location_id == 1:
            parent_id = dhis2_config['country_id']
        else:
            parent_id = codes_to_ids[locations[parent_location_id].country_location_id]
        json_dict = {
            "id": uid,
            "name": name,
            "shortName": name,
            "code": organisation_code,
            "openingDate": opening_date,
            "parent": {"id": parent_id}
        }
        payload = json.dumps(json_dict)
        response = requests.post("{}organisationUnits".format(api_url), headers=headers, data=payload)
        logging.info("Created location %s with response %d", name, response.status_code)
        logging.info(response.text)
        codes_to_ids[organisation_code] = uid
    else:
        logging.info("Organisation %s with code %s already exists", name, organisation_code)
        uid = json_res['organisationUnits'][0]['id']
        codes_to_ids[organisation_code] = uid


def clear_all_organisations():
    dhis2_organisations_res = requests.get("{}organisationUnits".format(api_url), auth=credentials)
    organisation_units = dhis2_organisations_res.json()['organisationUnits']

    for d in organisation_units:
        requests.delete("{}organisationUnits/{}".format(api_url, d['id']), auth=credentials)


def clear_all_data_elements():
    dhis2_organisations_res = requests.get("{}dataElements".format(api_url), auth=credentials)
    data_elements = dhis2_organisations_res.json()['dataElements']

    for d in data_elements:
        requests.delete("{}dataElements/{}".format(api_url, d['id']), auth=credentials)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Using config:\n {}".format(json.dumps(dhis2_config, indent=4)))
    form_config = dhis2_config['forms'][0]
    form_name = form_config['name']
    url = dhis2_config['url']
    api_resource = dhis2_config['api_resource']
    api_url = url + api_resource
    credentials = dhis2_config['credentials']
    headers = dhis2_config['headers']

    db, session = get_db_engine()
    ids = NewIdsProvider(api_url, credentials)

    location_data = all_location_data(session)
    (locations, locs_by_deviceid, zones, regions, districts, devices) = location_data

    populate_dhis2_locations(locations, zones, regions, districts)
    dhis2_organisations = get_dhis2_organisations()

    keys = __get_keys_from_db(db, form_name)
    dhis_keys = get_dhis2_keys(api_url, credentials, headers, keys)

    program_id = form_config.get('program_id', None)
    program_id = update_program(program_id)

    for organisation_id in dhis2_organisations.values():
        clear_old_events(program_id, organisation_id)

    status = form_config['status']
    stored_by = form_config['stored_by']

    data_values = []
    results = session.query(form_tables[form_name].data).all()

    event_payload_list = []
    for counter, result in enumerate(results):

        data_values, event_date, completed_date, organisation_code = prepare_data_values(keys, dhis_keys, result.data,
                                                                                         form_config)
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
