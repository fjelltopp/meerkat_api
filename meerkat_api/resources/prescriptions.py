"""
Data resource for completeness data
"""
from flask_restful import Resource

from meerkat_api.extensions import db, api
from meerkat_abacus.model import Data, CalculationParameters
from meerkat_api.util import get_children, fix_dates
from meerkat_abacus.util import get_locations
from meerkat_api.authentication import authenticate
from sqlalchemy import func
from meerkat_api.resources.explore import get_variables

DEFAULT_KIT_COUNT_IN_CLINIC = 1


class Prescriptions(Resource):
    """
    Return medicine prescription data based on scanned barcodes

    Args: \n
        location: location id
            Returns:\n
    """
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):

        start_date, end_date = fix_dates(start_date, end_date)
        self.locs = get_locations(db.session)
        clinics = get_children(parent=location, locations=self.locs, require_case_report=True)
        kit_contents = db.session.query(CalculationParameters.parameters) \
            .filter(CalculationParameters.name == 'medicine_kits') \
            .one()[0]
        barcode_category = 'barcode_prescription'
        conditions = [Data.categories.has_key(barcode_category), Data.clinic.in_(clinics)]

        # Get first and last prescription for a clinic and medicine without time constraints
        first_last_prescr_query = db.session.query(Data.clinic,
                                                   Data.categories[barcode_category].astext,
                                                   func.count(Data.id),
                                                   func.min(Data.date),
                                                   func.max(Data.date))
        first_last_prescr_query = first_last_prescr_query.filter(*conditions)
        first_last_prescr_query = first_last_prescr_query.group_by(Data.clinic,
                                                                   Data.categories[barcode_category].astext)

        # Get first and last prescription for a clinic without time constraints
        clinic_info = db.session.query(Data.clinic,
                                       func.count(Data.id),
                                       func.min(Data.date),
                                       func.max(Data.date))
        clinic_info = clinic_info.filter(*conditions).group_by(Data.clinic)


        # Get number of prescriptions within time constraints
        date_conditions = [Data.date >= start_date, Data.date < end_date]
        prescription_in_date_range_query = db.session.query(Data.clinic,
                                                            Data.categories[barcode_category].astext,
                                                            func.count(Data.id))
        prescription_in_date_range_query = prescription_in_date_range_query.filter(*conditions)
        prescription_in_date_range_query = prescription_in_date_range_query.filter(*date_conditions)
        prescription_in_date_range_query = prescription_in_date_range_query.group_by(Data.clinic, Data.categories[barcode_category].astext)

        prescriptions = {
            'clinic_table': [],
            'medicine_table': [],
            'clinic_table_title': 'Prescribing clinics',
            'clinic_data': {}
        }

        # Restructure the DB return sets into a JSON
        for prescription in first_last_prescr_query.all():

            prescription_location_id = prescription[0]
            medicine_key = prescription[1]
            prescription_count = prescription[2]
            prescription_min_date = prescription[3]
            prescription_max_date = prescription[4]

            # if the medicine type is not configured to be reported, skip
            if medicine_key not in kit_contents:
                continue

            # get number of kits in the clinic
            kits_in_clinic = self._get_number_of_kits_in_clinic(prescription_location_id)

            # If clinic is already in JSON
            if str(prescription_location_id) in prescriptions['clinic_data'].keys():

                prescriptions['clinic_data'][str(prescription_location_id)].update({
                    str(medicine_key): {
                        "min_date": prescription_min_date.strftime("%Y-%m-%d"),
                        "max_date": prescription_max_date.strftime("%Y-%m-%d"),
                        "total_prescriptions": prescription_count,
                        "inventory":
                            (kit_contents[medicine_key]["total"] * kits_in_clinic
                             if kit_contents[medicine_key]["tablets_in_kit"] == ""
                             else int(kit_contents[medicine_key]["tablets_in_kit"]) * kits_in_clinic - prescription_count
                             ),
                        "depletion":
                            (prescription_count / (float(kit_contents[medicine_key]["total"]) * kits_in_clinic)
                             if kit_contents[medicine_key]["tablets_in_kit"] == ""
                             else prescription_count / (float(kit_contents[medicine_key]["tablets_in_kit"]) * kits_in_clinic)
                             ),
                        "stock":
                            (1 - prescription_count / (float(kit_contents[medicine_key]["total"]) * kits_in_clinic)
                             if kit_contents[medicine_key]["tablets_in_kit"] == ""
                             else 1 - prescription_count / (float(kit_contents[medicine_key]["tablets_in_kit"]) * kits_in_clinic)
                             ),
                    }
                })
            # If clinic is not in the JSON object yet
            else:
                prescriptions['clinic_data'].update({
                    str(prescription_location_id): {
                        str(medicine_key):
                            {
                                "min_date": prescription_min_date.strftime("%Y-%m-%d"),
                                "max_date": prescription_max_date.strftime("%Y-%m-%d"),
                                "total_prescriptions": prescription_count,
                                "inventory":
                                    (kit_contents[medicine_key]["total"] * kits_in_clinic
                                     if kit_contents[medicine_key]["tablets_in_kit"] == ""
                                     else int(kit_contents[medicine_key]["tablets_in_kit"]) * kits_in_clinic - prescription_count
                                     ),
                                "depletion":
                                    (prescription_count / (float(kit_contents[medicine_key]["total"]) * kits_in_clinic)
                                     if kit_contents[medicine_key]["tablets_in_kit"] == ""
                                     else prescription_count / (float(kit_contents[medicine_key]["tablets_in_kit"]) * kits_in_clinic)
                                     ),
                                "stock":
                                    (1 - prescription_count / (float(kit_contents[medicine_key]["total"]) * kits_in_clinic)
                                     if kit_contents[medicine_key]["tablets_in_kit"] == ""
                                     else 1 - prescription_count / (
                                            float(kit_contents[medicine_key]["tablets_in_kit"]) * kits_in_clinic)
                                     ),
                            }
                    }
                })

        # Assign the number of prescriptions to data object
        for prescription in prescription_in_date_range_query.all():
            str_prescription_location = str(prescription[0])
            medicine_key = str(prescription[1])
            prescription_count = prescription[2]
            medicine = prescriptions['clinic_data'][str_prescription_location].setdefault(medicine_key, {})
            medicine['prescriptions'] = prescription_count

        barcode_variables = get_variables(barcode_category)
        # create clinic table info
        for prescription in clinic_info.all():
            location_id = prescription[0]
            location_id_str = str(location_id)
            prescription_min_date = prescription[2]
            prescription_max_date = prescription[3]

            prescriptions_for_location = prescriptions['clinic_data'].setdefault(location_id_str, {})
            highest_depletion = find_highest_depletion(prescriptions_for_location)
            if highest_depletion:
                depletion_round_percent = round(highest_depletion['depletion'] * 100, 1)
                prescriptions['clinic_table'].append({
                    "clinic_id": location_id_str,
                    "clinic_name": self.locs[location_id].name,
                    "min_date": prescription_min_date.strftime("%Y-%m-%d"),
                    "max_date": prescription_max_date.strftime("%Y-%m-%d"),
                    "most_depleted_medicine": barcode_variables[highest_depletion['medicine']],
                    "depletion": highest_depletion['depletion'],
                    "str_depletion": str(depletion_round_percent) + '%'
                })

        # create medicine table info
        for clinic in prescriptions['clinic_data']:
            for medicine_key, medicine in prescriptions['clinic_data'][clinic].items():
                kit_details_for_medicine = kit_contents.get(medicine_key, {})
                if kit_details_for_medicine.get('tablets_in_kit', '') != '':
                    medicine_round_stock_percentage = round(medicine['stock'] * 100, 1)
                    prescriptions['medicine_table'].append({
                        "clinic_id": clinic,
                        "clinic_name": self.locs[int(clinic)].name,
                        "medicine_name": barcode_variables[medicine_key],
                        "min_date": medicine['min_date'],
                        "max_date": medicine['max_date'],
                        "stock": medicine['stock'],
                        "str_stock": str(medicine_round_stock_percentage) + '%',
                        "old_str_stock": (
                            "-"
                            if kit_contents[medicine_key]["tablets_in_kit"] == ""
                            else str(medicine_round_stock_percentage) + '%'
                        ),
                        "total_prescriptions": medicine['total_prescriptions']
                    })

        return prescriptions

    def _get_number_of_kits_in_clinic(self, prescription_location_id):
        kits_in_clinic = self.locs[prescription_location_id].other.get('IEHK kits', '')
        try:
            kits_in_clinic = int(kits_in_clinic)
        except ValueError:
            kits_in_clinic = DEFAULT_KIT_COUNT_IN_CLINIC
        return kits_in_clinic


def find_highest_depletion(clinic_medicines):
    if not clinic_medicines:
        return {}
    depletion_list = []
    for medicine in clinic_medicines.keys():
        depletion_list.append({
            'medicine': medicine,
            'depletion': clinic_medicines[medicine].get('depletion', False)
        })

    sorted_depletion_list = sorted(depletion_list, key=lambda k: k['depletion'], reverse=True)
    return sorted_depletion_list[0]


api.add_resource(Prescriptions, "/prescriptions/<location>",
                 "/prescriptions/<location>/<end_date>",
                 "/prescriptions/<location>/<end_date>/<start_date>")
