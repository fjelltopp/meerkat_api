from meerkat_abacus.model import Alerts
import datetime

public_health_report= [
    Alerts(**{'data': {'gender': 'female', 'age': '33'}, 'clinic': 7, 'uuids': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce934d', 'date': datetime.datetime(2015, 5, 1, 0, 0), 'id': 'ce934d', 'region': [2], 'reason': 'cmd_11'}),
    Alerts(**{'data': {'gender': 'female', 'age': '0'}, 'clinic': 10, 'uuids': 'uuid:20b2022f-fbe7-43cb-8467-c569397f3f68', 'date': datetime.datetime(2015, 4, 18, 0, 0), 'id': '7f3f68', 'region': [2], 'reason': 'cmd_1'}),
    Alerts(**{'data': {'gender': 'female', 'age': '30'}, 'clinic': 7, 'uuids': 'uuid:c51ea7a2-5e2d-4c83-a9a9-85cce0928509', 'date': datetime.datetime(2015, 5, 2, 0, 0), 'id': '928509', 'region': [2], 'reason': 'cmd_2'}),
    Alerts(**{'data': {'gender': 'male', 'age': '63'}, 'clinic': 8, 'uuids': 'uuid:e4e92687-e7e1-4eff-9ec3-4f45421c1e93', 'date': datetime.datetime(2016, 4, 20, 0, 0), 'id': '1c1e93', 'region': [2], 'reason': 'cmd_19'})
]


cd_report = [
    Alerts(**{'data': {'gender': 'female', 'age': '33'}, 'clinic': 7, 'uuids': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce934d', 'date': datetime.datetime(2015, 5, 1, 0, 0), 'id': 'ce9341', 'region': [2], 'reason': 'cmd_11'}),
    Alerts(**{'data': {'gender': 'female', 'age': '33'}, 'clinic': 7, 'uuids': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce934d', 'date': datetime.datetime(2015, 5, 2, 0, 0), 'id': 'ce9342', 'region': [2], 'reason': 'cmd_11'}),
    Alerts(**{'data': {'gender': 'female', 'age': '33'}, 'clinic': 7, 'uuids': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce934d', 'date': datetime.datetime(2015, 5, 3, 0, 0), 'id': 'ce9343', 'region': [2], 'reason': 'cmd_11'}),
    Alerts(**{'data': {'gender': 'female', 'age': '33'}, 'clinic': 7, 'uuids': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce934d', 'date': datetime.datetime(2015, 5, 3, 0, 0), 'id': 'ce9344', 'region': [2], 'reason': 'cmd_11'}),
    Alerts(**{'data': {'gender': 'female', 'age': '0'}, 'clinic': 10, 'uuids': 'uuid:20b2022f-fbe7-43cb-8467-c569397f3f68', 'date': datetime.datetime(2015, 4, 18, 0, 0), 'id': '7f3f68', 'region': [2], 'reason': 'cmd_1'}),
    Alerts(**{'data': {'gender': 'female', 'age': '30'}, 'clinic': 7, 'uuids': 'uuid:c51ea7a2-5e2d-4c83-a9a9-85cce0928509', 'date': datetime.datetime(2015, 3, 2, 0, 0), 'id': '928501', 'region': [2], 'reason': 'cmd_2'}),
    Alerts(**{'data': {'gender': 'female', 'age': '30'}, 'clinic': 7, 'uuids': 'uuid:c51ea7a2-5e2d-4c83-a9a9-85cce0928509', 'date': datetime.datetime(2015, 5, 2, 0, 0), 'id': '928502', 'region': [2], 'reason': 'cmd_2'}),
    Alerts(**{'data': {'gender': 'male', 'age': '63'}, 'clinic': 11, 'uuids': 'uuid:e4e92687-e7e1-4eff-9ec3-4f45421c1e93', 'date': datetime.datetime(2016, 4, 20, 0, 0), 'id': '1c1e93', 'region': [3], 'reason': 'cmd_19'})
]

export_data = [
    Alerts(**{'data': {'gender': 'female', 'age': '33'}, 'clinic': 7, 'uuids': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce934d', 'date': datetime.datetime(2015, 5, 1, 0, 0), 'id': 'ee9376', 'region': [2], 'reason': 'cmd_11'}),
]

epi_monitoring= [
    Alerts(**{'data': {'gender': 'female', 'age': '33'}, 'clinic': 7, 'uuids': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce934d', 'date': datetime.datetime(2015, 1, 1, 0, 0), 'id': 'ce934d', 'region': [2], 'reason': 'cmd_11'}),
    Alerts(**{'data': {'gender': 'female', 'age': '0'}, 'clinic': 11, 'uuids': 'uuid:20b2022f-fbe7-43cb-8467-c569397f3f68', 'date': datetime.datetime(2015, 1, 1, 0, 0), 'id': '7f3f68', 'region': [2], 'reason': 'cmd_1'}),

]
