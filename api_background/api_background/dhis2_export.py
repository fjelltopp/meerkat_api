import json
import logging

from datetime import date

import requests

from api_background._populate_locations import populate_row_locations, set_empty_locations
from api_background.export_data import __get_keys_from_db
from meerkat_abacus.config import dhis2_config
from meerkat_abacus.model import form_tables
from meerkat_abacus.util import get_db_engine, all_location_data

db, session = get_db_engine()

__codes_to_ids = {}
__form_keys_to_data_elements_dict = {}
__dhis2_organisations = {}
__form_keys = {}

FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handler = logging.StreamHandler()
formatter = logging.Formatter(FORMAT)
handler.setFormatter(formatter)
logger = logging.getLogger('meerkat_api.dhis2')
level_name = dhis2_config.get("loggingLevel", "ERROR")
level = logging.getLevelName(level_name)
logger.setLevel(level)
logger.addHandler(handler)

form_config = dhis2_config['forms'][0]
form_name = form_config['name']
url = dhis2_config['url']
api_resource = dhis2_config['apiResource']
api_url = url + api_resource
credentials = dhis2_config['credentials']
headers = dhis2_config['headers']


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
        response = get("{}system/id.json?limit={}".format(self.dhis2_api_url, n), auth=self.credentials).json()
        result = response.get('codes', [])
        if not result:
            logger.error("Could not get ids from DHIS2.")
        return result


ids = NewIdsProvider(api_url, credentials)


def put(url, data=None, json=None, **kwargs):
    response = requests.put(url, data=data, json=json, **kwargs)
    return __check_if_response_is_ok(response)


def get(url, params=None, **kwargs):
    response = requests.get(url, params=params, **kwargs)
    return __check_if_response_is_ok(response)


def post(url, data=None, json=None, **kwargs):
    response = requests.post(url, data=data, json=json, **kwargs)
    return __check_if_response_is_ok(response)


def delete(url, **kwargs):
    response = requests.delete(url, **kwargs)
    return __check_if_response_is_ok(response)


def __check_if_response_is_ok(response):
    if response.status_code != requests.codes.ok:
        logger.error("Request failed with code %d.", response.status_code)
        logger.error(response.json().get("message"), stack_info=True)
    return response


def update_program(form_config, organisation_ids):
    a_program_id = form_config.get('programId', None)
    form_name = form_config['name']
    payload = {
        "name": form_name,
        "shortName": form_name,
        "programType": "WITHOUT_REGISTRATION",
    }
    organisation_ids_jarray = [{"id": x} for x in organisation_ids]
    if a_program_id is None:
        response = get("{}programs?filter=shortName:eq:{}".format(api_url, form_name), auth=credentials)
        try:
            id_ = response.json().get("programs")[0].get("id")
        except IndexError:
            id_ = None
        if id_:
            a_program_id = id_
            __update_existing_program_with_organisations(a_program_id, organisation_ids_jarray, payload)
        else:
            a_program_id = ids.pop()

            payload["id"] = a_program_id
            payload["organisationUnits"] = organisation_ids_jarray
            json_payload = json.dumps(payload)
            req = post("{}programs".format(api_url), data=json_payload, headers=headers)
            logger.info("Created program %s with status %d", payload["id"], req.status_code)

            dhis2_keys = get_form_keys_to_data_elements_dict(url, credentials, headers, form_name).values()
            data_element_keys = [{"dataElement": {"id": key}} for key in dhis2_keys]
            stage_payload = {
                "name": a_program_id,
                "program": {
                    "id": a_program_id
                },
                "programStageDataElements": data_element_keys
            }
            json_stage_payload = json.dumps(stage_payload)
            res = post("{}programStages".format(api_url), data=json_stage_payload, headers=headers)
            logger.info("Created stage for program %s with status %d", a_program_id, res.status_code)
    else:
        __update_existing_program_with_organisations(a_program_id, organisation_ids_jarray, payload)

    return a_program_id


def __update_existing_program_with_organisations(a_program_id, organisation_ids, payload):
    req = get("{}programs/{}".format(api_url, a_program_id), auth=credentials)
    old_organisation_ids = req.json().get('organisationUnits', [])
    payload["organisationUnits"] = old_organisation_ids + organisation_ids
    req = put("{}programs/{}".format(api_url, a_program_id), data=payload, auth=credentials)
    logger.info("Updated program %s with status %d", a_program_id, req.status_code)


def _clear_old_events(program_id, org_unit_id):
    events_id_list = []
    res = get("{}events?program={}&orgUnit={}&skipPaging=true".format(api_url, program_id, org_unit_id),
              auth=credentials)
    results = res.json()
    for result in results.get("events", []):
        event_id = result['event']
        events_id_list.append({'event': event_id})
    delete_json = json.dumps({"events": events_id_list})
    a_delete = post("{}events?strategy=DELETE".format(api_url), data=delete_json, headers=headers)
    logger.info("Deleted old events for program {} and organisation {}  with status {}\n{!r}".format(program_id,
                                                                                                     organisation_id,
                                                                                                     a_delete.status_code,
                                                                                                     a_delete.json().get(
                                                                                                         "message")))


def __update_data_elements(key, headers):
    payload = {'name': key, 'shortName': key, 'domainType': 'TRACKER', 'valueType': 'TEXT', 'aggregationType': 'NONE'}
    json_payload = json.dumps(payload)
    post_res = post("{}dataElements".format(api_url), data=json_payload, headers=headers)
    json_res = post_res.json()
    uid = json_res['response']['uid']
    logger.info("Created data element \"{}\" with uid: {}".format(key, uid))
    return uid


def prepare_data_values(data, form_config):
    data_values = []
    organisation_code = None
    form_name = form_config.get("name")
    dhis_keys = get_form_keys_to_data_elements_dict(api_url, credentials, headers, form_name)
    keys = __get_form_keys(form_name)
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


def get_form_keys_to_data_elements_dict(url, credentials, headers, form_name):
    global __form_keys_to_data_elements_dict
    if __form_keys_to_data_elements_dict.get(form_name):
        return __form_keys_to_data_elements_dict.get(form_name)
    result = {}
    dhis2_data_elements_res = get("{}dataElements?skipPaging=True".format(url), auth=credentials)
    dhis2_data_elements = dhis2_data_elements_res.json()['dataElements']
    data_elements_ids = []
    data_elements_names = []
    for d in dhis2_data_elements:
        data_elements_ids.append(d['id'])
        data_elements_names.append(d['displayName'])
    data_element_lookup = dict(zip(data_elements_names, data_elements_ids))
    for key in __get_form_keys(form_name):
        if key in data_element_lookup:
            dhis_key_id = data_element_lookup[key]
        else:
            dhis_key_id = __update_data_elements(key, headers)
        result[key] = dhis_key_id
    __form_keys_to_data_elements_dict[form_name] = result
    return __form_keys_to_data_elements_dict.get(form_name)


def send_events_batch(payload_list):
    payload = {}
    payload['events'] = payload_list
    json_event_payload = json.dumps(payload)
    s = requests.session()
    event_res = s.post("{}events".format(api_url), headers=headers, data=json_event_payload)
    logger.info("Send batch of events with status: %d", event_res.status_code)
    logger.info(event_res.json().get('message'))


def get_dhis2_organisations():
    global __dhis2_organisations
    if __dhis2_organisations:
        return __dhis2_organisations
    result = {}
    dhis2_organisations_res = get("{}organisationUnits?skipPaging=True&pageSize=2000".format(api_url),
                                  auth=credentials)
    dhis2_organisations = dhis2_organisations_res.json()['organisationUnits']
    for d in dhis2_organisations:
        res = get("{}organisationUnits/{}".format(api_url, d['id']), auth=credentials)
        organisation_code = res.json().get('code', None)
        result[organisation_code] = d['id']
    __dhis2_organisations = result
    return __dhis2_organisations


def populate_dhis2_locations(locations, zones, regions, districts):
    dhis2_organisations_res = get("{}organisationUnits".format(api_url), auth=credentials)
    organisation_units = dhis2_organisations_res.json()['organisationUnits']
    organisation_ids = []
    organisation_names = []
    organisation_codes = []
    for d in organisation_units:
        organisation_ids.append(d['id'])
        organisation_names.append(d['displayName'])

        res = get("{}organisationUnits/{}".format(api_url, d['id']), auth=credentials)
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
    json_res = get("{}organisationUnits?filter=code:eq:{}".format(api_url, organisation_code),
                   auth=credentials).json()
    if not json_res['organisationUnits']:
        __create_new_organisation(_location, opening_date, organisation_code)
    else:
        logger.info("Organisation %12s with code %15s already exists", _location.name, organisation_code)
        uid = json_res['organisationUnits'][0]['id']
        __codes_to_ids[organisation_code] = uid


def __create_new_organisation(_location, opening_date, organisation_code):
    uid = ids.pop()
    name = _location.name
    parent_location_id = _location.parent_location
    if parent_location_id == 1:
        parent_id = dhis2_config['countryId']
    else:
        parent_id = __codes_to_ids[locations[parent_location_id].country_location_id]
    json_dict = {
        "id": uid,
        "name": name,
        "shortName": name,
        "code": organisation_code,
        "openingDate": opening_date,
        "parent": {"id": parent_id}
    }
    payload = json.dumps(json_dict)
    response = post("{}organisationUnits".format(api_url), headers=headers, data=payload)
    logger.info("Created location %s with response %d", name, response.status_code)
    logger.info(response.text)
    __codes_to_ids[organisation_code] = uid


def clear_all_organisations():
    dhis2_organisations_res = get("{}organisationUnits".format(api_url), auth=credentials)
    organisation_units = dhis2_organisations_res.json()['organisationUnits']

    for d in organisation_units:
        delete("{}organisationUnits/{}".format(api_url, d['id']), auth=credentials)


def clear_all_data_elements():
    dhis2_organisations_res = get("{}dataElements".format(api_url), auth=credentials)
    data_elements = dhis2_organisations_res.json()['dataElements']

    for d in data_elements:
        delete("{}dataElements/{}".format(api_url, d['id']), auth=credentials)


def process_form_records(form_config, program_id):
    status = form_config['status']
    results = session.query(form_tables[form_name].data).all()
    event_payload_list = []
    for counter, result in enumerate(results):

        data_values, event_date, completed_date, organisation_code = prepare_data_values(result.data, form_config)
        event_payload = {
            'program': program_id,
            'orgUnit': get_dhis2_organisations().get(organisation_code),
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


def __get_form_keys(form_name=None):
    global __form_keys
    if not __form_keys.get(form_name):
        assert form_name
        __form_keys[form_name] = __get_keys_from_db(db, form_name)
    return __form_keys[form_name]


if __name__ == "__main__":
    logger.info("Using config:\n {}".format(json.dumps(dhis2_config, indent=4)))

    location_data = all_location_data(session)
    (locations, locs_by_deviceid, zones, regions, districts, devices) = location_data

    populate_dhis2_locations(locations, zones, regions, districts)

    program_id = update_program(form_config, get_dhis2_organisations().values())

    for organisation_id in get_dhis2_organisations().values():
        _clear_old_events(program_id, organisation_id)

    process_form_records(form_config, program_id)
