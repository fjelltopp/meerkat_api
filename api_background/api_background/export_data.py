"""
Functions to export data
"""
from meerkat_abacus.util import epi_week, get_locations, is_child
from meerkat_abacus.util import all_location_data, get_db_engine, get_links
from meerkat_abacus.model import form_tables, Data, Links
from meerkat_abacus.model import DownloadDataFiles, AggregationVariables
from meerkat_abacus.config import country_config, config_directory

import gettext


translation_dir = country_config.get("translation_dir", None)

if translation_dir:
    try:
        t = gettext.translation('messages',  translation_dir, languages=["en", "fr"])
    except FileNotFoundError:
        print("Translations not found")


import resource
import shelve
from sqlalchemy.orm import aliased
from sqlalchemy import text, or_, func, Float
from dateutil.parser import parse
from datetime import datetime
from io import StringIO, BytesIO
from celery import task
import pandas as pd
import csv
import json
import logging
import xlsxwriter
import os
base_folder = os.path.dirname(os.path.realpath(__file__))

def trim_locations(locs, children):
    inter = set(locs).intersection(set(children))
    if inter:
        return next(iter(inter))
    return None

@task
def export_data(uuid, allowed_location, use_loc_ids=False):
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
        generation_time=datetime.now(),
        type="data",
        success=0,
        status=0
    )
    session.add(status)
    session.commit()

    results = session.query(
        func.distinct(
            func.jsonb_object_keys(Data.variables)))
    variables = []
    for row in results:
        variables.append(row[0])
    locs = get_locations(session)
    fieldnames = ["id", "zone", "country", "region",
                  "district", "clinic", "clinic_type",
                  "geolocation", "date", "uuid"] + list(variables)
    dict_rows = []
    children = locs[allowed_location].children + [allowed_location]

    filename = base_folder + "/exported_data/" + uuid + "/data"
    os.mkdir(base_folder + "/exported_data/" + uuid)
    output = open(filename + ".csv", "w")
    writer = csv.DictWriter(output, fieldnames, extrasaction="ignore")
    writer.writeheader()
    results = session.query(Data).yield_per(500)
    i = 0

    for row in results:
        dict_row = dict(
            (col, getattr(row, col)) for col in row.__table__.columns.keys()
        )
        if not is_child(allowed_location,
                        trim_locations(dict_row["clinic"], children),
                        locs):
            continue

        for l in ["country", "zone", "region", "district", "clinic"]:
            if dict_row[l]:
                single_loc = trim_locations(dict_row[l], children)
                dict_row[l + "_id"] = single_loc
                dict_row[l] = locs[single_loc].name
        dict_row.update(dict_row.pop("variables"))
        dict_rows.append(dict_row)
        if i % 1000 == 0:
            writer.writerows(dict_rows)
            dict_rows = []
        i += 1
    writer.writerows(dict_rows)
    status.status = 1
    status.success = 1
    session.commit()
    return True


@task
def export_category(uuid, form_name, category, download_name,
                    variables,  data_type, allowed_location,
                    start_date=None, end_date=None, language="en"):
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
    db2, session2 = get_db_engine()
    status = DownloadDataFiles(
        uuid=uuid,
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
    print(language)
    if language != "en":
        os.environ["LANGUAGE"] = language

    locs = get_locations(session)
    print(uuid)
    children = locs[allowed_location].children
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

    def add_translations_from_file(details):
        # Load the csv file and reader
        file_path = '{}api/{}'.format(
            os.environ['COUNTRY_CONFIG_DIR'],
            details['dict_file']
        )
        csv_file = open(file_path, 'rt')
        reader = csv.reader(csv_file)
        # Establish which column in each row we're translating from and to.
        headers = next(reader)
        from_index = headers.index(details['from'])
        to_index = headers.index(details['to'])
        # Add translations to the translation dictionary.
        trans_dict = {}
        for row in reader:
            trans_dict[row[from_index]] = row[to_index]
#        logging.warning(trans_dict)
        return trans_dict

    # DB conditions
    conditions = [
        or_(Data.variables.has_key(key) for key in data_keys)
    ]
    if data_type:
        conditions.append(Data.type == data_type)
    if start_date:
        conditions.append(Data.date >= parse(start_date))
    if end_date:
        conditions.append(Data.date <= parse(end_date))

    # Set up icd_code_to_name if needed and determine if
    # alert_links are included
    query_links = False

    to_columns_translations = {}
    for v in variables:

        if "every$" in v[0]:
            # Want to include all the fields in the dictionary
            # in v[1] for all the links in the name

            # First determine the maximum number of links
            link_name = v[0].split("$")[1]
            length_q = session.query(
                func.max(func.jsonb_array_length(Data.links[link_name]))).filter(
                    *conditions)
            length = length_q.first()[0]
            for i in range(length):
                for variable in v[1]:
                    name = link_name + "_" + str(i) + " " + variable[1]
                    return_keys.append(name)
                    translation_dict[name] = "many_links&" + link_name + "&" + str(i) + "&" +variable[0]
            query_links = link_name
        else:
            return_keys.append(v[1])
            translation_dict[v[1]] = v[0]
        if "icd_name$" in v[0]:
            category = v[0].split("$")[-1]
            cat_variables = {}
            res = session.query(AggregationVariables).filter(
                AggregationVariables.category.has_key(category)
            )
            for r in res:
                cat_variables.setdefault(r.id, [])
                cat_variables[r.id].append(r)
            icd_code_to_name[v[0]] = {}
            for i in cat_variables.keys():
                for var in cat_variables[i]:
                    condition = var.condition
                    if ";" in condition:
                        condition = condition.split(";")[0]
                    if "," in condition:
                        # If a variable have many icd codes
                        # we take all of them into account
                        codes = condition.split(",")
                    else:
                        codes = [condition]
                    for c in codes:
                        if c:
                            icd_code_to_name[v[0]][c.strip()] = var.name
        if "$translate" in v[0]:
            split = v[0].split("$")
            field = "$".join(split[:-1])
            trans = split[-1]
            tr_dict = json.loads(trans.split(";")[1].replace("'", '"'))
            # If the json specifies file details, load translation from file.
            if tr_dict.get('dict_file', False):
                min_translation[v[1]] = add_translations_from_file(tr_dict)
            else:
                min_translation[v[1]] = tr_dict
            v[0] = field
            translation_dict[v[1]] = v[0]
        if "$to_columns" in v[0]:
            # Create columns of every possible value
            split = v[0].split("$")
            field = "$".join(split[:-1])
            trans = split[-1]
            tr_dict = {}
            if ";" in trans:
                tr_dict = json.loads(trans.split(";")[1].replace("'", '"'))

            # If the json specifies file details, load translation from file.

            # Get all possible options from the DB

            results = session2.query(
                func.distinct(
                    func.regexp_split_to_table(
                        form_tables[form_name].data[field].astext, ' '))).join(
                            Data,
                            Data.uuid == form_tables[form_name].uuid).filter(
                                *conditions).all()
            if tr_dict.get('dict_file', False):
                translations = add_translations_from_file(tr_dict)
            else:
                translations = {}
            return_keys.pop()
            for r in results:
                if r[0]:
                    name = v[1] + " " + translations.get(r[0], r[0])
                    if name not in return_keys:
                        return_keys.append(name)
                        if name in translation_dict:
                            translation_dict[name] = translation_dict[name] + "," + r[0]
                        else:
                            translation_dict[name] = field + "$to_columns$" + r[0]

        if "gen_link$" in v[0]:
            link_ids.append(v[0].split("$")[1])
    if "uuid" not in return_keys:
        return_keys.append("uuid")
        translation_dict["uuid"] = "meta/instanceID"
    link_ids = set(link_ids)
    links_by_type, links_by_name = get_links(config_directory +
                                             country_config["links_file"])
    # DB query, with yield_per(200) for memory reasons

    columns = [Data, form_tables[form_name]]

    link_id_index = {}
    joins = []

    if query_links:
        link_data = shelve.open(base_folder + "/exported_data/" + uuid)
        link_data_query = session.query(Links).filter(Links.type == link_name).yield_per(300)
        for row in link_data_query:
            link_data[row.uuid_to] = row.data_to

    for i, l in enumerate(link_ids):
        form = aliased(form_tables[links_by_name[l]["to_form"]])
        joins.append((form, Data.links[(l, -1)].astext == form.uuid))
        link_id_index[l] = i + 2
        columns.append(form.data)

    number_query = session2.query(func.count(Data.id)).join(
        form_tables[form_name], Data.uuid == form_tables[form_name].uuid)

    results = session2.query(*columns).join(
        form_tables[form_name], Data.uuid == form_tables[form_name].uuid)
    for join in joins:
        results = results.outerjoin(join[0], join[1])


    total_number = number_query.filter(*conditions).first()[0]
    results = results.filter(*conditions).yield_per(200)


    locs = get_locations(session)
    list_rows = []

    filename = base_folder + "/exported_data/" + uuid + "/" + download_name
    os.mkdir(base_folder + "/exported_data/" + uuid)
    csv_content = open(filename + ".csv", "w")
    csv_writer = csv.writer(csv_content)
    csv_writer.writerows([return_keys])

    # XlsxWriter with "constant_memory" set to true, flushes mem after each row
    xls_content = open(filename + ".xlsx", "wb")
    xls_book = xlsxwriter.Workbook(xls_content, {'constant_memory': True})
    xls_sheet = xls_book.add_worksheet()
    # xls_sheet = pyexcel.Sheet([keys])

    # Little utility function write a row to file.
    def write_xls_row(data, row, sheet):
        for cell in range(len(data)):
            xls_sheet.write(row, cell, data[cell])

    write_xls_row(return_keys, 0, xls_sheet)

    i = 0
    # Prepare each row
    for r in results:
        list_row = ['']*len(return_keys)
        if not is_child(allowed_location, trim_locations(r[0].clinic, children),
                        locs):
            continue

        dates = {}
        for k in return_keys:
            form_var = translation_dict[k]
            index = return_keys.index(k)

            raw_data = r[1].data
            if "many_links&" in form_var:
                link_name, number, form_var = form_var.split("&")[1:]
                number = int(number)
                if link_name in r[0].links:
                    links = r[0].links[link_name]
                    if len(links) >= number + 1:
                        link_uuid = links[number]
                        raw_data = link_data[link_uuid]
                    else:
                        list_row[index] = None
                        continue

                else:
                    list_row[index] = None
                    continue

            if "icd_name$" in form_var:
                fields = form_var.split("$")
                if len(fields) > 2:
                    field = fields[1]
                else:
                    field = "icd_code"
                if raw_data[field] in icd_code_to_name[form_var]:
                    list_row[index] = icd_code_to_name[form_var][raw_data[
                        field]]
                else:
                    list_row[index] = None
            elif form_var == "clinic":
                list_row[index] = locs[trim_locations(r[0].clinic, children)].name
            elif form_var == "region":
                list_row[index] = locs[trim_locations(r[0].region, children)].name
            elif form_var == "zone":
                list_row[index] = locs[trim_locations(r[0].zone, children)].name
            elif form_var == "district":
                if r[0].district:
                    list_row[index] = locs[trim_locations(r[0].district, children)].name
                else:
                    list_row[index] = None
            elif "$year" in form_var:
                field = form_var.split("$")[0]
                if field in raw_data and raw_data[field]:
                    if field not in dates:
                        dates[field] = parse(raw_data[field])
                    list_row[index] = dates[field].year
                else:
                    list_row[index] = None
            elif "$month" in form_var:
                field = form_var.split("$")[0]
                if field in raw_data and raw_data[field]:
                    if field not in dates:
                        dates[field] = parse(raw_data[field])
                    list_row[index] = dates[field].month
                else:
                    list_row[index] = None
            elif "$day" in form_var:
                field = form_var.split("$")[0]
                if field in raw_data and raw_data[field]:
                    if field not in dates:
                        dates[field] = parse(raw_data[field])
                    list_row[index] = dates[field].day
                else:
                    list_row[index] = None
            elif "$epi_week" in form_var:
                field = form_var.split("$")[0]
                if field in raw_data and raw_data[field]:
                    if field not in dates:
                        dates[field] = parse(raw_data[field])
                    list_row[index] = epi_week(dates[field])[1]
                else:
                    list_row[index] = None

            # A general framework for referencing links in the
            # download data.
            # link$<link id>$<linked form field>
            elif "gen_link$" in form_var:
                link = form_var.split("$")[1]
                link_index = link_id_index[link]
                if r[link_index]:
                    list_row[index] = r[link_index].get(
                        form_var.split("$")[2],
                        None
                    )
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
                for j in range(len(codes)):
                    if codes[j] in r[0].variables:
                        final_text.append(text[j])
                if len(final_text) > 0:
                    list_row[index] = " ".join(final_text)
                else:
                    list_row[index] = default_value

            elif "code_value" == form_var.split("$")[0]:
                code = form_var.split("$")[1]
                if code in r[0].variables:
                    list_row[index] = float(r[0].variables[code])
                else:
                    list_row[index] = None
            elif "value" == form_var.split(":")[0]:
                list_row[index] = form_var.split(":")[1]
            elif "$to_columns$" in form_var:
                field = form_var.split("$")[0]
                codes = form_var.split("$")[-1].split(",")
                has_code = 0
                data = raw_data.get(field, "").split(" ")
                for c in codes:
                    if c in data:
                        has_code = 1
                        break
                list_row[index] = has_code
            else:
                if form_var.split("$")[0] in raw_data:
                    list_row[index] = raw_data[form_var.split("$")[0]]
                else:
                    list_row[index] = None

            # Standardise date formating
            if "$date" in form_var:
                field = form_var.split("$")[0]
                if list_row[index]:
                    if field not in dates:
                        dates[field] = parse(list_row[index])
                    list_row[index] = dates[field].strftime(
                        "%d/%m/%Y"
                    )
                else:
                    list_row[index] = None

            # If the final value is a float, round to 2 dp.
            # This proceedure ensures integers are shown as integers.
            # Also accepts string values.
            try:
                a = float(list_row[index])
                b = int(float(list_row[index]))
                if a == b:
                    list_row[index] = b
                else:
                    list_row[index] = round(a, 2)
            except (ValueError, TypeError):
                pass

            # If a translation dictionary is defined in which the key exists...
            if min_translation and k in min_translation and list_row[index]:
                tr_dict = min_translation[k]
                if list_row[index] in tr_dict:
                    list_row[index] = tr_dict[list_row[index]]
                else:
                    parts = [x.strip() for x in str(list_row[index]).split(' ')]
                    for x in range(len(parts)):
                        # Get the translation using the appropriate key.
                        # If that doesn't exist get the wild card key: *
                        # If that doesn't exist just return the value
                        parts[x] = str(
                            tr_dict.get(parts[x], tr_dict.get('*', parts[x]))
                        )
                    list_row[index] = ' '.join(list(filter(bool, parts)))

            if translation_dir and language != "en" and list_row[index]:
                list_row[index] = t.gettext(list_row[index])
        list_rows.append(list_row)
        # Can write row immediately to xls file as memory is flushed after.
        write_xls_row(list_row, i+1, xls_sheet)
        # Append the row to list of rows to be written to csv.
        if i % 1000 == 0:
            logging.warning("{} rows completed...".format(i))
            csv_writer.writerows(list_rows)
            list_rows = []
            status.status = i / total_number
            session.commit()
        i += 1
    csv_writer.writerows(list_rows)

    csv_content.close()
    xls_book.close()

    xls_content.close()
    status.status = 1
    status.success = 1
    session.commit()

    if query_links:
        link_data.close()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        filename = dir_path + "/exported_data/" + uuid
        logging.warning("Filename: " + filename)
        if os.path.exists(filename+".dir"):
            os.remove(filename+".dir")
        if os.path.exists(filename+".dat"):
            os.remove(filename+".dat")
    return True


@task
def export_data_table(uuid, download_name,
                      restrict_by, variables, group_by,
                      location_conditions=None):
    """
    Export an aggregated data table restricted by restrict by,


    """
    return_keys = []
    db, session = get_db_engine()
    locs = get_locations(session)
    list_rows = []
    status = DownloadDataFiles(
        uuid=uuid,
        generation_time=datetime.now(),
        type=download_name,
        success=0,
        status=0
    )
    children = locs[1].children + [1]
    session.add(status)
    session.commit()
    columns = []
    groups = []
    location_subs = []
    for i, v in enumerate(group_by):
        field = v[0]
        if ":location" in field:
            field = field.split(":")[0]
            location_subs.append(i)
        columns.append(getattr(Data, field))
        groups.append(getattr(Data, field))
        return_keys.append(v[1])

    for v in variables:
        columns.append(func.sum(Data.variables[v[0]].astext.cast(Float)))
        return_keys.append(v[1])

    result = session.query(*columns).filter(
        Data.variables.has_key(restrict_by)).group_by(*groups)

    filename = base_folder + "/exported_data/" + uuid + "/" + download_name
    os.mkdir(base_folder + "/exported_data/" + uuid)
    csv_content = open(filename + ".csv", "w")
    csv_writer = csv.writer(csv_content)
    csv_writer.writerows([return_keys])

    # XlsxWriter with "constant_memory" set to true, flushes mem after each row
    xls_content = open(filename + ".xlsx", "wb")
    xls_book = xlsxwriter.Workbook(xls_content, {'constant_memory': True})
    xls_sheet = xls_book.add_worksheet()
    # xls_sheet = pyexcel.Sheet([keys])

    # Little utility function write a row to file.
    def write_xls_row(data, row, sheet):
        for cell in range(len(data)):
            xls_sheet.write(row, cell, data[cell])

    write_xls_row(return_keys, 0, xls_sheet)
    i = 0
    for row in result:
        # Can write row immediately to xls file as memory is flushed after.

        row_list = list(row)
        location_condition = True
        for l in location_subs:
            if row_list[l]:
                single_loc = trim_locations(row_list[l], children)
                if location_conditions:
                    if getattr(locs[single_loc],
                               location_conditions[0][0]) != location_conditions[0][1]:
                        location_condition = False
                row_list[l] = locs[single_loc].name
        if location_condition:
            row_list = [x if x is not None else 0 for x in row_list]
            write_xls_row(row_list, i+1, xls_sheet)
            list_rows.append(row_list)
            # Append the row to list of rows to be written to csv.
            i += 1
    csv_writer.writerows(list_rows)

    csv_content.close()
    xls_book.close()

    xls_content.close()
    status.status = 1
    status.success = 1
    session.commit()

    return True


@task
def export_form(uuid, form, allowed_location, fields=None):
    """
    Export a form. If fields is in the request variable we only include
    those fields.

    Starts background export

    Args:\n
       uuid: uuid of download\n
       form: the form to export\n
       fields: Fileds from form to export\n

    """

    db, session = get_db_engine()
    (locations, locs_by_deviceid, regions,
     districts, devices) = all_location_data(session)

    locs = get_locations(session)
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

    filename = base_folder + "/exported_data/" + uuid + "/" + form
    os.mkdir(base_folder + "/exported_data/" + uuid)
    csv_content = open(filename + ".csv", "w")
    csv_writer = csv.writer(csv_content)
    csv_writer.writerows([keys])

    # XlsxWriter with "constant_memory" set to true, flushes mem after each row
    xls_content = open(filename + ".xlsx", "wb")
    xls_book = xlsxwriter.Workbook(xls_content, {'constant_memory': True})
    xls_sheet = xls_book.add_worksheet()
    # xls_sheet = pyexcel.Sheet([keys])

    # Little utility function write a row to file.
    def write_xls_row(data, row, sheet):
        for cell in range(len(data)):
            xls_sheet.write(row, cell, data[cell])

    write_xls_row(keys, 0, xls_sheet)

    i = 0
    if locs_by_deviceid is None:
        session.add(
            DownloadDataFiles(
                uuid=uuid,
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
        list_rows = []
        for row in results:
            # Initialise empty row
            list_row = ['']*len(keys)
            # For each key requested, add the value to the row.
            for key in keys:
                try:
                    list_row[keys.index(key)] = row.data.get(key, '')
                except AttributeError as e:
                    logging.warning(e)
                    logging.warning(row)
                    logging.warning(row.data)

            # Add the location data if it has been requested and exists.
            if 'deviceid' in row.data:
                clinic_id = locs_by_deviceid.get(
                    row.data["deviceid"],
                    None
                )
            if clinic_id:
                if not is_child(allowed_location,clinic_id, locs):
                    continue

                if 'clinic' in keys:
                    list_row[keys.index("clinic")] = locations[clinic_id].name
                # Sort out district and region
                if locations[clinic_id].parent_location in districts:
                    if 'district' in keys:
                        list_row[keys.index("district")] = locations[
                            locations[clinic_id].parent_location
                        ].name
                    if 'region' in keys:
                        list_row[keys.index("region")] = locations[locations[
                            locations[clinic_id].parent_location
                        ].parent_location].name
                elif locations[clinic_id].parent_location in regions:
                    if 'district' in keys:
                        list_row[keys.index("district")] = ""
                    if 'region' in keys:
                        list_row[keys.index("region")] = locations[
                            locations[clinic_id].parent_location
                        ].name
            else:
                if allowed_location != 1:
                    continue
                if 'clinic' in keys:
                    list_row[keys.index("clinic")] = ""
                if 'district' in keys:
                    list_row[keys.index("district")] = ""
                if 'region' in keys:
                    list_row[keys.index("region")] = ""

            # Can write row immediately to xls file as memory is flushed after.
            write_xls_row(list_row, i+1, xls_sheet)
            # Append the row to list of rows to be written to csv.
            list_rows.append(list_row)

            # Store for every 1000 rows.
            if i % 5 == 0:
                csv_writer.writerows(list_rows)
                list_rows = []
            i += 1

        # Write any remaining unwritten data down.
        csv_writer.writerows(list_rows)

        xls_book.close()
        csv_content.close()
        xls_content.close()

        session.add(
            DownloadDataFiles(
                uuid=uuid,
                generation_time=datetime.now(),
                type=form,
                success=1,
                status=1
            )
        )
        session.commit()

        return True

if __name__ == "__main__":
    import uuid
    export_data_table(str(uuid.uuid4()), "test", "reg_1", [["reg_2", "Consultations"]], [["epi_year", "year"],["clinic:location", "clinic"], ["epi_week", "week"]],
                      location_conditions=[["case_type", "SARI"]])
