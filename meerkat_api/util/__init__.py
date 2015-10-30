"""
meerkat_api util functions

"""

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
