"""
Functions to export data
"""
from meerkat_abacus.util import epi_week, get_locations
from meerkat_abacus.util import all_location_data, get_db_engine, get_links
from meerkat_abacus.model import form_tables, Data, Links
from meerkat_abacus.model import DownloadDataFiles, AggregationVariables
from meerkat_abacus.config import country_config, config_directory
from sqlalchemy.orm import aliased
from sqlalchemy import text, or_, func
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
        xlscontent=b"",
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
    locs = get_locations(session)
    for row in results:
        variables.append(row[0])

    fieldnames = ["id", "country", "region",
                  "district", "clinic", "clinic_type",
                  "geolocation", "date", "uuid"] + list(variables)
    dict_rows = []
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames, extrasaction="ignore")
    writer.writeheader()
    results = session.query(Data).yield_per(500)
    i = 0
    for row in results:
        dict_row = dict(
            (col, getattr(row, col)) for col in row.__table__.columns.keys()
        )
        if not use_loc_ids:
            for l in ["country", "region", "district", "clinic"]:
                if dict_row[l]:
                    dict_row[l] = locs[dict_row[l]].name
        dict_row.update(dict_row.pop("variables"))
        dict_rows.append(dict_row)
        if i % 1000 == 0:
            writer.writerows(dict_rows)
            dict_rows = []
        i += 1
    writer.writerows(dict_rows)
    status.status = 1
    status.success = 1
    status.csvcontent = output.getvalue()
    session.commit()
    return True


@task
def export_category(uuid, form_name, category, download_name, variables, data_type):
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
        xlscontent=b"",
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
    conditions = [or_(Data.variables.has_key(key)
                      for key in data_keys)]

    if data_type:
        conditions.append(Data.type == data_type)

    # Set up icd_code_to_name if needed and determine if
    # alert_links are included
    query_links = False
    for v in variables:

        if "every$" in v[0]:
            # Want to include all the fields in the dictionary
            # in v[1] for all the links in the name

            # First determine the maximum number of links
            link_name = v[0].split("$")[1]
            length = session.query(
                func.max(func.jsonb_array_length(Data.links[link_name]))).filter(
                    *conditions).first()[0]
            print(length)

            for i in range(length):
                for variable in v[1]:
                    name = link_name + "_" + str(i) +" "+ variable[1]
                    return_keys.append(name)
                    translation_dict[name] = "many_links&" + link_name + "&" + str(i) + "&" +variable[0]
            query_links = link_name
        else:
            return_keys.append(v[1])
            translation_dict[v[1]] = v[0]
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
            # If the json specifies file details, load translation from file.
            if tr_dict.get('dict_file', False):
                min_translation[v[1]] = add_translations_from_file(tr_dict)
            else:
                min_translation[v[1]] = tr_dict
            v[0] = field

        if "gen_link$" in v[0]:
            link_ids.append(v[0].split("$")[1])


    link_ids = set(link_ids)
    links_by_type, links_by_name = get_links(config_directory +
                                             country_config["links_file"])
    # DB query, with yield_per(200) for memory reasons

    columns = [Data, form_tables[form_name]]

    link_id_index = {}
    joins = []

    if query_links:
        link_data = {}
        link_data_query = session.query(Links).filter(Links.type == link_name)
        for row in link_data_query:
            link_data[row.uuid_to] = row.data_to
    
    for i, l in enumerate(link_ids):
        form = aliased(form_tables[links_by_name[l]["to_form"]])
        joins.append((form, Data.links[(l, -1)].astext == form.uuid))
        link_id_index[l] = i + 2
        columns.append(form.data)

    results = session.query(*columns).join(
        form_tables[form_name], Data.uuid == form_tables[form_name].uuid)
    for join in joins:
        results = results.outerjoin(join[0], join[1])

    results = results.filter(*conditions).yield_per(200)
    locs = get_locations(session)
    list_rows = []

    df = pd.DataFrame(columns=return_keys)

    i = 0
    # Prepare each row
    for r in results:
        list_row = ['']*len(return_keys)
        for k in return_keys:
            form_var = translation_dict[k]
            index = return_keys.index(k)

            raw_data = r[1].data
            if "many_links&" in form_var:
                print("hei")
                link_name, number, form_var = form_var.split("&")[1:]
                number = int(number)
                if link_name in r[0].links:
                    links = r[0].links[link_name]
                    if len(links) >= number + 1:
                        print(r[0].uuid)
                        print(number, links)
                        link_uuid = links[number]
                        raw_data = link_data[link_uuid]
                    else:
                        list_row[index] = None
                        continue

                else:
                    list_row[index] = None
                    continue
            
            if "icd_name$" in form_var:
                if raw_data["icd_code"] in icd_code_to_name[form_var]:
                    list_row[index] = icd_code_to_name[form_var][raw_data[
                        "icd_code"]]
                else:
                    list_row[index] = None

            elif "$date" in form_var:
                field = form_var.split("$")[0]
                if field in raw_data and raw_data[field]:
                    list_row[index] = parse(raw_data[field]).strftime(
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
                if field in raw_data and raw_data[field]:
                    list_row[index] = parse(raw_data[field]).year
                else:
                    list_row[index] = None
            elif "$month" in form_var:
                field = form_var.split("$")[0]
                if field in raw_data and raw_data[field]:
                    list_row[index] = parse(raw_data[field]).month
                else:
                    list_row[index] = None
            elif "$day" in form_var:
                field = form_var.split("$")[0]
                if field in raw_data and raw_data[field]:
                    list_row[index] = parse(raw_data[field]).day
                else:
                    list_row[index] = None
            elif "$epi_week" in form_var:
                field = form_var.split("$")[0]
                if field in raw_data and raw_data[field]:
                    list_row[index] = epi_week(parse(raw_data[field]))[1]
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
                    list_row[index] = float(r[0].variables[code])
                else:
                    list_row[index] = None
            elif "value" == form_var.split(":")[0]:
                list_row[index] = form_var.split(":")[1]
            else:
                if form_var in raw_data:
                    list_row[index] = raw_data[form_var]
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

            if min_translation and k in min_translation and list_row[index]:
                tr_dict = min_translation[k]
                parts = [x.strip() for x in list_row[index].split(',')]
                for x in range(len(parts)):
                    parts[x] = tr_dict.get(parts[x], parts[x])
                list_row[index] = ', '.join(list(filter(bool, parts)))

        list_rows.append(list_row)
        if i % 10000 == 0:
            df1 = pd.DataFrame(list_rows, columns=return_keys)
            df = pd.concat([df, df1])
            list_rows = []
        i += 1

    df1 = pd.DataFrame(list_rows, columns=return_keys)
    df = pd.concat([df, df1])
    list_rows = []
    # Save the collected data in xlsx form
    xlscontent = BytesIO()
    writer = pd.ExcelWriter(xlscontent, engine='xlsxwriter')
    # sheet = pyexcel.Sheet(list_rows)
    # xlscontent = sheet.save_to_memory("xlsx", xlscontent)
    df.to_excel(writer, index=False)
    writer.save()
    # Save the collected data in csv form
    csvcontent = StringIO()
    # writer = csv.writer(csvcontent)
    # writer.writerows(list_rows)
    df.to_csv(csvcontent, index=False)
    # Write the two files to database
    status.csvcontent = csvcontent.getvalue()
    status.xlscontent = xlscontent.getvalue()

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

    db, session = get_db_engine()
    (locations, locs_by_deviceid, regions,
     districts, devices) = all_location_data(session)

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

    csv_content = StringIO()
    csv_writer = csv.writer(csv_content)
    csv_writer.writerows([keys])

    # XlsxWriter with "constant_memory" set to true, flushes mem after each row
    xls_content = BytesIO()
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
                csvcontent="",
                xlscontent=b"",
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
        session.add(
            DownloadDataFiles(
                uuid=uuid,
                csvcontent=csv_content.getvalue(),
                xlscontent=xls_content.getvalue(),
                generation_time=datetime.now(),
                type=form,
                success=1,
                status=1
            )
        )
        session.commit()

        return True
