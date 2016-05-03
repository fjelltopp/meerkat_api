from meerkat_abacus.model import Links
import datetime

public_health_report = [
    Links(**{'to_id': 'uuid:f294e740-9082-46c6-8853-5f095c9b8a28', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2015, 4, 23, 0, 0), 'to_date': datetime.datetime(2015, 4, 17, 13, 34, 15, 333927), 'data': {'investigator': '4', 'status': 'Confirmed', 'checklist': ['Contact Tracing', 'Referral']}, 'link_value': 'ce934d', 'id': 1}),
    Links(**{'to_id': 'uuid:c793a131-34cc-4d89-a31c-6141b4b949ff', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2015, 4, 26, 0, 0), 'to_date': datetime.datetime(2015, 5, 1, 15, 50, 37, 708804), 'data': {'investigator': '5', 'status': 'Disregarded', 'checklist': ['Case Management', 'Referral']}, 'link_value': '7f3f68', 'id': 2}),
    Links(**{'to_id': 'uuid:2119d5e0-fc33-4516-9e94-2651af56c31e', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2016, 4, 15, 0, 0), 'to_date': datetime.datetime(2015, 4, 29, 3, 10, 45, 244411), 'data': {'investigator': '6', 'status': 'Confirmed', 'checklist': 'Case Management'}, 'link_value': '4cd688', 'id': 3})
]


cd_report = [
    Links(**{'to_id': 'uuid:f294e740-9082-46c6-8853-5f095c9b8a28', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2015, 4, 23, 0, 0), 'to_date': datetime.datetime(2015, 4, 17, 13, 34, 15, 333927), 'data': {'investigator': '4', 'status': 'Confirmed', 'checklist': ['Contact Tracing', 'Referral']}, 'link_value': 'ce9341', 'id': 1}),
    Links(**{'to_id': 'uuid:f294e740-9082-46c6-8853-5f095c9b8a28', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2015, 4, 23, 0, 0), 'to_date': datetime.datetime(2015, 4, 17, 13, 34, 15, 333927), 'data': {'investigator': '4', 'status': 'Disregarded', 'checklist': ['Contact Tracing', 'Referral']}, 'link_value': 'ce9342', 'id': 2}),
    Links(**{'to_id': 'uuid:2119d5e0-fc33-4516-9e94-2651af56c31e', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2016, 4, 15, 0, 0), 'to_date': datetime.datetime(2015, 4, 29, 3, 10, 45, 244411), 'data': {'investigator': '6', 'status': 'Ongoing', 'checklist': 'Case Management'}, 'link_value': '928502', 'id': 3}),
    # Not linked to anything
    Links(**{'to_id': 'uuid:2119d5e0-fc33-4516-9e94-2651af56c31e', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2016, 4, 15, 0, 0), 'to_date': datetime.datetime(2015, 4, 29, 3, 10, 45, 244411), 'data': {'investigator': '6', 'status': 'Ongoing', 'checklist': 'Case Management'}, 'link_value': 'xxxxx', 'id': 4})
]


pip_report = [
    # Follow-up
    Links(**{'link_def': 'pip_followup', 'link_value': 'namru-1', 'id': 1, 'from_date': datetime.datetime(2015, 3, 31, 0, 0), 'to_id': 'uuid:ad953028-499d-4d56-ad56-a9e777a4b4b0', 'data': {'outcome': [], 'ventilated': "yes", 'admitted_to_icu': "yes"}, 'to_date': datetime.datetime(2015, 4, 13, 0, 0)}),
    Links(**{'link_def': 'pip_followup', 'link_value': 'namru-2', 'id': 2, 'from_date': datetime.datetime(2015, 3, 24, 0, 0), 'to_id': 'uuid:59a15d8d-adf6-4e1f-97e2-b3d020ebc8a0', 'data': {'outcome': [], 'ventilated': [], 'admitted_to_icu': "yes"}, 'to_date': datetime.datetime(2015, 3, 27, 0, 0)}),
    Links(**{'link_def': 'pip_followup', 'link_value': 'namru-3', 'id': 3, 'from_date': datetime.datetime(2015, 3, 23, 0, 0), 'to_id': 'uuid:e470d7b0-d211-4d82-b082-294c7a3415a6', 'data': {'outcome': [], 'ventilated': [], 'admitted_to_icu': []}, 'to_date': datetime.datetime(2015, 3, 24, 0, 0)}),
    Links(**{'link_def': 'pip_followup', 'link_value': 'namru-4', 'id': 4, 'from_date': datetime.datetime(2015, 4, 12, 0, 0), 'to_id': 'uuid:4e46f58e-74fd-42b6-b5ca-1350328152ee', 'data': {'outcome': "death", 'ventilated': "yes", 'admitted_to_icu': "yes"}, 'to_date': datetime.datetime(2015, 4, 14, 0, 0)}),
    # Labs
    Links(**{'link_def': 'pip', 'link_value': 'namru-1', 'id': 5, 'from_date': datetime.datetime(2015, 4, 30, 0, 0), 'to_id': 'uuid:ad953028-499d-4d56-ad56-a9e777a4b4b0', 'data': {"type": "H1"}, 'to_date': datetime.datetime(2015, 4, 30, 0, 0)}),
    Links(**{'link_def': 'pip', 'link_value': 'namru-1', 'id': 6, 'from_date': datetime.datetime(2015, 4, 30, 0, 0), 'to_id': 'uuid:ad953028-499d-4d56-ad56-a9e777a4b4b0', 'data': {"type": "H1N1"}, 'to_date': datetime.datetime(2015, 5, 3, 0, 0)}),
    Links(**{'link_def': 'pip', 'link_value': 'namru-1', 'id': 7, 'from_date': datetime.datetime(2015,7, 30, 0, 0), 'to_id': 'uuid:ad953028-499d-4d56-ad56-a9e777a4b4b0', 'data': {"type": ["H1", "H3"]}, 'to_date': datetime.datetime(2015, 6, 30, 0, 0)})
]
