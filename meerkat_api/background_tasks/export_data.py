"""

Functions to export data



"""
from sqlalchemy import text
import io
import csv
from celery imoport task

from meerkat_abacus.util import all_location_data
from meerkat_abacus.model import form_tables


@task
def export_form(db, form, fields=None):
    (locations, locs_by_deviceid, regions,
     districts, devices) = all_location_data(db.session)
    if fields:
        keys = fields
    else:
        keys = ["clinic", "region", "district"]
        if form not in form_tables:
            return {"filename": form, "file": io.StringIO()}
        sql = text("SELECT DISTINCT(jsonb_object_keys(data)) from {}".
                   format(form_tables[form].__tablename__))
        result = db.engine.execute(sql)
        for r in result:
            keys.append(r[0])
            
    f = io.StringIO()
    csv_writer = csv.DictWriter(f, keys, extrasaction='ignore')
    csv_writer.writeheader()
    i = 0
    if locs_by_deviceid is None:
        return {"filename": form, "file": io.StringIO()}
        
    if form in form_tables.keys():
        results = db.session.query(form_tables[form].data).yield_per(1000)
        dict_rows = []
        for row in results:
            dict_row = row.data
            if not dict_row:
                continue
            clinic_id = locs_by_deviceid.get(dict_row["deviceid"], None)
            if clinic_id:
                dict_row["clinic"] = locations[clinic_id].name
                # Sort out district and region
                if locations[clinic_id].parent_location in districts:
                    dict_row["district"] = locations[locations[clinic_id]
                                                     .parent_location].name
                    dict_row["region"] = locations[locations[locations[
                        clinic_id].parent_location].parent_location].name
                elif locations[clinic_id].parent_location in regions:
                    dict_row["district"] = ""
                    dict_row["region"] = locations[locations[clinic_id]
                                                   .parent_location].name
            else:
                dict_row["clinic"] = ""
                dict_row["district"] = ""
                dict_row["region"] = ""
            for key in list(row.data.keys()):
                if key in keys and key not in dict_row:
                    dict_row[key] = row.data[key]
            dict_rows.append(dict_row)
            if i % 1000 == 0:
                csv_writer.writerows(dict_rows)
                dict_rows = []
            i += 1
        csv_writer.writerows(dict_rows)
        return {"filename": form, "file": f}

    
