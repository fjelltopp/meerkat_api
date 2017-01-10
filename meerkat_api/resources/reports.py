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
Vaccination Report
"""

from flask_restful import Resource
from flask import request
from sqlalchemy import or_, func, desc, Integer
from datetime import datetime, timedelta
from dateutil import parser
from sqlalchemy.sql import text
import uuid
import traceback
from gettext import gettext
import logging, json, operator
from meerkat_api.util import get_children, is_child, fix_dates
from meerkat_api import db, app
from meerkat_abacus.model import Data, Locations, AggregationVariables
from meerkat_api.resources.completeness import Completeness, NonReporting
from meerkat_api.resources.variables import Variables, Variable
from meerkat_api.resources.epi_week import EpiWeek, epi_week_start, epi_year_start
from meerkat_api.resources.locations import TotClinics
from meerkat_api.resources.data import AggregateYear
from meerkat_api.resources.map import Clinics, MapVariable
from meerkat_api.resources import alerts
from meerkat_api.resources.explore import QueryVariable
from meerkat_api.util.data_query import query_sum
from meerkat_api.resources.incidence import IncidenceRate
from meerkat_abacus.util import get_locations, all_location_data
from meerkat_abacus import model
from meerkat_api.authentication import authenticate

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




#  Common variables_instance
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
        r = query_sum(db, [variable],
                      start_date,
                      end_date,
                      location,
                      )["total"]
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

def order_by_name(data_list):
  return 1

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
    decorators = [authenticate]
    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}
        # meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        #  Dates and Location Name
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
        #  Data on Hypertension and Diabebtes, there are two tables for each disease.
        #  One for the age breakdown, and one for labs and complications.
        #  For each table we have rows for each Region.
        #  Each of these tables have a title key for the X-axis titles
        #  Data is list of rows(dicts) with a title for the y-axis title and
        #  a list of values that are the values for the row in the right order

        ret["hypertension"] = {"age": {}, "complications": {}, "email_summary": {}}
        ret["diabetes"] = {"age": {}, "complications": {}, "email_summary": {}}

        diabetes_id = "ncd_1"
        hypertension_id = "ncd_2"
        diseases = {"hypertension": hypertension_id,
                    "diabetes": diabetes_id}
        ids_to_include = {"hypertension": [("lab_4", "lab_3"), ("lab_5", "lab_3"), ("lab_2", "lab_1"), ("com_1", "tot"), ("smo_2", "smo_4"), ("lab_11", "lab_10")],
                          "diabetes": [("lab_4", "lab_3"), ("lab_5", "lab_3"), ("lab_7", "lab_6"), ("lab_9", "lab_8"), ("com_2", "tot"), ("smo_2", "smo_4"), ("lab_11", "lab_10")]
        }

        locations, ldid, regions, districts, devices = all_location_data(db.session)
        v = Variables()
        ages = v.get("ncd_age")

        #  Loop through diabetes and hypertension
        for disease in diseases.keys():
            #  First sort out the titles
            ret[disease]["age"]["titles"] = [gettext("reg")]
            ret[disease]["age"]["data"] = []
            for age in sorted(ages.keys()):
                ret[disease]["age"]["titles"].append(ages[age]["name"])
            ret[disease]["age"]["titles"].insert(1,"Total")
            ret[disease]["complications"]["titles"] = ["reg",
                                                       "tot",
                                                       "gen_1",
                                                       "gen_2"]

            for i in ids_to_include[disease]:
                ret[disease]["complications"]["titles"].append(i[0])
            ret[disease]["complications"]["data"] = []


            #  Loop through each region, we add [1] to include the whole country
            for i, region in enumerate( sorted(regions) + [1]):

                d_id = diseases[disease]
                query_variable = QueryVariable()
                #  get the age breakdown
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
                ret[disease]["age"]["data"][i]["values"].insert(0,sum( [a["total"] for a in disease_age.values()]))

                # Add whole country summary for email report
                if region == 1:
                  ret[disease]["email_summary"]["cases"]=ret[disease]["age"]["data"][i]["values"][0]

                #  Get gender breakdown
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



                #  Get the lab breakdown
                for new_id in ids_to_include[disease]:
                    if new_id[0]:
                        numerator = query_sum(db, [d_id, new_id[0]], start_date, end_date_limit, region)["total"]
                        if new_id[1] == "tot":
                            denominator = table_two_total
                        else:
                            denominator = query_sum(db, [d_id, new_id[1]], start_date, end_date_limit, region)["total"]
                        if denominator == 0:
                            denominator = 1
                        ret[disease]["complications"]["data"][i]["values"].append(
                            [numerator, numerator/ denominator * 100])

                        # control for email report for the whole country
                        if region == 1:
                          if disease == "diabetes" and new_id[0] == "lab_9":
                            ret[disease]["email_summary"]["control"] = numerator/ denominator * 100
                          elif disease == "hypertension" and new_id[0] == "lab_2":
                            ret[disease]["email_summary"]["control"] = numerator/ denominator * 100
                    else:
                        #  We can N/A to the table if it includes data we are not collecting
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
    decorators = [authenticate]

    def get(self, location, start_date = None,end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        # meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        #  Date and Location information
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
        #  We use the data in the alert table with alert_investigation links
        #  Each alert is either classified as suspected, confirmed. We do not include
        #  discarded alerts.

        #  To get this data we loop through every alert and determine it's status
        #  and which week it belongs to. We then assemble this data in the return dict.

        central_review = False
        if "other" in request.args:
            if request.args["other"] == "central_review":
                central_review = True

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
                #  This is to add an indication that this is a new year
                w = "Week 1, " + str(end_date.year - i)
            nice_weeks.append(w)

        data_list = [0 for week in weeks]
        variable_query = db.session.query(AggregationVariables).filter(
            AggregationVariables.alert == 1)
        variable_names = {}
        for v in variable_query.all():
            variable_names[v.id] = v.name
        #  The loop through all alerts
        for a in all_alerts:
            if a["date"] <= end_date and a["date"] >= start_date:
                reason = variable_names[a["variables"]["alert_reason"]]
                report_status = None
                if central_review:
                    if "cre_2" in a["variables"]:
                        report_status = "confirmed"
                    elif "cre_3" in a["variables"]:
                        continue
                    else:
                        report_status = "suspected"
                else:
                    if "ale_2" in a["variables"]:
                        report_status = "confirmed"
                    elif "ale_3" in a["variables"]:
                        continue
                    else:
                        report_status = "suspected"

                epi_week = ew.get(a["date"].isoformat())["epi_week"]
                year_diff = end_date.year - a["date"].year
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

    This report shows data on the patients with severe acute respiratory
    infections (SARI). We include data on their treatmend and on lab data to
    confirm the type of Influenza.

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):

        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        # meta data
        ret["meta"] = {
            "uuid": str(uuid.uuid4()),
            "project_id": 1,
            "generation_timestamp": datetime.now().isoformat(),
            "schema_version": 0.1
        }

        #  Date and location information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {
            "epi_week_num": epi_week,
            "end_date": end_date.isoformat(),
            "project_epoch": datetime(2015, 5, 20).isoformat(),
            "start_date": start_date.isoformat(),
            "email_summary": {}
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)].name
        ret["data"]["project_region"] = location_name

        # We first find the number of SARI sentinel sites
        sari_clinics = get_children(location, locs, clinic_type="SARI")
        ret["data"]["num_clinic"] = len(sari_clinics)
        query_variable = QueryVariable()

        #  Now want the gender highlevel information about SARi patients
        #  the code pip_2 give patients with SARI
        sari_code = "pip_2"

        gender = query_variable.get(sari_code, "gender",
                                    end_date=end_date_limit.isoformat(),
                                    start_date=start_date.isoformat(),
                                    only_loc=location)
        total_cases = query_sum(db, [sari_code], start_date, end_date_limit, location)["total"]
        ret["data"]["total_cases"] = int(round(total_cases))
        ret["data"]["pip_indicators"] = [make_dict(gettext("Total Cases"), total_cases, 100)]
        if total_cases == 0:
            #  So the future divsions by total_cases does not break in case of zero cases
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

        #  We now want to get a timeline of the lab confirmed influenze types.
        #  The Influenza types and other pip related variables have category pip
        pip_cat = query_variable.get(sari_code, "pip",
                                         end_date=end_date.isoformat(),
                                         start_date=start_date.isoformat(),
                                         only_loc=location,
                                         use_ids=True)

        pip_labs = query_variable.get(sari_code, "pip_lab",
                                     end_date=end_date.isoformat(),
                                     start_date=start_date.isoformat(),
                                     only_loc=location,
                                     use_ids=True)
        if pip_labs == {}:
            return ret
        weeks = sorted(pip_cat["pip_2"]["weeks"].keys(), key=float)
        nice_weeks = []
        for w in weeks:
            i = 0
            while w > 53:
                w -= 52
                i += 1
            if w == 1:
                #  To get a nice display when the period spans multiple years
                w = "Week 1, " + str(start_date.year + i)
            nice_weeks.append(w)
        ret["data"]["timeline"] = {
            "suspected": [pip_cat[sari_code]["weeks"][k] if k in pip_cat[sari_code]["weeks"] else 0 for k in weeks],
            "weeks": nice_weeks,
            "confirmed": {
                gettext("B"): [pip_labs["pil_6"]["weeks"][w] for w in weeks],
                gettext("H3"): [pip_labs["pil_4"]["weeks"][w] for w in weeks],
                gettext("H1N1"): [pip_labs["pil_5"]["weeks"][w] for w in weeks],
                gettext("Mixed"): [pip_labs["pil_7"]["weeks"][w] for w in weeks],
                }
            }

        #  Treatment and situation indicators
        ret["data"]["percent_cases_chronic"] = (pip_cat["pip_3"]["total"] / total_cases ) * 100
        ret["data"]["cases_chronic"] = pip_cat["pip_3"]["total"]

        #  Lab links and follow up links
        total_lab_links = 0
        lab_types = {
            gettext("B"): pip_labs["pil_6"]["total"],
            gettext("H3"): pip_labs["pil_4"]["total"],
            gettext("H1N1"): pip_labs["pil_5"]["total"],
            gettext("Mixed"): pip_labs["pil_7"]["total"]
        }
        #  Assembling the timeline with suspected cases and the confirmed cases
        #  from the lab linkage


        total_lab_links = pip_labs["pil_2"]["total"] + pip_labs["pil_3"]["total"]
        ret["data"]["cases_pcr"] = total_lab_links
        ret["data"]["flu_type"] = []
        for l in ["B", "H3", "H1N1", "Mixed"]:
            ret["data"]["flu_type"].append(
                make_dict(l, lab_types[l], (lab_types[l]/total_cases) * 100)
            )

        pip_followup = query_variable.get(sari_code, "pip_followup",
                                         end_date=end_date.isoformat(),
                                         start_date=start_date.isoformat(),
                                         only_loc=location,
                                         use_ids=True)
        print(pip_followup)
        total_followup = pip_followup["pif_1"]["total"]
        icu = pip_followup["pif_3"]["total"]
        ventilated = pip_followup["pif_4"]["total"]
        mortality = pip_followup["pif_5"]["total"]
        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Patients followed up"), total_followup, total_followup / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Laboratory results recorded"), total_lab_links, total_lab_links / total_cases * 100))
        ret["data"]["email_summary"]["lab_recorded"] = total_lab_links
        ret["data"]["email_summary"]["lab_recorded_per"] = total_lab_links / total_cases * 100
        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Patients admitted to ICU"), icu, icu / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Patients ventilated"), ventilated, ventilated / total_cases * 100))
        ret["data"]["pip_indicators"].append(
            make_dict(gettext("Mortality"), mortality, mortality / total_cases * 100))
        ret["data"]["demographics"] = []

        #  Reportin sites
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if is_child(location, l.id, locs) and l.case_report and l.clinic_type == "SARI":
                num = query_sum(db, [sari_code],
                                      start_date,
                                      end_date_limit, l.id)["total"]
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))

        # Demographics
        ret["data"]["demographics"] = []
        age =  query_variable.get(sari_code,"age_gender",
                                  end_date=end_date_limit.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)
        age_gender = {}

        tot = sum([group["total"] for group in age.values()])
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
                a_perc = a_sum / tot *100 if tot != 0 else 0
                if a_sum == 0:
                    a_sum = 1
                ret["data"]["demographics"].append(
                    {"age": a,
                     "quantity": age_gender[a]["Male"] + age_gender[a]["Female"],
                     "percent": round(a_perc, 2),
                     "male": {"quantity": age_gender[a]["Male"],
                              "percent": age_gender[a]["Male"] / a_sum * 100
                     },
                     "female":{"quantity": age_gender[a]["Female"],
                               "percent": age_gender[a]["Female"]/float(a_sum)*100
                     }
                    })

        # Nationality
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
        # Status
        status_total = query_variable.get(
            sari_code,
            "status",
            end_date=end_date_limit.isoformat(),
            start_date=start_date.isoformat(),
            only_loc=location
        )
        status = {}
        for sta in status_total.keys():
            status[sta] = status_total[sta]["total"]
        tot_sta = sum(status.values())
        if tot_sta == 0:
            tot_sta = 1
        ret["data"]["patient_status"] = []
        for sta in sorted(status, key=status.get, reverse=True):
            ret["data"]["patient_status"].append(make_dict(
                sta,
                status[sta],
                status[sta] / tot_sta * 100
            ))

        #  Map
        clin = Clinics()
        ret["data"]["map"] = clin.get(1, clinic_type='SARI')

        return ret


class PublicHealth(Resource):
    """
    Public Health Profile Report

    This reports gives an overview summary over the data from the project
    Including NCD, Mental Health, CD, Injuries, reporting locations and
    demographics

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}
        # meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        #  Dates and Location
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

        # We first add all the summary level data
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]

        ret["data"]["global_clinic_num"] = tot_clinics.get(1)["total"]
        total_cases = query_sum(db, ["tot_1"], start_date, end_date_limit, location)["total"]
        ret["data"]["total_cases"] = int(round(total_cases))
        #  We need to divded by total cases(and some other numbers) so we make sure we don't divide
        #  by zero in cases of no cases.
        if total_cases == 0:
            total_cases = 1
        total_consultations = query_sum(db, ["reg_2"], start_date, end_date_limit, location)["total"]
        ret["data"]["total_consultations"] = int(round(total_consultations))
        female = query_sum(db, ["gen_2"], start_date, end_date_limit, location)["total"]
        male = query_sum(db ,["gen_1"], start_date, end_date_limit, location)["total"]
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

        #  Public health indicators
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
        smoking_prevalence = query_sum(db , ["smo_2"], start_date, end_date_limit, location)["total"]
        smoking_prevalence_ever = query_sum(db, ["smo_1"], start_date, end_date_limit, location)["total"]
        smoking_non_prevalence_ever = query_sum(db, ["smo_3"], start_date, end_date_limit, location)["total"]

        if (smoking_prevalence_ever + smoking_non_prevalence_ever) == 0:
            smoking_prevalence_ever = 1
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Smoking prevalence (current)"),
                      smoking_prevalence,
                      smoking_prevalence / (smoking_prevalence_ever+smoking_non_prevalence_ever) * 100))

        # Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if l.level == "clinic" and l.case_report == 0:
                continue
            if l.parent_location and int(l.parent_location) == int(location):
                num = query_sum(db, ["tot_1"],
                                start_date,
                                end_date_limit, l.id)["total"]
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))


        # Alerts
        alerts = db.session.query(
            Data.variables["alert_reason"], func.count(Data.uuid).label("count")).filter(
                Data.date >= start_date,
                Data.date < end_date_limit,
                Data.variables.has_key("alert")).group_by(Data.variables["alert_reason"]).order_by(desc("count")).limit(5)
        ret["data"]["alerts"]=[]
        for a in alerts.all():
            ret["data"]["alerts"].append(
                {"subject": a[0],
                 "quantity": a[1]})
        all_alerts = db.session.query(func.count(Data.uuid)).filter(
            Data.date >= start_date,
            Data.date < end_date_limit,
            Data.variables.has_key("alert")
        )
        ret["data"]["alerts_total"] = all_alerts.first()[0]

        # Gender
        query_variable = QueryVariable()
        gender = query_variable.get("prc_1", "gender",
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

        # Demographics
        ret["data"]["demographics"] = []
        age = get_variables_category("age_gender", start_date, end_date_limit, location, conn)
        age_gender={}
        tot = sum([group for group in age.values()])
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
                a_perc = a_sum / tot *100 if tot != 0 else 0
                if a_sum == 0:
                    a_sum = 1
                ret["data"]["demographics"].append(
                    {"age": a,
                     "quantity": age_gender[a]["Male"] + age_gender[a]["Female"],
                     "percent": round(a_perc, 2),
                     "male": {"quantity": age_gender[a]["Male"],
                              "percent": age_gender[a]["Male"] / a_sum * 100
                     },
                     "female":{"quantity": age_gender[a]["Female"],
                               "percent": age_gender[a]["Female"]/float(a_sum)*100
                     }
                 })




        # Nationality
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
        # Status
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


        # Presenting Complaint

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

        #  Map
        clin = Clinics()
        ret["data"]["map"] = clin.get(1)

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
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):

        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret={}
        # meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        # Date and Location Information
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

        # We first add all the summary level data
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]

        ret["data"]["global_clinic_num"] = tot_clinics.get(1)["total"]

        total_consultations = query_sum(db, ["reg_2"], start_date, end_date_limit, location)["total"]
        ret["data"]["total_consultations"] = int(round(total_consultations))
        total_cases = query_sum(db, ["prc_1"], start_date, end_date_limit, location)["total"]
        ret["data"]["total_cases"] = int(round(total_cases))
        total_deaths = query_sum(db, ["dea_1"], start_date, end_date_limit, location)["total"]
        ret["data"]["total_deaths"] = int(round(total_deaths))

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

        # public health indicators

        medicines = query_variable.get("prc_1", "medicine",
                                     end_date=end_date_limit.isoformat(),
                                     start_date=start_date.isoformat(),
                                     only_loc=location, use_ids=True)

        if "med_1" in medicines and "med_2" in medicines:
            tot_med = medicines["med_1"]["total"]
            if tot_med == 0:
                tot_med = 1
            ret["data"]["public_health_indicators"].append(
                make_dict(gettext("Availability of prescribed medicines"),
                          medicines["med_2"]["total"],
                          medicines["med_2"]["total"] / tot_med * 100))
        else:
            ret["data"]["public_health_indicators"].append(
                make_dict(gettext("Availability of prescribed medicines"),
                          0,0))


        # Alerts
        all_alerts = alerts.get_alerts({"location": location})
        tot_alerts = 0
        investigated_alerts = 0
        for a in all_alerts:
            if a["date"] <= end_date and a["date"] > start_date:
                tot_alerts += 1
                report_status = False
                if "ale_1" in a["variables"]:
                    investigated_alerts += 1
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Alerts generated"),
                      tot_alerts,
                      100)
        )
        ret["data"]["alerts_total"] = tot_alerts
        if tot_alerts == 0:
            tot_alerts = 1

        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Alerts investigated"),
                      investigated_alerts,
                      investigated_alerts / tot_alerts * 100)
        )
        # Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if l.level == "clinic" and l.case_report == 0:
                continue
            if l.parent_location and int(l.parent_location) == int(location):
                num = query_sum(db, ["prc_1"],
                                      start_date,
                                      end_date_limit, l.id)["total"]
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))





        # Demographics
        ret["data"]["demographics"] = []
        age =  query_variable.get("prc_1","age_gender",
                                  end_date=end_date_limit.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)

        age_gender={}
        tot = sum([group["total"] for group in age.values()])
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
                a_perc = a_sum / tot *100 if tot != 0 else 0
                if a_sum == 0:
                    a_sum = 1
                ret["data"]["demographics"].append(
                    {"age": a,
                     "quantity": age_gender[a]["Male"] + age_gender[a]["Female"],
                     "percent": round(a_perc, 2),
                     "male": {"quantity": age_gender[a]["Male"],
                              "percent": age_gender[a]["Male"] / a_sum * 100
                     },
                     "female":{"quantity": age_gender[a]["Female"],
                               "percent": age_gender[a]["Female"]/float(a_sum)*100
                     }
                    })

        # Nationality
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
        # Status
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

        #  Map
        clin = Clinics()
        ret["data"]["map"] = clin.get(1)

        return ret

class CdPublicHealthMad(Resource):
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
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):

        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        conn = db.engine.connect()

        # This report is nearly the same as the CDPublicHealth Report
        # Let's just get that report and tweak it slightly.
        rv = CdPublicHealth()
        ret = rv.get( location, start_date.isoformat(), end_date.isoformat() )

        # Other values required for the email.
        ret['email'] = {
            'cases': int(round(query_sum(db, ['tot_1'], start_date, end_date_limit, location)["total"])),
            'consultations': int(round(query_sum(db, ['reg_2'],
                                                 start_date, end_date_limit, location)["total"])),
            'clinics': int(round(TotClinics().get(location)["total"]))
        }

        # Delete unwanted indicators.
        del ret["data"]["public_health_indicators"][1:3]

        # Replace with new indicators.
        comp = Completeness()
        # ret["data"]["public_health_indicators"].append({
        #   'percent' : comp.get( 'reg_1', 5 )["regions"][1]['last_year'],
        #   'title' : 'Yearly completeness across Madagascar',
        #   'quantity' : -1
        # })

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
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):

        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        # meta data
        ret["meta"] = {
            "uuid": str(uuid.uuid4()),
            "project_id": 1,
            "generation_timestamp": datetime.now().isoformat(),
            "schema_version": 0.1
        }

        # Date and Location Information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {
            "epi_week_num": epi_week,
            "end_date": end_date.isoformat(),
            "project_epoch": datetime(2015, 5, 20).isoformat(),
            "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        location_name = db.session.query(Locations.name).filter(
            Locations.id == location).first()
        if not location_name:
            return None
        ret["data"]["project_region"] = location_name.name

        # We first add all the summary level data
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        ret["data"]["global_clinic_num"] = tot_clinics.get(1)["total"]

        total_cases = query_sum(db, ["prc_2"], start_date, end_date_limit, location)["total"]
        ret["data"]["total_cases"] = int(round(total_cases))
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
        less_5yo = query_variable.get(
            "prc_2", "under_five",
            end_date=end_date_limit.isoformat(),
            start_date=start_date.isoformat(),
            only_loc=location
        )
        less_5yo = sum(less_5yo[k]["total"] for k in less_5yo.keys())

        ret["data"]["percent_cases_lt_5yo"] = less_5yo / total_cases * 100
        if less_5yo == 0:
            less_5yo = 1


        smoking = query_sum(db, ["prc_2", "smo_4"], start_date, end_date, location)["total"]
        tot_diabetes = query_sum(db, ["ncd_1"], start_date, end_date, location)["total"]
        tot_hypertension = query_sum(db, ["ncd_2"], start_date, end_date, location)["total"]


        if tot_diabetes == 0:
            tot_diabetes = 1
        if tot_hypertension == 0:
            tot_hypertension = 1
        diabetes_with_hba1c = query_sum(db, ["ncd_1", "lab_8"], start_date, end_date,location)["total"]
        hypertension_with_bp = query_sum(db, ["ncd_2", "lab_1"], start_date, end_date, location)["total"]

        ret["data"]["public_health_indicators"] = [
            make_dict("Cases Reported", total_cases, 100)]

        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Patient have smoking status recorded"),
                      smoking,
                      smoking / total_cases * 100))

        ret["data"]["public_health_indicators"].append(make_dict(
            gettext("Diabetes mellitus patients have HbA1C recorded"),
            diabetes_with_hba1c,
            diabetes_with_hba1c / tot_diabetes * 100
        ))

        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Hypertension patients have BP recorded"),
                      hypertension_with_bp,
                      hypertension_with_bp / tot_hypertension * 100))

        medicines = query_variable.get("prc_2", "medicine",
                                     end_date=end_date_limit.isoformat(),
                                     start_date=start_date.isoformat(),
                                     only_loc=location, use_ids=True)
        if "med_1" in medicines and "med_2" in medicines:
            tot_med = medicines["med_1"]["total"]
            if tot_med == 0:
                tot_med = 1
            ret["data"]["public_health_indicators"].append(
                make_dict(gettext("Availability of prescribed medicines"),
                          medicines["med_2"]["total"],
                          medicines["med_2"]["total"] / tot_med * 100))
        else:
            ret["data"]["public_health_indicators"].append(
                make_dict(gettext("Availability of prescribed medicines"),
                          0,0))

        # Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for l in locs.values():
            if l.parent_location and int(l.parent_location) == int(location):
                if l.level == "clinic" and l.case_report == 0:
                    continue
                num = query_sum(db , ["prc_2"],
                                start_date,
                                end_date_limit, l.id)["total"]
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))

        # Demographics
        ret["data"]["demographics"] = []
        age =  query_variable.get("prc_2","ncd_age_gender",
                                  end_date=end_date_limit.isoformat(),
                                  start_date=start_date.isoformat(),
                                  only_loc=location)

        logging.warning(age)
        age_gender={}
        tot = sum([group["total"] for group in age.values()])

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
                a_perc = a_sum / tot *100 if tot != 0 else 0
                if a_sum == 0:
                    a_sum = 1
                ret["data"]["demographics"].append(
                    {"age": a,
                     "quantity": age_gender[a]["Male"] + age_gender[a]["Female"],
                     "percent": round(a_perc, 2),
                     "male": {"quantity": age_gender[a]["Male"],
                              "percent": age_gender[a]["Male"] / a_sum * 100
                     },
                     "female":{"quantity": age_gender[a]["Female"],
                               "percent": age_gender[a]["Female"]/float(a_sum)*100
                     }
                    })

        # Nationality
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
        # Status
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

        #  Map
        clin = Clinics()
        ret["data"]["map"] = clin.get(1)

        return ret


class RefugeePublicHealth(Resource):
    """
    Refugee Public Health Profile Report

    This reports gives an overview summary over the refugee data from the
    project Including NCD, Mental Health, CD, Injuries, reporting locations and
    demographics.

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """

    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):
        if not app.config["TESTING"] and "jor_refugee" not in model.form_tables:
            return {}
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        # meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        # Date and Location Information
        ew = EpiWeek()
        end_date = end_date
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015, 5, 20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        conn = db.engine.connect()
        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)].name
        ret["data"]["project_region"] = location_name

        # We first find all the refugee clinics
        refugee_clinics = get_children(location, locs, clinic_type="Refugee")
        ret["data"]["clinic_num"] = len(refugee_clinics)

        #  Total_population we want the latest submitted total population
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
        total_consultations = query_sum(db, ["ref_13"], start_date, end_date_limit, location)["total"]

        ret["data"]["total_consultations"] = int(round(total_consultations))
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

        #  Morbidity
        morbidity_cd = get_variables_category("refugee_cd", start_date, end_date_limit, location, conn)
        morbidity_ncd = get_variables_category("refugee_ncd", start_date, end_date_limit, location, conn)
        morbidity_injury = get_variables_category("refugee_trauma", start_date, end_date_limit, location, conn)
        morbidity_mh = get_variables_category("refugee_mh", start_date, end_date_limit, location, conn)
        morbidity_cd_no = sum(morbidity_cd.values())
        morbidity_ncd_no = sum(morbidity_ncd.values())
        morbidity_injury_no = sum(morbidity_injury.values())
        morbidity_mh_no = sum(morbidity_mh.values())
        total_cases = morbidity_cd_no + morbidity_ncd_no + morbidity_injury_no + morbidity_mh_no
        ret["data"]["total_cases"] = int(round(total_cases))
        if total_cases == 0:
            total_cases = 1
        ret["data"]["percent_morbidity_communicable"] = morbidity_cd_no / total_cases * 100
        ret["data"]["percent_morbidity_non_communicable"] = morbidity_ncd_no / total_cases * 100
        ret["data"]["percent_morbidity_mental_health"] = morbidity_mh_no / total_cases * 100
        ret["data"]["percent_morbidity_injury_health"] = morbidity_injury_no / total_cases * 100

        #  Mortality
        mortality =  get_variables_category("mortality", start_date, end_date_limit, location, conn)
        mortality_u5 = get_variables_category("u5_mortality", start_date, end_date_limit, location, conn)
        crude_mortality_rate = sum(mortality.values()) / tot_pop * 1000
        u5_crude_mortality_rate = sum(mortality_u5.values()) / u5 * 1000
        ret["data"]["crude_mortality_rate"] = crude_mortality_rate
        ret["data"]["u5_crude_mortality_rate"] = u5_crude_mortality_rate

        #  Public health indicators
        days_of_report = (end_date - start_date).days

        ret["data"]["public_health_indicators"] = [
            make_dict(gettext("Health Utilisation Rate"), total_consultations / tot_pop / days_of_report * 365 , None)] #  per year
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Number of consultations per clinician per day"), total_consultations / no_clinicians / days_of_report, None)
            )
        hospital_referrals = query_sum(db, ["ref_15"], start_date, end_date_limit, location)["total"]
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Hospitalisation rate"),
                      hospital_referrals /total_consultations, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Referral rate"),
                      (query_sum(db, ["ref_16"], start_date, end_date_limit, location)["total"] + hospital_referrals) /total_consultations, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Crude Mortality Rate (CMR)"),
                     crude_mortality_rate, None)
        )
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Under-five Mortality Rate (U5MR)"),
                       u5_crude_mortality_rate, None)
        )

        #  Reporting sites
        locs = get_locations(db.session)
        ret["data"]["reporting_sites"] = []
        for clinic in refugee_clinics:
            num =  sum(get_variables_category("morbidity_refugee", start_date, end_date_limit, clinic, conn, use_ids = True).values())
            ret["data"]["reporting_sites"].append(
                    make_dict(locs[clinic].name,
                              num,
                              num / total_cases * 100))

        #  Demographics
        ret["data"]["demographics"] = []

        age_order = ["0-1", "1-4", "5-14", "15-44", "45-64", ">65"]
        ret["data"]["age"] = []

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
                ret["data"]["age"].append({
                    "age": a,
                    "quantity": a_sum,
                    "percent": a_sum / tot_pop * 100
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

        #  Map
        clin = Clinics()
        ret["data"]["map"] = clin.get(1, clinic_type='Refugee')

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
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):
        if not app.config["TESTING"] and "jor_refugee" not in model.form_tables:
            return {}
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        #  Meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }
        #  Dates and Location Information
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

        #  Total_population we want the latest submitted total population
        male = 0
        female = 0
        age_gender = {}
        no_clinicians = 0
        for clinic in refugee_clinics:
            clinic_data = get_latest_category("population", clinic,
                                              start_date, end_date_limit)
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
        # 1. Population
        age_gender["total"] = tot_pop
        ret["data"]["population"] = {"Refugee Population": age_gender}
        if tot_pop == 0:
            tot_pop = 1

        # 2. Mortality
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
        total_consultations = query_sum(db, ["ref_13"], start_date, end_date_limit, location)["total"]

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
            make_dict(gettext("Health Utilisation Rate"), total_consultations / tot_pop / days_of_report * 365 , None)) #  per year
        ret["data"]["staffing"].append(
            make_dict(gettext("Number of consultations per clinician per day"), total_consultations / no_clinicians / days_of_report, None)
            )

        #  3.2 Communciable Diseases
        morbidity_cd = get_variables_category("refugee_cd", start_date, end_date_limit, location, conn)
        ret["data"]["communicable_diseases"] = disease_breakdown(morbidity_cd)

        #  3.3 Non-Communicable Diseases
        morbidity_ncd = get_variables_category("refugee_ncd", start_date, end_date_limit, location, conn)
        ret["data"]["non_communicable_diseases"] = disease_breakdown(morbidity_ncd)

        #  3.4 Mental Health
        morbidity_mh = get_variables_category("refugee_mh", start_date, end_date_limit, location, conn)
        ret["data"]["mental_health"] = disease_breakdown(morbidity_mh)

        #  3.5 Injuries
        morbidity_injury = get_variables_category("refugee_trauma", start_date, end_date_limit, location, conn)
        ret["data"]["injury"] = disease_breakdown(morbidity_injury)
        # 4 Referral
        hospital_referrals = query_sum(db, ["ref_15"], start_date, end_date_limit, location)["total"]
        other_referrals = query_sum(db, ["ref_16"], start_date, end_date_limit, location)["total"]
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

        #  Map
        clin = Clinics()
        ret["data"]["map"] = clin.get(1, clinic_type="Refugee")

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

    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):
        if not app.config["TESTING"] and "jor_refugee" not in model.form_tables:
            return {}
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        #  Meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        # Date and Location Information
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

        #  We first find all the refugee clinics
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
                #  This is to add an indication that this is a new year
                w = "Week 1, " + str(end_date.year - i)
            nice_weeks.append(w)



        # List of cds
        variables = variables_instance.get("refugee_cd")
        ret["data"]["communicable_diseases"] = {}
        for v in variables.values():
            ret["data"]["communicable_diseases"].setdefault(v["name"].split(",")[0],
                                                            {"weeks": nice_weeks,
                                                             "suspected": []})
            #  Need to loop through each epi week and add data for population and all cds per week.
        for week in weeks:
            first_day = epi_week_start(end_date.year, week)
            last_day = first_day + timedelta(days=7)
            #  #  Population
            #  tot_pop = 0
            #  no_clinicians = 0
            #  for clinic in refugee_clinics:
            #      result = db.session.query(Data.variables).filter(
            #          or_(Data.variables.has_key("ref_1"),
            #              Data.variables.has_key("ref_2"),
            #              Data.variables.has_key("ref_3"),
            #              Data.variables.has_key("ref_4"),
            #              Data.variables.has_key("ref_5"),
            #              Data.variables.has_key("ref_6"),
            #              Data.variables.has_key("ref_7"),
            #              Data.variables.has_key("ref_8")),
            #          Data.clinic == clinic,
            #          Data.date >= first_day,
            #          Data.date < last_day
            #      ).order_by(Data.date.desc()).first()
            #      if(result):
            #          tot_pop += sum(result[0].values())
            #  result = db.session.query(Data.variables).filter(
            #      Data.variables.has_key("ref_10"),
            #      Data.clinic == clinic,
            #      Data.date >= first_day,
            #      Data.date < last_day
            #  ).order_by(Data.date.desc()).first()
            #  if result:
            #      no_clinicians += result[0]["ref_10"]
            #  ret["data"].setdefault("population", {"weeks": weeks,
            #                                        "suspected": []})
            #  ret["data"].setdefault("number_clinicians", {"weeks": weeks,
            #                                               "suspected": []})
            #  ret["data"]["population"]["suspected"].append(tot_pop)
            #  ret["data"]["number_clinicians"]["suspected"].append(no_clinicians)
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
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        ret = {}

        #  Meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        #  Dates and Location Information
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

        #  Actually get the data.
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
        for key, value in ret['tot_mortality'].items():
            if type( value ) == float:
                ret['tot_mortality'][key] = int(round(value))
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
        for key, value in ret['deaths'].items():
            if type( value ) == float:
                ret['deaths'][key] = int(round(value))
        var.update( variables_instance.get('deaths') )

        ret['epi_monitoring'] = get_variables_category(
            'epi_monitoring',
            start_date,
            end_date_limit,
            location,
            conn,
            use_ids=True
        )
        for key, value in ret['epi_monitoring'].items():
            if type( value ) == float:
                ret['epi_monitoring'][key] = int(round(value))

        # Alerts
        all_alerts = alerts.get_alerts({
            "location": location,
            "start_date": start_date,
            "end_date": end_date_limit
        })

        tot_alerts = 0
        investigated_alerts = 0

        for a in all_alerts:
                tot_alerts += 1
                report_status = False
                if "ale_1" in a["variables"]:
                    investigated_alerts += 1


        ret['alerts'] = {
            'total': tot_alerts,
            'investigated': investigated_alerts
        }

        # Other values required for the email.
        ret['email'] = {
            'cases': int(round(query_sum(db, ['tot_1'], start_date, end_date_limit, location)["total"])),
            'consultations': int(round(query_sum(db, ['reg_2'], start_date, end_date_limit, location)["total"])),
            'clinics': TotClinics().get(location)["total"]
        }

        var.update( variables_instance.get('epi_monitoring') )
        ret['variables'] = var

        return ret


class Malaria(Resource):
    """
    Malaria Report or "Rapport de Surveillance Epidemiologique Hebdomadaire du Paludisme"

    This reports gives detailed tables on aspects concerning Malaria.
    As requested by Madagascar.

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):

        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)

        ret = {}

        #  Meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        #  Dates and Location Information
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
        ret["data"]["project_region_id"] = location

        #  Actually get the data.
        conn = db.engine.connect()

        var = {}
        query_variable = QueryVariable()
                #  get the age breakdown
        malaria_data = query_variable.get("cmd_17", "malaria_situation",
                                          end_date=end_date_limit.isoformat(),
                                          start_date=start_date.isoformat(),
                                          only_loc=location,
                                          use_ids=True)
        malaria_data_totals = {}
        for key in malaria_data.keys():
            malaria_data_totals[key] = malaria_data[key]["total"]
        malaria_data_totals.update(get_variables_category(
            'malaria_situation_no_case',
            start_date,
            end_date_limit,
            location,
            conn,
            use_ids=True
        ))
        ret['malaria_situation'] = malaria_data_totals
        for key, value in ret['malaria_situation'].items():
            if type( value ) == float:
                ret['malaria_situation'][key] = int(round(value))

        var.update( variables_instance.get('malaria_situation') )

        ret['malaria_prevention'] = get_variables_category(
            'malaria_prevention',
            start_date,
            end_date_limit,
            location,
            conn,
            use_ids=True
        )
        for key, value in ret['malaria_prevention'].items():
            if type( value ) == float:
                ret['malaria_prevention'][key] = int(round(value))

        var.update( variables_instance.get('malaria_prevention') )

        # Other values required for the email.
        ret['email'] = {
            'clinics': TotClinics().get(location)["total"]
        }

        ret['map'] = MapVariable().get(
            'epi_1',
            location,
            start_date.isoformat(),
            end_date.isoformat()
        )

        ret['variables'] = var

        return ret

class VaccinationReport(Resource):
    """
    Vaccination Report or "Vaccination de Routine"

    This reports gives detailed tables on aspects concerning vaccination sessions.
    As requested by Madagascar.

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)

        ret = {}

        #  Meta data
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        #  Dates and Location Information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]

        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015, 5, 20).isoformat(),
                       "start_date": start_date.isoformat()
        }

        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)]
        ret["data"]["project_region"] = location_name.name
        ret["data"]["project_region_id"] = location

        #  Actually get the data.
        conn = db.engine.connect()
        counts = {}
        categories = [
          'vaccination_sessions',
          'vaccinated_pw',
          'vaccinated_notpw',
          'vaccinated_0_11_mo_infants',
          'vaccinated_12_mo_infants'
          ]

        for category in categories:

            counts[category] = get_variables_category(
                category,
                start_date,
                end_date_limit,
                location,
                conn,
                use_ids=True
            )
        try:
            if "vac_ses" in counts['vaccination_sessions']:
                ret['data'].update({'vaccination_sessions':counts['vaccination_sessions']['vac_ses']})
            else:
                ret['data'].update({'vaccination_sessions': 0})

            ret['data'].update({'infants': []})
            category1 = 'vaccinated_0_11_mo_infants'
            category2 = 'vaccinated_12_mo_infants'
            infant_vaccinations_variables = {}
            infant_vaccinations_variables[category1] = variables_instance.get(category1)
            infant_vaccinations_variables[category2] = variables_instance.get(category2)

            for key in counts[category1]:
                ret['data']['infants'].append({
                    'name': infant_vaccinations_variables[category1][key]['name'],
                    category1: counts[category1][key]
                })

            for key in counts[category2]:
                for item in ret['data']['infants']:
                    if infant_vaccinations_variables[category2][key]['name'] == item['name']:
                        item[category2] = counts[category2][key]
            for item in ret['data']['infants']:
                if category2 not in item.keys():
                    item[category2] = 0
            ret['data'].update({'females': []})
            category1 = 'vaccinated_pw'
            category2 = 'vaccinated_notpw'
            female_vaccinations_variables = {}
            female_vaccinations_variables[category1] = variables_instance.get(category1)
            female_vaccinations_variables[category2] = variables_instance.get(category2)

            for key in counts[category1]:
                ret['data']['females'].append({
                    'name': female_vaccinations_variables[category1][key]['name'],
                    category1: counts[category1][key]
                })

            for key in counts[category2]:
                for item in ret['data']['females']:
                    if female_vaccinations_variables[category2][key]['name'] == item['name']:
                        item[category2] = counts[category2][key]
            for item in ret['data']['females']:
                if category2 not in item.keys():
                    item[category2] = 0
            # sort vaccination lists
            ret['data']['infants'].sort(key=lambda tup: tup['name'])
            ret['data']['females'].sort(key=lambda tup: tup['name'])
        except KeyError as e:
            print("Error")
            print(e)
            ret['data'] = {'message': 'invalid data'}

        # vials used
        vials = {
          "BCG": 20,
          "DTCHepHib": 10,
          "PCV10": 2,
          "ROTARIX": 1,
          "VPO": 20,
          "VPI": 5,
          "VAR": 10,
          "VAT": 20,
        }

        vials_total_doses = {
          "BCG": 0,
          "DTCHepHib": 0,
          "PCV10": 0,
          "ROTARIX": 0,
          "VPO": 0,
          "VPI": 0,
          "VAR": 0,
          "VAT": 0
        }

        #Types of vaccinations:
        vials_types = {
            "vac_pw_vat4": "VAT",
            "vac_pw_vat5": "VAT",
            "vac_pw_vat3": "VAT",
            "vac_pw_vat1": "VAT",
            "vac_pw_vat2": "VAT",
            "vac_i0_dtc2": "DTCHepHib",
            "vac_i0_vpo0": "VPO",
            "vac_i0_dtc1": "DTCHepHib",
            "vac_i0_vpo1": "VPO",
            "vac_i0_bcg": "BCG",
            "vac_i0_var": "VAR",
            "vac_i0_dtc3": "DTCHepHib",
            "vac_i0_pcv3": "PCV10",
            "vac_i0_rota1": "ROTARIX",
            "vac_i0_rota3": "ROTARIX",
            "vac_i0_rota2": "ROTARIX",
            "vac_i0_vpo2": "VPO",
            "vac_i0_vpi": "VPI",
            "vac_i0_vpo3": "VPO",
            "vac_i0_pcv1": "PCV10",
            "vac_i0_pcv2": "PCV10",
            "vac_i12_vpi": "VPI",
            "vac_i12_dtc1": "DTCHepHib",
            "vac_i12_vpo1": "VPO",
            "vac_i12_dtc3": "DTCHepHib",
            "vac_i12_vpo3": "VPO",
            "vac_i12_dtc2": "DTCHepHib",
            "vac_i12_rota1": "ROTARIX",
            "vac_i12_rota3": "ROTARIX",
            "vac_i12_pcv3": "PCV10",
            "vac_i12_vpo0": "VPO",
            "vac_i12_pcv2": "PCV10",
            "vac_i12_pcv1": "PCV10",
            "vac_i12_vpo2": "VPO",
            "vac_i12_bcg": "BCG",
            "vac_i12_var": "VAR",
            "vac_i12_rota2": "ROTARIX",
            "vac_notpw_vat3": "VAT",
            "vac_notpw_vat4": "VAT",
            "vac_notpw_vat5": "VAT",
            "vac_notpw_vat1": "VAT",
            "vac_notpw_vat2": "VAT"}


        for category in counts:
            for vacc in counts[category].keys():
                try:
                    vials_total_doses[vials_types[vacc]] += counts[category][vacc]
                except:
                    pass

        ret['data']['vials'] = []

        for vial_key in vials_total_doses.keys():
            print("Key is " + vial_key)
            doses_per_vial = vials[vial_key]
            total_doses = vials_total_doses[vial_key]
            no_vials = total_doses / doses_per_vial
            ret["data"]['vials'].append(
                {
                    'name': vial_key, 'total_doses': total_doses,
                    'doses_per_vial': doses_per_vial, 'vials': no_vials
                }
            )

        return ret


class AFROBulletin(Resource):
    """
    AFRO Bulletin

    This reports gives a comple summary of the state of the system.

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate]

    def get(self, location, start_date=None, end_date=None):
        # Hack the tests for now.
        if app.config["TESTING"]:
            return {}

        # Set default date values to last epi week.
        today = datetime.now()
        epi_week = EpiWeek().get()
        # Calulation for start date is:
        # month_day - ( week_day-week_offset % 7) - 7
        # The offset is the # days into the current epi week.
        offset = (today.weekday() - epi_week["offset"]) % 7
        # Start date is today minus the offset minus one week.
        if not start_date:
            start_date = (datetime(today.year, today.month, today.day) -
                          timedelta(days=offset + 7)).isoformat()
        # End date is today minus the offset,
        # minus 1 day (because our end date is "inclusive")
        if not end_date:
            end_date = (datetime(today.year, today.month, today.day) -
                        timedelta(days=offset + 1)).isoformat()

        # Initialise some stuff.
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        first_day_of_year = datetime(year=datetime.now().year,
                                     month=1, day=1)
        ret = {}

        #  Meta data.
        ret["meta"] = {"uuid": str(uuid.uuid4()),
                       "project_id": 1,
                       "generation_timestamp": datetime.now().isoformat(),
                       "schema_version": 0.1
        }

        #  Dates and Location Information
        ew = EpiWeek()
        epi_week = ew.get(end_date.isoformat())["epi_week"]
        ret["data"] = {"epi_week_num": epi_week,
                       "end_date": end_date.isoformat(),
                       "project_epoch": datetime(2015, 5, 20).isoformat(),
                       "start_date": start_date.isoformat()
        }
        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)]

        regions = [loc for loc in locs.keys()
                   if locs[loc].parent_location == 1]
        districts = [loc for loc in locs.keys()
                     if locs[loc].parent_location in regions]

        ret["data"]["project_region"] = location_name.name
        ret["data"]["project_region_id"] = location

        #  Actually get the data.
        conn = db.engine.connect()

        # WEEKLY HIGHLIGHTS-----------------------------------------------------------------

        # Get single variables
        ret["data"]["weekly_highlights"] = get_variables_category(
            'afro',
            start_date,
            end_date_limit,
            location,
            conn,
            use_ids=True
        )
        # Get number of clinics
        tot_clinics = TotClinics()
        ret["data"]["weekly_highlights"]["clinic_num"] = tot_clinics.get(location)["total"]

        comp = json.loads(Completeness().get('reg_1',
                                             location, 4).data.decode('UTF-8'))
        # Get completeness figures, assuming 4 registers to be submitted a week.
        try:
            timeline = comp["timeline"][str(location)]['values']
            ret["data"]["weekly_highlights"]["comp_week"] = comp["score"][str(location)]
            ret["data"]["weekly_highlights"]["comp_year"] = comp["yearly_score"][str(location)]
        except AttributeError:
            comp = {"Error": "No data available"}

        # Get multi-variable figures.
        # Assign them the key "var_id1_var_id2", e.g. "cmd_21_ale_1"
        multi_vars = [
            ['cmd_21', 'ale_1'],
            ['cmd_22', 'ale_1'],
            ['cmd_15', 'ale_1'],
            ['cmd_7',  'ale_1'],
            ['cmd_15', 'ale_2'],
            ['cmd_10', 'ale_2'],
            ['cmd_11', 'ale_2'],
            ['cmd_7',  'ale_2'],
            ['cmd_15', 'age_1']
        ]
        for vars_list in multi_vars:
            ret["data"]["weekly_highlights"]["_".join(vars_list)] = query_sum(
                db,
                vars_list,
                start_date,
                end_date,
                location
            )["total"]

        # Add a figure that is the sum of simple and sever malaria to the return data.
        # Used specifically to calulate a percentage.
        mls = ret["data"]["weekly_highlights"]["mls_12"] + ret["data"]["weekly_highlights"]["mls_24"]
        ret["data"]["weekly_highlights"]["mls_12_or_mls_24"] = mls

        # Calculate percentages. Assign them key "var_id1_perc_var_id2" e.g. "mls_3_perc_mls_2".
        # Each element in list is 2 element list of a numerator and denominator for a perc calc.
        perc_vars = [
            ['mls_3', 'mls_2'],
            ['cmd_17', 'mls_2'],
            ['mls_48', 'mls_12_or_mls_24'],
            ['cmd_15_ale_1', 'cmd_15'],
            ['cmd_15_ale_2', 'cmd_15'],
            ['cmd_15_age_1', 'cmd_15'],
            ['cmd_10_ale_2', 'cmd_10'],
            ['cmd_7_ale_1', 'cmd_7'],
            ['cmd_7_ale_2', 'cmd_7']
        ]
        for perc in perc_vars:
            numer = ret["data"]["weekly_highlights"][perc[0]]
            denom = ret["data"]["weekly_highlights"][perc[1]]
            try:
                ret["data"]["weekly_highlights"][perc[0]+"_perc_" + perc[1]] = (numer / denom) * 100
            except ZeroDivisionError:
                ret["data"]["weekly_highlights"][perc[0]+"_perc_"+perc[1]] = 0

        # Top 3 regions of malnutrition.
        nutri = query_sum(
            db,
            ['cmd_24'],
            start_date,
            end_date_limit,
            location,
            level="region"
        )["region"]
        # Sort the regions by counts of malnutrtion
        nutri_top_3 = top(nutri, 3)
        # For each of the top three regions, structure the data.
        nutri_top = []
        for reg in nutri_top_3:
            nutri_top.insert(0, {
                'region': locs[reg].name,
                'number': nutri[reg]
            })
        ret["data"]["weekly_highlights"]["malnutrition"] = nutri_top

        # Top 3 causes of mortality.
        mort = get_variables_category(
            'deaths',
            start_date,
            end_date_limit,
            location,
            conn,
            use_ids=True
        )
        # Sort mortality counts and slice off top three.
        mort = sorted(mort.items(), key=operator.itemgetter(1))[-3:]
        # For each count get the name of the disease that caused it, and structure the data.
        mort_top = []
        for var in mort:
            # Extract the cause's id from the count variables name e.g. mor_1 name is "Deaths icd_17"
            mort_var = Variable().get( var[0] )
            cause_var = Variable().get(mort_var['name'][7:])
            # Only return if there are more than zero deaths.
            if var[1] > 0:
                mort_top.insert(0, {
                    'id': cause_var['id'],
                    'name': cause_var['name'],
                    'number': var[1]
                })
        ret["data"]["weekly_highlights"]["mortality"] = mort_top


        # FIGURE 1: COMPLETENESS BY DISTRICT
        ret["data"]["figure_completeness"] = []
        district_completeness_data = {}
        district_timeliness_data = {}
        comp_reg = {}
        for reg in regions:
            try: # If data is completely missing there is no iformation for districts in the region
                comp_reg = json.loads(Completeness().get('reg_1',
                                                           reg, 4).data.decode('UTF-8'))
                time_reg = json.loads(Completeness().get('reg_5',
                                                         reg, 4).data.decode('UTF-8'))
                for loc_s in comp_reg["yearly_score"].keys():
                    try:
                        ret["data"]["figure_completeness"].append({
                            "district": locs[int(loc_s)].name,
                            "value": comp_reg["yearly_score"][loc_s]
                        })
                    except KeyError:
                        ret["data"]["figure_completeness"].append({
                            "district": locs[int(loc_s)].name,
                            "value": -1
                        })
                for loc_s in comp_reg["score"].keys():
                    district_completeness_data[loc_s] = comp_reg["score"][loc_s]
                for loc_s in time_reg["score"].keys():
                    district_timeliness_data[loc_s] = time_reg["score"][loc_s]

            except AttributeError:
                pass


        # FIGURE 2: CUMULATIVE REPORTED MATERNAL DEATHS BY DISTRICT (MAP)
        mat_deaths = {}
        mat_deaths_ret = query_sum(
            db,
            ['cmd_21'],
            first_day_of_year,
            end_date_limit,
            location,
            level="district"
        )["district"]
        for district in mat_deaths_ret.keys():
            mat_deaths[locs[district].name] = {
                "value": mat_deaths_ret[district]
            }

        # fill the rest of the districts with zeroes
        for district in districts:
            if not locs[district].name in mat_deaths:
                mat_deaths.update(
                    {
                        locs[district].name: {
                            "value": 0
                        }
                    }
                )

        ret["data"].update({"figure_mat_deaths_map": mat_deaths})

        # FIGURE 3: INCIDENCE OF CONFIRMED MALARIA CASES BY REGION (MAP)
        ir = IncidenceRate()
        mal_incidence = ir.get('epi_1', 'region', mult_factor=100000)
        mapped_mal_incidence = {}

        # Structure the data.
        for region in regions:
            if region not in mal_incidence:
                mal_incidence[region] = 0
            mapped_mal_incidence[locs[region].name] = {
                'value': int(mal_incidence[region])
            }

        ret["data"].update({
            "figure_malaria_map":  mapped_mal_incidence
        })

        # FIGURE 4: NUMBER OF CONFIRMED MALARIA CASES BY TYPE AND WEEK
        aggregate_year = AggregateYear()

        simple = aggregate_year.get(variable_id="mls_12",
                                    location_id=location)['weeks']
        severe = aggregate_year.get(variable_id="mls_24",
                                    location_id=location)['weeks']
        rdt = aggregate_year.get(variable_id="mls_3",
                                 location_id=location)['weeks']
        all_weeks = set(simple.keys()) | set(severe.keys()) | set(rdt.keys())

        def calc_positivity(key):
            try:
                return (key,
                        100 * (simple.get(key, 0) + severe.get(key, 0)) / rdt.get(key, 0))
            except ZeroDivisionError:
                return (key, 0)

        ret["data"]["figure_malaria"] = {
            "simple_malaria": simple,
            "severe_malaria": severe,
            "positivity": dict(map(calc_positivity, all_weeks)),
        }

        # FIGURE 5: TREND OF SUSPECTED MEASLES CASES BY AGE GROUP
        qv = QueryVariable()
        measles = qv.get(variable="cmd_15", group_by="age")

        measles_under_5yo = aggregate_year.get(variable_id="cmd_15",
                                               location_id=location)

        ret["data"].update({"figure_measles": {
            "measles_under_5yo": measles_under_5yo,
            "measles_over_5yo": {}
        }})

        #  Aggregate over age groups
        for age_group in measles:
            if age_group == '<5':
                ret["data"]["figure_measles"]["measles_under_5yo"].update(measles[age_group])
            else:
                if "total" in ret["data"]["figure_measles"]["measles_over_5yo"]:
                    ret["data"]["figure_measles"]["measles_over_5yo"]["total"] += measles[age_group]["total"]
                    for week in measles[age_group]["weeks"]:
                        ret["data"]["figure_measles"]["measles_over_5yo"]["weeks"][week] += measles[age_group]["weeks"][week]
                else:
                    ret["data"]["figure_measles"]["measles_over_5yo"].update({"total": measles[age_group]["total"]})
                    ret["data"]["figure_measles"]["measles_over_5yo"].update({"weeks": {}})
                    for week in measles[age_group]["weeks"]:
                        ret["data"]["figure_measles"]["measles_over_5yo"]["weeks"].update({week: measles[age_group]["weeks"][week]})

        # FIGURE 6: TREND OF REPORTED SEVERE MALNUTRITION CASES IN UNDER FIVES
        # Epi 8 tracks severe malnutrition in under 5s. epi_8
        malnutrition = aggregate_year.get(variable_id="epi_8",
                                          location_id=location)
        ret["data"].update({"figure_malnutrition": {
            "malnutrition": malnutrition,
        }})


        # TABLE 1: Reported Priority Diseases, Conditions and Events by District, week X
        # TODO: Connect cmd_codes to mortality

        #  Required priority diseases:
        #  cmd_13 A94    Arbovirus    Arbovirose suspecte
        #  cmd_28 !00    Other / Unusual or Alert    Autre évènement inhabituel nécessitant une alerte
        #  cmd_2  A00    Cholera    Choléra
        #  cmd_1  A09.0    Acute Watery Diarrhoea    Diarrhée aiguë aqueuse
        #  cmd_4  A03    Bloody diarrhoea    Diarrhée sanglante
        #  cmd_19   T61    Seafood poisoning    Episode d’Intoxication par consommation d’animaux marins (ICAM)
        #  cmd_14    A99    Acute Haemorrhagic Fever    Fièvre hémorragique aiguë
        #  cmd_3  A01    Typhoid fever    Fièvre typhoïde
        #  cmd_26 B74.0    Lymphatic Filariasis    Filariose lymphatique
        #  cmd_16 B19    Acute Jaundice Syndrome    Ictère
        #  cmd_25 J06.9    Acute Respiratory Tract Infection    Infection respiratoire aiguë (IRA)
        #  cmd_20 A64    Sexually Transmitted Infection    Infection sexuellement transmissible (IST)
        #  cmd_8  A30    Leprosy    Lèpre
        #  cmd_23 E46    Moderate malnutrition    Malnutrition aigue modérée (MAM)
        #  cmd_24 E43    Severe malnutrition    Malnutrition aigue sévère (MAS)
        #  cmd_12 A87.9    Meningitis    Méningite
        #  cmd_27 T14.1    Animal bite    Morsure ou griffure (animal à sang chaud)
        #  cmd_17 B54    Malaria    Paludisme
        #  cmd_10 A80.10    Acute Flaccid Paralysis    Paralysie flasque aiguë (PFA)
        #  cmd_7     A20    Plague    Peste
        #  cmd_11    A82    Rabies    Rage humaine
        #  cmd_15    B05.06    Measles / Rubella    Rougeole / Rubéole
        #  cmd_18    J11    Influenza-like lllness    Syndrome grippal
        #  cmd_9  A33    Neonatal Tetanus    Tétanos néonatal
        #  cmd_5 A05    Foodborne disease    Toxi Infection Alimentaire collective (TIAC)
        #  cmd_6  A16.9    Tuberculosis    Tuberculose

        ret["data"]['table_priority_diseases'] = {}
        priority_diseases = [
            'cmd_1', 'cmd_2', 'cmd_3',
            'cmd_4', 'cmd_5', 'cmd_6',
            'cmd_7', 'cmd_8', 'cmd_9',
            'cmd_10', 'cmd_11', 'cmd_12',
            'cmd_13', 'cmd_14', 'cmd_15',
            'cmd_16', 'cmd_17', 'cmd_18',
            'cmd_19', 'cmd_20', 'cmd_23',
            'cmd_24', 'cmd_25', 'cmd_26',
            'cmd_27', 'cmd_28'
        ]
        mortality_codes = {
            'cmd_1': 'mor_18',
            'cmd_2': 'mor_26',
            'cmd_3': 'mor_28',
            'cmd_4': 'mor_1',
            'cmd_5': 'mor_6',
            'cmd_6': 'mor_20',
            'cmd_7': 'mor_5',
            'cmd_8': 'mor_14',
            'cmd_9': 'mor_12',
            'cmd_10': 'mor_11',
            'cmd_11': 'mor_10',
            'cmd_12': 'mor_4',
            'cmd_13': 'mor_3',
            'cmd_14': 'mor_29',
            'cmd_15': 'mor_13',
            'cmd_16': 'mor_8',
            'cmd_17': 'mor_16',
            'cmd_18': 'mor_2',
            'cmd_19': 'mor_7',
            'cmd_20': 'mor_19',
            'cmd_23': 'mor_21',
            'cmd_24': 'mor_22',
            'cmd_25': 'mor_17',
            'cmd_26': 'mor_15',
            'cmd_27': 'mor_9',
            'cmd_28': 'mor_23'
        }

        # insert disease names and regions
        for disease in priority_diseases:
            ret["data"]['table_priority_diseases'].update(
                {
                    disease: {
                        "name": Variable().get(disease)["name"],
                        "mortality": 0,
                        "cfr": 0
                    }
                })
            for region in regions:
                ret["data"]['table_priority_diseases'][disease].update(
                    {
                        locs[region].name: 0
                    }
                )

        # disease mortality
        mort = get_variables_category(
            'deaths',
            start_date,
            end_date_limit,
            location,
            conn,
            use_ids=True
        )

        # insert case figures
        for disease in priority_diseases:
            priority_disease_cases = query_sum(
                db,
                [disease],
                start_date,
                end_date_limit,
                location,
                level="region"
            )["region"]
            priority_disease_cases_total = query_sum(
                db,
                [disease],
                start_date,
                end_date_limit,
                location,
            )["total"]

            # add regional case breakdown


            for region in priority_disease_cases:
                try:
                    ret["data"]["table_priority_diseases"][disease][locs[region].name] = priority_disease_cases[region]
                except KeyError:
                    logging.warning("Error: Data not available for disease " + disease)

                # add total case breakdown
            ret["data"]["table_priority_diseases"][disease].update(
                {
                    "cases_total": priority_disease_cases_total
                }
            )

            # add mortality
            try:
                ret["data"]["table_priority_diseases"][disease]["mortality"] = mort[mortality_codes[disease]]
            except KeyError:
                ret["data"]["table_priority_diseases"][disease]["mortality"] = 0

            # add cfr
            try:
                ret["data"]["table_priority_diseases"][disease]["cfr"] = ret["data"]["table_priority_diseases"][disease]["mortality"] / ret["data"]["table_priority_diseases"][disease]["cases_total"] * 100
            except KeyError:
                ret["data"]["table_priority_diseases"][disease]["cfr"] = 'N/A'
            except ZeroDivisionError:
                ret["data"]["table_priority_diseases"][disease]["cfr"] = 'N/A'



        # TABLE 2: Summary of Priority Diseases, Conditions and Events for Weeks 1 to X, 2016 -----------

        ret["data"]["table_priority_diseases_cumulative"]={}


        mort = get_variables_category(
              'deaths',
              start_date,
              end_date_limit,
              location,
              conn,
              use_ids=True
          )

        mort_cumulative = get_variables_category(
              'deaths',
              first_day_of_year,
              end_date_limit,
              location,
              conn,
              use_ids=True
          )


        for disease in priority_diseases:
            ret["data"]["table_priority_diseases_cumulative"].update({disease: {
                "name": Variable().get(disease)["name"],
                "cases": 0,
                "cases_cumulative": 0,
                "mortality": 0,
                "mortality_cumulative": 0,
                "cfr": 0,
                "cfr_cumulative": 0}})

            priority_disease_cases_cumulative = query_sum(
                db,
                [disease],
                first_day_of_year,
                end_date_limit,
                location
            )["total"]

            priority_disease_cases_total = query_sum(
                db,
                [disease],
                start_date,
                end_date_limit,
                location,
            )["total"]


            ret["data"]["table_priority_diseases_cumulative"][disease].update(
                {
                    "cases": priority_disease_cases_total
                }
            )
            ret["data"]["table_priority_diseases_cumulative"][disease].update(
                {
                    "cases_cumulative":priority_disease_cases_cumulative
                })

                # add mortality
            try:
                ret["data"]["table_priority_diseases_cumulative"][disease]["mortality"] = mort[mortality_codes[disease]]
            except KeyError:
                ret["data"]["table_priority_diseases_cumulative"][disease]["mortality"] = 0

            # add cfr
            try:
                ret["data"]["table_priority_diseases_cumulative"][disease]["cfr"] = ret["data"]["table_priority_diseases_cumulative"][disease]["mortality"] / ret["data"]["table_priority_diseases_cumulative"][disease]["cases"] * 100

            except KeyError:
                ret["data"]["table_priority_diseases_cumulative"][disease]["cfr"] = 'N/A'
            except ZeroDivisionError:
                ret["data"]["table_priority_diseases_cumulative"][disease]["cfr"] = 'N/A'

            # add cumulative mortality
            try:
                ret["data"]["table_priority_diseases_cumulative"][disease]["mortality_cumulative"] = mort_cumulative[mortality_codes[disease]]
            except KeyError:
                ret["data"]["table_priority_diseases_cumulative"][disease]["mortality_cumulative"] = 0

            # add cumulative cfr
            try:
                ret["data"]["table_priority_diseases_cumulative"][disease]["cfr_cumulative"] = ret["data"]["table_priority_diseases_cumulative"][disease]["mortality_cumulative"] / ret["data"]["table_priority_diseases_cumulative"][disease]["cases_cumulative"] * 100
            except KeyError:
                ret["data"]["table_priority_diseases_cumulative"][disease]["cfr_cumulative"] = 'N/A'
            except ZeroDivisionError:
                ret["data"]["table_priority_diseases_cumulative"][disease]["cfr_cumulative"] = 'N/A'


        # TABLE 3: Timeliness and Completeness of reporting for Week X, 2016
        ret["data"]["table_timeliness_completeness"] = {}
        for district in districts:
            try:
                if tot_clinics.get(district)["total"] > 0:
                #  District names
                    ret["data"]["table_timeliness_completeness"].update(
                        {str(district): {"name": locs[district].name}})

                    #  Number of clinics in district
                    ret["data"]["table_timeliness_completeness"][str(district)].update({
                        "clinics": tot_clinics.get(district)["total"]
                    })
                    #  Number of clinics that reported
                    ret["data"]["table_timeliness_completeness"][str(district)].update({
                        "clinics_reported": tot_clinics.get(district)["total"] - len(NonReporting().get("reg_1", district))
                    })

                    #  District completeness
                    ret["data"]["table_timeliness_completeness"][str(district)].update({
                        "completeness":district_completeness_data[str(district)]
                    })

                    #  District timeliness
                    ret["data"]["table_timeliness_completeness"][str(district)].update({
                        "timeliness":district_timeliness_data[str(district)]
                    })
            except AttributeError:
                pass

        return ret
