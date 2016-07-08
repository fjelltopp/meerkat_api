from meerkat_abacus.model import Locations
from datetime import datetime


locations = [
    Locations(**{'clinic_type': None, 'deviceid': None, 'case_report': None, 'geolocation': None, 'parent_location': None, 'level': "country", 'name': 'Demo', 'id': 1, 'other': None}),
    Locations(**{'clinic_type': None, 'deviceid': None, 'case_report': None, 'geolocation': '', 'parent_location': 1, 'level': 'region', 'name': 'Region 1', 'id': 2, 'other': None}),
    Locations(**{'clinic_type': None, 'deviceid': None, 'case_report': None, 'geolocation': '', 'parent_location': 1, 'level': 'region', 'name': 'Region 2', 'id': 3, 'other': None}),
    Locations(**{'clinic_type': None, 'deviceid': None, 'case_report': None, 'geolocation': None, 'parent_location': 2, 'level': 'district', 'name': 'District 1', 'id': 4, 'other': None}),
    Locations(**{'clinic_type': None, 'deviceid': None, 'case_report': None, 'geolocation': None, 'parent_location': 2, 'level': 'district', 'name': 'District 2', 'id': 5, 'other': None}),
    Locations(**{'clinic_type': None, 'deviceid': None, 'case_report': None, 'geolocation': None, 'parent_location': 3, 'level': 'district', 'name': 'District 3', 'id': 6, 'other': None}),
    Locations(**{'clinic_type': 'SARI', 'deviceid': '2', 'case_report': 1, 'geolocation': '0.2,0.2', 'parent_location': 4, 'level': 'clinic', 'name': 'Clinic 2', 'id': 8, 'start_date': datetime(2016, 1, 1), 'other': None}),
    Locations(**{'clinic_type': 'Focal', 'deviceid': '3', 'case_report': 0, 'geolocation': '0.2,0.3', 'parent_location': 4, 'start_date': datetime(2016, 1, 1), 'level': 'clinic', 'name': 'Clinic 3', 'id': 9, 'other': None}),
    Locations(**{'clinic_type': 'SARI', 'deviceid': '4', 'case_report': 1, 'geolocation': '0.3,0.2', 'parent_location': 5, 'start_date': datetime(2016, 1, 1), 'level': 'clinic', 'name': 'Clinic 4', 'id': 10, 'other': None}),
    Locations(**{'clinic_type': 'Refugee', 'deviceid': '5', 'case_report': 1, 'geolocation': '-0.1,0.4', 'parent_location': 6, 'start_date': datetime(2016, 1, 1), 'level': 'clinic', 'name': 'Clinic 5', 'id': 11, 'other': None}),
    Locations(**{'clinic_type': 'Refugee', 'deviceid': '1,6', 'case_report': 1, 'geolocation': '0.1,0.1', 'parent_location': 4, 'start_date': datetime(datetime.now().year, 2, 1), 'level': 'clinic', 'name': 'Clinic 1', 'id': 7, 'other': None})
]
