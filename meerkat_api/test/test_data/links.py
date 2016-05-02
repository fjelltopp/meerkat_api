from meerkat_abacus.model import Links
import datetime

public_health_report = [
    Links(**{'to_id': 'uuid:f294e740-9082-46c6-8853-5f095c9b8a28', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2015, 4, 23, 0, 0), 'to_date': datetime.datetime(2015, 4, 17, 13, 34, 15, 333927), 'data': {'investigator': '4', 'status': 'Confirmed', 'checklist': ['Contact Tracing', 'Referral']}, 'link_value': 'ce934d', 'id': 1}),
    Links(**{'to_id': 'uuid:c793a131-34cc-4d89-a31c-6141b4b949ff', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2015, 4, 26, 0, 0), 'to_date': datetime.datetime(2015, 5, 1, 15, 50, 37, 708804), 'data': {'investigator': '5', 'status': 'Disregarded', 'checklist': ['Case Management', 'Referral']}, 'link_value': '7f3f68', 'id': 2}),
    Links(**{'to_id': 'uuid:2119d5e0-fc33-4516-9e94-2651af56c31e', 'link_def': 'alert_investigation', 'from_date': datetime.datetime(2016, 4, 15, 0, 0), 'to_date': datetime.datetime(2015, 4, 29, 3, 10, 45, 244411), 'data': {'investigator': '6', 'status': 'Confirmed', 'checklist': 'Case Management'}, 'link_value': '4cd688', 'id': 3})
]
