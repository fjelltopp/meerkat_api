"""
meerkat_api util functions

"""
from datetime import datetime


def row_to_dict(row):
    """
    translate sql alchemy row to dict

    Args:
    row: SQL alchemy class

    Returns:
    data_dict: data as dictionary
    """
    return dict((col, getattr(row, col))
                for col in row.__table__.columns.keys())


def rows_to_dicts(rows):
    """
    translate sql alchemy rows to dicts

    Args:
    rows: SQL alchemy class

    Returns:
    data_dicts: data as dictionary
    """
    data_dicts = []
    for row in rows:
        data_dicts.append(row_to_dict(row))
    return data_dicts


def date_to_epi_week(day=datetime.today()):
    """
    Converts a datetime object to an epi_week
 
    Args:
       day: datetime
    Returns:
        epi_week(int): epi week

    """
    return int((day - datetime(day.year, 1, 1)).days // 7 + 1)


def is_child(parent, child, locations):
    """
    Determines if child is child of parent

    Args:
        parent: parent_id
        child: child_id
        locations: all locations in dict

    Reutrns
       is_child(Boolean)
    """
    parent = int(parent)
    child = int(child)
    if child == parent or parent == 1:
        return True
    loc_id = child
    while loc_id != 1:
        loc_id = locations[loc_id].parent_location
        if loc_id == parent:
            return True
    return False
