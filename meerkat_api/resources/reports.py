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
from flask import request, jsonify, g
from sqlalchemy import or_, func, desc, Integer
from datetime import datetime, timedelta
from dateutil import parser
from sqlalchemy.sql import text
import uuid
import math
import numpy as np
import traceback
from functools import wraps
from gettext import gettext
import logging, json, operator
from meerkat_api.util import get_children, is_child, fix_dates, rows_to_dicts, find_level, trim_locations
from meerkat_api import db, app
from meerkat_abacus.model import Data, Locations, AggregationVariables, CalculationParameters
from meerkat_api.resources.completeness import Completeness, NonReporting
from meerkat_api.resources.variables import Variables, Variable
from meerkat_api.resources.epi_week import EpiWeek, epi_week_start, epi_year_start
from meerkat_api.resources.locations import TotClinics
from meerkat_api.resources.data import AggregateYear
from meerkat_api.resources.map import Clinics, MapVariable
from meerkat_api.resources import alerts
from meerkat_api.resources.explore import QueryVariable, QueryCategory, get_variables
from meerkat_api.util.data_query import query_sum, latest_query
from meerkat_api.resources.incidence import IncidenceRate
from meerkat_abacus.util import get_locations, all_location_data, get_regions_districts
from meerkat_abacus import model
from meerkat_api.authentication import authenticate, is_allowed_location
from geoalchemy2.shape import to_shape


def report_allowed_location(f):
    """
    Decorator to check allowed locations for reports
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        location = kwargs["location"]
        if not is_allowed_location(location, g.allowed_location):
            return {}
        return f(*args, **kwargs)
    return decorated

def mean(input_list):

    if len(input_list)>0:
        return sum(input_list)/len(input_list)
    else:
        return None

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
        Data.clinic.contains([clinic]),
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



def generateMHtable(table_type, start_date, end_date, location, y_category_variables, y_variables_name, x_variables, x_variables_name, sub_category_variables, sub_category_name, require_variable=None):

    #Define variables
    query_category = QueryCategory()
    query_variable = QueryVariable()
    y_category_dict = dict()
    table_data = []
    mh_id = ""

    if table_type == "case":
        mh_id = "prc_3"
    elif table_type == "visit":
        mh_id = "visit_prc_3"

    # Create an object for totals
    totals_name = "Totals"
    totals_dict = {"type": totals_name,
                   x_variables_name: []}
    totals_accumulator = {}

    for xcat_id in x_variables.keys():
        totals_accumulator[xcat_id] = dict()
        for sub_id in sub_category_variables.keys():
            totals_accumulator[xcat_id][sub_id] = 0

    # Here is the main loop
    # Loop through visit types / governorate
    for y_category_id in y_category_variables.keys():
        y_category_name = y_category_variables[y_category_id]
        y_category_dict = {"type": y_category_name,
                           x_variables_name: []}

        # Loop through nationalities/age
        for xcat_id in sorted(x_variables.keys()):
            xcat_name = x_variables[xcat_id]
            xcat_dict = {"name": xcat_name}
            if y_variables_name == "regions":
                additional_variables = [xcat_id]
                if require_variable:
                    additional_variables.append(require_variable)
                sub_data = query_variable.get(
                    variable=mh_id,
                    group_by=sub_category_name,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    only_loc=y_category_id,
                    use_ids=True,
                    date_variable=None,
                    additional_variables=additional_variables,

                )
            else:
                additional_variables = [y_category_id, xcat_id]
                if require_variable:
                    additional_variables.append(require_variable)
                sub_data = query_variable.get(
                    variable=mh_id,
                    group_by=sub_category_name,
                    start_date=start_date.isoformat(),
                    end_date=end_date.isoformat(),
                    only_loc=location,
                    use_ids=True,
                    date_variable=None,
                    additional_variables=additional_variables,
                    group_by_variables=sub_category_variables,
                )

            sub_category_keys = []
            sub_category_ids = []
            sub_category_values = []

            # Fetch standard gender values
            for sub_id in sub_category_variables.keys():
                sub_category_keys.append(sub_category_variables[sub_id])
                sub_category_ids.append(sub_id)
                current_val = sub_data[sub_id]["total"]
                sub_category_values.append(current_val)
                totals_accumulator[xcat_id][sub_id] = totals_accumulator[xcat_id][sub_id] + current_val
            # Calculate total
            sub_category_total = sum(sub_category_values)

            # Insert percentages
            for sub_id in sub_category_variables.keys():
                sub_id_index = sub_category_keys.index(sub_category_variables[sub_id])+1
                sub_category_keys.insert(sub_id_index, sub_category_variables[sub_id] + '(%)')
                sub_category_values.insert(
                    sub_id_index, 100 *sub_category_values[sub_id_index-1]/(1 if sub_category_total == 0 else sub_category_total))
            # Insert gender totals
            sub_category_keys.append('Total')
            sub_category_values.append(sub_category_total)

            xcat_dict.update({
                sub_category_name: sub_category_keys,
                sub_category_name + "_values": sub_category_values
            })

            y_category_dict[x_variables_name].append(xcat_dict)

        # Insert national totals
        national_totals = {
            sub_category_name: [],
            sub_category_name + "_values": []
        }

        # 2 keys and values in the dictionary per gender code plus total
        if len(sub_category_variables.keys()) > 0:
            sub_keys_in_dict = 2*len(sub_category_variables.keys())+1
        else:
            sub_keys_in_dict = 0

        for i in range(0, sub_keys_in_dict):
            try: 
                national_totals[sub_category_name].append(y_category_dict[x_variables_name][0][sub_category_name][i])
                national_totals[sub_category_name + "_values"].append(sum(item[sub_category_name + "_values"][i] for item in y_category_dict[x_variables_name]))
            except IndexError:
                national_totals[sub_category_name].append(0)
                national_totals[sub_category_name + "_values"].append(0)

        # Calculate national/age total percentages
        for i in range(1, sub_keys_in_dict, 2):
            national_totals[sub_category_name + "_values"][i] = \
                                                100 * national_totals[sub_category_name + "_values"][i-1]/ \
                                                (1 if national_totals[sub_category_name + "_values"][-1] == 0 else national_totals[sub_category_name + "_values"][-1])
            national_totals["name"]="Total"

        y_category_dict[x_variables_name].append(national_totals)
        table_data.append(y_category_dict)
    # End of category variables loop

    #append y-totals
    # Loop through nationalities/age to update percentages
    for xcat_id in sorted(x_variables.keys()):
        sub_category_keys = []
        sub_category_ids = []
        sub_category_values = []
        for sub_category_id in sub_category_variables.keys():
            sub_category_keys.append(sub_category_variables[sub_category_id])
            sub_category_ids.append(sub_category_id)
            sub_category_values.append(totals_accumulator[xcat_id][sub_category_id])

        sub_category_total = sum(sub_category_values)
        # Insert percentages
        for sub_category_id in sub_category_variables.keys():
            sub_category_id_index = sub_category_keys.index(sub_category_variables[sub_category_id])+1
            sub_category_keys.insert(sub_category_id_index, sub_category_variables[sub_category_id] + '(%)')
            sub_category_values.insert(
                sub_category_id_index, 100 * sub_category_values[sub_category_id_index-1]/(1 if sub_category_total == 0 else sub_category_total))
        # Insert sub_category totals
        sub_category_keys.append('Total')
        sub_category_values.append(sub_category_total)

        totals_dict[x_variables_name].append({
            sub_category_name: sub_category_keys,
            sub_category_name + "_values": sub_category_values
        })
        #for each x_category

    # Insert national totals
    national_totals = {
        sub_category_name: [],
        sub_category_name + "_values": []
    }

    # 2 keys and values in the dictionary per gender code plus totat
    if len(sub_category_variables.keys())>0:
        sub_category_keys_in_dict = 2*len(sub_category_variables.keys())+1
    else:
        sub_category_keys_in_dict = 0

    for i in range(0,sub_category_keys_in_dict):
        try:
            national_totals[sub_category_name].append(totals_dict[x_variables_name][0][sub_category_name][i])
            national_totals[sub_category_name + "_values"].append(sum(item[sub_category_name + "_values"][i] for item in totals_dict[x_variables_name]))
        except IndexError:
            national_totals[sub_category_name].append(0)
            national_totals[sub_category_name + "_values"].append(0)
            

    # Calculate national/age total percentages
    for i in range(1,sub_category_keys_in_dict,2):
        national_totals[sub_category_name + "_values"][i] = \
                                            100 * national_totals[sub_category_name + "_values"][i-1]/ \
                                            (1 if national_totals[sub_category_name + "_values"][-1] == 0 else national_totals[sub_category_name + "_values"][-1])
        national_totals["name"]="Total"

    totals_dict[x_variables_name].append(national_totals)

    table_data.append(totals_dict)

    return table_data


def transposeMHtable(table, category1, category2, key1, key2):
    if len(table) == 0:
        return table
    # initialize empty table
    ret_table = []
    # initialize category 1
    for j in range(len(table[0][category1])):
        ret_table.append({key1:table[0][category1][j][key1], category2:[]})
    # loop through both categories and transpose table
    for i in range(len(table)):
        cat = table[i][key2]
        for j in range(len(table[i][category1])):
            ret_table[j][category2].append(table[i][category1][j])
            ret_table[j][category2][i].update({key2:cat})
    return ret_table

"""
Ncd Reports to show data on Hypertension and Diabetes. The data includes
breakdowns by age and on lab data, complications and comorbidity. We create
tables with rows for regions.

Args:\n
   location: Location to generate report for\n
   start_date: Start date of report\n
   end_date: End date of report\n
Returns:\n
   report_data\n
"""
class NcdReportNewVisits(Resource):

    decorators = [authenticate, report_allowed_location]

    def get(self, location, start_date=None, end_date=None):
        retval = create_ncd_report(location=location, start_date=start_date,\
            end_date=end_date, params=['new'])
        return retval

class NcdReportReturnVisits(Resource):

    decorators = [authenticate, report_allowed_location]

    def get(self, location, start_date=None, end_date=None):
        retval = create_ncd_report(location=location, start_date=start_date,\
            end_date=end_date, params=['return'])
        return retval

class NcdReport(Resource):

    decorators = [authenticate, report_allowed_location]

    def get(self, location, start_date=None, end_date=None):
        retval = create_ncd_report(location=location, start_date=start_date,\
            end_date=end_date, params=['case'])
        return retval


def create_ncd_report(location, start_date=None, end_date=None, params=['case']):

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

    #  read from params if creating new visit or return visit report
    if 'new' in params or 'return' in params:
        total_variable = 'vis_0'
        diabetes_id = "visit_ncd_1"
        hypertension_id = "visit_ncd_2"
        age_category = "visit_ncd_age"
        gender_category = "visit_gender"
        gender_variables = ["visit_gen_1", "visit_gen_2"]
        email_report_control_diabetes = "visit_lab_9"
        email_report_control_hypertension = "visit_lab_2"
        diseases = {"hypertension": hypertension_id,
                    "diabetes": diabetes_id}
        ids_to_include = {"hypertension": [("visit_lab_4", "visit_lab_3"), ("visit_lab_5", "visit_lab_3"), \
                            ("visit_lab_2", "visit_lab_1"), ("visit_com_1", "visit_ncd_2"), \
                            ("visit_smo_2", "visit_smo_4"), ("visit_lab_11", "visit_lab_10")],
                          "diabetes": [("visit_lab_4", "visit_lab_3"), ("visit_lab_5", "visit_lab_3"), \
                            ("visit_lab_7", "visit_lab_6"), ("visit_lab_9", "visit_lab_8"), \
                            ("visit_com_2", "visit_ncd_1"), ("visit_smo_2", "visit_smo_4"),\
                            ("visit_lab_11", "visit_lab_10")]
        }
        if 'new' in params:
            additional_variables = ['vis_4']
        elif 'return' in params:
            additional_variables = ['vis_5']

    else:
        total_variable = 'tot'
        diabetes_id = "ncd_1"
        hypertension_id = "ncd_2"
        age_category = "ncd_age"
        gender_category = "gender"
        gender_variables = ["gen_1", "gen_2"]
        email_report_control_diabetes = "lab_9"
        email_report_control_hypertension = "lab_2"
        diseases = {"hypertension": hypertension_id,
                    "diabetes": diabetes_id}
        ids_to_include = {
            "hypertension": [("lab_4", "lab_3"),
                             ("lab_5", "lab_3"),
                             ("lab_2", "lab_1"),
                             ("com_1", "ncd_2"),
                             ("smo_2", "smo_4"),
                             ("lab_11", "lab_10")],
            "diabetes": [
                ("lab_4", "lab_3"),
                ("lab_5", "lab_3"),
                ("lab_7", "lab_6"),
                ("lab_9", "lab_8"),
                ("com_2", "ncd_1"),
                ("smo_2", "smo_4"),
                ("lab_11", "lab_10")]
        }
        additional_variables = []

    locations, ldid, regions, districts, devices = all_location_data(db.session)
    v = Variables()

    children = locations[1].children
    ages = v.get(age_category)

    #  Loop through diabetes and hypertension
    for disease in diseases.keys():
        #  First sort out the titles
        ret[disease]["age"]["titles"] = [gettext("reg")]
        ret[disease]["age"]["data"] = []
        for age in sorted(ages.keys()):
            ret[disease]["age"]["titles"].append(ages[age]["name"])
        ret[disease]["age"]["titles"].insert(1, "Total")
        ret[disease]["complications"]["titles"] = ["reg",
                                                   total_variable,
                                                   gender_variables[0],
                                                   gender_variables[1]]

        for i in ids_to_include[disease]:
            ret[disease]["complications"]["titles"].append(i[0])
        ret[disease]["complications"]["data"] = []

        regions = [r for r in regions if r in children]

        #  Loop through each region, we add [1] to include the whole country
        for i, region in enumerate(sorted(regions) + [1]):
            d_id = diseases[disease]
            query_variable = QueryVariable()


            #  get the age breakdown
            disease_age = query_variable.get(d_id, age_category,
                                             end_date=end_date_limit.isoformat(),
                                             start_date=start_date.isoformat(),
                                             only_loc=region,
                                             use_ids=True,
                                             additional_variables=additional_variables)
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
            disease_gender = query_variable.get(d_id, gender_category,
                                                end_date=end_date_limit.isoformat(),
                                                start_date=start_date.isoformat(),
                                                only_loc=region,
                                                additional_variables=additional_variables)

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
                numerator = query_sum(db, [d_id, new_id[0]] + additional_variables,
                                      start_date, end_date_limit,1, level="region")

                denominator = query_sum(db, [d_id, new_id[1]] + additional_variables,
                                    start_date, end_date_limit, 1, level="region")

                for i, r in enumerate(sorted(regions)):
                    num = numerator["region"].get(int(r), 0)
                    den = denominator["region"].get(int(r), 0)
                    if den == 0:
                        den = 1
                    ret[disease]["complications"]["data"][i]["values"].append(
                        [int(num), num / den * 100])

                num = numerator["total"]
                den = denominator["total"]
                if den == 0:
                    den = 1
                ret[disease]["complications"]["data"][i+1]["values"].append(
                    [int(num), num / den * 100])
                if disease == "diabetes" and new_id[0] == email_report_control_diabetes:
                    ret[disease]["email_summary"]["control"] = num/ den * 100
                elif disease == "hypertension" and new_id[0] == email_report_control_hypertension:
                    ret[disease]["email_summary"]["control"] = num/ den * 100

            else:
                #  We can N/A to the table if it includes data we are not collecting
                 for r in range(len(regions) +1):
                     ret[disease]["complications"]["data"][r]["values"].append("N/A")
    return ret

class MhReport(Resource):
    """
    Mental Health Report to show data on all mental health related diseases and visits.

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate, report_allowed_location]
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

        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)].name
        ret["data"]["project_region"] = location_name
        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]

        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)].name

        # Visit variables
        visit_type_variables = get_variables('visit')
        gender_visit_variables = get_variables('visit_gender')
        nationality_visit_variables = get_variables('mh_visit_nationality')
        age_visit_variables = get_variables('visit_ncd_age')
        #Case based tables:
        [regions,districts] = get_regions_districts(db.session)
        mhgap_variables = get_variables('mhgap')
        gender_case_variables = get_variables('gender')
        nationality_case_variables = get_variables('mh_case_nationality')
        age_case_variables = get_variables('ncd_age')

        service_provider_variables = get_variables('service_provider')
        icd_codes_variables = get_variables('mh_icd_block')

        result_new = get_variables("mh_result_new")
        result_return = get_variables("mh_result_return")
        
        #Prepare region data to be in the same form as a visit list
        region_variables = dict()
        for region_id in regions:
            region_name = locs[int(region_id)].name
            region_variables[region_id]=region_name

        # Tables
        # Table 1: visity type / nationality
        ret['table_1_data'] = generateMHtable("visit", start_date,
                                              end_date, location,
                                              visit_type_variables,
                                              "visit_types",
                                              nationality_visit_variables,
                                              "nationalities",
                                              gender_visit_variables,
                                              "visit_gender")
        # Table 2: visity type / age
        ret['table_2_data'] = generateMHtable(
            "visit", start_date, end_date, location, visit_type_variables,
            "visit_types", age_visit_variables, "age_categories",
            gender_visit_variables, "visit_gender")

        # Table 3: governorate / nationality / gender
        ret['table_3_data'] = generateMHtable(
            "case", start_date, end_date, location, region_variables,
            "regions",  nationality_case_variables, "nationalities",
            gender_case_variables,
            "gender")
        # Table 4: governorate / nationality / visit_type
        ret['table_4_data'] = generateMHtable(
            "visit", start_date, end_date, location, region_variables,
            "regions",  nationality_visit_variables, "nationalities",
            visit_type_variables, "visit")

        ret['table_5_data'] = generateMHtable(
            "case", start_date, end_date, location, region_variables,
            "regions",  age_case_variables, "age_categories",
            gender_case_variables,
            "gender")
        
        ret['table_6_data'] = generateMHtable(
            "visit", start_date, end_date, location, region_variables,
            "regions",  age_visit_variables, "age_categories",
            visit_type_variables, "visit")

        ret['table_7_data'] = generateMHtable(
            "case", start_date, end_date, location, mhgap_variables,
            "mhgap",  nationality_case_variables, "nationalities",
            gender_case_variables,
            "gender", require_variable="mh_provider_mhgap")
        
        ret['table_8_data'] = generateMHtable(
            "case", start_date, end_date, location, mhgap_variables,
            "mhgap",  age_case_variables, "age_categories",
            gender_case_variables, "gender",require_variable="mh_provider_mhgap")
        
        ret['table_9_data'] = generateMHtable(
            "case", start_date, end_date, location, icd_codes_variables,
            "mh_icd_block",  nationality_case_variables, "nationalities",
            gender_case_variables,
            "gender",require_variable="mh_provider_icd")
        
        ret['table_10_data'] = generateMHtable(
            "case", start_date, end_date, location, icd_codes_variables,
            "mh_icd_block",  age_case_variables, "age_categories",
            gender_case_variables, "gender",require_variable="mh_provider_icd")

        ret['table_11_data'] = generateMHtable(
            "visit", start_date, end_date, location, result_new,
            "mh_result_new",  age_visit_variables, "age_categories",
            gender_visit_variables, "gender")
        ret['table_12_data'] = generateMHtable(
            "visit", start_date, end_date, location, result_return,
            "mh_result_return",  age_visit_variables, "age_categories",
            gender_visit_variables, "gender")
        ret['table_13_data'] = generateMHtable(
            "case", start_date, end_date, location, service_provider_variables,
            "service_provider",  age_case_variables, "age_categories",
            gender_case_variables, "gender")
       
       
        # Transposing
        
        ret['table_1_data'] = transposeMHtable(ret['table_1_data'], "nationalities","visit_types",'name',"type")
        ret['table_2_data'] = transposeMHtable(ret['table_2_data'], "age_categories","visit_types",'name',"type")
        ret['table_3_data'] = transposeMHtable(ret['table_3_data'], "nationalities","regions",'name',"type")
        ret['table_4_data'] = transposeMHtable(ret['table_4_data'], "nationalities","regions",'name',"type")
        
        ret['table_5_data'] = transposeMHtable(ret['table_5_data'], "age_categories","regions",'name',"type")
        ret['table_6_data'] = transposeMHtable(ret['table_6_data'], "age_categories","regions",'name',"type")
        ret['table_7_data'] = transposeMHtable(ret['table_7_data'], "nationalities","mhgap",'name',"type")
        ret['table_8_data'] = transposeMHtable(ret['table_8_data'], "age_categories","mhgap",'name',"type")
        ret['table_9_data'] = transposeMHtable(ret['table_9_data'], "nationalities","mh_icd_block",'name',"type")

        ret['table_10_data'] = transposeMHtable(ret['table_10_data'], "age_categories","mh_icd_block",'name',"type")
        ret['table_11_data'] = transposeMHtable(ret['table_11_data'], "age_categories", "mh_result_new",'name',"type")
        ret['table_12_data'] = transposeMHtable(ret['table_12_data'], "age_categories", "mh_result_return",'name',"type")

        ret['table_13_data'] = transposeMHtable(ret['table_13_data'], "age_categories","service_provider",'name',"type")
        print(ret["table_13_data"])
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
    decorators = [authenticate, report_allowed_location]

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
        weeks = list(range(1, 53))
        data_list = [0 for week in weeks]
        variable_query = db.session.query(AggregationVariables).filter(
            AggregationVariables.alert == 1)
        variable_names = {}
        variable_type = {}
        for v in variable_query.all():
            variable_names[v.id] = v.name
            variable_type[v.name] = v.alert_type
        #  The loop through all alerts
        current_year = start_date.year
        previous_years = {}
        for a in all_alerts:
            alert_year = a["date"].year
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
            if epi_week == 53:
                if a["date"].month == 1:
                    epi_week = 1
                else:
                    epi_week = 52
            if report_status:
                if alert_year == current_year:
                    data.setdefault(reason, {"weeks": weeks,
                                             "suspected": list(data_list),
                                             "confirmed": list(data_list)})
                    data[reason][report_status][weeks.index(epi_week)] += 1
                else:
                    previous_years.setdefault(reason, {})
                    previous_years[reason].setdefault(alert_year, list(data_list))
                    previous_years[reason][alert_year][weeks.index(epi_week)] += 1

        # For now we show last years data
        last_year = current_year - 1
        for reason in data.keys():
            data[reason]["previous"] = previous_years.get(reason,{last_year:list(data_list)}).get(
                last_year, list(data_list))
        ret["data"]["communicable_diseases"] = data
        ret["data"]["variables"] = variable_type
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
    decorators = [authenticate, report_allowed_location]

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
        sari_clinics = get_children(location, locs, case_type="SARI")
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
        print("pip_followup:")
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
            if is_child(location, l.id, locs) and l.case_report and l.case_type == "SARI":
                num = query_sum(db, [sari_code],
                                      start_date,
                                      end_date_limit, l.id)["total"]
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))
        ret["data"]["reporting_sites"].sort(key=lambda x: x["quantity"], reverse=True)
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
    decorators = [authenticate, report_allowed_location]

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
            if l.parent_location and int(location) in l.parent_location:
                num = query_sum(db, ["tot_1"],
                                start_date,
                                end_date_limit, l.id)["total"]
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))

        ret["data"]["reporting_sites"].sort(key=lambda x: x["quantity"], reverse=True)
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
    decorators = [authenticate, report_allowed_location]

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
        total_deaths = query_sum(db, ["dea_0"], start_date, end_date_limit, location)["total"]
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

        # medicines = query_variable.get("prc_1", "medicine",
        #                              end_date=end_date_limit.isoformat(),
        #                              start_date=start_date.isoformat(),
        #                              only_loc=location, use_ids=True)

        # if "med_1" in medicines and "med_2" in medicines:
        #     tot_med = medicines["med_1"]["total"]
        #     if tot_med == 0:
        #         tot_med = 1
        #     ret["data"]["public_health_indicators"].append(
        #         make_dict(gettext("Availability of prescribed medicines"),
        #                   medicines["med_2"]["total"],
        #                   medicines["med_2"]["total"] / tot_med * 100))
        # else:
        #     ret["data"]["public_health_indicators"].append(
        #         make_dict(gettext("Availability of prescribed medicines"),
        #                   0,0))


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

        ir = IncidenceRate()

        all_cd_cases = "prc_1"
        locs = get_locations(db.session)
        #level = "district"
        #areas = [loc for loc in locs.keys()
        #         if locs[loc].level == "district"]
        #if location = "1":
        level = "region"
        areas = [loc for loc in locs.keys()
                 if locs[loc].level == "region"]
        incidence = ir.get(all_cd_cases, level, mult_factor=1000,
                           start_date=start_date,
                           end_date=end_date_limit)

        max_number = 0
        if len(incidence.values()) > 0:
            max_number = max(incidence.values())
        mult_factor = 1
        if max_number < 1:
            mult_factor = 10
        in_map = {}
        # Structure the data.
        reporting_sites = []
       
        for area in areas:
            if area not in incidence:
                in_map[locs[area].name] = 0
            else:
                in_map[locs[area].name] = {
                    'value': incidence[area] * mult_factor
                }
        ret["data"].update({
            "incidence_map":  in_map
        })

        current_level = locs[int(location)].level
        next_level = {"country": "region",
                      "zone": "region",
                      "region": "district",
                      "district": "clinic",
                      "clinic": None}[current_level]
        if next_level in ["region", "district"]:
            areas = [loc for loc in locs.keys()
                     if locs[loc].level == next_level]
            incidence = ir.get(all_cd_cases, next_level, mult_factor=1000,
                               start_date=start_date,
                               end_date=end_date_limit)
            for area in areas:
                if is_child(location, area, locs) and area in incidence:
                    reporting_sites.append(make_dict(locs[area].name,
                                                     incidence[area] * mult_factor,
                                                     0))
        reporting_sites.sort(key=lambda x: x["quantity"], reverse=True)
        ret["data"]["reporting_sites_incidence"] = reporting_sites
        ret["data"]["reporting_sites"] = []
        ret["data"]["incidence_area"] = next_level
        ret["data"]["incidence_denominator"] = 1000 * mult_factor

        for l in locs.values():
            if l.level == "clinic" and l.case_report == 0:
                continue
            if l.parent_location and int(location) in l.parent_location:
                num = query_sum(db, ["prc_1"],
                                      start_date,
                                      end_date_limit, l.id)["total"]
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))
        ret["data"]["reporting_sites"].sort(key=lambda x: x["quantity"], reverse=True)
        


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
        print(age_gender)
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
    decorators = [authenticate, report_allowed_location]

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



class CdPublicHealthSom(Resource):
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
    decorators = [authenticate, report_allowed_location]

    def get(self, location, start_date=None, end_date=None):

        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        conn = db.engine.connect()
        query_variable = QueryVariable()

        locs = get_locations(db.session)
        if int(location) not in locs:
            return None
        location_name = locs[int(location)]

        regions = [loc for loc in locs.keys()
                   if locs[loc].level == "region"]
        districts = [loc for loc in locs.keys()
                     if locs[loc].level == "district"]


        zone_location = location
        # Determine zone
        logo_dict = {"Puntland": "moh_pl.png",
                     "Somaliland": "moh_sl.png"}
        zone_name = locs[int(location)].name        
        if location == "1":
            #All of somalia
            logo = "som_moh.png"
            zone_location = location
        else:
            zone_location = find_level(location, "zone", locs)
            zone_name = locs[zone_location].name
            logo = logo_dict.get(zone_name, "som_moh.png")
        

        # This report is nearly the same as the CDPublicHealth Report
        # Let's just get that report and tweak it slightly.
        rv = CdPublicHealth()
        ret = rv.get( location, start_date.isoformat(), end_date.isoformat() )

        ret["data"]["logo"] = logo
        ret["data"]["project_region"] = zone_name
        query_variable = QueryVariable()
        total_cases = query_sum(db, ["tot_1"], start_date, end_date_limit, location)["total"]
        gender = query_variable.get("tot_1", "gender",
                                    end_date=end_date_limit.isoformat(),
                                    start_date=start_date.isoformat(),
                                    only_loc=location)
        age = query_variable.get("tot_1", "age",
                                 end_date=end_date_limit.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)
        ret["data"]["total_cases"] = total_cases
        if total_cases == 0:
            total_cases = 1
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
        less_5yo = query_variable.get("tot_1", "under_five",
                                 end_date=end_date_limit.isoformat(),
                                 start_date=start_date.isoformat(),
                                 only_loc=location)
        less_5yo = sum(less_5yo[k]["total"] for k in less_5yo.keys())

        ret["data"]["percent_cases_lt_5yo"] = less_5yo / total_cases * 100
        if less_5yo == 0:
            less_5yo = 1



        # Other values required for the email.
        ret['email'] = {
            'cases': int(round(query_sum(db, ['tot_1'], start_date, end_date_limit, location)["total"])),
            'consultations': int(round(query_sum(db, ['reg_2'],
                                                 start_date, end_date_limit, location)["total"])),
            'clinics': int(round(TotClinics().get(location)["total"]))
        }

        # Delete unwanted indicators.
        # leaving only Case Reported and Alerts Investigated
        del ret["data"]["public_health_indicators"][0:3] #TODO, we are relying here on the structure of standard profile report. 

        # IMCI algorithm indicator
  
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Cases Reported"),
                      total_cases,
                      100))
        imci_cases = query_sum(
            db,
            ["imci_case"],
            start_date.isoformat(),
            end_date_limit.isoformat(),
            location
        )["total"]
        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Child Health (IMCI) algorithm followed"),
                      imci_cases,
                      imci_cases / total_cases * 100))

        # Replace with new indicators.
        comp = Completeness()
        comp_reg = json.loads(Completeness().get('reg_1',
                                                    location, 4, end_date=end_date + timedelta(days=2)).data.decode('UTF-8')) #TODO HARDCODED no of registers required per week
        time_reg = json.loads(Completeness().get('reg_5',
                                                    location, 4, end_date=end_date + timedelta(days=2)).data.decode('UTF-8'))

        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Completeness"),
                      "-",
                      comp_reg["yearly_score"].get(str(location), "-")))

        ret["data"]["public_health_indicators"].append(
            make_dict(gettext("Timeliness"),
                      "-",
                      time_reg["yearly_score"].get(str(location), "-")))

        # Remove non-reporting sites from data structure
        somalia_reporting_sites = []
        for site in ret["data"]["reporting_sites"]:
            if site["quantity"]> 0:
                somalia_reporting_sites.append(site)

        ret["data"]["reporting_sites"]=somalia_reporting_sites

        # Add demographic totals
        gender_totals=sum(item['quantity'] for item in ret["data"]["gender"])
        ret["data"]["gender_totals"] = gender_totals

        # COMPLETENESS CHART
        ret["data"]["figure_completeness"] = []
        district_completeness_data = {}
        district_timeliness_data = {}
        comp_reg = {}
        comp_reg = json.loads(Completeness().get('reg_1',
                                                 zone_location, 4,
                                                 sublevel="district",
                                                 end_date=end_date + timedelta(days=2)).data.decode('UTF-8'))
        time_reg = json.loads(Completeness().get('reg_5',
                                                 zone_location, 4,
                                                 sublevel="district",
                                                 end_date=end_date + timedelta(days=2)).data.decode('UTF-8'))
        for loc_s in comp_reg["yearly_score"].keys():
            if loc_s != str(zone_location):
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



        # FIGURE 3: INCIDENCE OF CONFIRMED MALARIA CASES BY REGION (MAP)
        ir = IncidenceRate()

        severe_malnutrition = "cmd_7"
        mal_incidence = ir.get(severe_malnutrition, 'district', mult_factor=10000,
                               start_date=start_date,
                               end_date=end_date_limit)
        mapped_mal_incidence = {}
        locs = get_locations(db.session)
        districts = [loc for loc in locs.keys()
                     if locs[loc].level == "district"]
        # Structure the data.
        for district in districts:
            if district not in mal_incidence:
                mal_incidence[district] = 0
            if is_child(zone_location, district, locs):
                mapped_mal_incidence[locs[district].name] = {
                    'value': int(mal_incidence[district])
                }
        ret["data"].update({
            "figure_malnutrition_map":  mapped_mal_incidence
        })

        ret["data"]["morbidity_communicable_imci"] = get_disease_types("imci", start_date, end_date_limit, location, conn)

        clin = Clinics()
        ret["data"]["map"] = clin.get(zone_location)

        
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
    decorators = [authenticate, report_allowed_location]

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
            if l.parent_location and int(location) in l.parent_location:
                if l.level == "clinic" and l.case_report == 0:
                    continue
                num = query_sum(db , ["prc_2"],
                                start_date,
                                end_date_limit, l.id)["total"]
                ret["data"]["reporting_sites"].append(
                    make_dict(l.name,
                              num,
                              num / total_cases * 100))
        ret["data"]["reporting_sites"].sort(key=lambda x: x["quantity"], reverse=True)
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

        regions = [loc for loc in locs.keys()
                   if locs[loc].parent_location == 1]
        # Diabets map
        ir = IncidenceRate()
        dia_incidence = ir.get('ncd_1', 'region', mult_factor=1000)
        hyp_incidence = ir.get('ncd_2', 'region', mult_factor=1000)
        mapped_dia_incidence = {}
        mapped_hyp_incidence = {}

        # Structure the data.
        for region in regions:
            if region not in dia_incidence:
                dia_incidence[region] = 0
            if region not in hyp_incidence:
                hyp_incidence[region] = 0

            mapped_dia_incidence[locs[region].name] = {
                'value': int(dia_incidence[region])
            }
            mapped_hyp_incidence[locs[region].name] = {
                'value': int(hyp_incidence[region])
            }

        ret["data"].update({
            "figure_diabetes_map":  mapped_dia_incidence,
            "figure_hyp_map":  mapped_hyp_incidence
        })


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

    decorators = [authenticate, report_allowed_location]

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
                Data.clinic.contains([clinic]),
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
        ret["data"]["reporting_sites"].sort(key=lambda x: x["quantity"], reverse=True)
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
    decorators = [authenticate, report_allowed_location]

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
                Data.clinic.contains([clinic]),
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

    decorators = [authenticate, report_allowed_location]

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
    decorators = [authenticate, report_allowed_location]

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
            'deaths_epi_monitoring',
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
    decorators = [authenticate, report_allowed_location]

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
        var.update( variables_instance.get('malaria_situation_no_case') )

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
    decorators = [authenticate, report_allowed_location]

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
            logging.error("Error: " + str(e))
            ret['data'] = {'message': 'invalid data'}

        # get vaccination data from database
        vaccination_parameters = db.session.query(CalculationParameters.parameters)\
            .filter(CalculationParameters.name == 'vaccination_vials')\
            .one()[0]

        vials = vaccination_parameters["vials"]
        vials_total_doses = vaccination_parameters["vials_total_doses"]
        vials_types = vaccination_parameters["vials_types"]

        for category in counts:
            for vacc in counts[category].keys():
                try:
                    vials_total_doses[vials_types[vacc]] += counts[category][vacc]
                except:
                    pass

        ret['data']['vials'] = []

        for vial_key in vials_total_doses.keys():
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
    decorators = [authenticate, report_allowed_location]

    def get(self, location, start_date=None, end_date=None):
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
        first_day_of_year = datetime(year=end_date.year,
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
                   if locs[loc].level == "region"]
        districts = [loc for loc in locs.keys()
                     if locs[loc].level == "district"]

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
                                             location, 4, end_date=end_date + timedelta(days=2)).data.decode('UTF-8'))
        # Get completeness figures, assuming 4 registers to be submitted a week.
        try:
            # TODO: Handle case where there is no completeness data properly.
            timeline = comp["timeline"][str(location)]['values']
            ret["data"]["weekly_highlights"]["comp_week"] = comp["score"][str(location)]
            ret["data"]["weekly_highlights"]["comp_year"] = comp["yearly_score"][str(location)]
        except (AttributeError, KeyError):
            comp = {"Error": "No data available"}

        # Get multi-variable figures.
        # Assign them the key "var_id1_var_id2", e.g. "cmd_21_ale_1"
        multi_vars = [
            ['cmd_21', 'ale_1'],
            ['cmd_22', 'ale_1'],
            ['cmd_15', 'ale_1'],
            ['cmd_7',  'ale_1'],
            ['cmd_15', 'ale_2'],
            ['cmd_10', 'ale_1'],
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

        if ret["data"]["weekly_highlights"]["cmd_25"] != 0:
            ret["data"]["weekly_highlights"]["cmd_18_perc_cmd_25"] = 100 * ret["data"]["weekly_highlights"]["cmd_18"] / ret["data"]["weekly_highlights"]["cmd_25"]
        else:
            ret["data"]["weekly_highlights"]["cmd_18_perc_cmd_25"] = 0

        # Calculate percentages. Assign them key "var_id1_perc_var_id2" e.g. "mls_3_perc_mls_2".
        # Each element in list is 2 element list of a numerator and denominator for a perc calc.
        perc_vars = [
            ['mls_3', 'mls_2'],
            ['cmd_17', 'mls_2'],
            ['mls_48', 'mls_12_or_mls_24'],
            ['cmd_15_ale_1', 'cmd_15'],
            ['cmd_15_ale_2', 'cmd_15'],
            ['cmd_15_age_1', 'cmd_15'],
            ['cmd_10_ale_1', 'cmd_10'],
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
#            mort_var = Variable().get( var[0] )
            cause_var = Variable().get(var[0].replace("mor", "cmd"))
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
        comp_reg = json.loads(Completeness().get('reg_1',
                                                 location, 4,
                                                 sublevel="district",
                                                 end_date=end_date + timedelta(days=2)).data.decode('UTF-8'))
        time_reg = json.loads(Completeness().get('reg_5',
                                                 location, 4,
                                                 sublevel="district",
                                                 end_date=end_date + timedelta(days=2)).data.decode('UTF-8'))
        for loc_s in comp_reg["yearly_score"].keys():
            if loc_s != location:
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
        mal_incidence = ir.get('epi_1', 'region', mult_factor=100000,
                               start_date=first_day_of_year,
                               end_date=end_date_limit)
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

        simple =  query_sum(
            db, ["mls_12"], first_day_of_year, end_date_limit, location, weeks=True
        )["weeks"]
        severe =  query_sum(
            db, ["mls_24"], first_day_of_year, end_date_limit, location, weeks=True
        )["weeks"]
        rdt = query_sum(
            db, ["mls_3"], first_day_of_year, end_date_limit, location, weeks=True
        )["weeks"]
        all_weeks = set(simple.keys()) | set(severe.keys()) | set(rdt.keys())

        def calc_positivity(key):
            try:
                return (key,
                        100 * (simple.get(key, 0) + severe.get(key, 0)) / rdt.get(key, 0))
            except ZeroDivisionError:
                print("hei")
                return (key, 0)

        ret["data"]["figure_malaria"] = {
            "simple_malaria": simple,
            "severe_malaria": severe,
            "positivity": dict(map(calc_positivity, all_weeks)),
        }
        # FIGURE 5: TREND OF SUSPECTED MEASLES CASES BY AGE GROUP
        qv = QueryVariable()
        measles = qv.get(variable="cmd_15", group_by="age", only_loc=location,
                         start_date=first_day_of_year.isoformat(), end_date=end_date.isoformat())

        measles_under_5yo = aggregate_year.get(variable_id="cmd_15",
                                               location_id=location, year=end_date.year)

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

        malnutrition = query_sum(
            db, ["epi_8"], first_day_of_year, end_date_limit, location, weeks=True
        )

        ret["data"].update({"figure_malnutrition": {
            "malnutrition": {"weeks": malnutrition["weeks"], "year": malnutrition["total"]},
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
            'cmd_1': 'mor_1',
            'cmd_2': 'mor_2',
            'cmd_3': 'mor_3',
            'cmd_4': 'mor_4',
            'cmd_5': 'mor_5',
            'cmd_6': 'mor_6',
            'cmd_7': 'mor_7',
            'cmd_8': 'mor_8',
            'cmd_9': 'mor_9',
            'cmd_10': 'mor_10',
            'cmd_11': 'mor_11',
            'cmd_12': 'mor_12',
            'cmd_13': 'mor_13',
            'cmd_14': 'mor_14',
            'cmd_15': 'mor_15',
            'cmd_16': 'mor_16',
            'cmd_17': 'mor_17',
            'cmd_18': 'mor_18',
            'cmd_19': 'mor_19',
            'cmd_20': 'mor_20',
            'cmd_23': 'mor_23',
            'cmd_24': 'mor_24',
            'cmd_25': 'mor_15',
            'cmd_26': 'mor_26',
            'cmd_27': 'mor_27',
            'cmd_28': 'mor_28'
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
            priority_disease_cases_q = query_sum(
                db,
                [disease],
                start_date,
                end_date_limit,
                location,
                level="region"
            )
            priority_disease_cases = priority_disease_cases_q["region"]
            priority_disease_cases_total = priority_disease_cases_q["total"]

            # add regional case breakdown

            print(disease, priority_disease_cases)
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

        nr = NonReporting().get("reg_1", 1)["clinics"]

        
        
        for district in districts:
            try:
                n_clin = tot_clinics.get(district)["total"]
                if n_clin> 0:
                #  District names
                    ret["data"]["table_timeliness_completeness"].update(
                        {str(district): {"name": locs[district].name}})

                    clinics = get_children(district, locs, require_case_report=True)
                    n_nr = sum([1 if c in nr else 0 for c in clinics])
                    #  Number of clinics in district
                    ret["data"]["table_timeliness_completeness"][str(district)].update({
                        "clinics": n_clin
                    })
                    #  Number of clinics that reported
                    ret["data"]["table_timeliness_completeness"][str(district)].update({
                        "clinics_reported": n_clin - n_nr
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
            except KeyError:
                pass
        return ret



class PlagueReport(Resource):
    """
    PlagueReport

    This reports gives a summary of the plague situation

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate, report_allowed_location]

    def get(self, location, start_date=None, end_date=None):

        # Set default date values to last epi week.
        today = datetime.now()
        epi_week = EpiWeek().get()
        # Initialise some stuff.
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        first_day_of_year = datetime(year=end_date.year,
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
                   if locs[loc].level == "region"]
        districts = [loc for loc in locs.keys()
                     if locs[loc].level == "district"]
        ret["data"]["project_region"] = location_name.name
        ret["data"]["project_region_id"] = location

        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]
        plague_code = "cmd_7"
        start_week = 34
        current_year = end_date.year

        weeks = list(range(34, 53)) + list(range(1, start_week))
        data_list = [0 for week in weeks]
        if epi_week > start_week:
            current_year = current_year + 1
        plague_cases = alerts.get_alerts({"location": location, "reason": plague_code})

        # Figure 1: Epi curve for plague cases
        # Figure 2: Status breakdown 
        fig_1 = {"weeks": weeks,
                 "total": list(data_list)}
        fig_2 = {"weeks": weeks,
                  "suspected": list(data_list),
                  "confirmed": list(data_list)}

        total = 0
        confirmed = 0
        deaths = 0
        for case in plague_cases:
            case_year = case["date"].year

            report_status = None
            if "ale_2" in case["variables"]:
                report_status = "confirmed"
            elif "ale_3" in case["variables"]:
                continue
            else:
                report_status = "suspected"
            
            epi_week = ew.get(case["date"].isoformat())["epi_week"]
            if epi_week == 53:
                if case["date"].month == 1:
                    epi_week = 1
                else:
                    epi_week = 52
            if report_status:
                total += 1
                if report_status == "confirmed":
                    confirmed += 1
                if "pla_3" in case["variables"]:
                    deaths += 1

                if ((case_year == current_year and epi_week < start_week) or
                    (case_year == current_year -1 and epi_week >= start_week)):
                  
                    fig_2[report_status][weeks.index(epi_week)] += 1

                    fig_1["total"][weeks.index(epi_week)] += 1

        ret["data"]["epi_curve"] = fig_1
        ret["data"]["status"] = fig_2
        ret["data"]["total"] = total
        ret["data"]["confirmed"] = confirmed
        ret["data"]["deaths"] = deaths
        if total == 0:
            total = 1
        ret["data"]["mortality_rate"] = (deaths / total) * 1000
        
                    
       
        first_day_of_season = epi_week_start(current_year - 1, start_week)
        end_date_season = epi_week_start(current_year, start_week) - timedelta(days=1)
        

        # FIGURE 3: MAP of plague cases
        plague_cases = {}
        plague_cases_ret = query_sum(
            db,
            [plague_code],
            first_day_of_season,
            end_date_season,
            location,
            level="district"
        )["district"]
        for district in plague_cases_ret.keys():
            plague_cases[locs[district].name] = {
                "value": plague_cases_ret[district]
            }
        # fill the rest of the districts with zeroes
        for district in districts:
            if not locs[district].name in plague_cases:
                plague_cases.update(
                    {
                        locs[district].name: {
                            "value": 0
                        }
                    }
                )
        print(plague_cases_ret)
        ret["data"].update({"plague_map": plague_cases})

        plague_top_3 = top(plague_cases_ret, 3)
        # For each of the top three regions, structure the data.
        plague_top = []
        for dist in plague_top_3:
            plague_top.insert(0, {
                'district': locs[dist].name,
                'number': plague_cases_ret[dist]
            })
        ret["data"]["top_plague_dists"] = plague_top
        
        return ret
class EBSReport(Resource):
    """
    EBSReport

    This reports gives a summary of the plague situation

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate, report_allowed_location]

    def get(self, location, start_date=None, end_date=None):

        # Set default date values to last epi week.
        today = datetime.now()
        epi_week = EpiWeek().get()
        # Initialise some stuff.
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        first_day_of_year = datetime(year=end_date.year,
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
                   if locs[loc].level == "region"]
        districts = [loc for loc in locs.keys()
                     if locs[loc].level == "district"]
        ret["data"]["project_region"] = location_name.name
        ret["data"]["project_region_id"] = location

        tot_clinics = TotClinics()
        ret["data"]["clinic_num"] = tot_clinics.get(location)["total"]


        # Tot events:
        tot_events = query_sum(
            db,
            ["ebs_case"],
            start_date,
            end_date_limit,
            location,
            )["total"]
        ret["data"]["total_events"] = tot_events
        tot_cases = query_sum(
            db,
            ["ebs_cases"],
            start_date,
            end_date_limit,
            location,
            )["total"]
        ret["data"]["total_cases"] = tot_cases
        confirmed = query_sum(
            db,
            ["ebs_confirmed"],
            start_date,
            end_date_limit,
            location,
            )["total"]
        ret["data"]["confirmed_events"] = confirmed
        disregarded= query_sum(
            db,
            ["ebs_no_confirm"],
            start_date,
            end_date_limit,
            location,
            )["total"]
        ret["data"]["disregarded_events"] = disregarded


        
        event_types = get_variables_category("ebs_event_type", start_date, end_date_limit,
                                              location, db)
        event_risks = get_variables_category("ebs_risk_level", start_date, end_date_limit,
                                              location, db)
        ret["data"]["event_types"] = event_types
        ret["data"]["event_types_top_2"] = top(event_types, 2)
        ret["data"]["event_risk_level"] = event_risks
        ret["data"]["event_risk_level_top_2"] = top(event_risks, 2)


        records = db.session.query(Data).filter(
            Data.variables.has_key(str("ebs_case")),
            Data.date >= start_date,
            Data.date < end_date_limit,
            or_(
                loc.contains([int(location)]) for loc in (Data.country,
                                               Data.region,
                                               Data.district,
                                               Data.clinic))).all()

        ret["data"]["records"] = []

        var = Variables()

        ebs_variables = var.get("ebs")
        ebs_variables["-"] = {"name": "-"}
        for r in records:

            row = {
                "reported_date": r.date.isoformat().split("T")[0],
                "clinic": locs[r.clinic].name,
                "region": locs[r.region].name,
                "initial_investigation": r.variables.get("ebs_initial", "-").split("T")[0],
                "followup_date": r.variables.get("ebs_followup", "-").split("T")[0],
                "event_type": ebs_variables[r.categories.get("ebs_event_type", "-")]["name"],
                "risk_level": ebs_variables[r.categories.get("ebs_risk_level", "-")]["name"],
                "central_review_date":r.variables.get("ebs_central_review", "-").split("T")[0],
                "outcome": ebs_variables[r.categories.get("ebs_outcome", "-")]["name"],
            }
            ret["data"]["records"].append(row)

        ret["data"]["records"].sort(key=lambda element: element["reported_date"],
                                    reverse=True)
            
        mv = MapVariable()

        ebs_map = mv.get("ebs_case", location=location, start_date=start_date.isoformat(),
                         end_date=end_date_limit.isoformat())
        ret["data"]["map"] = ebs_map
        return ret

class CTCReport(Resource):

    """
    CTCReport

    This reports gives a summary of the Cholera Treatment Centre surveillance

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate, report_allowed_location]

    def get(self, location, start_date=None, end_date=None):

        # Set default date values to last epi week.
        today = datetime.now()
        epi_week = EpiWeek().get()
        # Initialise some stuff.
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        first_day_of_year = datetime(year=end_date.year,
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
        fix_children = locs[int(location)].children
        regions = [loc for loc in locs.keys()
                   if locs[loc].level == "region"]
        districts = [loc for loc in locs.keys()
                     if locs[loc].level == "district"]
        zones = [loc for loc in locs.keys()
                     if locs[loc].level == "zone"]
        ret["data"]["project_region"] = location_name.name
        ret["data"]["project_region_id"] = location

        children = get_children(location, locs, require_case_report=False)

        ctcs = db.session.query(Locations).filter(
            or_(Locations.clinic_type == "CTC", Locations.clinic_type == "CTU")).filter(
                Locations.id.in_(children)
                ).all()

        ret["data"]["clinic_num"] = len(ctcs)

        cholera_cases_variable = 'ctc_cases'
        cholera_cases_u5_variable = 'ctc_cases_u5'
        cholera_deaths_variable = 'ctc_deaths'


        cholera_var = "ctc_1"
        # Summary data
        ret['summary']={}

        # Aggregate numbers of cholera cases and deaths as an epi curve and a map.

        cholera_cases = latest_query(db, cholera_cases_variable, cholera_var, start_date, end_date_limit, location, weeks=True, week_offset=1)
        cholera_cases_u5 = latest_query(db, cholera_cases_u5_variable, cholera_var, start_date, end_date_limit, location, weeks=True, week_offset=1)

        cholera_deaths = latest_query(db, cholera_deaths_variable, cholera_var, start_date, end_date_limit, location, weeks=True, week_offset=1)
        cholera_cases_o5 = {"total": cholera_cases["total"] - cholera_cases_u5["total"]}
        cholera_cases_o5["weeks"] = {week: cholera_cases["weeks"][week] - cholera_cases_u5["weeks"].get(week, 0) for week in cholera_cases["weeks"].keys()}
        ret['summary'].update({
            'cholera_cases': cholera_cases
            })
        ret['summary'].update({
            'cholera_cases_u5': cholera_cases_u5
            })
        ret['summary'].update({
            'cholera_cases_o5': cholera_cases_o5
            })
        
        ret['summary'].update({
            'cholera_deaths': cholera_deaths
            })


        protocols = ["ctc_case_management", "ctc_ipc", "ctc_wash", "ctc_lab_protocol"]
        total = latest_query(db, cholera_var, cholera_var,
                             start_date, end_date_limit, location,
                             weeks=True)["weeks"].get(epi_week -1, 0)
        ret["summary"]["surveyed"] = total

        if total == 0:
            total = 1
        for p in protocols:
            r = latest_query(db, p, cholera_var, start_date, end_date_limit, location, weeks=True)
            value = r["weeks"].get(epi_week - 1, 0) / total
            ret["summary"][p] = value * 100


        
        # FIGURE 2: MAP of cholera cases
        cholera_cases_map = {}
        cholera_cases_ret = latest_query(
            db,
            "ctc_cases_per_bed",
            cholera_var,
            start_date,
            end_date_limit,
            location,
            weeks=True
        )["district"]
        for district in cholera_cases_ret.keys():
            cholera_cases_map[locs[district].name] = {
                "value": cholera_cases_ret[district]["total"]
            }
        # fill the rest of the districts with zeroes
        for district in districts:
            if not locs[district].name in cholera_cases_map:
                cholera_cases_map.update(
                    {
                        locs[district].name: {
                            "value": 0
                        }
                    }
                )
        ret["data"].update({"cholera_map": cholera_cases_map})

        



        # Displaying indicators like the percentage of CTC with case management protocols etc.

        # A list of clinics with no report in the last week ( A form of completeness).

        # List of clinics that do not have case management or wash etc.

        # We also build up an overview dictionary
        var = Variables()
        num_codes = var.get("ctc_structure").keys()
        yes_codes = var.get("ctc_overview_yes_no")

        overview_data = {}


        overview_data["cases_total"] = cholera_cases.get("total", 0)
        overview_data["cases_u5_total"] = cholera_cases_u5.get("total", 0)
        overview_data["deaths_total"] = cholera_deaths.get("total", 0)

        weekly_cases = np.array([cholera_cases["clinic"][c]["total"] for c in sorted(cholera_cases["clinic"].keys())])
        weekly_deaths = np.array([cholera_deaths["clinic"][c]["total"] for c in sorted(cholera_cases["clinic"].keys())])


        weekly_cases[weekly_cases == 0] = 1
        clinic_cfr = weekly_deaths / weekly_cases * 100
        tot_cases = overview_data["cases_total"]
        if tot_cases == 0:
            tot_cases = 1
        average_cfr = np.mean((overview_data["deaths_total"] / tot_cases)* 100)

        if len(clinic_cfr) == 0:
            max_cfr = 0
            min_cfr = 0
        else:
            max_cfr = np.max(clinic_cfr)
            min_cfr = np.min(clinic_cfr)
        overview_data["cfr"] = (average_cfr, min_cfr, max_cfr )
        ctc_lat_variables = var.get("ctc_lat_type")
        ret["variables"] = ctc_lat_variables
        ctc_rec_variables = var.get("ctc_recommendations")

        clinic_data_list = []

        location_condtion = [
                or_(loc.contains([int(location)]) for loc in (
                    Data.country, Data.zone, Data.region, Data.district, Data.clinic))]
        conditions = location_condtion  + [Data.variables.has_key(cholera_var)]
        query = db.session.query(Data.clinic.op("&")(fix_children)[1].label("clinic"),
                                 Data.date,
                                 Data.region.op("&")(fix_children)[1].label("region"),
                                 Data.district.op("&")(fix_children)[1].label("district"),
                                 Data.variables,
                                 Data.categories).distinct(
                                    Data.clinic).filter(*conditions).order_by(
                                             Data.clinic).order_by(Data.date.desc())

        latest_ctc = {}
        surveyed_clinics_map = []
        non_surveyed_clinics_map = []
        for r in query:
            latest_ctc[r.clinic] = r
        overview_data.setdefault("baseline", {"Y": 0, "N": 0})
        overview_data.setdefault("surveyed_last_week", {"Y": 0, "N": 0})

        ret["contents"] = []
        ret["contents_offset"] = 3 #Here we HACK how many pages before first clinic page
        pageNumber = 0

        for current_zone in zones:
            for ctc in ctcs:
                clinic_data = {"name": ctc.name}
                district = trim_locations(locs[ctc.id].parent_location, fix_children)
                region = trim_locations(locs[district].parent_location, fix_children)
                zone = trim_locations(locs[region].parent_location, fix_children)
                if zone != current_zone:
                    continue
                clinic_data["region"] = locs[region].name
                clinic_data["district"] = locs[district].name
                point = to_shape(locs[ctc.id].point_location)
                clinic_data["gps"] = [point.y, point.x]


                overview_data["baseline"]["N"] += 1
                overview_data["surveyed_last_week"]["N"] += 1
                if ctc.id in latest_ctc:
                    overview_data["baseline"]["Y"] += 1
                    ctc_data = latest_ctc[ctc.id]
                    clinic_data["status"] = "Surveyed"
                    ret["contents"].append((locs[zone].name + ": " + ctc.name,pageNumber))
                    pageNumber = pageNumber + 1
                    surveyed_clinics_map.append(clinic_data["gps"]+[ctc.name])
                    clinic_data["latest_data"] = ctc_data.variables
                    clinic_data["latest_categories"] = ctc_data.categories
                    clinic_data["latest_date"] = ctc_data.date.isoformat().split("T")[0]

                    if ew.get(ctc_data.date.isoformat())["epi_week"] in [epi_week, epi_week - 1]:
                        overview_data["surveyed_last_week"]["Y"] += 1
                    # clinic_data["cases_history"] = cholera_cases["clinic"].get(ctc.id, {})

                    # cholera_cases_o5_ctc = {"total": cholera_cases["clinic"][ctc.id]["total"] - cholera_cases_u5["clinic"][ctc.id]["total"]}
                    # cholera_cases_o5_ctc["weeks"] = {week: cholera_cases["clinic"][ctc.id]["weeks"][week] - cholera_cases_u5["clinic"][ctc.id]["weeks"].get(week, 0) for week in cholera_cases["clinic"][ctc.id]["weeks"].keys()}

                #    clinic_data["deaths_history"] = cholera_deaths["clinic"][ctc.id]
                #   clinic_data["cases_u5_history"] = cholera_cases_u5["clinic"][ctc.id]
                #  clinic_data["cases_o5_history"] =cholera_cases_o5_ctc

                    # Deal with recomendations

                    recommendations = []
                    cases = ctc_data.variables.get("ctc_cases", 0)
                    if cases == 0:
                        cases = 1
                    cfr = ctc_data.variables.get("ctc_deaths", 0) / cases * 100
                    cfr_threshold = 2
                    if cfr > cfr_threshold:
                        recommendations.append("High CFR ratio of {} %".format(round(cfr, 1)))

                    if ctc_data.variables.get("ctc_beds", 0) < ctc_data.variables.get("ctc_patients", 0):
                        recommendations.append("Not sufficent beds")

                    for code in ctc_rec_variables.keys():
                        if ctc_data.variables.get(code, "missing") =="no":
                            recommendations.append("No {}".format(ctc_rec_variables[code]["name"]))

                    clinic_data["recommendations"] = recommendations



                    # Overview data

                    for num_code in num_codes:
                        overview_data.setdefault(num_code, 0)
                        overview_data[num_code] += ctc_data.variables.get(num_code, 0)
                    for yes_code in yes_codes:
                        overview_data.setdefault(yes_code, {"Y": 0, "N": 0})
                        overview_data[yes_code]["N"] += 1
                        if ctc_data.variables.get(yes_code, "missing") == "yes":
                            overview_data[yes_code]["Y"] += 1
                    overview_data.setdefault("ctc_beds_sufficient", {"Y": 0, "N": 0})
                    overview_data["ctc_beds_sufficient"]["N"] += 1
                    if "ctc_beds_sufficient" in ctc_data.variables:
                        overview_data["ctc_beds_sufficient"]["Y"] += 1
                else:
                    clinic_data["status"] = "Not Surveyed"
                    non_surveyed_clinics_map.append(clinic_data["gps"]+[ctc.name])
                # Initialize data structure for current clinic

                # Append clinic data to clinic data list
                clinic_data_list.append(clinic_data)
        num_clin = overview_data["baseline"]["Y"]
        if num_clin == 0:
            num_clin = 1
        overview_data["ctc_doctors_per_facility"] = overview_data.get("ctc_doctors", 0) / num_clin
        overview_data["ctc_nurses_per_facility"] = overview_data.get("ctc_nurses", 0) / num_clin
        ret["overview"] = overview_data
        ret.update({'clinic_data' : clinic_data_list})
        ret["data"].update({"surveyed_clinics_map":{
            "surveyed":surveyed_clinics_map,
            "non_surveyed":non_surveyed_clinics_map
        }})

        #In page numbering take into account amount of pages of table of content. Depends on styling etc, so it is a MASSIVE HACK indeed.
        noOfContentPages = overview_data["baseline"]["Y"] / 45 
        ret["contents_offset"] = ret["contents_offset"] + math.ceil( noOfContentPages )

        return ret


class SCReport(Resource):

    """
    SCReport

    This reports gives a summary of the Stabilisation Centre surveillance

    Args:\n
       location: Location to generate report for\n
       start_date: Start date of report\n
       end_date: End date of report\n
    Returns:\n
       report_data\n
    """
    decorators = [authenticate, report_allowed_location]

    def get(self, location, start_date=None, end_date=None):

        # Set default date values to last epi week.
        today = datetime.now()
        epi_week = EpiWeek().get()
        # Initialise some stuff.
        start_date, end_date = fix_dates(start_date, end_date)
        end_date_limit = end_date + timedelta(days=1)
        first_day_of_year = datetime(year=end_date.year,
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
        fix_children = locs[int(location)].children
        regions = [loc for loc in locs.keys()
                   if locs[loc].level == "region"]
        districts = [loc for loc in locs.keys()
                     if locs[loc].level == "district"]
        zones = [loc for loc in locs.keys()
                     if locs[loc].level == "zone"]
        ret["data"]["project_region"] = location_name.name
        ret["data"]["project_region_id"] = location

        children = get_children(location, locs, require_case_report=False)

        scs = db.session.query(Locations).filter(
            Locations.clinic_type == "SU").filter(
                Locations.id.in_(children)
            ).all()

        ret["data"]["clinic_num"] = len(scs)

        nutrition_cases_variable = 'sc_cases'
        nutrition_cases_u5_variable = 'sc_cases_u5'
        nutrition_deaths_variable = 'sc_deaths'


        nutrition_var = "sc_1"
        # Summary data
        ret['summary']={}

        # Aggregate numbers of nutrition cases and deaths as an epi curve and a map.

        nutrition_cases = latest_query(db, nutrition_cases_variable, nutrition_var, start_date, end_date_limit, location, weeks=True, week_offset=1)
        nutrition_cases_u5 = latest_query(db, nutrition_cases_u5_variable, nutrition_var, start_date, end_date_limit, location, weeks=True, week_offset=1)

        nutrition_deaths = latest_query(db, nutrition_deaths_variable, nutrition_var, start_date, end_date_limit, location, weeks=True, week_offset=1)
        nutrition_cases_o5 = {"total": nutrition_cases["total"] - nutrition_cases_u5["total"]}
        nutrition_cases_o5["weeks"] = {week: nutrition_cases["weeks"][week] - nutrition_cases_u5["weeks"].get(week, 0) for week in nutrition_cases["weeks"].keys()}
        ret['summary'].update({
            'nutrition_cases': nutrition_cases
            })
        ret['summary'].update({
            'nutrition_cases_u5': nutrition_cases_u5
            })
        ret['summary'].update({
            'nutrition_cases_o5': nutrition_cases_o5
            })
        
        ret['summary'].update({
            'nutrition_deaths': nutrition_deaths
            })


        total = latest_query(db, nutrition_var, nutrition_var,
                             start_date, end_date_limit, location,
                             weeks=True)["weeks"].get(epi_week -1, 0)
        ret["summary"]["surveyed"] = total
        
        # FIGURE 2: MAP of nutrition cases
        nutrition_cases_map = {}
        nutrition_cases_ret = latest_query(
            db,
            "sc_cases_per_bed",
            nutrition_var,
            start_date,
            end_date_limit,
            location,
            weeks=True
        )["district"]
        for district in nutrition_cases_ret.keys():
            nutrition_cases_map[locs[district].name] = {
                "value": nutrition_cases_ret[district]["total"]
            }
        # fill the rest of the districts with zeroes
        for district in districts:
            if not locs[district].name in nutrition_cases_map:
                nutrition_cases_map.update(
                    {
                        locs[district].name: {
                            "value": 0
                        }
                    }
                )
        ret["data"].update({"nutrition_map": nutrition_cases_map})

        



        # Displaying indicators like the percentage of SC with case management protocols etc.

        # A list of clinics with no report in the last week ( A form of completeness).

        # List of clinics that do not have case management or wash etc.

        # We also build up an overview dictionary
        var = Variables()
        num_codes = var.get("sc_overview_num").keys()
        yes_codes = var.get("sc_overview_yes_no")

        sc_type_codes = var.get("sc_facility_type")
        overview_data = {}


        overview_data["cases_total"] = nutrition_cases.get("total", 0)
        overview_data["cases_u5_total"] = nutrition_cases_u5.get("total", 0)
        overview_data["deaths_total"] = nutrition_deaths.get("total", 0)

        weekly_cases = np.array([nutrition_cases["clinic"][c]["total"] for c in sorted(nutrition_cases["clinic"].keys())])
        weekly_deaths = np.array([nutrition_deaths["clinic"][c]["total"] for c in sorted(nutrition_cases["clinic"].keys())])


        sc_rec_variables = var.get("sc_recommendations")

        clinic_data_list = []

        location_condtion = [
                or_(loc.contains([int(location)]) for loc in (
                    Data.country, Data.zone, Data.region, Data.district, Data.clinic))]
        conditions = location_condtion  + [Data.variables.has_key(nutrition_var)]
        query = db.session.query(Data.clinic.op("&")(fix_children)[1].label("clinic"),
                                 Data.date,
                                 Data.region.op("&")(fix_children)[1].label("region"),
                                 Data.district.op("&")(fix_children)[1].label("district"),
                                 Data.variables,
                                 Data.categories).distinct(
                                     Data.clinic).filter(*conditions).order_by(
                                             Data.clinic).order_by(Data.date.desc())

        
        latest_sc = {}
        surveyed_clinics_map = []
        non_surveyed_clinics_map = []
        for r in query:
            latest_sc[r.clinic] = r
        overview_data.setdefault("baseline", {"Y": 0, "N": 0})
        overview_data.setdefault("surveyed_last_week", {"Y": 0, "N": 0})

        ret["contents"] = []
        ret["contents_offset"] = 3 #Here we HACK how many pages before first clinic page
        pageNumber = 0

        for current_zone in zones:
            for sc in scs:
                clinic_data = {"name": sc.name}
                district = trim_locations(locs[sc.id].parent_location, fix_children)
                region = trim_locations(locs[district].parent_location, fix_children)
                zone = trim_locations(locs[region].parent_location, fix_children)
                if zone != current_zone:
                    continue
                clinic_data["region"] = locs[region].name
                clinic_data["district"] = locs[district].name
                if locs[sc.id].point_location is not None:
                    point = to_shape(locs[sc.id].point_location)
                    clinic_data["gps"] = [point.y, point.x]


                overview_data["baseline"]["N"] += 1
                overview_data["surveyed_last_week"]["N"] += 1
                if sc.id in latest_sc:
                    overview_data["baseline"]["Y"] += 1
                    sc_data = latest_sc[sc.id]
                    clinic_data["status"] = "Surveyed"
                    ret["contents"].append((locs[zone].name + ": " + sc.name,pageNumber))
                    pageNumber = pageNumber + 1
                    surveyed_clinics_map.append(clinic_data["gps"]+[sc.name])
                    clinic_data["latest_data"] = sc_data.variables
                    clinic_data["latest_categories"] = sc_data.categories
                    clinic_data["latest_date"] = sc_data.date.isoformat().split("T")[0]

                    if ew.get(sc_data.date.isoformat())["epi_week"] in [epi_week, epi_week - 1]:
                        overview_data["surveyed_last_week"]["Y"] += 1
                    # Deal with recomendations
                    recommendations = []
                    cases = sc_data.variables.get("sc_cases", 0)
                    if cases == 0:
                        cases = 1
                    if sc_data.variables.get("sc_beds", 0) < sc_data.variables.get("sc_patients", 0):
                        recommendations.append("Insufficient beds")

                    for code in ["sc_deaths", "sc_cured", "sc_default"]:
                        try:
                            if sc_data.variables.get(code, 0) / sc_data.variables.get("sc_discharge", 0) > 1:
                                recommendations.append("Data quality check needed")
                                break
                        except ZeroDivisionError:
                            recommendations.append("Data quality check needed")
                            break
                    for code in sc_rec_variables.keys():
                        if sc_data.variables.get(code, "missing") =="no":
                            recommendations.append("No {}".format(sc_rec_variables[code]["name"]))
                        if sc_data.variables.get(code, "missing") == 1:
                            recommendations.append("{}".format(sc_rec_variables[code]["name"]))
                    clinic_data["recommendations"] = recommendations

                    clinic_data["services"] = []

                    for code in sc_type_codes.keys():
                        if code in sc_data.variables:
                            clinic_data["services"].append(sc_type_codes[code]["name"])

                    # Overview data

                    for num_code in num_codes:
                        overview_data.setdefault(num_code, 0)
                        overview_data[num_code] += int(sc_data.variables.get(num_code, 0))
                    for yes_code in yes_codes:
                        overview_data.setdefault(yes_code, {"Y": 0, "N": 0})
                        overview_data[yes_code]["N"] += 1
                        if sc_data.variables.get(yes_code, "missing") == "yes":
                            overview_data[yes_code]["Y"] += 1
                    overview_data.setdefault("sc_beds_sufficient", {"Y": 0, "N": 0})
                    overview_data["sc_beds_sufficient"]["N"] += 1
                    if "sc_beds_sufficient" in sc_data.variables:
                        overview_data["sc_beds_sufficient"]["Y"] += 1
                else:
                    clinic_data["status"] = "Not Surveyed"
                    if "gps" in clinic_data:
                        non_surveyed_clinics_map.append(clinic_data["gps"]+[sc.name])
                # Initialize data structure for current clinic

                # Append clinic data to clinic data list
                clinic_data_list.append(clinic_data)
        num_clin = overview_data["baseline"]["Y"]
        if num_clin == 0:
            num_clin = 1
        overview_data["sc_doctors_per_facility"] = overview_data.get("sc_doctors", 0) / num_clin
        overview_data["sc_nurses_per_facility"] = overview_data.get("sc_nurses", 0) / num_clin
        ret["overview"] = overview_data
        ret.update({'clinic_data' : clinic_data_list})
        ret["data"].update({"surveyed_clinics_map":{
            "surveyed":surveyed_clinics_map,
            "non_surveyed":non_surveyed_clinics_map
        }})

        #In page numbering take into account amount of pages of table of content. Depends on styling etc, so it is a MASSIVE HACK indeed.
        noOfContentPages = overview_data["baseline"]["Y"] / 45 
        ret["contents_offset"] = ret["contents_offset"] + math.ceil( noOfContentPages )

        return ret

