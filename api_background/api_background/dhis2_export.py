import requests
import json
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

    event_payload = {}
    data_elements = {}
    results = session.query(form_tables[form].data).yield_per(1000)

    result = results[0]
    data = result.data
    for key in keys:
        key_dhis_id_req = requests.get("{}dataElements?query={}".format(api_resource, key, headers=headers))
        dhis_key_id = key_dhis_id_req.json()






    res = requests.get("%s%sdataElements" % (url, api_resource), auth=credentials)
    print(res.status_code)
    print(res.text)
