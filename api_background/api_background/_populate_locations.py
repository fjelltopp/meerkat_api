def set_empty_locations(keys, row):
    for location_type in ['clinic', 'district', 'region']:
        if location_type in keys:
            index = keys.index(location_type)
            row[index] = ""


def populate_row_locations(row, keys, clinic_id, location_data):
    (locations, locs_by_deviceid, zones, regions, districts, devices) = location_data
    if 'clinic' in keys:
        clinic_name = locations[clinic_id].name
        row[keys.index("clinic")] = clinic_name
    int_parent_location = locations[clinic_id].parent_location
    if int_parent_location in districts:
        __handle_district(clinic_id, keys, row, locations)
    elif int_parent_location in regions:
        parent_location = locations[int_parent_location]
        __handle_region(parent_location, keys, row)


def __handle_region(parent_location, keys, row):
    if 'district' in keys:
        row[keys.index('district')] = ""
    if 'region' in keys:
        row[keys.index('region')] = parent_location.name


def __handle_district(clinic_id, keys, row, locations):
    parent_location = locations[clinic_id].parent_location
    if 'district' in keys:
        row[keys.index('district')] = locations[parent_location].name
    if 'region' in keys:
        grandparent_location = locations[parent_location].parent_location
        row[keys.index('region')] = locations[grandparent_location].name
