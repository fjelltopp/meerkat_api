def set_empty_locations(keys, row):
    for location_type in ['clinic', 'district', 'region']:
        if location_type in keys:
            index = keys.index(location_type)
            row[index] = ""


def populate_row_locations(row, keys, clinic_id, location_data, use_integer_keys=True):
    (locations, locs_by_deviceid, zones, regions, districts, devices) = location_data
    if 'clinic' in keys:
        clinic_name = locations[clinic_id].name
        row[__get_key(keys, "clinic", use_integer_keys)] = clinic_name
    int_parent_location = locations[clinic_id].parent_location
    if int_parent_location in districts:
        __handle_district(clinic_id, keys, row, locations, use_integer_keys)
    elif int_parent_location in regions:
        parent_location = locations[int_parent_location]
        __handle_region(parent_location, keys, row, use_integer_keys)


def __get_key(keys, key_name, integer_keys):
    if integer_keys:
        return keys.index(key_name)
    else:
        return key_name


def __handle_region(parent_location, keys, row, use_integer_keys):
    if 'district' in keys:
        row[__get_key(keys, 'district', use_integer_keys)] = ""
    if 'region' in keys:
        row[__get_key(keys, 'region', use_integer_keys)] = parent_location.name


def __handle_district(clinic_id, keys, row, locations, use_integer_keys):
    parent_location = locations[clinic_id].parent_location
    if 'district' in keys:
        row[__get_key(keys, 'district', use_integer_keys)] = locations[parent_location].name
    if 'region' in keys:
        grandparent_location = locations[parent_location].parent_location
        row[__get_key(keys, 'region', use_integer_keys)] = locations[grandparent_location].name
