"""
Functions to export data
"""
from meerkat_abacus.util import epi_week, get_locations
from meerkat_abacus.util import all_location_data, get_db_engine, get_links
from meerkat_abacus.model import form_tables, Data
from meerkat_abacus.model import DownloadDataFiles, AggregationVariables
from meerkat_abacus.config import country_config, config_directory
from sqlalchemy.orm import aliased
from sqlalchemy import text, or_
from dateutil.parser import parse
from datetime import datetime
from io import StringIO
from celery import task
import csv
import json


@task
def export_data(uuid, use_loc_ids=False):
    """
    Exports the data table from db

    Inserts finished file in to databse

    Args:
       uuid: uuid for download
       use_loc_ids: If we use names are location ids
    """
    db, session = get_db_engine()
    status = DownloadDataFiles(
        uuid=uuid,
        csvcontent="",
        json_data="",
        generation_time=datetime.now(),
        type="data",
        success=0,
        status=0
    )
    session.add(status)
    session.commit()

    results = session.query(Data)
    variables = set()
    locs = get_locations(session)
    for row in results:
        variables = variables.union(set(row.variables.keys()))
    fieldnames = [
        "id", "country", "region", "district", "clinic",
        "clinic_type", "geolocation", "date", "uuid"
    ] + list(variables)
    dict_rows = []
    for row in results:
        dict_row = dict(
            (col, getattr(row, col)) for col in row.__table__.columns.keys()
        )
        dict_row["date"] = dict_row["date"].isoformat()
        if not use_loc_ids:
            for l in ["country", "region", "district", "clinic"]:
                if dict_row[l]:
                    dict_row[l] = locs[dict_row[l]].name
        dict_row.update(dict_row.pop("variables"))
        dict_rows.append(dict_row)
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(dict_rows)
    status.csvcontent = output.getvalue()

    status.json_data = json.dumps(dict_rows)
    status.status = 1
    status.success = 1
    session.commit()
    return True


@task
def export_category(uuid, form_name, category, download_name, variables):
    """
    We take a variable dictionary of form field name: display_name.
    There are some special commands that can be given in the form field name:

    * icd_name$category will translate an icd code in icd_code to names given
       by the variables in category
    * clinic,region and district will give this location information

    * the $translate keyword can be used to translate row values to other ones.
       I.e to change gender from male, female to M, F

    * field$month, field$year, field$epi_week: will extract the month, year
       or epi_week from the field

    * alert_links$alert_investigation$field: will get the field in the c
       orrepsonding alert_investigation

    Inserts the resulting csv file in the database

    Args:\n
       category: category to match\n
       variables: variable dictionary\n

    """
    db, session = get_db_engine()

    status = DownloadDataFiles(
        uuid=uuid,
        csvcontent="",
        json_data="",
        generation_time=datetime.now(),
        type=download_name,
        success=0,
        status=0
    )
    session.add(status)
    session.commit()
    res = session.query(AggregationVariables).filter(
        AggregationVariables.category.has_key(category)
    )

    data_keys = []
    cat_variables = {}
    for r in res:
        data_keys.append(r.id)
        cat_variables[r.id] = r
    if len(data_keys) == 0:
        status.status = 1
        session.commit()
    return_keys = []
    translation_dict = {}
    icd_code_to_name = {}
    link_ids = []
    min_translation = {}

    # Set up icd_code_to_name if needed and determine if
    # alert_links are included
    for v in variables:
        return_keys.append(v[1])

        if "icd_name$" in v[0]:
            category = v[0].split("$")[1]
            cat_variables = {}
            res = session.query(AggregationVariables).filter(
                AggregationVariables.category.has_key(category)
            )
            for r in res:
                cat_variables[r.id] = r
            icd_code_to_name[v[0]] = {}
            for i in cat_variables.keys():
                condition = cat_variables[i].condition
                if ";" in condition:
                    codes = condition.split(";")[0]
                if "," in condition:
                    # If a variable have many icd codes
                    # we take all of them into account
                    codes = condition.split(",")
                else:
                    codes = [condition]
                for c in codes:
                    icd_code_to_name[v[0]][c.strip()] = cat_variables[i].name
        if "$translate" in v[0]:
            split = v[0].split("$")
            field = "$".join(split[:-1])
            trans = split[-1]
            tr_dict = json.loads(trans.split(";")[1].replace("'", '"'))
            min_translation[v[1]] = tr_dict
            v[0] = field
            print(min_translation)
        if "gen_link$" in v[0]:
            link_ids.append(v[0].split("$")[1])
        translation_dict[v[1]] = v[0]

    link_ids = set(link_ids)
    links_by_type, links_by_name = get_links(config_directory +
                                             country_config["links_file"])
    # DB query, with yield_per(200) for memory reasons

    columns = [Data, form_tables[form_name]]

    link_id_index = {}
    joins = []
    for i, l in enumerate(link_ids):
        form = aliased(form_tables[links_by_name[l]["to_form"]])
        joins.append((form, Data.links[(l, -1)].astext == form.uuid))
        link_id_index[l] = i + 2
        columns.append(form.data)

    results = session.query(*columns).join(
        form_tables[form_name], Data.uuid == form_tables[form_name].uuid)
    for join in joins:
        results = results.outerjoin(join[0], join[1])
    results = results.filter(
        or_(Data.variables.has_key(key)
            for key in data_keys)).yield_per(200)
    locs = get_locations(session)
    list_rows = [return_keys]

    # Prepare each row
    for r in results:
        list_row = ['']*len(return_keys)
        for k in return_keys:
            form_var = translation_dict[k]
            index = return_keys.index(k)

            if "icd_name$" in form_var:
                if r[1].data["icd_code"] in icd_code_to_name[form_var]:
                    list_row[index] = icd_code_to_name[form_var][r[1].data[
                        "icd_code"]]
                else:
                    list_row[index] = None

            elif "$date" in form_var:
                if form_var in r[1].data:
                    list_row[index] = parse(r[1].data[form_var]).strftime(
                        "%d/%m/%Y"
                    )
                else:
                    list_row[index] = None
            elif form_var == "clinic":
                list_row[index] = locs[r[0].clinic].name
            elif form_var == "region":
                list_row[index] = locs[r[0].region].name
            elif form_var == "district":
                if r[0].district:
                    list_row[index] = locs[r[0].district].name
                else:
                    list_row[index] = None
            elif "$year" in form_var:
                field = form_var.split("$")[0]
                if field in r[1].data and r[1].data[field]:
                    list_row[index] = parse(r[1].data[field]).year
                else:
                    list_row[index] = None
            elif "$month" in form_var:
                field = form_var.split("$")[0]
                if field in r[1].data and r[1].data[field]:
                    list_row[index] = parse(r[1].data[field]).month
                else:
                    list_row[index] = None
            elif "$day" in form_var:
                field = form_var.split("$")[0]
                if field in r[1].data and r[1].data[field]:
                    list_row[index] = parse(r[1].data[field]).day
                else:
                    list_row[index] = None
            elif "$epi_week" in form_var:
                field = form_var.split("$")[0]
                if field in r[1].data and r[1].data[field]:
                    list_row[index] = epi_week(parse(r[1].data[field]))[1]
                else:
                    list_row[index] = None

            # A general framework for referencing links in the
            # download data.
            # link$<link id>$<linked form field>
            elif "gen_link$" in form_var:
                link = form_var.split("$")[1]
                link_index = link_id_index[link]
                if r[link_index]:
                    list_row[index] = r[link_index][form_var.split("$")[-1]]
                else:
                    list_row[index] = None

            elif "code" == form_var.split("$")[0]:
                # code$cod_1,cod_2,Text_1,Text_2$default_value
                split = form_var.split("$")
                codes = split[1].split(",")
                text = split[2].split(",")
                if len(split) > 3:
                    default_value = split[3]
                else:
                    default_value = None
                final_text = []
                for i in range(len(codes)):
                    if codes[i] in r[0].variables:
                        final_text.append(text[i])
                if len(final_text) > 0:
                    list_row[index] = " ".join(final_text)
                else:
                    list_row[index] = default_value

            elif "code_value" == form_var.split("$")[0]:
                code = form_var.split("$")[1]
                if code in r[0].variables:
                    list_row[index] = r[0].variables[code]
                else:
                    list_row[index] = None
            elif "value" == form_var.split(":")[0]:
                list_row[index] = form_var.split(":")[1]
            else:
                if form_var in r[1].data:
                    list_row[index] = r[1].data[form_var]
                else:
                    list_row[index] = None

            if min_translation and k in min_translation:
                tr_dict = min_translation[k]
                if list_row[index] in tr_dict.keys():
                    list_row[index] = tr_dict[list_row[index]]

        list_rows.append(list_row)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerows(list_rows)
    status.csvcontent = output.getvalue()
    status.json_data = json.dumps(list_rows)
    status.status = 1
    status.success = 1
    session.commit()
    return True


@task
def export_form(uuid, form, fields=None):
    """
    Export a form. If fields is in the request variable we only include
    those fields.

    Starts background export

    Args:\n
       uuid: uuid of download\n
       form: the form to export\n
       fields: Fileds from form to export\n

    """
    # A method that glues json arrays together into a single string.
    def build_json(new_string, json_string):
        if not json_string:
            return new_string
        else:
            return json_string[:-1] + ', ' + new_string[1:]

    db, session = get_db_engine()
    (locations, locs_by_deviceid, regions,
     districts, devices) = all_location_data(session)
    json_string = ""

    if fields:
        keys = fields
    else:
        keys = ["clinic", "region", "district"]
        if form not in form_tables:
            return {"filename": form, "file": StringIO()}
        sql = text("SELECT DISTINCT(jsonb_object_keys(data)) from {}".
                   format(form_tables[form].__tablename__))
        result = db.execute(sql)
        for r in result:
            keys.append(r[0])

    file_object = StringIO()

    csv_writer = csv.DictWriter(file_object, keys, extrasaction='ignore')
    csv_writer.writeheader()

    i = 0
    if locs_by_deviceid is None:
        session.add(
            DownloadDataFiles(
                uuid=uuid,
                csvcontent="",
                json_data="",
                generation_time=datetime.now(),
                type=form,
                success=0,
                status=1
                )
            )
        session.commit()
        return False

    if form in form_tables.keys():
        results = session.query(form_tables[form].data).yield_per(1000)
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
                print(dict_rows)
                csv_writer.writerows(dict_rows)
                json_string = build_json(json.dumps(dict_rows), json_string)
                dict_rows = []
            i += 1

        # Write any remaining unwritten data down.
        csv_writer.writerows(dict_rows)
        json_string = build_json(json.dumps(dict_rows), json_string)

        session.add(
            DownloadDataFiles(
                uuid=uuid,
                csvcontent=file_object.getvalue(),
                json_data=json_string,
                generation_time=datetime.now(),
                type=form,
                success=1,
                status=1
            )
        )
        session.commit()

        return True
