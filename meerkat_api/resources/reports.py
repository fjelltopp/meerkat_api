"""
Resource for Reports. 

The Reports are specified collections of data that can easily be visualised
in a html or pdf report. 

This large file includes the following reports:

NCD Report
CD Report
Public Health Profile
NCD Profile
CD Profile
Refugee Profile
Refugee CD Report
Refugee Detailed Report
"""

from flask_restful import Resource
from sqlalchemy import or_, func, desc
from datetime import datetime, timedelta
from dateutil import parser
from sqlalchemy.sql import text
import uuid
from gettext import gettext

from meerkat_api.util import get_children, is_child
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
    """
    We parse the start and end date and remove any timezone information

    Args: 
       start_date: start date
       end_date: end_date
    Returns:
       dates(tuple): (start_date, end_date)
    """
    if end_date:
        end_date  = parser.parse(end_date).replace(tzinfo=None)
    else:
        end_date = datetime.now()
    if start_date:
        start_date = parser.parse(start_date).replace(tzinfo=None)
    else:
        start_date = end_date.replace(month=1, day=1,
                                      hour=0, second=0,
                                      minute=0,
                                      microsecond=0)
    return start_date, end_date



def get_disease_types(category, start_date, end_date, location, conn):
    """ 
    Get and return top five disease of a type

    Args: 
       category: the category to get the top five disease from
       start_date: the start date for the aggregation
       end_date: the end_date for the aggregation
       location: the location to incldue
       conn: db.connection

    Returns: 
       top_five_disease(list): ordered list of top five disease with percentage
    
    """
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

def make_dict(title, quantity, percent):
    """
    Small utility to create dictionary with title, quantity and percent

    Args: 
       title: The title
       quantity: quantity
       percent: percent
    
    Returns: 
       dict(dict): Dictionary
    """
    return {"title": title,
            "quantity": quantity,
            "percent": percent}

def top(values, number=5):
    """
    Return the dict containg the top number(defaults to 5) values.
    If we ask for the top 2 and the data looks like {"A": 5, "B": 5, "C": 5}
    we will sort on the keys and take A and B. 

    Args:
       values: the dict with data
       number: how many we include (default=5)
    Returns:
       top_x(dict): dict with the number highest values
    """
    return sorted(values, key=lambda k: (-values[k], k))[:number]


# A predifend query to use in get_variable_id
qu = text("SELECT sum(CAST(data.variables ->> :variables_1 AS INTEGER)) AS sum_1  FROM data WHERE (data.variables ? :variables_2) AND data.date >= :date_1 AND data.date < :date_2 AND (data.country = :country_1 OR data.region = :region_1 OR data.district = :district_1 OR data.clinic = :clinic_1)")


def get_variable_id(variable_id, start_date, end_date, location, conn):
    """
    Get the sum of variable_id between start and end date with location

    Args: 
       variable_id: the variable_id to aggregate
       start_date: the start date for the aggregation
       end_date: the end_date for the aggregation
       location: the location to incldue
       conn: db.connection

    Returns: 
       result(int): result of the aggregation
    """

    result = conn.execute(qu, variables_1=variable_id,
                          variables_2=variable_id,
                          date_1=start_date,
                          date_2=end_date,
                          country_1=location,
                          region_1=location,
                          district_1=location,
                          clinic_1=location).fetchone()[0]
    if result:
        return result
    else:
        return 0

# Commond variables_instance
variables_instance = Variables()


def get_variables_category(category, start_date, end_date, location, conn, use_ids=False):
    """
    Aggregate category between dates and with location

    Args: 
       category: the category to get the top five disease from
       start_date: the start date for the aggregation
       end_date: the end_date for the aggregation
       location: the location to incldue
       conn: db.connection
       use_ids: we use ids instead of names as keys for the return dict

    Returns: 
       aggregate_category(dict): dict with {variable: number, variable2: number3, ...}
    """
    variables = variables_instance.get(category)

    return_data = {}
    for variable in variables.keys():
        r = get_variable_id(variable,
                           start_date,
                           end_date,
                            location,
                            conn)
        if use_ids:
            return_data[variable] = r
        else:
            return_data[variables[variable]["name"]] = r
    return return_data


def disease_breakdown(diseases):
    """
    Calculate the age and gender breakdown of dieases with codes of the following 
    format: "Disease, Gender AgeGroup". This is to deal with the refugee data
    that is submitted in an aggregated format instead of by cases.

    Args: 
       diseases: dict with Variable Name: value
    Returns:
      diseases(dict): formatted disease dict with dieases and age and gender breakdown

    """
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
    """
    To deal with data submitted in an aggregated way. We have e.g Population data that is
    submitted as the number of males <5, males 5-14 etc. These indicators are also not cumulative, 
    we just want to find the latest record where any of the population data(in this example) has
    been submitted. Once that record is found we sort out the variable names that are of this format
    "Category, Gender AgeGroup" into a structured dict of demographics. 

    Args:get_variables_category(category, start_date, end_date, location, conn, use_ids=False):
       category: the category to get the top five disease from
       clinic: the clinic we are looking at
       start_date: the start date for the aggregation
       end_date: the end_date for the aggregation
    Returns: 
       latest_demo(dict): the demographics from the latest record

    """
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
        if(result and key in result[0]):
            ret[age][gender] += result[0][key]

    return ret

def refugee_disease(disease_demo):
    """
    From a dict of Variable Name: value where variable name includes
    gender and age information we want to just find the total numbers
    for each diseases.

    Args: 
       disease_demo: dict with disease data that includes demographics in the variable name
    Returns: 
       diseases(dict): diseases with their aggregated value over all demographics
    """
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


class NcdReport(Resource):
    """
    Ncd Report to show data on Hypertension and Diabetes. The data includes 
    breakdowns by age and on lab data, complications and comorbidity. We create
    tables with rows for regions. 

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [require_api_key]
    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        # Dates and Location Name
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015, 5, 20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first()
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name.name
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        # Data on Hypertension and Diabebtes, there are two tables for each disease.
        # One for the age breakdown, and one for labs and complications.
        # For each table we have rows for each Region.
        # Each of these tables have a title key for the X-axis titles
        # Data is list of rows(dicts) with a title for the y-axis title and
        # a list of values that are the values for the row in the right order
        
        ret["hypertension"] = {"age": {}, "complications": {}}
        ret["diabetes"] = {"age": {}, "complications": {}}

        diabetes_id = "ncd_1"
        hypertension_id = "ncd_2"
        diseases = {"hypertension": hypertension_id,
                    "diabetes": diabetes_id}
        ids_to_include = {"hypertension": [("lab_4", "lab_3"), ("lab_5", "lab_3"), ("lab_2", "lab_1"), ("com_1", "tot"), ("smo_2", "smo_4"), ("lab_11", "lab_10")],
                          "diabetes": [("lab_4", "lab_3"), ("lab_5", "lab_3"), ("lab_7", "lab_6"), ("lab_9", "lab_8"), ("com_2", "tot"), ("smo_2", "smo_4"), ("lab_11", "lab_10")]
        }
  
        locations, ldid, regions, districts = all_location_data(db.session)
        v = Variables()
        ages = v.get("ncd_age")
        
        # Loop through diabetes and hypertension
        for disease in diseases.keys():
            # First sort out the titles
            ret[disease]["age"]["titles"] = [gettext("reg")]
            ret[disease]["age"]["data"] = []
            for age in sorted(ages.keys()):
                ret[disease]["age"]["titles"].append(ages[age]["name"])
            ret[disease]["age"]["titles"].append("Total")
            ret[disease]["complications"]["titles"] = [gettext("reg"),
                                                       gettext("tot"),
                                                       gettext("gen_1"),
                                                       gettext("gen_2")]
  
            for i in ids_to_include[disease]:
                ret[disease]["complications"]["titles"].append(i[0])
            ret[disease]["complications"]["data"] = []

            # Loop through each region, we add [1] to include the whole country
            for i, region in enumerate(sorted(regions) + [1]):
                d_id = diseases[disease]
                query_variable = QueryVariable()
                # get the age breakdown
                disease_age = query_variable.get(d_id, "ncd_age",
                                                 end_date=end_date_limit.isoformat(),
                                                 start_date=start_date.isoformat(),
                                                 only_loc=region,
                                                 use_ids=True)
                loc_name = locations[region].name
                if region == 1:
                    loc_name = gettext("Total")
                ret[disease]["age"]["data"].append(
                    {"title": loc_name, "values": []}
                )
                
                for age in sorted(ages.keys()):
                    ret[disease]["age"]["data"][i]["values"].append(disease_age[age]["total"])
                ret[disease]["age"]["data"][i]["values"].append(sum( [a["total"] for a in disease_age.values()]))
                # Get gender breakdown
                disease_gender = query_variable.get(d_id, "gender",
                                                    end_date=end_date_limit.isoformat(),
                                                    start_date=start_date.isoformat(),
                                                    only_loc=region)

                table_two_total = sum([disease_gender[gender]["total"] for gender in disease_gender])
                ret[disease]["complications"]["data"].append(
                    {
                        "title": loc_name,
                        "values": [table_two_total]
                    })
                if table_two_total == 0:
                    table_two_total = 1
                ret[disease]["complications"]["data"][i]["values"].append([disease_gender["Male"]["total"],  disease_gender["Male"]["total"] /table_two_total * 100])
                ret[disease]["complications"]["data"][i]["values"].append([disease_gender["Female"]["total"],  disease_gender["Female"]["total"] / table_two_total * 100])

                
                # Get the lab breakdown
                for new_id in ids_to_include[disease]:
                    if new_id[0]:
                        numerator = query_ids([d_id, new_id[0]], start_date, end_date_limit, only_loc=region)
                        if new_id[1] == "tot":
                            denominator = table_two_total
                        else:
                            denominator = query_ids([d_id, new_id[1]], start_date, end_date_limit, only_loc=region)
                        if denominator == 0:
                            denominator = 1
                        ret[disease]["complications"]["data"][i]["values"].append(
                            [numerator, numerator/ denominator * 100])
                    else:
                        # We can N/A to the table if it includes data we are not collecting
                        ret[disease]["complications"]["data"][i]["values"].append("N/A")
            
        return ret


class CdReport(Resource):
    """
    Communicable Disease Report

    This report includes data on all disease that generate alerts. For each
    of these diseases we generate a timeline of the number of cases per week. 
    We split these cases into supected and confrimed cases and only show data
    for disease where there at least one case. 

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [require_api_key]
    
    def get(self, location, start_date = None,end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        # Date and Location information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": start_date.isoformat(),
                       "start_date": start_date.isoformat()
        }

        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first()
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name.name
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        # We use the data in the alert table with alert_investigation links
        # Each alert is either classified as suspected, confirmed. We do not include
        # discarded alerts.

        # To get this data we loop through every alert and determine it's status
        # and which week it belongs to. We then assemble this data in the return dict.
        
        all_alerts = alerts.get_alerts({"location": location})
        data = {}
        ewg = ew.get(start_date.isoformat())
        start_epi_week = ewg["epi_week"]
        start_year = ewg["year"]
        year_diff = end_date.year - start_year
        start_epi_week = start_epi_week - year_diff * 52
        weeks = [i for i in range(start_epi_week, epi_week + 1, 1)]

        nice_weeks = []
        for w in weeks:
            i = 0
            while w <= 0:
                w += 52
                i += 1
            if w == 1:
                # This is to add an indication that this is a new year
                w = "Week 1, " + str(end_date.year - i)
            nice_weeks.append(w)
        
        data_list = [0 for week in weeks]
        variable_query = db.session.query(AggregationVariables).filter(
            AggregationVariables.alert == 1)
        variable_names = {}
        for v in variable_query.all():
            variable_names[v.id] = v.name
        # The loop through all alerts
        for a in all_alerts.values():
            if a["alerts"]["date"] <= end_date and a["alerts"]["date"] >= start_date:
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
                year_diff = end_date.year - a["alerts"]["date"].year
                epi_week = epi_week - 52 * year_diff
                if report_status:
                    data.setdefault(reason, {"weeks": nice_weeks,
                                             "suspected": list(data_list),
                                             "confirmed": list(data_list)})
                    data[reason][report_status][weeks.index(epi_week)] += 1

        ret["data"]["communicable_diseases"] = data
        return ret


class Pip(Resource):
    """
    Pandemic Influenza Preparedness (PIP) Report

    This report shows data on the patients with severe acute respiratory infections (SARI).
    We include data on their treatmend and on lab data to confirm the type of Influenza.

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [require_api_key]

    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        # Date and location information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)].name
        ret["data"]["project_region"] = location_name
        
        #We first find the number of SARI sentinel sites
        sari_clinics = get_children(location, locs, clinic_type="SARI")
        ret["data"]["num_clinic"] = len(sari_clinics)
        query_variable = QueryVariable()

        # Now want the gender highlevel information about SARi patients
        # the code pip_2 give patients with SARI
        sari_code = "pip_2"
        
        gender = query_variable.get(sari_code, "gender",
                                    end_date=end_date_limit.isoformat(),
                                    start_date=start_date.isoformat(),
                                    only_loc=location)
        total_cases = get_variable_id(sari_code, start_date, end_date_limit, location, conn)
        ret["data"]["total_cases"] = total_cases
        ret["data"]["pip_indicators"] = [make_dict(gettext("Total Cases"), total_cases, 100)]
        if total_cases == 0:
            # So the future divsions by total_cases does not break in case of zero cases
            total_cases = 1
        ret["data"]["gender"] = [
            make_dict(gettext("Female"),
                      gender["Female"]["total"],
                      gender["Female"]["total"] / total_cases * 100),
            make_dict(gettext("Male"),
                      gender["Male"]["total"],
                      gender["Male"]["total"] / total_cases * 100)
            ]
        ret["data"]["percent_cases_female"] = (gender["Female"]["total"] / total_cases) * 100
        ret["data"]["percent_cases_male"] = (gender["Male"]["total"] / total_cases) * 100

        # We now want to get a timeline of the lab confirmed influenze types.
        # The Influenza types and other pip related variables have category pip
        pip_cat = query_variable.get(sari_code, "pip",
                                         end_date=end_date.isoformat(),
                                         start_date=start_date.isoformat(),
                                         only_loc=location,
                                         use_ids=True)
        if pip_cat == {}:
            return ret
        weeks = sorted(pip_cat[sari_code]["weeks"].keys(), key=float)
        nice_weeks = []
        for w in weeks:
            i = 0
            while w > 53:
                w -= 52
                i += 1
            if w == 1:
                # To get a nice display when the period spans multiple years
                w = "Week 1, " + str(start_date.year + i)
            nice_weeks.append(w)
        ret["data"]["timeline"] = {
            "suspected": [pip_cat[sari_code]["weeks"][k] if k in pip_cat[sari_code]["weeks"] else 0 for k in weeks],
            "weeks": nice_weeks,
            "confirmed": {
                gettext("Influenza A"): [0 for w in weeks],
                gettext("Influenza B"): [0 for w in weeks],
                gettext("H1"): [0 for w in weeks],
                gettext("H3"): [0 for w in weeks],
                gettext("H1N1"): [0 for w in weeks],
                gettext("Mixed"): [0 for w in weeks]
                }
            }

        # Treatment and situation indicators
        ret["data"]["percent_cases_chronic"] = (pip_cat["pip_3"]["total"] / total_cases ) * 100
        ret["data"]["cases_chronic"] = pip_cat["pip_3"]["total"]
        
        # Lab links and follow up links
        lab_links = db.session.query(model.Links).filter(model.Links.link_def == "pip")
        total_lab_links = 0
        lab_types = {gettext("Influenza A"): 0,
                     gettext("Influenza B"): 0,
                     gettext("H1"): 0,
                     gettext("H3"): 0,
                     gettext("H1N1"): 0,
                     gettext("Mixed"): 0
                     }
        # Assembling the timeline with suspected cases and the confirmed cases
        # from the lab linkage
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
        ret["data"]["timeline"]["confirmed"] = [
            {"title": key, "values": list(tl[key])} for key in sorted(tl, key=lambda k: (-sum(tl[k]), k))
        ]
                                                 
        ret["data"]["cases_pcr"] = total_lab_links
        
        ret["data"]["flu_type"] = []
        for l in ["Influenza A", "Influenza B", "H1", "H3", "H1N1", "Mixed"]:
            ret["data"]["flu_type"].append(
                make_dict(l, lab_types[l], (lab_types[l]/total_cases) * 100)
            )
        #Followup indicators
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

        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Patients followed up"), total_followup, total_followup / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Laboratory results recorded"), total_lab_links, total_lab_links / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Patients admitted to ICU"), icu, icu / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Patients ventilated"), ventilated, ventilated / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Mortality"), mortality, mortality / total_cases * 100))
        ret["data"]["demographics"] = []

        # Reportin sites
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if is_child(location, l.id, locs) and l.case_report and l.clinic_type == "SARI":
                num = get_variable_id(sari_code,
                                      start_date,
                                      end_date_limit, l.id, conn)
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))


        # Demographis
        age =  query_variable.get(sari_code,"age_gender",
                                  end_date=end_date_limit.isoformat(),
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
        nationality_total = query_variable.get(sari_code,"nationality",
                                  end_date=end_date_limit.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)
        nationality = {}
        for nat in nationality_total.keys():
            nationality[nat] = nationality_total[nat]["total"]
        tot_nat = sum(nationality.values())
        if tot_nat == 0:
            tot_nat = 1
        ret["data"]["nationality"] = []
        for nat in sorted(nationality, key=nationality.get, reverse=True):
            if nationality[nat] > 0:
                ret["data"]["nationality"].append(
                    make_dict(nat,
                              nationality[nat],
                              nationality[nat] / tot_nat * 100))
        #Status
        status_total = query_variable.get(sari_code,"status",
                                               end_date=end_date_limit.isoformat(),
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


    
class PublicHealth(Resource):
    """
    Public Health Profile Report

    This reports gives an overview summary over the data from the project 
    Including NCD, Mental Health, CD, Injuries, reporting locations and demographics

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [require_api_key]

    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        # Dates and Location
        ew = EpiWeek()
        end_date = end_date
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "start_date": start_date.isoformat(),
                       "project_epoch": datetime(2015, 5, 20).isoformat()
        }
        conn = db.engine.connect()
        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first()
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name.name

        #We first add all the summary level data
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        
        ret["data"]["global_clinic_num"] = tot_clinics.get(1)["total"]
        total_cases = get_variable_id("tot_1", start_date, end_date_limit, location, conn)
        ret["data"]["total_cases"] = total_cases
        # We need to divded by total cases(and some other numbers) so we make sure we don't divide
        # by zero in cases of no cases. 
        if total_cases == 0:
            total_cases = 1
        total_consultations = get_variable_id("reg_2", start_date, end_date_limit, location, conn)
        ret["data"]["total_consultations"] = total_consultations
        female = get_variable_id("gen_2", start_date, end_date_limit, location, conn)
        male = get_variable_id("gen_1", start_date, end_date_limit, location, conn)
        ret["data"]["percent_cases_male"] = male / total_cases*100
        ret["data"]["percent_cases_female"] = female / total_cases*100
        less_5yo = sum(get_variables_category("under_five", start_date, end_date_limit, location, conn).values())
        ret["data"]["percent_cases_lt_5yo"] = less_5yo / total_cases*100
        if less_5yo == 0:
            less_5yo = 1
        presenting_complaint = get_variables_category("pc", start_date, end_date_limit, location, conn)
        ret["data"]["percent_morbidity_communicable"] = presenting_complaint["Communicable disease"] / total_cases * 100
        ret["data"]["percent_morbidity_non_communicable"] = presenting_complaint["Non-communicable disease"] / total_cases * 100
        ret["data"]["percent_morbidity_mental_health"] = presenting_complaint["Mental Health"] / total_cases * 100

        # Public health indicators
        ret["data"]["public_health_indicators"] = [
            make_dict("Cases Reported", total_cases, 100)]
        modules = get_variables_category("module", start_date, end_date_limit, location, conn)
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Mental Health (mhGAP) algorithm followed"),
                      modules["Mental Health (mhGAP)"],
                      modules["Mental Health (mhGAP)"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Child Health (IMCI) algorithm followed"),
                      modules["Child Health (IMCI)"],
                      modules["Child Health (IMCI)"] / less_5yo * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Reproductive Health screening"),
                      modules["Reproductive Health"],
                      modules["Reproductive Health"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Laboratory results recorded"),
                      modules["Laboratory Results"],
                      modules["Laboratory Results"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Prescribing practice recorded"),
                      modules["Prescribing"],
                      modules["Prescribing"] / total_cases * 100))
        smoking_prevalence = get_variable_id("smo_2", start_date, end_date_limit, location, conn)
        smoking_prevalence_ever = get_variable_id("smo_1", start_date, end_date_limit, location, conn)
        smoking_non_prevalence_ever = get_variable_id("smo_3", start_date, end_date_limit, location, conn)

        if (smoking_prevalence_ever + smoking_non_prevalence_ever) == 0:
            smoking_prevalence_ever = 1
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Smoking prevalence (current)"),
                      smoking_prevalence,
                      smoking_prevalence / (smoking_prevalence_ever+smoking_non_prevalence_ever) * 100))

        #Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if l.level == "clinic" and l.case_report == 0:
                continue
            if l.parent_location and int(l.parent_location) == int(location):
                num = get_variable_id("tot_1",
                                      start_date,
                                      end_date_limit, l.id, conn)
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))


        #Alerts
        alerts = db.session.query(
            Alerts.reason, func.count(Alerts.id).label("count")).filter(
                Alerts.date >= start_date,
                Alerts.date < end_date_limit).group_by(Alerts.reason).order_by(desc("count")).limit(5)
        ret["data"]["alerts"]=[]
        for a in alerts.all():
            ret["data"]["alerts"].append(
                {"subject": a[0],
                 "quantity": a[1]})
        all_alerts = db.session.query(func.count(Alerts.id)).filter(
                Alerts.date >= start_date,
                Alerts.date < end_date_limit)
        ret["data"]["alerts_total"] = all_alerts.first()[0]

        #Demographics
        ret["data"]["demographics"] = []
        age = get_variables_category("age_gender", start_date, end_date_limit, location, conn)
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
        nationality = get_variables_category("nationality", start_date, end_date_limit, location, conn)
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
        status = get_variables_category("status", start_date, end_date_limit, location, conn)
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
        for p in sorted(presenting_complaint, key=presenting_complaint.get, reverse=True):
            ret["data"]["presenting_complaints"].append(
                make_dict(p,
                          presenting_complaint[p],
                          presenting_complaint[p] / tot_pc * 100))

            
        ret["data"]["morbidity_communicable"] = get_disease_types("cd", start_date, end_date_limit, location, conn)
        ret["data"]["morbidity_communicable_tab"] = get_disease_types("cd_tab", start_date, end_date_limit, location, conn)
        ret["data"]["morbidity_non_communicable"] = get_disease_types("ncd", start_date, end_date_limit, location, conn)
        ret["data"]["morbidity_non_communicable_tab"] = get_disease_types("ncd_tab", start_date, end_date_limit, location, conn)
        ret["data"]["mental_health"] = get_disease_types("mh", start_date, end_date_limit, location, conn)

        ch={}
        query_variable = QueryVariable()
        child_disease = query_variable.get("age_1","for_child",
                                           end_date=end_date_limit.isoformat(),
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
    """
    Public Health Profile Report for Communicable Diseases

    This reports gives an overview summary over the CD data from the project 
    Including disease brekdowns reporting locations and demographics

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [require_api_key]

    def get(self, location, start_date=None, end_date=None):

        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        #Date and Location Information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first()
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name.name

        #We first add all the summary level data
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        
        ret["data"]["global_clinic_num"] = tot_clinics.get(1)["total"]

        total_cases = get_variable_id("prc_1", start_date, end_date_limit, location, conn)
        ret["data"]["total_cases"] = total_cases
        ret["data"]["public_health_indicators"] = [
            make_dict(gettext("Cases Reported"), total_cases, 100)]

        if total_cases == 0:
            total_cases = 1
        query_variable = QueryVariable()
        gender = query_variable.get("prc_1", "gender",
                                    end_date=end_date_limit.isoformat(),
                                    start_date=start_date.isoformat(),
                                    only_loc=location)
        age = query_variable.get("prc_1", "age",
                                 end_date=end_date_limit.isoformat(),
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
        ret["data"]["percent_cases_male"] = male / total_cases * 100
        ret["data"]["percent_cases_female"] = female / total_cases * 100
        less_5yo = query_variable.get("prc_1", "under_five",
                                 end_date=end_date_limit.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)
        less_5yo = sum(less_5yo[k]["total"] for k in less_5yo.keys())
        
        ret["data"]["percent_cases_lt_5yo"] = less_5yo / total_cases * 100
        if less_5yo == 0:
            less_5yo = 1
        #public health indicators
        modules = query_variable.get("prc_1", "module",
                                 end_date=end_date_limit.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Laboratory results recorded"),
                      modules["Laboratory Results"]["total"],
                      modules["Laboratory Results"]["total"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Prescribing practice recorded"),
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
        if tot_alerts == 0:
            tot_alerts = 1
        ret["data"]["public_health_indicators"].append(
            make_dict("Alerts investigated",
                      investigated_alerts,
                      investigated_alerts / tot_alerts * 100)
        )
        #Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if l.level == "clinic" and l.case_report == 0:
                continue
            if l.parent_location and int(l.parent_location) == int(location):
                num = get_variable_id("prc_1",
                                      start_date,
                                      end_date_limit, l.id, conn)
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))


        ret["data"]["alerts_total"] = tot_alerts

        #Demographics
        ret["data"]["demographics"] = []
        age =  query_variable.get("prc_1","age_gender",
                                  end_date=end_date_limit.isoformat(),
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
                                  end_date=end_date_limit.isoformat(),
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
                                               end_date=end_date_limit.isoformat(),
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
            

            
        ret["data"]["morbidity_communicable_icd"] = get_disease_types("cd", start_date, end_date_limit, location, conn)
        ret["data"]["morbidity_communicable_cd_tab"] = get_disease_types("cd_tab", start_date, end_date_limit, location, conn)
        return ret
class NcdPublicHealth(Resource):
    """
    Public Health Profile Report for Non-Communicable Diseases

    This reports gives an overview summary over the NCD data from the project 
    Including disease brekdowns reporting locations and demographics

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [require_api_key]
    
    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret={}
        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        #Date and Location Information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first()
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name.name

        #We first add all the summary level data
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        
        ret["data"]["global_clinic_num"] = tot_clinics.get(1)["total"]

        total_cases = get_variable_id("prc_2", start_date, end_date_limit, location, conn)
        ret["data"]["total_cases"] = total_cases
        if total_cases == 0:
            total_cases = 1
        query_variable = QueryVariable()
        gender = query_variable.get("prc_2", "gender",
                                    end_date=end_date_limit.isoformat(),
                                    start_date=start_date.isoformat(),
                                    only_loc=location)
        age = query_variable.get("prc_2", "ncd_age",
                                 end_date=end_date_limit.isoformat(),
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
            
        ret["data"]["percent_cases_male"] = male / total_cases * 100
        ret["data"]["percent_cases_female"] = female / total_cases * 100
        less_5yo = query_variable.get("prc_2", "under_five",
                                 end_date=end_date_limit.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)
        less_5yo = sum(less_5yo[k]["total"] for k in less_5yo.keys())

                    
        ret["data"]["percent_cases_lt_5yo"] = less_5yo / total_cases * 100

        if less_5yo == 0:
            less_5yo = 1
        #public health indicators
        modules = query_variable.get("prc_2", "module",
                                 end_date=end_date_limit.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)

        ret["data"]["public_health_indicators"] = [
            make_dict("Cases Reported", total_cases, 100)]
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Laboratory results recorded"),
                      modules["Laboratory Results"]["total"],
                      modules["Laboratory Results"]["total"] / total_cases * 100))
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Prescribing practice recorded"),
                      modules["Prescribing"]["total"],
                      modules["Prescribing"]["total"] / total_cases * 100))
        #Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if l.parent_location and int(l.parent_location) == int(location):
                if l.level == "clinic" and l.case_report == 0:
                    continue
                num = get_variable_id("prc_2",
                                      start_date,
                                      end_date_limit, l.id, conn)
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))

        #Demographics
        ret["data"]["demographics"] = []
        age =  query_variable.get("prc_2","ncd_age_gender",
                                  end_date=end_date_limit.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)
        age_gender={}
        for a in age:
            gender,ac = a.split(" ")
            if ac in age_gender.keys():
                age_gender[ac][gender] = age[a]["total"]
            else:
                age_gender[ac] = {gender: age[a]["total"]}
        age_variables = variables_instance.get("ncd_age")
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
                                  end_date=end_date_limit.isoformat(),
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
                                               end_date=end_date_limit.isoformat(),
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
            

            
        ret["data"]["morbidity_non_communicable_icd"] = get_disease_types("ncd", start_date, end_date_limit, location, conn)
        ret["data"]["morbidity_non_communicable_ncd_tab"] = get_disease_types("ncd_tab", start_date, end_date_limit, location, conn)
        return ret

class RefugeePublicHealth(Resource):
    """
    Refugee Public Health Profile Report

    This reports gives an overview summary over the refugee data from the project 
    Including NCD, Mental Health, CD, Injuries, reporting locations and demographics

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """

    decorators = [require_api_key]
    
    def get(self, location, start_date=None, end_date=None):
        if not app.config["TESTING"] and "refugee" not in model.form_tables:
            return {}
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        #meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        #Date and Location Information
        ew = EpiWeek()
        end_date = end_date
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015, 5, 20).isoformat(),
                       "start_date": start_date.isoformat(),
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)].name
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
            clinic_data = get_latest_category("population", clinic, start_date, end_date_limit)
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
                Data.date < end_date_limit
            ).order_by(Data.date.desc()).first()
            if result:
                no_clinicians += result[0]["ref_14"]
        tot_pop = male + female
        ret["data"]["total_population"] = tot_pop
        # Demographic and overview information
        total_consultations = get_variable_id("ref_13", start_date, end_date_limit, location, conn)
        ret["data"]["total_consultations"] = total_consultations
        if tot_pop == 0:
            tot_pop = 1
        if "0-1" in age_gender and "1-4" in age_gender:
            u5 = sum(age_gender["0-1"].values()) + sum(age_gender["1-4"].values())
        else:
            u5 = 0
        
        ret["data"]["percent_cases_male"] = male / tot_pop * 100
        ret["data"]["percent_cases_female"] = female / tot_pop * 100
        ret["data"]["percent_cases_lt_5yo"] = u5 / tot_pop * 100
        ret["data"]["n_clinicians"] = no_clinicians
        
        if u5 == 0:
            u5 = 1
        if total_consultations == 0:
            total_consultations = 1
        if no_clinicians == 0:
            no_clinicians = 1
            
        # Morbidity
        morbidity_cd = get_variables_category("refugee_cd", start_date, end_date_limit, location, conn)
        morbidity_ncd = get_variables_category("refugee_ncd", start_date, end_date_limit, location, conn)
        morbidity_injury = get_variables_category("refugee_trauma", start_date, end_date_limit, location, conn)
        morbidity_mh = get_variables_category("refugee_mh", start_date, end_date_limit, location, conn)
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
        
        # Mortality
        mortality =  get_variables_category("mortality", start_date, end_date_limit, location, conn)
        mortality_u5 = get_variables_category("u5_mortality", start_date, end_date_limit, location, conn)
        crude_mortality_rate = sum(mortality.values()) / tot_pop * 1000
        u5_crude_mortality_rate = sum(mortality_u5.values()) / u5 * 1000
        ret["data"]["crude_mortality_rate"] = crude_mortality_rate
        ret["data"]["u5_crude_mortality_rate"] = u5_crude_mortality_rate
        
        # Public health indicators
        days_of_report = (end_date - start_date).days
        
        ret["data"]["public_health_indicators"] = [
            make_dict(gettext("Health Utilisation Rate"), total_consultations / tot_pop / days_of_report * 365 , None)] # per year
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Number of consultations per clinician per day"), total_consultations / no_clinicians / days_of_report, None)
            )
        hospital_referrals = get_variable_id("ref_15", start_date, end_date_limit, location, conn)
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Hospitalisation rate"),
                      hospital_referrals /total_consultations, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Referral rate"),
                      (get_variable_id("ref_16", start_date, end_date_limit, location, conn) + hospital_referrals) /total_consultations, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Crude Mortality Rate (CMR)"),
                     crude_mortality_rate, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Under-five Mortality Rate (U5MR)"),
                       u5_crude_mortality_rate, None)
        )

        # Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for clinic in refugee_clinics:
            num =  sum(get_variables_category("morbidity_refugee", start_date, end_date_limit, clinic, conn, use_ids = True).values())
            ret["data"]["reporting_sites"].append(
                    make_dict(locs[clinic].name,
                              num,
                              num / total_cases * 100))

        # Demographics
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
            make_dict(gettext("Communicable Disease"), morbidity_cd_no, morbidity_cd_no / total_cases * 100),
            make_dict(gettext("Non-Communicable Disease"), morbidity_ncd_no, morbidity_ncd_no / total_cases * 100),
            make_dict(gettext("Mental Health"), morbidity_mh_no, morbidity_mh_no / total_cases * 100),
            make_dict(gettext("Injury"), morbidity_injury_no, morbidity_injury_no / total_cases * 100)
        ]

        ret["data"]["morbidity_communicable"] = refugee_disease(morbidity_cd)
        ret["data"]["morbidity_non_communicable"] = refugee_disease(morbidity_ncd)
        ret["data"]["mental_health"] = refugee_disease(morbidity_mh)
        ret["data"]["injury"] = refugee_disease(morbidity_injury)

        return ret
    
class RefugeeDetail(Resource):
    """
    Refugee Detailed Report

    This reports gives detailed tables on all aspects of the refugee data

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [require_api_key]
    
    def get(self, location, start_date=None, end_date=None):
        if not app.config["TESTING"] and "refugee" not in model.form_tables:
            return {}
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        # Meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        # Dates and Location Information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)]
        ret["data"]["project_region"] = location_name.name
        
        #We first find all the refugee clinics
        refugee_clinics = get_children(location, locs, clinic_type="Refugee")
        ret["data"]["clinic_num"] = len(refugee_clinics)

        # Total_population we want the latest submitted total population
        male = 0
        female = 0
        age_gender = {}
        no_clinicians = 0
        for clinic in refugee_clinics:
            clinic_data = get_latest_category("population", clinic, start_date, end_date_limit)
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
                Data.date < end_date_limit
            ).order_by(Data.date.desc()).first()
            if result:
                no_clinicians += result[0]["ref_14"]
        tot_pop = male + female
        ret["data"]["total_population"] = tot_pop
        ret["data"]["n_clinicians"] = no_clinicians
        if "0-1" in age_gender and "1-4" in age_gender:
            u5 =  sum(age_gender["0-1"].values()) + sum(age_gender["1-4"].values())
        else:
            u5 = 0
        if u5 == 0:
            u5 = 1

        #1. Population
        age_gender["total"] = tot_pop
        ret["data"]["population"] = {"Refugee Population": age_gender}
        if tot_pop == 0:
            tot_pop = 1

        #2. Mortality
        mortality =  get_variables_category("mortality", start_date, end_date_limit, location, conn)
        mortality_u5 = get_variables_category("u5_mortality", start_date, end_date_limit, location, conn)
        crude_mortality_rate = sum(mortality.values()) / tot_pop * 1000
        u5_crude_mortality_rate = sum(mortality_u5.values()) / u5 * 1000
        ret["data"]["mortality"] = []
        ret["data"]["mortality"].append(
            make_dict(gettext("Crude Mortality Rate"), crude_mortality_rate, None)
        )
        ret["data"]["mortality"].append(
            make_dict(gettext("Under five crude mortality rate"), u5_crude_mortality_rate,None)
            )
        ret["data"]["mortality_breakdown"] = disease_breakdown(mortality)

        # 3. Morbidity
        # 3.1 Staffing
        total_consultations = get_variable_id("ref_13", start_date, end_date_limit, location, conn)
        days_of_report = (end_date - start_date).days
        ret["data"]["staffing"] = [
            make_dict(gettext("Total Consultations"), total_consultations, None)
            ]
        ret["data"]["staffing"].append(
            make_dict(gettext("Number of Clinicians"), no_clinicians, None)
            )
        if tot_pop == 0:
            tot_pop = 1
        if total_consultations == 0:
            total_consultations = 1
        if no_clinicians == 0:
            no_clinicians = 1
        ret["data"]["staffing"].append(
            make_dict(gettext("Health Utilisation Rate"), total_consultations / tot_pop / days_of_report * 365 , None)) # per year
        ret["data"]["staffing"].append(
            make_dict(gettext("Number of consultations per clinician per day"), total_consultations / no_clinicians / days_of_report, None)
            )
        
        # 3.2 Communciable Diseases
        morbidity_cd = get_variables_category("refugee_cd", start_date, end_date_limit, location, conn)
        ret["data"]["communicable_diseases"] = disease_breakdown(morbidity_cd)

        # 3.3 Non-Communicable Diseases
        morbidity_ncd = get_variables_category("refugee_ncd", start_date, end_date_limit, location, conn)
        ret["data"]["non_communicable_diseases"] = disease_breakdown(morbidity_ncd)

        # 3.4 Mental Health
        morbidity_mh = get_variables_category("refugee_mh", start_date, end_date_limit, location, conn)
        ret["data"]["mental_health"] = disease_breakdown(morbidity_mh)
        
        # 3.5 Injuries
        morbidity_injury = get_variables_category("refugee_trauma", start_date, end_date_limit, location, conn)
        ret["data"]["injury"] = disease_breakdown(morbidity_injury)
        
        # 4 Referral
        hospital_referrals = get_variable_id("ref_15", start_date, end_date_limit, location, conn)
        other_referrals = get_variable_id("ref_16", start_date, end_date_limit, location, conn)
        ret["data"]["referrals"] = [
            make_dict(gettext("Hospital Referrals"), hospital_referrals, None)
            ]
        ret["data"]["referrals"].append(
            make_dict(gettext("Other Referrals"), other_referrals, None)
            )
        ret["data"]["referrals"].append(
            make_dict(gettext("Hospitalisation rate"),
                      hospital_referrals /total_consultations, None)
        )
        ret["data"]["referrals"].append(
            make_dict(gettext("Referral rate"),
                      (other_referrals + hospital_referrals) /total_consultations, None)
        )
        return ret

class RefugeeCd(Resource):
    """
    Refugee CD Report

    Gives timelines for the refugee CD cases

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """

    decorators = [require_api_key]

    def get(self, location, start_date=None, end_date=None):
        if not app.config["TESTING"] and "refugee" not in model.form_tables:
            return {}
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}
        
        # Meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        
        #Date and Location Information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)]
        ret["data"]["project_region"] = location_name.name

        # We first find all the refugee clinics
        refugee_clinics = get_children(location, locs, clinic_type="Refugee")
        ret["data"]["clinic_num"] = len(refugee_clinics)

        ewg = ew.get(start_date.isoformat())
        start_epi_week = ewg["epi_week"]
        start_year = ewg["year"]
        year_diff = end_date.year - start_year
        start_epi_week = start_epi_week - year_diff * 52
        weeks = [i for i in range(start_epi_week, epi_week + 1, 1)]

        nice_weeks = []
        for w in weeks:
            i = 0
            while w <= 0:
                w += 52
                i += 1
            if w == 1:
                # This is to add an indication that this is a new year
                w = "Week 1, " + str(end_date.year - i)
            nice_weeks.append(w)
     

        
        #List of cds
        variables = variables_instance.get("refugee_cd")
        ret["data"]["communicable_diseases"] = {}
        for v in variables.values():
            ret["data"]["communicable_diseases"].setdefault(v["name"].split(",")[0],
                                                            {"weeks": nice_weeks,
                                                             "suspected": []})
            # Need to loop through each epi week and add data for population and all cds per week.
        for week in weeks:
            first_day = epi_week_start(end_date.year, week)
            last_day = first_day + timedelta(days=7)
            # # Population
            # tot_pop = 0
            # no_clinicians = 0
            # for clinic in refugee_clinics:
            #     result = db.session.query(Data.variables).filter(
            #         or_(Data.variables.has_key("ref_1"),
            #             Data.variables.has_key("ref_2"),
            #             Data.variables.has_key("ref_3"),
            #             Data.variables.has_key("ref_4"),
            #             Data.variables.has_key("ref_5"),
            #             Data.variables.has_key("ref_6"),
            #             Data.variables.has_key("ref_7"),
            #             Data.variables.has_key("ref_8")),
            #         Data.clinic == clinic,
            #         Data.date >= first_day,
            #         Data.date < last_day
            #     ).order_by(Data.date.desc()).first()
            #     if(result):
            #         tot_pop += sum(result[0].values())
            # result = db.session.query(Data.variables).filter(
            #     Data.variables.has_key("ref_10"),
            #     Data.clinic == clinic,
            #     Data.date >= first_day,
            #     Data.date < last_day
            # ).order_by(Data.date.desc()).first()
            # if result:
            #     no_clinicians += result[0]["ref_10"]
            # ret["data"].setdefault("population", {"weeks": weeks,
            #                                       "suspected": []})
            # ret["data"].setdefault("number_clinicians", {"weeks": weeks,
            #                                              "suspected": []})
            # ret["data"]["population"]["suspected"].append(tot_pop)
            # ret["data"]["number_clinicians"]["suspected"].append(no_clinicians)
            morbidity_cd = get_variables_category("refugee_cd", first_day, last_day, location, conn)
            diseases = {}
            for disease in morbidity_cd:
                disease_name = disease.split(",")[0]
                diseases.setdefault(disease_name, 0)
                diseases[disease_name] += morbidity_cd[disease]
            for d in diseases:
                ret["data"]["communicable_diseases"][d]["suspected"].append(diseases[d])
        return ret

class WeeklyEpiMonitoring(Resource):
    """
    Weekly Epi Monitoring or "Rapport de Surveillance Epidémiologique Hebdomadaire"

    This reports gives detailed tables on all aspects the epidiemiological data.
    As requested by Madagascar. 

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [require_api_key]
    
    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        # Meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        # Dates and Location Information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]

        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015,5,20).isoformat(),
                       "start_date": start_date.isoformat()
        }

        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)]
        ret["data"]["project_region"] = location_name.name
        
        # Actually get the data.
        conn = db.engine.connect()

        var = {}

        ret['tot_mortality'] = get_variables_category(
            'tot_mortality', 
            start_date, 
            end_date_limit, 
            location, 
            conn, 
            use_ids=True
        )

        var.update( variables_instance.get('tot_mortality') )

        ret['mat_mortality'] = get_variables_category(
            'mat_mortality', 
            start_date, 
            end_date_limit, 
            location, 
            conn, 
            use_ids=True
        )

        var.update( variables_instance.get('mat_mortality') )

        ret['deaths'] = get_variables_category(
            'deaths', 
            start_date, 
            end_date_limit, 
            location, 
            conn, 
            use_ids=True
        )

        var.update( variables_instance.get('deaths') )

        ret['epi_monitoring'] = get_variables_category(
            'epi_monitoring', 
            start_date, 
            end_date_limit, 
            location, 
            conn, 
            use_ids=True
        )

        #Alerts
        all_alerts = alerts.get_alerts({
            "location": location,
            "start_date": start_date,
            "end_date": end_date_limit
        })

        tot_alerts = 0
        investigated_alerts = 0

        for a in all_alerts.values():
                tot_alerts += 1
                report_status = False
                if "links" in a and "alert_investigation" in a["links"]:
                    investigated_alerts += 1


        ret['alerts'] = {
            'total': tot_alerts,
            'investigated': investigated_alerts
        }        

        var.update( variables_instance.get('epi_monitoring') )
        ret['variables'] = var 

        return ret
