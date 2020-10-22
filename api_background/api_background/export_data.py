"""
Functions to export data
"""
import gettext
import shelve
import csv
import json
import logging
import xlsxwriter
import os
import yaml
from sqlalchemy.orm import aliased
from sqlalchemy import text, or_, func, Float
from dateutil.parser import parse
from datetime import datetime
from celery import task
import requests
import pandas
from api_background._populate_locations import set_empty_locations, populate_row_locations
from api_background.xls_csv_writer import XlsCsvFileWriter
from meerkat_abacus import config
from meerkat_abacus.model import DownloadDataFiles, AggregationVariables
from meerkat_abacus.model import form_tables, Data, Links
from meerkat_abacus.util import all_location_data, get_db_engine, get_links
from meerkat_abacus.util import get_locations, is_child
from meerkat_abacus.util.epi_week import epi_week_for_date
from api_background.celery_app import app
import meerkat_libs

base_folder = os.path.dirname(os.path.realpath(__file__))



@app.task
def export_data(uuid, allowed_location, use_loc_ids=False, param_config_yaml=yaml.dump(config)):
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
                  "district", "clinic", "zone_id", "country_id", "region_id",
                  "district_id", "clinic_id", "clinic_type",
                  "geolocation", "date", "uuid"] + list(variables)
    dict_rows = []

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

        for l in ["country", "zone", "region", "district", "clinic"]:
            if dict_row[l]:
                dict_row[l + "_id"] = dict_row[l]
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
    session.commit()
    return True


@app.task
def export_category(uuid, form_name, category, download_name,
                    variables, data_type, allowed_location,
                    start_date=None, end_date=None, language="en",
                    param_config_yaml=yaml.dump(config)):
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
    # Runner loads the config object through a function parameter.
    param_config = yaml.load(param_config_yaml)
    country_config = param_config.country_config
    config_directory = param_config.config_directory

    # Some strings in download data need to be translated
    translation_dir = country_config.get("translation_dir", None)
    t = get_translator(param_config, language)

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


    locs = get_locations(session)
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
        file_path = '{}api/{}'.format(config_directory, details['dict_file'])
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
                    translation_dict[name] = "many_links&" + link_name + "&" + str(i) + "&" + variable[0]
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
                        form_tables(param_config)[form_name].data[field].astext, ' '))).join(
                Data,
                Data.uuid == form_tables(param_config)[form_name].uuid).filter(
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
    columns = [Data, form_tables(param_config)[form_name]]

    link_id_index = {}
    joins = []

    if query_links:
        link_data = shelve.open(base_folder + "/exported_data/" + uuid)
        link_data_query = session.query(Links).filter(Links.type == link_name).yield_per(300)
        for row in link_data_query:
            link_data[row.uuid_to] = row.data_to

    for i, l in enumerate(link_ids):
        form = aliased(form_tables(param_config)[links_by_name[l]["to_form"]])
        joins.append((form, Data.links[(l, -1)].astext == form.uuid))
        link_id_index[l] = i + 2
        columns.append(form.data)

    number_query = session2.query(func.count(Data.id)).join(
        form_tables(param_config)[form_name], Data.uuid == form_tables(param_config)[form_name].uuid)

    results = session2.query(*columns).join(
        form_tables(param_config)[form_name], Data.uuid == form_tables(param_config)[form_name].uuid)
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

    def _list_category_variables(category, data_row):
        """
        Lists the variables from the specified category that are assigned to
        the specified row. This can be used to create data columns such as
        'Age Group' using 'category$ncd_age'.
        """
        # Get the category's variables' data, indexed by ID.
        cat_variables = {}
        variable_list = ""
        db_results = session.query(AggregationVariables).filter(
            AggregationVariables.category.has_key(category)
        )
        for variable in db_results:
            cat_variables[variable.id] = variable
        # Build a string listing the row's variables from specified category.
        for var_id, var in cat_variables.items():
            if var_id in r[0].variables:
                variable_list += var.name + ", "
        # Remove the last comma and space.
        return variable_list[:-2]

    # Prepare each row
    for r in results:
        list_row = [''] * len(return_keys)
        if not is_child(allowed_location, r[0].clinic, locs):
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
                list_row[index] = locs[r[0].clinic].name
            elif form_var == "region":
                list_row[index] = locs[r[0].region].name
            elif form_var == "zone":
                list_row[index] = locs[r[0].zone].name
            elif form_var == "district":
                if r[0].district:
                    list_row[index] = locs[r[0].district].name
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
            elif "$quarter" in form_var:
                field = form_var.split("$")[0]
                if raw_data.get(field):
                    if field not in dates:
                        dates[field] = parse(raw_data[field])
                    quarter = 1 + (dates[field].month - 1)//3
                    list_row[index] = quarter
                else:
                    list_row[index] = None
            elif "$epi_week" in form_var:
                field = form_var.split("$")[0]
                if field in raw_data and raw_data[field]:
                    if field not in dates:
                        dates[field] = parse(raw_data[field])
                    list_row[index] = epi_week_for_date(dates[field])[1]
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

            elif "category" == form_var.split("$")[0]:
                list_row[index] = _list_category_variables(
                    form_var.split("$")[1],
                    r
                )

            elif "code_value" == form_var.split("$")[0]:
                code = form_var.split("$")[1]
                if code in r[0].variables:
                    list_row[index] = float(r[0].variables[code])
                else:
                    list_row[index] = None
            elif "value" == form_var.split(":")[0]:
                list_row[index] = form_var.split(":")[1]
            elif "$to_columns$" in form_var:
                int_has_code = 0
                field = form_var.split("$")[0]
                codes = form_var.split("$")[-1].split(",")
                str_elements = raw_data.get(field)
                if type(str_elements) == str:
                    elements = str_elements.split(" ")
                    has_code = any(code in elements for code in codes)
                    int_has_code = int(has_code)
                list_row[index] = int_has_code
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
        write_xls_row(list_row, i + 1, xls_sheet)
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
        if os.path.exists(filename + ".dir"):
            os.remove(filename + ".dir")
        if os.path.exists(filename + ".dat"):
            os.remove(filename + ".dat")
    return True


def construct_completeness_call(variable_config, sublevel, start_date, end_date):
    """
    Construct the correct completess calls based on the dates

    Args:\n
       variable_config: The base api call
       sublevel: The level to aggregate over
       start_date: Start date
       end_date: End date
    """
    api_calls = []
    for year in range(start_date.year, end_date.year + 1):
        year_start_week = 1
        year_end_date_str = "{}-12-31".format(year)
        if year == start_date.year:
            year_start_week = epi_week_for_date(start_date)[1]
            if year_start_week > 52:
                year_start_week = 1
        if year == end_date.year:
            year_end_date_str = end_date.isoformat()
        api_call = variable_config.split(":")[1]
        api_call = api_call.replace("<start_week>", str(year_start_week))
        api_call = api_call.replace("<end_date>", str(year_end_date_str))
        api_call += "?sublevel={}".format(sublevel)
        api_calls.append((api_call, year, year_start_week))
    return api_calls


def _export_week_level_completeness(uuid, download_name, level,
                                    completeness_config, translator, param_config,
                                    start_date=None, end_date=None,
                                    wide_data_format=False):
    """
    Exports completeness data by location and week ( and year),

    Args:\n
      uuid: uuid for the download process
      download_name: Name of download file
      level: level of location
      competeness_config: Specified the completeness call we want to make
      translator: Translator
      param_config: param config
      start_date: The date to start the data set
      end_date: End date for the aggregation
      wide_data_format: If true the data is returned in the wide format, else in long format
    """
    db, session = get_db_engine()
    locs = get_locations(session)
    operation_status = OperationStatus(download_name, uuid)

    if start_date:
        start_date = parse(start_date).replace(tzinfo=None)
    if end_date:
        end_date = parse(end_date).replace(tzinfo=None)
    completeness_calls = construct_completeness_call(completeness_config[0],
                                                     level,
                                                     start_date,
                                                     end_date)
    jwt_auth_token = meerkat_libs.authenticate(
        username=param_config.server_auth_username,
        password=param_config.server_auth_password,
        auth_root=param_config.auth_root)
    if not jwt_auth_token:
        raise AttributeError("Not sucessfully logged in for api access")
    headers = {'content-type': 'application/json',
               'authorization': 'Bearer {}'.format(jwt_auth_token)}
    data = []

    year_label = translator.gettext("Year")
    location_label = translator.gettext(level.title())
    week_label = translator.gettext("Week")
    district_label = translator.gettext("District")
    completeness_config_label = translator.gettext(completeness_config[1])

    for call, year, start_week in completeness_calls:
        api_result = requests.get(param_config.api_root + call, headers=headers)
        timeline = api_result.json()["timeline"]
        max_per_week = int(call.split("/")[4])  # Extract the maximum number from api call
        for location in timeline:
            loc_id = int(location)
            for week in range(len(timeline[location]["weeks"])):
                week_start_day = datetime.strptime(timeline[location]["weeks"][week], '%Y-%m-%dT%H:%M:%S')
                data.append({year_label: year,
                             location_label: locs[loc_id].name,
                             week_label: epi_week_for_date(week_start_day)[1],
                             completeness_config_label: timeline[location]["values"][week] / max_per_week * 100
                             })
                if level == "clinic" and loc_id != 1:
                    data[-1][district_label] = locs[locs[loc_id].parent_location].name

    filename = base_folder + "/exported_data/" + uuid + "/" + download_name
    os.mkdir(base_folder + "/exported_data/" + uuid)
    df = pandas.DataFrame(data)
    if wide_data_format:
        if level == "clinic":
            index_labels = [year_label, district_label, location_label, week_label]
        else:
            index_labels = [year_label, location_label, week_label]
        df = df.set_index(index_labels).unstack()
    df.to_csv(filename + ".csv")
    df.to_excel(filename + ".xlsx")
    operation_status.submit_operation_success()



def get_translator(param_config, language):
    translation_dir = param_config.country_config.get("translation_dir", None)
    if translation_dir:
        try:
            t = gettext.translation('messages', translation_dir, languages=["en", "fr"])
        except (FileNotFoundError, OSError):
            logging.warning("Translations not found", exc_info=True)
            t = gettext.NullTranslations()
    else:
        t = gettext.NullTranslations()

    if language != "en":
        os.environ["LANGUAGE"] = language
    return t

@app.task
def export_week_level(uuid, download_name, level,
                      variable_config, start_date=None, end_date=None,
                      wide_data_format=False, language="en",
                      param_config_yaml=yaml.dump(config)):
    """
    Export aggregated data by location and week ( and year),

    Args:\n
      uuid: uuid for the download process
      download_name: Name of download file
      level: level of location
      variable_config: the variable we want to aggregate
      data_orientation: long or wide data set
      start_date: The date to start the data set
      end_date: End date for the aggregation
      wide_data_format: If true the data is returned in the wide format, else in long format
      param_config: The configuration values
    """
    param_config = yaml.load(param_config_yaml)
    translator = get_translator(param_config, language)
    if "completeness" in variable_config[0]:
        _export_week_level_completeness(uuid, download_name, level,
                                        variable_config, translator,
                                        param_config, start_date=start_date,
                                        end_date=end_date, wide_data_format=wide_data_format)
    else:
        _export_week_level_variable(uuid, download_name, level,
                                    variable_config, translator,
                                    start_date=start_date, end_date=end_date,
                                    wide_data_format=wide_data_format,
                                    param_config_yaml=param_config_yaml)


def _export_week_level_variable(uuid, download_name, level,
                                variable_config, translator,
                                start_date=None, end_date=None,
                                wide_data_format=False,
                                param_config_yaml=yaml.dump(config)):
    """
    Export aggregated data by location and week ( and year),

    Args:\n
      uuid: uuid for the download process
      download_name: Name of download file
      level: level of location
      variable_config: the variable we want to aggregate. Consits of the restrict_by, variable to aggregate and the display name
      data_orientation: long or wide data set
      start_date: The date to start the data set
      end_date: End date for the aggregation
      wide_data_format: If true the data is returned in the wide format, else in long format
      param_config: The configuration values
    """

    restrict_by, variable, display_name = variable_config
    if level == "clinic":
        group_by = [["epi_year", translator.gettext("Year")],
                    ["district:location", translator.gettext("District")],
                    [level + ":location", translator.gettext(level.title())],
                    ["epi_week", translator.gettext("Week")]
        ]
    else:
        group_by = [["epi_year", translator.gettext("Year")],
                    [level + ":location", translator.gettext(level.title())],
                    ["epi_week", translator.gettext("Week")]
        ]
    return export_data_table(uuid,
                             download_name,
                             restrict_by,
                             [[variable, display_name]],
                             group_by,
                             start_date=start_date,
                             end_date=end_date,
                             wide_data_format=wide_data_format,
                             param_config_yaml=param_config_yaml)

        
@app.task
def export_data_table(uuid, download_name,
                      restrict_by, variables, group_by,
                      location_conditions=None,
                      start_date=None, end_date=None,
                      wide_data_format=False,
                      param_config_yaml=yaml.dump(config)):
    """
    Export an aggregated data table restricted by restrict by,

    Args:\n
      uuid: uuid for the download process
      variables: the variables we want to aggregate
      group_by: The data to group by (clinic, epi_week)
      data_orientation: long or wide data set
      start_date: The date to start the data set
      end_date: End date for the aggregation
      wide_data_format: If true the data is returned in the wide format, else in long format
      param_config: The configuration values
    """
    return_keys = []
    db, session = get_db_engine()
    locs = get_locations(session)
    list_rows = []
    operation_status = OperationStatus(download_name, uuid)
    level = "region"
    columns = []
    groups = []
    location_subs = []
    only_latest_from_clinic_in_week = False
    if "only_latest_from_clinic_in_week:" in restrict_by:
        restrict_by_variable = restrict_by.split(":")[1]
        only_latest_from_clinic_in_week = True
    else:
        restrict_by_variable = restrict_by

    for i, v in enumerate(group_by):
        field = v[0]
        if ":location" in field:
            field_column = field.split(":")[0]
            level = field_column
            location_subs.append(i)
        else:
            field_column = field

        columns.append(getattr(Data, field_column))
        groups.append(getattr(Data, field_column))
        return_keys.append(v[1])
    conditions = [Data.variables.has_key(restrict_by_variable)]
    if start_date:
        start_date = parse(start_date).replace(tzinfo=None)
        conditions.append(Data.date >= start_date)
    if end_date:
        end_date = parse(end_date).replace(tzinfo=None)
        conditions.append(Data.date <= end_date)
    for v in variables:
        if only_latest_from_clinic_in_week:
            columns.append(Data.variables[v[0]].astext.cast(Float))
        else:
            columns.append(func.sum(Data.variables[v[0]].astext.cast(Float)))
        return_keys.append(v[1])

    if only_latest_from_clinic_in_week:
        conditions.append(Data.variables.has_key(restrict_by_variable))
        result =  session.query(*columns).distinct(Data.clinic).filter(*conditions).order_by(Data.clinic).order_by(Data.date.desc())
    else:
        result = session.query(*columns).filter(*conditions).group_by(*groups)

    filename = base_folder + "/exported_data/" + uuid + "/" + download_name
    os.mkdir(base_folder + "/exported_data/" + uuid)
    i = 0
    for row in result:
        row_list = list(row)
        location_condition = True
        for l in location_subs:
            if row_list[l]:
                if location_conditions:
                    tmp = getattr(locs[row_list[l]], location_conditions[0][0])
                    if location_conditions[0][1] in tmp:
                        location_condition = False
                row_list[l] = locs[row_list[l]].name
        if location_condition:
            row_list = [x if x is not None else 0 for x in row_list]
            list_rows.append(row_list)
            i += 1

    df = pandas.DataFrame(list_rows, columns=return_keys)
    if wide_data_format:
        df = df.set_index(return_keys[:-len(variables)]).unstack().fillna(0)

    df.to_csv(filename + ".csv")
    df.to_excel(filename + ".xlsx")
    operation_status.submit_operation_success()

    return True


@app.task
def export_form(uuid, form, allowed_location, fields=None, param_config_yaml=yaml.dump(config)):
    """
    Export a form. If fields is in the request variable we only include
    those fields.

    Starts background export

    Args:\n
       uuid: uuid of download\n
       form: the form to export\n
       allowed_location: will extract result only for this location
       fields: Fields from form to export\n

    Returns:\n
        bool: The return value. True for success, False otherwise.\n

    """

    # Runner loads the config object through a function parameter.
    param_config = yaml.load(param_config_yaml)

    db, session = get_db_engine()
    operation_status = OperationStatus(form, uuid)
    if form not in form_tables(param_config):
        operation_status.submit_operation_failure()
        return False

    location_data = all_location_data(session)
    locs_by_deviceid = location_data[1]
    if locs_by_deviceid is None:
        operation_status.submit_operation_failure()
        return False

    if fields:
        keys = fields
    else:
        keys = __get_keys_from_db(db, form, param_config)

    xls_csv_writer = XlsCsvFileWriter(base_folder, form, uuid)
    xls_csv_writer.write_xls_row(keys)
    xls_csv_writer.write_csv_row(keys)

    query_form_data = session.query(form_tables(param_config)[form].data)
    __save_form_data(xls_csv_writer, query_form_data, operation_status, keys, allowed_location, location_data)
    operation_status.submit_operation_success()
    xls_csv_writer.flush_csv_buffer()
    xls_csv_writer.close_cvs_xls_buffers()
    return True


def __get_keys_from_db(db, form, param_config=config):
    keys = ["clinic", "region", "district"]
    sql = text(f"SELECT DISTINCT(jsonb_object_keys(data)) from {form_tables(param_config)[form].__tablename__}")
    results = db.execute(sql)
    for r in results:
        keys.append(r[0])
    return keys


class OperationStatus:
    def __init__(self, form, uuid):
        self.db, self.session = get_db_engine()
        self.__initialize(form, uuid)

    def __initialize(self, form, uuid):
        self.download_data_file = DownloadDataFiles(uuid=uuid,
                                                    generation_time=datetime.now(),
                                                    type=form,
                                                    success=0,
                                                    status=0.0)
        self.session.add(self.download_data_file)
        self.session.commit()

    def update_operation_status(self, status):
        self.download_data_file.status = status
        self.download_data_file.success = 0
        self.session.commit()

    def submit_operation_success(self):
        self.download_data_file.status = 1.0
        self.download_data_file.success = 1
        self.session.commit()

    def submit_operation_failure(self):
        self.download_data_file.status = 1.0
        self.download_data_file.success = 0
        self.session.commit()


def __save_form_data(xls_csv_writer, query_form_data, operation_status, keys, allowed_location, location_data):
    (locations, locs_by_deviceid, zones, regions, districts, devices) = location_data
    results = query_form_data.yield_per(1000)
    results_count = query_form_data.count()
    for i, result in enumerate(results):
        if not result:
            logging.error("Skipping result %d which is None", i)
            continue
        if not result.data:
            logging.error("Skipping result %d. Data is None", i)
            continue
        if not isinstance(result.data, dict):
            logging.error("Skipping result %d which data is not of a dictionary type", i)
            continue
        # Initialise empty result for header line
        row = []
        for key in keys:
            try:
                row.append(result.data.get(key, ''))
            except AttributeError:
                logging.exception("Error while parsing row %s with data:\n%s", result, result.data, exc_info=True)
        # Add the location data if it has been requested and exists.
        if 'deviceid' in result.data:
            clinic_id = locs_by_deviceid.get(result.data["deviceid"], None)
            if not is_child(allowed_location, clinic_id, locations):
                continue
            populate_row_locations(row, keys, clinic_id, location_data)

        else:
            if allowed_location != 1:
                continue
            set_empty_locations(keys, row)

        xls_csv_writer.write_xls_row(row)
        xls_csv_writer.write_csv_row(row)

        five_percent_progress = i % (results_count / 20) == 0
        if five_percent_progress:
            new_status = float(i) / results_count
            operation_status.update_operation_status(new_status)


if __name__ == "__main__":
    import uuid

    export_data_table(
        str(uuid.uuid4()), "test", "reg_1", [["reg_2", "Consultations"]],
        [["epi_year", "year"], ["clinic:location", "clinic"], ["epi_week", "week"]],
        location_conditions=[["case_type", "SARI"]]
    )
