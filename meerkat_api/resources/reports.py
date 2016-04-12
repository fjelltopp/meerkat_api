"""
Data resource for querying data
"""
from flask_restful import Resource
from sqlalchemy import or_, extract, func, Integer, desc
from datetime import datetime, timedelta
from dateutil import parser
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql import text
import uuid
import time

from meerkat_api.util import row_to_dict, rows_to_dicts, date_to_epi_week, get_children, is_child
from meerkat_api import db, app
from meerkat_abacus.model import Data, Locations, Alerts, AggregationVariables
from meerkat_api.resources.variables import Variables
from meerkat_api.resources.epi_week import EpiWeek, epi_week_start
from meerkat_api.resources.locations import TotClinics
from meerkat_api.resources import alerts
from meerkat_api.resources.explore import QueryVariable, query_ids
from meerkat_abacus.util import get_locations, all_location_data
from meerkat_abacus import model
from meerkat_api.authentication import require_api_key


def fix_dates(start_date, end_date):
    if start_date:
        start_date = parser.parse(start_date).replace(tzinfo=None)
    else:
        start_date = datetime.now().replace(month=1, day=1,
                                            hour=0, second=0,
                                            minute=0,
                                            microsecond=0)
        
    if end_date:
        end_date  = parser.parse(end_date).replace(tzinfo=None)
    else:
        end_date = datetime.now()
    return start_date, end_date
    

class NcdReport(Resource):
    """
    Class for ncd report
    """
    decorators = [require_api_key]
    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first().name

        if not location_name:
            return None
        ret["data"]["project_region"] = location_name

        ret["hypertension"] = {"age": {}, "complications": {}}
        ret["diabetes"] = {"age": {}, "complications": {}}

        diabetes_id = "ncd_1"
        hypertension_id = "ncd_2"
        diseases = {"hypertension": hypertension_id, "diabetes": diabetes_id}
        labs_to_include = {"hypertension": ["lab_1", "lab_2", "lab_3"], "diabetes": ["lab_2", "lab_3", "lab_4", "lab_5"]}
        ids_to_include = {"hypertension":
                          [["With Diabetes", "com_1"], ["Smoking", "smo_2"], ["Complication", "lab_6"]],
                          "diabetes":
                          [["With Hypertension", "com_2"], ["Smoking", "smo_2"], ["Complication", "lab_6"]]
                          }
        locations, ldid, regions, districts = all_location_data(db.session)
        v = Variables()
        lab_categories = v.get("lab")
        ages = v.get("age")
        for disease in diseases.keys():
            ret[disease]["age"]["titles"] = ["Region", ]
            ret[disease]["age"]["data"] = []
            for age in sorted(ages.keys()):
                ret[disease]["age"]["titles"].append(ages[age]["name"])
            ret[disease]["age"]["titles"].append("Total")
            ret[disease]["complications"]["titles"] = ["Region",
                                                       "Total",
                                                       "Female",
                                                       "Male"]
            for l in labs_to_include[disease]:
                ret[disease]["complications"]["titles"].append(
                    lab_categories[l]["name"])
            for i in ids_to_include[disease]:
                ret[disease]["complications"]["titles"].append(i[0])
                
            ret[disease]["complications"]["data"] = []
            for i, region in enumerate(sorted(regions) + [1]):
                d_id = diseases[disease]
                query_variable = QueryVariable()
                disease_age = query_variable.get(d_id, "age",
                                                 end_date=end_date.isoformat(),
                                                 start_date=start_date.isoformat(),
                                                 only_loc=region,
                                                 use_ids=True)
                loc_name = locations[region].name
                if loc_name == "Jordan":
                    loc_name = "Total"
                ret[disease]["age"]["data"].append({"title": loc_name, "values": []})
                
                for age in sorted(ages.keys()):
                    ret[disease]["age"]["data"][i]["values"].append(disease_age[age]["total"])
                
                ret[disease]["age"]["data"][i]["values"].append(sum( [a["total"] for a in disease_age.values()]))
                disease_gender = query_variable.get(d_id, "gender",
                                                    end_date=end_date.isoformat(),
                                                    start_date=start_date.isoformat(),
                                                    only_loc=region)
                ret[disease]["complications"]["data"].append({"title": loc_name,
                                                              "values": [sum([disease_gender[gender]["total"] for gender in disease_gender])]})
                
                ret[disease]["complications"]["data"][i]["values"].append(disease_gender["Female"]["total"])
                ret[disease]["complications"]["data"][i]["values"].append(disease_gender["Male"]["total"])
                labs = query_variable.get(d_id, "lab",
                                          end_date=end_date.isoformat(),
                                          start_date=start_date.isoformat(),
                                          only_loc=region,
                                          use_ids=True)
                
                for l in labs_to_include[disease]:
                    if l in labs:
                        ret[disease]["complications"]["data"][i]["values"].append(labs[l]["total"])

                for new_id in ids_to_include[disease]:
                    if new_id[1]:
                        
                        ret[disease]["complications"]["data"][i]["values"].append(
                            query_ids([d_id, new_id[1]], start_date, end_date, only_loc=region)
                            )
                    else:
                        ret[disease]["complications"]["data"][i]["values"].append("N/A")
            
        return ret
    

class CdReport(Resource):
    """Class for communical disease report"""
    decorators = [require_api_key]
    def get(self, location, end_date=None):
        """ generates data for the CD report for the year until the end date for the given location"""

        start_date, end_date = fix_dates(None, end_date)
        start_date = datetime(end_date.year, 1, 1)
        ret = {}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]

        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": start_date.isoformat(),
                       "start_date": start_date.isoformat()
        }

        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first().name
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name

        all_alerts = alerts.get_alerts({"location": location})
        data = {}
        weeks = [i for i in range(1, 52, 1)]
        data_list = [0 for week in weeks]
        variable_query = db.session.query(AggregationVariables).filter(
            AggregationVariables.alert == 1)
        variable_names = {}
        for v in variable_query.all():
            variable_names[v.id] = v.name
        for a in all_alerts.values():
            if a["alerts"]["date"] <= end_date and a["alerts"]["date"] > start_date:
                reason = variable_names[a["alerts"]["reason"]]
                report_status = None
                if "links" in a and "alert_investigation" in a["links"]:
                    status = a["links"]["alert_investigation"]["data"]["status"]
                    if "central_review" in a["links"]:
                        status = a["links"]["central_review"]["data"]["status"]
                    if status == "Confirmed":
                        report_status = "confirmed"
                    elif status != "Disregarded":
                        report_status = "suspected"
                else:
                    report_status = "suspected"
                epi_week = ew.get(a["alerts"]["date"].isoformat())["epi_week"]
                if report_status:
                    data.setdefault(reason, {"weeks": weeks,
                                             "suspected": list(data_list),
                                             "confirmed": list(data_list)})
                    data[reason][report_status][epi_week - 1] += 1
        ret["data"]["communicable_diseases"] = data
        return ret


class RefugeePublicHealth(Resource):
    """ Class to return data for the public health report """
    decorators = [require_api_key]
    def get(self, location, start_date=None, end_date=None):
        """ generates date for the refugee public health report for the year 
        up to epi_week for the given location"""

        if "refugee" not in model.form_tables:
            return {}
        start_date, end_date = fix_dates(None, end_date)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        ew = EpiWeek()
        end_date = end_date - timedelta(days=1)
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat(),
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        location_name = locs[int(location)].name
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name
        #We first find all the refugee clinics
        refugee_clinics = get_children(location, locs, clinic_type="Refugee")
        
        ret["data"]["clinic_num"] = len(refugee_clinics)
        # Total_population we want the latest submitted total population
        male = 0
        female = 0
        no_clinicians = 0
        age_gender = {}
        for clinic in refugee_clinics:
            clinic_data = get_latest_category("population", clinic, start_date, end_date)
            for age in clinic_data:
                age_gender.setdefault(age, {})
                for gender in clinic_data[age]:
                    age_gender[age].setdefault(gender, 0)
                    age_gender[age][gender] += clinic_data[age][gender]
                    if gender == "female":
                        female += clinic_data[age][gender]
                    if gender == "male":
                        male += clinic_data[age][gender]
                
            result = db.session.query(Data.variables).filter(
                Data.variables.has_key("ref_14"),
                Data.clinic == clinic,
                Data.date >= start_date,
                Data.date < end_date
            ).order_by(Data.date.desc()).first()
            if result:
                no_clinicians += result[0]["ref_14"]
        tot_pop = male + female
        ret["data"]["total_population"] = tot_pop
                
        total_consultations = get_variable_id("ref_13", start_date, end_date, location, conn)
        ret["data"]["total_consultations"] = total_consultations
        if tot_pop == 0:
            tot_pop = 1
        u5 =  sum(age_gender["0-1"].values()) + sum(age_gender["1-4"].values())
        
        ret["data"]["percent_cases_male"] = male / tot_pop*100
        ret["data"]["percent_cases_female"] = female / tot_pop*100
        ret["data"]["percent_cases_lt_5yo"] =u5 / tot_pop*100
        ret["data"]["n_clinicians"] = no_clinicians
        
        if u5 == 0:
            u5 = 1
        if total_consultations == 0:
            total_consultations = 1
        if no_clinicians == 0:
            no_clinicians = 1
        # Morbidity
        morbidity_cd = get_variables_category("refugee_cd", start_date, end_date, location, conn)
        morbidity_ncd = get_variables_category("refugee_ncd", start_date, end_date, location, conn)
        morbidity_injury = get_variables_category("refugee_trauma", start_date, end_date, location, conn)
        morbidity_mh = get_variables_category("refugee_mh", start_date, end_date, location, conn)
        morbidity_cd_no = sum(morbidity_cd.values())
        morbidity_ncd_no = sum(morbidity_ncd.values())
        morbidity_injury_no = sum(morbidity_injury.values())
        morbidity_mh_no = sum(morbidity_mh.values())
        total_cases = morbidity_cd_no + morbidity_ncd_no + morbidity_injury_no + morbidity_mh_no
        ret["data"]["total_cases"] = total_cases
        if total_cases == 0:
            total_cases = 1
        ret["data"]["percent_morbidity_communicable"] = morbidity_cd_no / total_cases * 100
        ret["data"]["percent_morbidity_non_communicable"] = morbidity_ncd_no / total_cases * 100
        ret["data"]["percent_morbidity_mental_health"] = morbidity_mh_no / total_cases * 100
        ret["data"]["percent_morbidity_injury_health"] = morbidity_injury_no / total_cases * 100
        
        #Mortality
        mortality =  get_variables_category("mortality", start_date, end_date, location, conn)
        mortality_u5 = get_variables_category("u5_mortality", start_date, end_date, location, conn)
        crude_mortality_rate = sum(mortality.values()) / tot_pop * 1000
        u5_crude_mortality_rate = sum(mortality_u5.values()) /  u5 * 1000
        ret["data"]["crude_mortality_rate"] = crude_mortality_rate
        ret["data"]["u5_crude_mortality_rate"] = u5_crude_mortality_rate
        #public health indicators
        days_of_report = (end_date-start_date).days
        ret["data"]["public_health_indicators"] = [
            make_dict("Health Utilisation Rate", total_consultations / tot_pop / days_of_report * 365 , None)] # per year
        ret["data"]["public_health_indicators"].append(
            make_dict("Number of consultations per clinician per day", total_consultations / no_clinicians / days_of_report, None)
            )
        hospital_referrals = get_variable_id("ref_15", start_date, end_date, location, conn)
        ret["data"]["public_health_indicators"].append(
            make_dict("Hospitalisation rate",
                      hospital_referrals /total_consultations, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict("Referral rate",
                      (get_variable_id("ref_16", start_date, end_date, location, conn) + hospital_referrals) /total_consultations, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict("Crude Mortality Rate (CMR) ",
                     crude_mortality_rate, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict("Under-five Mortality Rate (U5MR) ",
                       u5_crude_mortality_rate / total_consultations, None)
        )
   
   
        #Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for clinic in refugee_clinics:
            num =  sum(get_variables_category("morbidity_refugee", start_date, end_date, clinic, conn).values())
            ret["data"]["reporting_sites"].append(
                    make_dict(locs[clinic].name,
                              num,
                              num / total_cases * 100))

      
        #Demographics
        ret["data"]["demographics"] = []
      
        age_order = ["0-1", "1-4", "5-14", "15-44", "45-64", ">65"]
        for a in age_order:
            if a in age_gender.keys():
                a_sum = sum(age_gender[a].values())
                if a_sum == 0:
                    a_sum = 1
                ret["data"]["demographics"].append(
                    {"age": a,
                     "male": {"quantity": age_gender[a]["male"],
                              "percent": age_gender[a]["male"] / a_sum * 100
                     },
                     "female":{"quantity": age_gender[a]["female"],
                               "percent": age_gender[a]["female"]/float(a_sum)*100
                     }
                    })
        ret["data"]["gender"] = [
            make_dict("Female",
                      female,
                      female / tot_pop * 100),
            make_dict("Male",
                      male,
                      male / tot_pop * 100)
        ]
        ret["data"]["presenting_complaints"] = [
            make_dict("Communicable Disease", morbidity_cd_no, morbidity_cd_no / total_cases *100),
            make_dict("Non-Communicable Disease", morbidity_ncd_no, morbidity_ncd_no / total_cases *100),
            make_dict("Mental Health", morbidity_mh_no, morbidity_mh_no / total_cases *100),
            make_dict("Injury", morbidity_injury_no, morbidity_injury_no / total_cases *100)
        ]

        

        ret["data"]["morbidity_communicable"] = refugee_disease(morbidity_cd)

        ret["data"]["morbidity_non_communicable"] = refugee_disease(morbidity_ncd)
        ret["data"]["mental_health"] = refugee_disease(morbidity_mh)
        ret["data"]["injury"] = refugee_disease(morbidity_injury)
        
        return ret


class Pip(Resource):
    """ Class to return data for the pip report """
    decorators = [require_api_key]
    def get(self, location, start_date=None, end_date=None):
        """ generates date for the pip report for the year 
        up to epi_week for the given location"""
        start_date, end_date = fix_dates(None, end_date)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        location_name = locs[int(location)].name
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name
        #We first find the number of SARI sentinel sites
        sari_clinics = get_children(location, locs, clinic_type="SARI")
        ret["data"]["num_clinic"] = len(sari_clinics)
        query_variable = QueryVariable()
        gender = query_variable.get("pip_2","gender",
                                    end_date=end_date.isoformat(),
                                    start_date=start_date.isoformat(),
                                    only_loc=location)
        total_cases = get_variable_id("pip_2", start_date, end_date, location, conn)
        ret["data"]["total_cases"] = total_cases
        if total_cases == 0:
            total_cases = 1

        ret["data"]["gender"] = [
            make_dict("Female",
                      gender["Female"]["total"],
                      gender["Female"]["total"] / total_cases * 100),
            make_dict("Male",
                      gender["Male"]["total"],
                      gender["Male"]["total"] / total_cases * 100)
            ]
        ret["data"]["percent_cases_female"] = (gender["Female"]["total"] / total_cases) * 100
        ret["data"]["percent_cases_male"] = (gender["Male"]["total"] / total_cases) * 100
        pip_cat = query_variable.get("pip_2","pip",
                                         end_date=end_date.isoformat(),
                                         start_date=start_date.isoformat(),
                                         only_loc=location,
                                         use_ids=True)

        weeks = list(range(1,53))#sorted(pip_cat["pip_2"]["weeks"].keys())
        
        ret["data"]["timeline"] = {
            "suspected": [pip_cat["pip_2"]["weeks"][k] if k in pip_cat["pip_2"]["weeks"] else 0 for k in weeks],
            "weeks": weeks,
            "confirmed": {
                "Influenza A": [0 for w in weeks],
                "Influenza B": [0 for w in weeks],
                "H1": [0 for w in weeks],
                "H3": [0 for w in weeks],
                "H1N1": [0 for w in weeks],
                "Mixed": [0 for w in weeks]
                }
            }
        
        ret["data"]["percent_cases_chronic"] = (pip_cat["pip_3"]["total"] / total_cases ) * 100
        ret["data"]["cases_chronic"] = pip_cat["pip_3"]["total"]
        # Lab links and follow up links
        lab_links = db.session.query(model.Links).filter(model.Links.link_def == "pip")
        total_lab_links = 0
        lab_types = {"Influenza A": 0,
                     "Influenza B": 0,
                     "H1": 0,
                     "H3": 0,
                     "H1N1": 0,
                     "Mixed": 0
                     }
        for link in lab_links:
            total_lab_links += 1
            epi_week = ew.get(link.from_date.isoformat())["epi_week"]
            t = link.data["type"]
            if isinstance(t, list):
                if epi_week in weeks:
                    ret["data"]["timeline"]["confirmed"]["Mixed"][epi_week - 1] += 1
                lab_types["Mixed"] += 1
            else:
                if epi_week in weeks:
                    ret["data"]["timeline"]["confirmed"][t][epi_week -1] += 1
                lab_types[t] += 1
        tl = ret["data"]["timeline"]["confirmed"]
        ret["data"]["timeline"]["confirmed"] = [ {"title": key, "values": list(tl[key])}
                                                 for key in sorted(tl.keys(), key=lambda key: sum(tl[key]), reverse=True)
                                                 ]
                                                 
        ret["data"]["cases_pcr"] = total_lab_links
        
        ret["data"]["flu_type"] = []
        for l in ["Influenza A", "Influenza B", "H1", "H3", "H1N1", "Mixed"]:
            ret["data"]["flu_type"].append(
                make_dict(l, lab_types[l], (lab_types[l]/total_cases) * 100)
            )
        followup_links = db.session.query(model.Links).filter(model.Links.link_def == "pip_followup")

        total_followup = 0
        icu = 0
        ventilated = 0
        mortality = 0
        for link in followup_links:
            total_followup += 1
            if link.data["outcome"] == "death":
                mortality += 1
            if link.data["ventilated"] == "yes":
                ventilated += 1
            if link.data["admitted_to_icu"] == "yes":
                icu += 1
        ret["data"]["pip_indicators"] = [make_dict("Total Cases", total_cases, 100)]
        ret["data"]["pip_indicators"].append(
            make_dict("Patients followed up", total_followup, total_followup / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict("Laboratory results recorded", total_lab_links, total_lab_links / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict("Patients admitted to ICU  ", icu, icu / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict("Patients ventilated", ventilated, ventilated / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict("Mortality", mortality, mortality / total_cases * 100))
        ret["data"]["demographics"] = []


        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if is_child(location, l.id, locs) and l.case_report and l.clinic_type == "SARI":
                num = get_variable_id("pip_2",
                                      start_date,
                                      end_date, l.id, conn)
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))


        # Demographis
        age =  query_variable.get("pip_2","age_gender",
                                  end_date=end_date.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)
        age_gender={}
        for a in age:
            gender,ac = a.split(" ")
            if ac in age_gender.keys():
                age_gender[ac][gender] = age[a]["total"]
            else:
                age_gender[ac] = {gender: age[a]["total"]}
        age_variables = variables_instance.get("age")
        for age_key in sorted(age_variables.keys()):
            a = age_variables[age_key]["name"]

            if a in age_gender.keys():
                a_sum = sum(age_gender[a].values())
            
                if a_sum == 0:
                    a_sum = 1
                ret["data"]["demographics"].append(
                    {"age": a,
                     "male": {"quantity": age_gender[a]["Male"],
                              "percent": age_gender[a]["Male"] / a_sum * 100
                     },
                     "female":{"quantity": age_gender[a]["Female"],
                               "percent": age_gender[a]["Female"]/float(a_sum)*100
                     }
                    })

        #Nationality
        nationality_total = query_variable.get("pip_2","nationality",
                                  end_date=end_date.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)
        nationality = {}
        for nat in nationality_total.keys():
            nationality[nat] = nationality_total[nat]["total"]
        tot_nat = sum(nationality.values())
        if tot_nat == 0:
            tot_nat=1
        ret["data"]["nationality"] = []
        for nat in sorted(nationality, key=nationality.get, reverse=True):
            if nationality[nat] > 0:
                ret["data"]["nationality"].append(
                    make_dict(nat,
                              nationality[nat],
                              nationality[nat] / tot_nat * 100))
        #Status
        status_total = query_variable.get("pip_2","status",
                                               end_date=end_date.isoformat(),
                                               start_date=start_date.isoformat(),
                                               only_loc=location)
        status = {}
        for sta in status_total.keys():
            status[sta] = status_total[sta]["total"]
        tot_sta = sum(status.values())
        if tot_sta == 0:
            tot_sta = 1
        ret["data"]["patient_status"] = []
        for sta in sorted(status, key=status.get, reverse=True):
            ret["data"]["patient_status"].append(
                make_dict(sta,
                          status[sta],
                          status[sta] / tot_sta * 100))
        return ret
    
class RefugeeDetail(Resource):
    """ Class to return data for the public health report """
    decorators = [require_api_key]
    def get(self, location, start_date=None, end_date=None):
        """ generates date for the refugee public health report for the year 
        up to epi_week for the given location"""

        if "refugee" not in model.form_tables:
            return {}

        
        start_date, end_date = fix_dates(start_date, end_date)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        location_name = locs[int(location)].name
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name
        #We first find all the refugee clinics
        refugee_clinics = get_children(location, locs, clinic_type="Refugee")
        
        ret["data"]["clinic_num"] = len(refugee_clinics)
        # Total_population we want the latest submitted total population
        male = 0
        female = 0
        age_gender = {}
        no_clinicians = 0
        for clinic in refugee_clinics:
            clinic_data = get_latest_category("population", clinic, start_date, end_date)
            for age in clinic_data:
                age_gender.setdefault(age, {})
                for gender in clinic_data[age]:
                    age_gender[age].setdefault(gender, 0)
                    age_gender[age][gender] += clinic_data[age][gender]
                    if gender == "female":
                        female += clinic_data[age][gender]
                    if gender == "male":
                        male += clinic_data[age][gender]
            result = db.session.query(Data.variables).filter(
                Data.variables.has_key("ref_14"),
                Data.clinic == clinic,
                Data.date >= start_date,
                Data.date < end_date
            ).order_by(Data.date.desc()).first()
            if result:
                no_clinicians += result[0]["ref_14"]
        tot_pop = male + female
        ret["data"]["total_population"] = tot_pop

        ret["data"]["n_clinicians"] = no_clinicians
        u5 =  sum(age_gender["0-1"].values()) + sum(age_gender["1-4"].values())
        if u5 == 0:
            u5 = 1

        #1. Population
        age_gender["total"] = tot_pop
        ret["data"]["population"] = {"Refugee Population": age_gender}

        #2. Mortality
        mortality =  get_variables_category("mortality", start_date, end_date, location, conn)
        mortality_u5 = get_variables_category("u5_mortality", start_date, end_date, location, conn)
        crude_mortality_rate = sum(mortality.values()) / tot_pop * 1000
        u5_crude_mortality_rate = sum(mortality_u5.values()) / u5 * 1000
        ret["data"]["mortality"] = []
        ret["data"]["mortality"].append(
            make_dict("Crude Mortality Rate", crude_mortality_rate, None)
        )
        ret["data"]["mortality"].append(
            make_dict("Under five crude mortality rate", u5_crude_mortality_rate,None)
            )
        ret["data"]["mortality_breakdown"] = disease_breakdown(mortality)

        #3. Morbidity
        #3.1 Staffing
        total_consultations = get_variable_id("ref_13", start_date, end_date, location, conn)
        days_of_report = (end_date-start_date).days
        ret["data"]["staffing"] = [
            make_dict("Total Consultations", total_consultations, None)
            ]
        ret["data"]["staffing"].append(
            make_dict("Number of Clinicians", no_clinicians, None)
            )
        if tot_pop == 0:
            tot_pop = 1
        if total_consultations == 0:
            total_consultations = 1
        if no_clinicians == 0:
            no_clinicians = 1
        ret["data"]["staffing"].append(
            make_dict("Health Utilisation Rate", total_consultations / tot_pop / days_of_report * 365 , None)) # per year
        ret["data"]["staffing"].append(
            make_dict("Number of consultations per clinician per day", total_consultations / no_clinicians / days_of_report, None)
            )
        #3.2 Communciable Diseases
        morbidity_cd = get_variables_category("refugee_cd", start_date, end_date, location, conn)
        ret["data"]["communicable_diseases"] = disease_breakdown(morbidity_cd)

        #3.3 Non-Communicable Diseases
        morbidity_ncd = get_variables_category("refugee_ncd", start_date, end_date, location, conn)
        ret["data"]["non_communicable_diseases"] = disease_breakdown(morbidity_ncd)

        #3.4 Mental Health
        morbidity_mh = get_variables_category("refugee_mh", start_date, end_date, location, conn)
        ret["data"]["mental_health"] = disease_breakdown(morbidity_mh)
        #3.5 Injuries
        morbidity_injury = get_variables_category("refugee_trauma", start_date, end_date, location, conn)
        ret["data"]["injury"] = disease_breakdown(morbidity_injury)
        #4 Referral
        hospital_referrals = get_variable_id("ref_15", start_date, end_date, location, conn)
        other_referrals = get_variable_id("ref_16", start_date, end_date, location, conn)
        ret["data"]["referrals"] = [
            make_dict("Hospital Referrals", hospital_referrals, None)
            ]
        ret["data"]["referrals"].append(
            make_dict("Other Referrals", other_referrals, None)
            )
        ret["data"]["referrals"].append(
            make_dict("Hospitalisation rate",
                      hospital_referrals /total_consultations, None)
        )
        ret["data"]["referrals"].append(
            make_dict("Referral rate",
                      (other_referrals + hospital_referrals) /total_consultations, None)
        )


        return ret

# Morbidity
        morbidity_cd = get_variables_category("refugee_cd", start_date, end_date, location, conn)
        morbidity_ncd = get_variables_category("refugee_ncd", start_date, end_date, location, conn)
        morbidity_injury = get_variables_category("refugee_trauma", start_date, end_date, location, conn)
        morbidity_mh = get_variables_category("refugee_mh", start_date, end_date, location, conn)
        morbidity_cd_no = sum(morbidity_cd.values())
        morbidity_ncd_no = sum(morbidity_ncd.values())
        morbidity_injury_no = sum(morbidity_injury.values())
        morbidity_mh_no = sum(morbidity_mh.values())
        total_cases = morbidity_cd_no + morbidity_ncd_no + morbidity_injury_no + morbidity_mh_no
        ret["data"]["total_cases"] = total_cases
        if total_cases == 0:
            total_cases = 1
        ret["data"]["percent_morbidity_communicable"] = morbidity_cd_no / total_cases * 100
        ret["data"]["percent_morbidity_non_communicable"] = morbidity_ncd_no / total_cases * 100
        ret["data"]["percent_morbidity_mental_health"] = morbidity_mh_no / total_cases * 100
        ret["data"]["percent_morbidity_injury_health"] = morbidity_injury_no / total_cases * 100
        hospital_referrals = get_variable_id("ref_11", start_date, end_date, location, conn)
        ret["data"]["public_health_indicators"].append(
            make_dict("Crude Mortality Rate (CMR) ",
                     crude_mortality_rate, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict("Under-five Mortality Rate (U5MR) ",
                       u5_crude_mortality_rate / total_consultations, None)
        )
        
        

   
   
        #Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for clinic in refugee_clinics:
            num =  sum(get_variables_category("refugee_morbidity", start_date, end_date, clinic, conn).values())
            ret["data"]["reporting_sites"].append(
                    make_dict(locs[clinic].name,
                              num,
                              num / total_cases * 100))

      

        ret["data"]["presenting_complaints"] = [
            make_dict("Communicable Disease", morbidity_cd_no, morbidity_cd_no / total_cases *100),
            make_dict("Non-Communicable Disease", morbidity_ncd_no, morbidity_ncd_no / total_cases *100),
            make_dict("Mental Health", morbidity_mh_no, morbidity_mh_no / total_cases *100),
            make_dict("Injury", morbidity_injury_no, morbidity_injury_no / total_cases *100)
        ]

        

        ret["data"]["morbidity_communicable"] = refugee_disease(morbidity_cd)

        ret["data"]["morbidity_non_communicable"] = refugee_disease(morbidity_ncd)
        ret["data"]["mental_health"] = refugee_disease(morbidity_mh)
        ret["data"]["injury"] = refugee_disease(morbidity_injury)
        
        return ret

def disease_breakdown(diseases):
    ret = {"diseases": {}}
    disease_total = {}
    age_gender_total = {}
    age_total = {}
    for d in diseases:
        split = d.split(",")
        disease_name = ",".join(split[:-1])
        age_gender = split[-1]
        disease_name = disease_name.strip()
        gender, age = age_gender.strip().split(" ")
        
        gender = gender.lower()
        age = age.strip()
        gender = gender.strip()
        disease_total.setdefault(disease_name, 0)
        disease_total[disease_name] += diseases[d]
        age_total.setdefault(age, 0)
        age_total[age] += diseases[d]
        age_gender_total.setdefault(age, {"male": 0, "female": 0})
        age_gender_total[age][gender] += diseases[d]
        ret["diseases"].setdefault(disease_name, {})
        ret["diseases"][disease_name].setdefault(age, {})
        ret["diseases"][disease_name][age][gender] = diseases[d]
    for d in disease_total:
        ret["diseases"][d]["total"] = disease_total[d]
    ret["age_gender"] = age_gender_total
    ret["age"] = age_total
    return ret


def get_latest_category(category, clinic, start_date, end_date):
    variables = variables_instance.get(category)
    keys = sorted(variables.keys())

    result = db.session.query(Data.variables).filter(
        or_(Data.variables.has_key(key) for key in keys),
        Data.clinic == clinic,
        Data.date >= start_date,
        Data.date < end_date
            ).order_by(Data.date.desc()).first()
    ret = {}
    for key in keys:
        name = variables[key]["name"]
        gender, age = name.split(",")[1].strip().split(" ")
        gender = gender.lower()
        age = age.strip()
        gender = gender.strip()
        ret.setdefault(age, {"female": 0, "male": 0})        
        if(result):
            ret[age][gender] += result[0][key]

    return ret


class RefugeeCd(Resource):
    """ Class to return data for the refugee cd report """
    decorators = [require_api_key]
    def get(self, location, start_date=None, end_date=None):
        """ generates date for the refugee public health report for the year 
        up to epi_week for the given location"""

        if "refugee" not in model.form_tables:
            return {}
        start_date, end_date = fix_dates(start_date, end_date)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        location_name = locs[int(location)].name
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name
        #We first find all the refugee clinics
        refugee_clinics = get_children(location, locs, clinic_type="Refugee")
        ret["data"]["clinic_num"] = len(refugee_clinics)
        weeks = list(range(1, epi_week + 1, 1))
        #List of cds
        variables = variables_instance.get("refugee_cd")
        ret["data"]["communicable_diseases"] = {}
        for v in variables.values():
            ret["data"]["communicable_diseases"].setdefault(v["name"].split(",")[0], {"weeks": weeks,
                                                                                      "suspected": []})
            # Need to loop through each epi week and add data for population and all cds per week.
        for week in weeks:
            first_day = epi_week_start(end_date.year, week)
            last_day = first_day + timedelta(days=7)
            # Population
            tot_pop = 0
            no_clinicians = 0
            for clinic in refugee_clinics:
                result = db.session.query(Data.variables).filter(
                    or_(Data.variables.has_key("ref_1"),
                        Data.variables.has_key("ref_2"),
                        Data.variables.has_key("ref_3"),
                        Data.variables.has_key("ref_4"),
                        Data.variables.has_key("ref_5"),
                        Data.variables.has_key("ref_6"),
                        Data.variables.has_key("ref_7"),
                        Data.variables.has_key("ref_8")),
                    Data.clinic == clinic,
                    Data.date >= first_day,
                    Data.date < last_day
                ).order_by(Data.date.desc()).first()
                if(result):
                    tot_pop += sum(result[0].values())
            result = db.session.query(Data.variables).filter(
                Data.variables.has_key("ref_10"),
                Data.clinic == clinic,
                Data.date >= first_day,
                Data.date < last_day
            ).order_by(Data.date.desc()).first()
            if result:
                no_clinicians += result[0]["ref_10"]
            ret["data"].setdefault("population", {"weeks": weeks,
                                                  "suspected": []})
            ret["data"].setdefault("number_clinicians", {"weeks": weeks,
                                                         "suspected": []})
            ret["data"]["population"]["suspected"].append(tot_pop)
            ret["data"]["number_clinicians"]["suspected"].append(no_clinicians)
            morbidity_cd = get_variables_category("refugee_cd", first_day, last_day, location, conn)
            diseases = {}
            for disease in morbidity_cd:
                disease_name = disease.split(",")[0]
                diseases.setdefault(disease_name, 0)
                diseases[disease_name] += morbidity_cd[disease]
            for d in diseases:
                ret["data"]["communicable_diseases"][d]["suspected"].append(diseases[d])
        return ret
def refugee_disease(disease_demo):
    diseases = {}
    for disease in disease_demo.keys():
        disease_name = disease.split(",")[0].strip()
        diseases.setdefault(disease_name, 0)
        diseases[disease_name] += disease_demo[disease]

    tot_n = sum(diseases.values())
    if tot_n == 0:
        tot_n = 1
    ret = []
    for disease in top(diseases):
        if diseases[disease] > 0:
            ret.append(make_dict(disease,
                                 diseases[disease],
                                 diseases[disease] / tot_n * 100))
    return ret
class PublicHealth(Resource):
    """ Class to return data for the public health report """
    decorators = [require_api_key]
    def get(self, location, start_date=None, end_date=None):
        """ generates date for the public health report for the year 
        up to epi_week for the given location"""
        start_date, end_date = fix_dates(start_date, end_date)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        ew = EpiWeek()
        end_date = end_date - timedelta(days=1)
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "start_date": start_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat()
        }
        conn = db.engine.connect()
        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first().name

        if not location_name:
            return None
        ret["data"]["project_region"] = location_name
        #We first add all the summary level data
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        
        ret["data"]["global_clinic_num"] = tot_clinics.get(1)["total"]
        total_cases = get_variable_id("tot_1", start_date, end_date, location, conn)
        ret["data"]["total_cases"] = total_cases
        if total_cases == 0:
            total_cases = 1
        total_consultations = get_variable_id("reg_2", start_date, end_date, location, conn)
        ret["data"]["total_consultations"] = total_consultations
        
        female = get_variable_id("gen_2", start_date, end_date, location, conn)
        male = get_variable_id("gen_1", start_date, end_date, location, conn)
        ret["data"]["percent_cases_male"] = male / total_cases*100
        ret["data"]["percent_cases_female"] = female / total_cases*100
        less_5yo = get_variable_id("age_1", start_date, end_date, location, conn)
        ret["data"]["percent_cases_lt_5yo"] = less_5yo / total_cases*100

        if less_5yo == 0:
            less_5yo = 1
        presenting_complaint = get_variables_category("pc", start_date, end_date, location, conn)
        ret["data"]["percent_morbidity_communicable"] = presenting_complaint["Communicable disease"] / total_cases * 100
        ret["data"]["percent_morbidity_non_communicable"] = presenting_complaint["Non-communicable disease"] / total_cases * 100
        ret["data"]["percent_morbidity_mental_health"] = presenting_complaint["Mental Health"] / total_cases * 100

        #public health indicators
        ret["data"]["public_health_indicators"] = [
            make_dict("Cases Reported", total_cases, 100)]
        modules = get_variables_category("module", start_date, end_date, location, conn)
        ret["data"]["public_health_indicators"].append(
            make_dict("Mental Health (mhGAP) algorithm followed",
                      modules["Mental Health (mhGAP)"],
                      modules["Mental Health (mhGAP)"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict("Child Health (IMCI) algorithm followed",
                      modules["Child Health (IMCI)"],
                      modules["Child Health (IMCI)"] / less_5yo * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict("Reproductive Health screening",
                      modules["Reproductive Health"],
                      modules["Reproductive Health"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict("Laboratory results recorded",
                      modules["Laboratory Results"],
                      modules["Laboratory Results"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict("Prescribing practice recorded",
                      modules["Prescribing"],
                      modules["Prescribing"] / total_cases * 100))
        smoking_prevalence = get_variable_id("smo_1", start_date, end_date, location, conn)
        smoking_prevalence_ever = get_variable_id("smo_2", start_date, end_date, location, conn)
        smoking_non_prevalence_ever = get_variable_id("smo_3", start_date, end_date, location, conn)

        if (smoking_prevalence_ever + smoking_non_prevalence_ever) == 0:
            smoking_prevalence_ever = 1
            ret["data"]["public_health_indicators"].append(
                make_dict("Smoking prevalence (current)",
                          smoking_prevalence,
                          smoking_prevalence / (smoking_prevalence_ever+smoking_non_prevalence_ever) * 100))

        #Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if l.parent_location and int(l.parent_location) == int(location):
                num = get_variable_id("tot_1",
                                      start_date,
                                      end_date, l.id, conn)
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))


        #Alerts
        #        aggregate_alerts = AggregateAlerts
        alerts = db.session.query(
            Alerts.reason, func.count(Alerts.id).label("count")).filter(
                Alerts.date >= start_date,
                Alerts.date < end_date).group_by(Alerts.reason).order_by(desc("count")).limit(5)
        ret["data"]["alerts"]=[]
        for a in alerts.all():
            ret["data"]["alerts"].append(
                {"subject": a[0],
                 "quantity": a[1]})
        all_alerts = db.session.query(func.count(Alerts.id)).filter(
                Alerts.date >= start_date,
                Alerts.date < end_date)
        ret["data"]["alerts_total"] = all_alerts.first()[0]

        #Demographics
        ret["data"]["demographics"] = []
        age = get_variables_category("age_gender", start_date, end_date, location, conn)
        age_gender={}
        for a in age:
            gender,ac = a.split(" ")
            if ac in age_gender.keys():
                age_gender[ac][gender] = age[a]
            else:
                age_gender[ac] = {gender: age[a]}
        age_variables = variables_instance.get("age")
        for age_key in sorted(age_variables.keys()):
            a = age_variables[age_key]["name"]
            if a in age_gender.keys():
                a_sum = sum(age_gender[a].values())
                if a_sum == 0:
                    a_sum = 1
                ret["data"]["demographics"].append(
                    {"age": a,
                     "male": {"quantity": age_gender[a]["Male"],
                              "percent": age_gender[a]["Male"] / a_sum * 100
                     },
                     "female":{"quantity": age_gender[a]["Female"],
                               "percent": age_gender[a]["Female"]/float(a_sum)*100
                     }
                    })

        #Nationality
        nationality = get_variables_category("nationality", start_date, end_date, location, conn)
        tot_nat = sum(nationality.values())
        if tot_nat == 0:
            tot_nat=1
        ret["data"]["nationality"] = []
        for nat in sorted(nationality, key=nationality.get, reverse=True):
            if nationality[nat] > 0:
                ret["data"]["nationality"].append(
                    make_dict(nat,
                              nationality[nat],
                              nationality[nat] / tot_nat * 100))
        #Status
        status = get_variables_category("status", start_date, end_date, location, conn)
        tot_sta = sum(status.values())
        if tot_sta == 0:
            tot_sta = 1
        ret["data"]["patient_status"] = []
        for sta in sorted(status, key=status.get, reverse=True):
            ret["data"]["patient_status"].append(
                make_dict(sta,
                          status[sta],
                          status[sta] / tot_sta * 100))
            

        #Presenting Complaint

        tot_pc = sum(presenting_complaint.values())
        if tot_pc == 0:
            tot_pc = 1
        ret["data"]["presenting_complaints"] = []
        for p in presenting_complaint:
            ret["data"]["presenting_complaints"].append(
                make_dict(p,
                          presenting_complaint[p],
                          presenting_complaint[p] / tot_pc * 100))

            
        ret["data"]["morbidity_communicable"] = get_disease_types("cd", start_date, end_date, location, conn)
        ret["data"]["morbidity_communicable_tab"] = get_disease_types("cd_tab", start_date, end_date, location, conn)
        ret["data"]["morbidity_non_communicable"] = get_disease_types("ncd", start_date, end_date, location, conn)
        ret["data"]["morbidity_non_communicable_tab"] = get_disease_types("ncd_tab", start_date, end_date, location, conn)
        ret["data"]["mental_health"] = get_disease_types("mh", start_date, end_date, location, conn)

        ch={}
        query_variable = QueryVariable()
        child_disease = query_variable.get("age_1","for_child",
                                           end_date=end_date.isoformat(),
                                           start_date=start_date.isoformat(),
                                           only_loc=location)
        for chi in child_disease.keys():
            ch[chi] = child_disease[chi]["total"]

        tot_ch = sum(ch.values())
        if tot_ch == 0:
            tot_ch = 1
        ret["data"]["child_health"] = []
        for disease in top(ch):
            if ch[disease] > 0:
                ret["data"]["child_health"].append(
                    make_dict(disease,
                              ch[disease],
                              ch[disease] / tot_ch * 100))
        return ret




    

class CdPublicHealth(Resource):
    """ Class to return data for the public health report """
    decorators = [require_api_key]
    def get(self, location, start_date=None, end_date=None):
        """ generates date for the public health report for the year 
        up to epi_week for the given location"""
        start_date, end_date = fix_dates(start_date, end_date)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first().name

        if not location_name:
            return None
        ret["data"]["project_region"] = location_name
        #We first add all the summary level data
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        
        ret["data"]["global_clinic_num"] = tot_clinics.get(1)["total"]

        total_cases = get_variable_id("prc_1", start_date, end_date, location, conn)
        ret["data"]["total_cases"] = total_cases
        if total_cases == 0:
            total_cases = 1
        query_variable = QueryVariable()
        gender = query_variable.get("prc_1","gender",
                                    end_date=end_date.isoformat(),
                                    start_date=start_date.isoformat(),
                                    only_loc=location)
        age = query_variable.get("prc_1","age",
                                 end_date=end_date.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)
        female = gender["Female"]["total"]
        male = gender["Male"]["total"]
        ret["data"]["gender"] = [
            make_dict("Female",
                      female,
                      female / total_cases * 100),
            make_dict("Male",
                      male,
                      male / total_cases * 100)
            ]
            
        ret["data"]["percent_cases_male"] = male / total_cases*100
        ret["data"]["percent_cases_female"] = female / total_cases*100
        less_5yo = age["<5"]["total"]
        ret["data"]["percent_cases_lt_5yo"] = less_5yo / total_cases*100

        if less_5yo == 0:
            less_5yo = 1
        #public health indicators
        modules = query_variable.get("prc_1","module",
                                 end_date=end_date.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)

        ret["data"]["public_health_indicators"] = [
            make_dict("Cases Reported", total_cases, 100)]
        ret["data"]["public_health_indicators"].append(
            make_dict("Laboratory results recorded",
                      modules["Laboratory Results"]["total"],
                      modules["Laboratory Results"]["total"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict("Prescribing practice recorded",
                      modules["Prescribing"]["total"],
                      modules["Prescribing"]["total"] / total_cases * 100))
        #Alerts
        all_alerts = alerts.get_alerts({"location": location})
        tot_alerts = 0
        investigated_alerts = 0
        for a in all_alerts.values():
            if a["alerts"]["date"] <= end_date and a["alerts"]["date"] > start_date:
                tot_alerts += 1
                report_status = False
                if "links" in a and "alert_investigation" in a["links"]:
                    investigated_alerts += 1
        ret["data"]["public_health_indicators"].append(
            make_dict("Alerts generated",
                      tot_alerts,
                      100)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict("Alerts investigated",
                      investigated_alerts,
                      investigated_alerts / tot_alerts * 100)
        )
        
                
        #Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if l.parent_location and int(l.parent_location) == int(location):
                num = get_variable_id("prc_1",
                                      start_date,
                                      end_date, l.id, conn)
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))


        ret["data"]["alerts_total"] = tot_alerts

        #Demographics
        ret["data"]["demographics"] = []
        age =  query_variable.get("prc_1","age_gender",
                                  end_date=end_date.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)
        age_gender={}
        for a in age:
            gender,ac = a.split(" ")
            if ac in age_gender.keys():
                age_gender[ac][gender] = age[a]["total"]
            else:
                age_gender[ac] = {gender: age[a]["total"]}

        age_variables = variables_instance.get("age")
        for age_key in sorted(age_variables.keys()):
            a = age_variables[age_key]["name"]
            if a in age_gender.keys():
                a_sum = sum(age_gender[a].values())
            
                if a_sum == 0:
                    a_sum = 1
                ret["data"]["demographics"].append(
                    {"age": a,
                     "male": {"quantity": age_gender[a]["Male"],
                              "percent": age_gender[a]["Male"] / a_sum * 100
                     },
                     "female":{"quantity": age_gender[a]["Female"],
                               "percent": age_gender[a]["Female"]/float(a_sum)*100
                     }
                    })

        #Nationality
        nationality_total = query_variable.get("prc_1","nationality",
                                  end_date=end_date.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)
        nationality = {}
        for nat in nationality_total.keys():
            nationality[nat] = nationality_total[nat]["total"]
        tot_nat = sum(nationality.values())
        if tot_nat == 0:
            tot_nat=1
        ret["data"]["nationality"] = []
        for nat in sorted(nationality, key=nationality.get, reverse=True):
            if nationality[nat] > 0:
                ret["data"]["nationality"].append(
                    make_dict(nat,
                              nationality[nat],
                              nationality[nat] / tot_nat * 100))
        #Status
        status_total = query_variable.get("prc_1","status",
                                               end_date=end_date.isoformat(),
                                               start_date=start_date.isoformat(),
                                               only_loc=location)
        status = {}
        for sta in status_total.keys():
            status[sta] = status_total[sta]["total"]
        tot_sta = sum(status.values())
        if tot_sta == 0:
            tot_sta = 1
        ret["data"]["patient_status"] = []
        for sta in sorted(status, key=status.get, reverse=True):
            ret["data"]["patient_status"].append(
                make_dict(sta,
                          status[sta],
                          status[sta] / tot_sta * 100))
            

            
        ret["data"]["morbidity_communicable_icd"] = get_disease_types("cd", start_date, end_date, location, conn)
        ret["data"]["morbidity_communicable_cd_tab"] = get_disease_types("cd_tab", start_date, end_date, location, conn)
        return ret
class NcdPublicHealth(Resource):
    """ Class to return data for the public health report """
    decorators = [require_api_key]
    def get(self, location, start_date=None, end_date=None):
        """ generates date for the ncd public health report for the year 
        up to epi_week for the given location"""
        start_date, end_date = fix_dates(start_date, end_date)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first().name

        if not location_name:
            return None
        ret["data"]["project_region"] = location_name
        #We first add all the summary level data
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        
        ret["data"]["global_clinic_num"] = tot_clinics.get(1)["total"]

        total_cases = get_variable_id("prc_2", start_date, end_date, location, conn)
        ret["data"]["total_cases"] = total_cases
        if total_cases == 0:
            total_cases = 1
        query_variable = QueryVariable()
        gender = query_variable.get("prc_2","gender",
                                    end_date=end_date.isoformat(),
                                    start_date=start_date.isoformat(),
                                    only_loc=location)
        age = query_variable.get("prc_2","age",
                                 end_date=end_date.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)
        female = gender["Female"]["total"]
        male = gender["Male"]["total"]
        ret["data"]["gender"] = [
            make_dict("Female",
                      female,
                      female / total_cases * 100),
            make_dict("Male",
                      male,
                      male / total_cases * 100)
            ]
            
        ret["data"]["percent_cases_male"] = male / total_cases*100
        ret["data"]["percent_cases_female"] = female / total_cases*100
        less_5yo = age["<5"]["total"]
        ret["data"]["percent_cases_lt_5yo"] = less_5yo / total_cases*100

        if less_5yo == 0:
            less_5yo = 1
        #public health indicators
        modules = query_variable.get("prc_2","module",
                                 end_date=end_date.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)

        ret["data"]["public_health_indicators"] = [
            make_dict("Cases Reported", total_cases, 100)]
        ret["data"]["public_health_indicators"].append(
            make_dict("Laboratory results recorded",
                      modules["Laboratory Results"]["total"],
                      modules["Laboratory Results"]["total"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict("Prescribing practice recorded",
                      modules["Prescribing"]["total"],
                      modules["Prescribing"]["total"] / total_cases * 100))
        #Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if l.parent_location and int(l.parent_location) == int(location):
                num = get_variable_id("prc_2",
                                      start_date,
                                      end_date, l.id, conn)
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))

        #Demographics
        ret["data"]["demographics"] = []
        age =  query_variable.get("prc_2","age_gender",
                                  end_date=end_date.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)
        age_gender={}
        for a in age:
            gender,ac = a.split(" ")
            if ac in age_gender.keys():
                age_gender[ac][gender] = age[a]["total"]
            else:
                age_gender[ac] = {gender: age[a]["total"]}
        age_variables = variables_instance.get("age")
        for age_key in sorted(age_variables.keys()):
            a = age_variables[age_key]["name"]

            if a in age_gender.keys():
                a_sum = sum(age_gender[a].values())
            
                if a_sum == 0:
                    a_sum = 1
                ret["data"]["demographics"].append(
                    {"age": a,
                     "male": {"quantity": age_gender[a]["Male"],
                              "percent": age_gender[a]["Male"] / a_sum * 100
                     },
                     "female":{"quantity": age_gender[a]["Female"],
                               "percent": age_gender[a]["Female"]/float(a_sum)*100
                     }
                    })

        #Nationality
        nationality_total = query_variable.get("prc_2","nationality",
                                  end_date=end_date.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)
        nationality = {}
        for nat in nationality_total.keys():
            nationality[nat] = nationality_total[nat]["total"]
        tot_nat = sum(nationality.values())
        if tot_nat == 0:
            tot_nat=1
        ret["data"]["nationality"] = []
        for nat in sorted(nationality, key=nationality.get, reverse=True):
            if nationality[nat] > 0:
                ret["data"]["nationality"].append(
                    make_dict(nat,
                              nationality[nat],
                              nationality[nat] / tot_nat * 100))
        #Status
        status_total = query_variable.get("prc_2","status",
                                               end_date=end_date.isoformat(),
                                               start_date=start_date.isoformat(),
                                               only_loc=location)
        status = {}
        for sta in status_total.keys():
            status[sta] = status_total[sta]["total"]
        tot_sta = sum(status.values())
        if tot_sta == 0:
            tot_sta = 1
        ret["data"]["patient_status"] = []
        for sta in sorted(status, key=status.get, reverse=True):
            ret["data"]["patient_status"].append(
                make_dict(sta,
                          status[sta],
                          status[sta] / tot_sta * 100))
            

            
        ret["data"]["morbidity_non_communicable_icd"] = get_disease_types("ncd", start_date, end_date, location, conn)
        ret["data"]["morbidity_non_communicable_ncd_tab"] = get_disease_types("ncd_tab", start_date, end_date, location, conn)
        return ret




def get_disease_types(category, start_date, end_date, location, conn):
    """ Get and return top five disease of a type """
    diseases = get_variables_category(category, start_date,
                                      end_date, location, conn)
    tot_n = sum(diseases.values())
    if tot_n == 0:
        tot_n = 1

    ret = []
    for disease in top(diseases):
        if diseases[disease] > 0:
            ret.append(make_dict(disease,
                                 diseases[disease],
                                 diseases[disease] / tot_n * 100))
    return ret
def make_dict(name,quantity,percent):
    return {"title": name,
            "quantity": quantity,
            "percent": percent}

def top(values, number=5):
    return sorted(values,key=values.get,reverse=True)[:number]


qu = text("SELECT sum(CAST(data.variables ->> :variables_1 AS INTEGER)) AS sum_1  FROM data WHERE (data.variables ? :variables_2) AND data.date >= :date_1 AND data.date < :date_2 AND (data.country = :country_1 OR data.region = :region_1 OR data.district = :district_1 OR data.clinic = :clinic_1)")

def get_variable_id(variable_id, start_date, end_date, location, conn):
    """ Get the sum of variable_id between start and end date with location"""
    result = conn.execute(qu,variables_1 = variable_id, variables_2=variable_id,
                          date_1=start_date,date_2=end_date,country_1=location,
                          region_1=location,district_1=location,clinic_1=location).fetchone()[0]
    if result:
        return result
    else:
        return 0

variables_instance = Variables()

def get_variables_category(category, start_date, end_date, location, conn, category2=None):
    """ Aggregate category between dates and with location"""

    variables = variables_instance.get(category)
    return_data = {}
    for variable in variables.keys():
        r = get_variable_id(variable,
                           start_date,
                           end_date,
                            location,
                            conn)
        return_data[variables[variable]["name"]] = r
    return return_data



# if __name__ == "__main__":
#     print(get_variables_category("cd", datetime(2016,1,1),datetime(2017,1,1)))
