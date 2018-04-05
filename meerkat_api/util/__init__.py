"""
meerkat_api util functions

"""
from datetime import datetime
from dateutil import parser
import meerkat_abacus.util as abacus_util
import numpy as np

import meerkat_abacus.util.epi_week


def series_to_json_dict(series):
    """
    Takes pandas series and turns into a dict with string keys

    Args: 
        series: pandas series
    
    Returns: 
       dict: dict
    """
    #np.asscalar is necessary to cast numpy types to python native
    if series is not None:
        return dict((str(key), float(np.asscalar(value))) for key, value in series.to_dict().items())
    else:
        return {}


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
        end_date = parser.parse(end_date).replace(hour=23,
                                                  minute=59,
                                                  second=59,
                                                  tzinfo=None)
    else:
        end_date = datetime.now()

    if start_date:
        start_date = parser.parse(start_date).replace(hour=0,
                                                      minute=0,
                                                      second=0,
                                                      tzinfo=None)
    else:
        start_date = end_date.replace(month=1, day=1,
                                      hour=0, second=0,
                                      minute=0,
                                      microsecond=0)
    if start_date < meerkat_abacus.util.epi_week.epi_year_start_date(date=start_date):
        start_date = meerkat_abacus.util.epi_week.epi_year_start_date(date=start_date)
    return start_date, end_date


def row_to_dict(row):
    """
    Translate sql alchemy row to dict

    Args:
    row: SQL alchemy class

    Returns:
      data_dict(dict): data as dictionary
    """
    if not row:
        return {}
    if hasattr(row, "__table__"):
        return dict((col, getattr(row, col))
                    for col in row.__table__.columns.keys())
    else:
        ret = {}
        for table in row:
            if table:
                ret[table.__tablename__] = dict(
                    (col, getattr(table, col)) for col
                    in table.__table__.columns.keys())
        return ret


def rows_to_dicts(rows, dict_id=None):
    """
    Translate sql alchemy rows to dicts

    Args:
       rows: List of SQL alchemy rows
       dict_id: If True we return a dict with the dict_id column as index
    Returns:
       data_dicts(dict): data as dictionary
    """
    if dict_id:
        if len(rows) >0 and isinstance(rows[0], tuple):
            raise TypeError("Can not use dict_id=True with tuple rows")
        data_dicts = {}
        for row in rows:
            data_dicts[getattr(row, dict_id)] = row_to_dict(row)
    else:
        data_dicts = []
        for row in rows:
            data_dicts.append(row_to_dict(row))
    return data_dicts


def find_level(location, sublevel, locations):
    """
    Returns the isntance of level that location is a child of

    Args:
        location: location
        sublevel: the sublevel we are interested in
        locations: all locations in dict

    Returns:
       location_id(int): id of the mathcing location
    """
    location = int(location)

    for loc in locations:
        if locations[loc].level == sublevel and abacus_util.is_child(loc, location, locations):
            return loc
        
    return None

def get_children(parent, locations, clinic_type=None, require_case_report=True, case_type=None):
    """
    Return all clinics that are children of parent

    Args:
        parent: parent_id
        locations: all locations in dict

    Returns:
       list of location ids
    """
    ret = []
    for location_id in locations.keys():
        if ( (not require_case_report or locations[location_id].case_report) and
            (not clinic_type or locations[location_id].clinic_type == clinic_type)):
            if( case_type is None or locations[location_id].case_type == case_type):
                if abacus_util.is_child(parent, location_id, locations):
                    ret.append(location_id)
    return ret
