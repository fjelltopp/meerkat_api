#!/usr/bin/env python3
"""
Utility functions for setting up the DB for Meerkat API tests

"""
from datetime import datetime, timedelta
from importlib import reload
import uuid
from freezegun import freeze_time
import random, csv, os, logging
import json

from meerkat_api.test.test_data import locations, cases
from meerkat_api import app
from meerkat_abacus import model
from meerkat_abacus.util import get_db_engine

engine, session = get_db_engine(app.config["SQLALCHEMY_DATABASE_URI"])


def insert_cases(session, dataset_name, date=None, delete=True):
    """ Add a variable with cases from the cases.py file in test_data

    Args:
       session: db session
       dataset_name: name of the dataset from cases.py we want
       delete: Boolean, True if clean db before insert case data.
    """
    if date:
        freezer = freeze_time(date)
        freezer.start()
        reload(cases)
    if delete:
        session.query(model.Data).delete()
        session.query(model.DisregardedData).delete()
    reload(cases)
    session.bulk_save_objects(getattr(cases, dataset_name))
    session.commit()
    if date:
        freezer.stop()


def insert_links(session, variable):
    """ Add a variable with links from the links.py file in test_data

    Args:
       session: db session
       variable: name of the varible from links.py we want
    """
    session.query(model.Links).delete()
    session.bulk_save_objects(getattr(links, variable))
    session.commit()


def insert_alerts(session, variable):
    """ Add a variable with alerts from the alerts.py file in test_data

    Args:
       session: db session
       variable: name of the varible from alerts.py we want
    """
    session.query(model.Alerts).delete()
    session.bulk_save_objects(getattr(alerts, variable))
    session.commit()


def insert_codes(session):
    """ Add the codes from the codes.py file in test_data

    Args:
       session: db session
    """
    insert_codes_from_file(session, "demo_codes.csv")


def insert_calculation_parameters(session):
    """ Add the codes from the calculation_parameters.json file

    Args:
       session: db session
    """
    session.query(model.CalculationParameters).delete()
    session.commit()

    parameter_files = ["medicine_kits.json", "vaccination_vials.json"]

    for file in parameter_files:
        file_name = os.path.splitext(file)[0]
        file_extension = os.path.splitext(file)[-1]
        if file_extension == '.json':
            with open(os.path.dirname(
                    os.path.realpath(__file__)) + "/test_data/" + "demo_calculation_parameters/" + file) as json_data:
                parameter_data = json.load(json_data)
                session.add(
                    model.CalculationParameters(
                        name=file_name,
                        type=file_extension,
                        parameters=parameter_data
                    ))
        elif file_extension == '.csv':
            # TODO: CSV implementation
            pass

    session.commit()


def insert_codes_from_file(session, filename):
    """
    Import variables from codes csv-file.

    Args:
       session: db-session
    """

    session.query(model.AggregationVariables).delete()
    session.commit()

    for row in read_csv(filename):
        if "" in row.keys():
            row.pop("")
        row = field_to_list(row, "category")
        keys = model.AggregationVariables.__table__.columns._data.keys()
        row = {key: row[key] for key in keys if key in row}
        session.add(model.AggregationVariables(**row))

    session.commit()


def insert_locations(session, date=None):
    """ Add the locations from the locations.py file in test_data

    Args:
       session: db session
    """

    if date:
        freezer = freeze_time(date)
        freezer.start()
        reload(locations)

    reload(locations)
    session.query(model.Locations).delete()
    session.bulk_save_objects(locations.locations)
    session.commit()

    if date:
        freezer.stop()


def insert_specific_locations(session, variable, date=None):
    """ Add specific variable locations from the locations.py file in test_data

    Args:
       session: db session
       variable: name of the varible from locations.py we want
    """
    if date:
        freezer = freeze_time(date)
        freezer.start()
        reload(locations)
    session.query(model.Locations).delete()
    session.bulk_save_objects(getattr(locations, variable))
    session.commit()

    if date:
        freezer.stop()


def create_category(session, variables, category, names=None):
    """
    Make sure the aggregation_variables table has only the variables
    specified with the given cateogry

    Args:
       session: the db session
       variables: list of variable ids we want to add
       category: a single or list of categories to add to the variables
       names: If give we use those names for the variables, otherwise we just use the ids
    """

    if not isinstance(category, list):
        category = [category]
    if not names:
        names = variables
    if len(variables) != len(names):
        raise IndexError("Varibles and names need to have the same length")
    session.query(model.AggregationVariables).delete()
    session.commit()
    for i, v in enumerate(variables):
        session.add(model.AggregationVariables(
            id=v,
            name=names[i],
            category=category
        ))
    session.commit()


def create_data(session, variables,
                locations=(1, 2, 3, 4), dates="year",
                clinic_types="hospital", geolocations="POINT(0 0)"):
    """
    Makes sure the data table has records with the variables in the variables list

    Args:
       session: db session
       variables: list of variable dicts to give the records
       locations: either one location tuple(country, region, dsitrict, clinic) to give all the records or a list of Locations
       dates: either year(to create dates for this year) or a list of dates to create
       clinic_types: either one clinic_type or list of clinics_types
    """
    session.query(model.Data).delete()
    session.commit()
    N = len(variables)
    if not isinstance(locations, list):
        locations = [locations for i in range(N)]
    if not isinstance(clinic_types, list):
        clinic_types = [clinic_types for i in range(N)]
    if not isinstance(geolocations, list):
        geolocations = [geolocations for i in range(N)]

    if dates == "year":
        year = datetime(datetime.now().year, 1, 1)
        days = (datetime.now() - year).days
        dates = []
        for i in range(N):
            date = year + timedelta(days=random.randint(0, days))
            dates.append(date)

    if len(locations) != N or len(dates) != N or len(clinic_types) != N or len(geolocations) != N:
        raise IndexError("Variables, locations, clinic_types, geolocations and dates need to have the same length")

    for i in range(N):
        session.add(model.Data(
            uuid=uuid.uuid4(),
            country=locations[i][0],
            region=locations[i][1],
            district=locations[i][2],
            clinic=locations[i][3],
            clinic_type=clinic_types[i],
            date=dates[i],
            variables=variables[i],
            geolocation=geolocations[i]
        ))
    session.commit()


def read_csv(filename):
    """
    Reads csvfile from the test data and returns list of rows

    Args:
        file_path: path of file to read (relative to the test_data folder)

    Returns:
        rows(list): list of rows
    """
    file_path = os.path.dirname(os.path.realpath(__file__)) + "/test_data/" + filename
    with open(file_path, "r", encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append(row)
    return rows


def field_to_list(row, key):
    """
    Transforms key in row to a list. We split on semicolons if they exist in the string,
    otherwise we use commas.

    Args:
        row: row of data
        key: key for the field we want
    Reutrns:
        row: modified row
    """
    if ";" in row[key]:
        row[key] = [c.strip() for c in row[key].split(";")]
    elif "," in row[key]:
        row[key] = [c.strip() for c in row[key].split(",")]
    else:
        row[key] = [row[key]]
    return row


def insert_statuses(session):
    """
    Insert DownloadDataFiles for /export/get_status tests

    Args:
       session: db session
    """
    session.query(model.DownloadDataFiles).delete()
    session.add(
        model.DownloadDataFiles(
            uuid='1',
            generation_time=datetime.now(),
            type='Foobar',
            success=1,
            status=1
        )
    )
    session.commit()
