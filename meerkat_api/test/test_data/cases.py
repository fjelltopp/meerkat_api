from meerkat_abacus.model import Data, DisregardedData
import datetime

public_health_report = [
    # Registers, total cases = 15
    Data(**{'uuid': 'uuid:b59474ed-29e7-490b-a947-558babdf80a1', 'clinic_type': 'Primary', 'district': 4, 'variables': { 'reg_2': 15 }, 'clinic': 8, 'geolocation': '0.2,0.2', 'id': 1, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 11, 32, 51, 80545)}),
    # Cases, total cases = 10, 3 Males, 7 females, 2 per age category, 7 Demo Nationality 3 Null
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9371', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_1": 1, "age_13": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1 }, 'categories': {'gender': 'gen_1', 'pc': 'prc_1'}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 2, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9373', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_1": 1, "age_13": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1, "mod_1":1, "mod_2": 1, "mod_3": 1, "mod_4": 1, "mod_5": 1, "alert": 1 }, 'categories': {'gender': 'gen_1', 'pc': 'prc_1'},'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 3, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9372', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_2": 1, "age_8": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1 }, 'categories': {'gender': 'gen_2', 'pc': 'prc_1'}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 4, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9374', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_2": 1, "age_8": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1, "alert": 1 }, 'categories': {'gender': 'gen_2', 'pc': 'prc_1'}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 5, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9375', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_3": 1, "age_9": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1, "alert": 1 }, 'categories': {'gender': 'gen_2', 'pc': 'prc_1'}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 6, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9376', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_3": 1, "age_15": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1, "smo_2": 1, "smo_1": 1 }, 'categories': {'gender': 'gen_1', 'pc': 'prc_1'}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 7, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9377', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1 , "age_10": 1, "nat_2": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1}, 'categories': {'gender': 'gen_2', 'pc': 'prc_1'}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 8, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9378', 'clinic_type': 'Hospital', 'district': 5, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1 , "age_10": 1, "nat_2": 1, "sta_1": 1, "prc_2": 1, "ncd_2": 1}, 'categories': {'gender': 'gen_2', 'pc': 'prc_2'}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 9, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 5, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9379', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_5": 1, "age_11": 1, "nat_2": 1, "sta_1": 1, "prc_2": 1 , "ncd_1": 1, "icb_47": 1}, 'categories': {'gender': 'gen_2', 'pc': 'prc_2'}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 10, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9380', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_5": 1, "age_11": 1, "nat_1": 1, "sta_2": 1, "prc_3": 1, "icb_54": 1}, 'categories': {'gender': 'gen_2', 'pc': 'prc_3'}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 11, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9312', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1": 1, "gen_2": 1}, 'categories': {'gender': 'gen_2'}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 12, 'region': 3, 'country': 1, 'date': datetime.datetime(2016, 4, 30, 23, 54, 16, 49059)})
]


ncd_public_health_report = [
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9377', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_1": 1 , "age_7": 1, "nat_2": 1, "sta_1": 1, "prc_2": 1, "ncd_2": 1, "icb_31": 1 , "mod_4": 1, "mod_5": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 1, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9378', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_1": 1, "age_13": 1, "nat_2": 1, "sta_1": 1, "prc_2": 1 , "ncd_1": 1, "icb_47": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 2, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9379', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1 , "age_10": 1, "nat_2": 1, "sta_1": 1, "prc_2": 1, "ncd_2": 1, "icb_31": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 3, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9380', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_5": 1, "age_11": 1, "nat_2": 1, "sta_1": 1, "prc_2": 1 , "ncd_1": 1, "icb_47": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 4, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9381', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_2": 1 , "age_14": 1, "nat_2": 1, "sta_1": 1, "prc_2": 1, "ncd_2": 1, "icb_31": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 5, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9382', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_2": 1, "age_14": 1, "nat_1": 1, "sta_2": 1, "prc_2": 1 , "ncd_1": 1, "icb_47": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 6 , 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9383', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_5": 1, "age_11": 1, "nat_1": 1, "sta_2": 1, "prc_3": 1, "icb_54": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 11, 'region': 7, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9384', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1": 1 }, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 8, 'region': 3, 'country': 1, 'date': datetime.datetime(2016, 4, 30, 23, 54, 16, 49059)})
]


ncd_report = [
    # Diabetes
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9323', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_1": 1, "age_13": 1, "prc_2": 1, "ncd_1": 1, "lab_3": 1, "smo_4": 1}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 1, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9371', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_1": 1, "age_13": 1, "prc_2": 1, "ncd_1": 1, "lab_4": 1, "lab_5": 1, "lab_3":1, "smo_2": 1, "smo_4": 1, "lab_8": 1}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 2, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9372', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_3": 1, "age_8": 1, "prc_2": 1, "ncd_1": 1, "lab_8": 1, "lab_9": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 3, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9373', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1, "age_9": 1, "prc_2": 1, "ncd_1": 1, "com_2": 1, "lab_7": 1, "lab_6":1, "lab_10":1, "lab_11": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 4, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    #Hypertension
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9324', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_2": 1, "age_14": 1, "prc_2": 1, "ncd_2": 1, "lab_1": 1}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 5, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9375', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_2": 1, "age_14": 1, "prc_2": 1, "ncd_2": 1, "lab_1": 1, "lab_2": 1,"smo_4": 1, "smo_2": 1, "lab_10": 1, "lab_11": 1}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 6, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9376', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_3": 1, "age_8": 1, "prc_2": 1, "ncd_2": 1, "lab_3": 1, "lab_4": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 7, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9377', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1, "age_9": 1, "prc_2": 1, "ncd_2": 1, "com_1": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 8, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)})
    
]


pip_report = [
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9321', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_1": 1, "age_7": 1,"nat_1": 1, "sta_1": 1, "pip_1": 1, "pip_2": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 1, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9372', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_1": 1,"nat_1": 1, "sta_1": 1, "age_13": 1, "pip_1": 1, "pip_2": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 2, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9373', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_3": 1,"nat_1": 1, "sta_1": 1, "age_9": 1, "pip_1": 1, "pip_2": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 3, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9374', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1,"nat_1": 1, "sta_1": 1, "age_10": 1, "pip_1": 1, "pip_2": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 4, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9325', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_2": 1,"nat_1": 1, "sta_1": 1, "age_14": 1, "pip_1": 1, "pip_2": 1, "pip_3": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 5, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 6, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9376', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_2": 1, "nat_1": 1, "sta_1": 1,"age_14": 1, "pip_1": 1, "pip_2": 1, "pip_3": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 6, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 6, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9377', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_3": 1, "nat_1": 1, "sta_1": 1,"age_9": 1, "pip_1": 1, "pip_2": 1}, 'clinic': 10, 'geolocation': '-0.1,0.4', 'id': 7, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 7, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9378', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1,"nat_2": 1, "sta_2": 1, "age_10": 1, "pip_1": 1, "pip_2": 1}, 'clinic': 10, 'geolocation': '-0.1,0.4', 'id': 8, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 7, 30, 23, 54, 16, 49059)}),
        Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9379', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1,"nat_2": 1, "sta_2": 1, "age_9": 1, "pip_1": 1, "pip_3": 1}, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 9, 'region': 2, 'country': 1, 'date': datetime.datetime(2016, 4, 30, 23, 54, 16, 49059)})
    
]

refugee_data = [
    # Population and other cumulative numbers should be taken from second entry
    Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Refugee', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {'ref_1': 1, 'ref_2': 1, 'ref_3': 1, 'ref_4': 1, 'ref_5': 1, 'ref_6': 1, 'ref_7': 1, 'ref_8': 1, 'ref_9': 1, 'ref_10': 1, 'ref_11': 1, 'ref_12': 1, 'ref_14': 1, 'ref_13': 50,'ref_15': 1, 'ref_16': 2, 'ref_19': 1, 'ref_20': 1, 'ref_60': 1, 'ref_61': 2, 'ref_95': 1, 'ref_96': 1, 'ref_331': 1, 'ref_332': 1, 'ref_460': 1, 'ref_462': 2, 'ref_557': 1}, 'geolocation': '0,0', 'uuid': 'uuid:fe301f1b-c541-4dde-a355-1552b03e6b7f', 'country': 1, 'id': 1001}),
    Data(**{'date': datetime.datetime(2015, 4, 13, 0, 0), 'clinic_type': 'Refugee', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {'ref_1': 2, 'ref_2': 3, 'ref_3': 4, 'ref_4': 5, 'ref_5': 6, 'ref_6': 7, 'ref_7': 8, 'ref_9': 9, 'ref_10': 10, 'ref_11': 11, 'ref_12': 12, 'ref_14': 5, 'ref_13': 100,'ref_15': 1, 'ref_16': 2,  'ref_19': 1, 'ref_20': 1, 'ref_60': 1, 'ref_61': 2, 'ref_95': 1, 'ref_96': 1, 'ref_331': 1, 'ref_332': 1, 'ref_460': 1, 'ref_462': 2, 'ref_557': 1}, 'geolocation': '0,0', 'uuid': 'uuid:1d337c48-853c-4fc2-93b9-2e5aa74d72b3', 'country': 1, 'id': 1002}),
    Data(**{'date': datetime.datetime(2015, 4, 29, 0, 0), 'clinic_type': 'Refugee', 'district': 5, 'region': 2, 'clinic': 7, 'variables': {'ref_1': 1, 'ref_2': 1, 'ref_3': 1, 'ref_4': 1, 'ref_5': 1, 'ref_6': 1, 'ref_7': 1, 'ref_8': 1, 'ref_9': 1, 'ref_10': 1, 'ref_11': 1, 'ref_12': 1, 'ref_14': 1, 'ref_13': 20, 'ref_15': 1, 'ref_16': 2, 'ref_19': 1, 'ref_20': 1, 'ref_60': 1, 'ref_61': 1, 'ref_95': 1, 'ref_96': 1, 'ref_331': 1, 'ref_332': 1, 'ref_460': 1, 'ref_462': 3, 'ref_557': 1}, 'geolocation': '0,0', 'uuid': 'uuid:c35445a9-eabc-4609-bcb7-4a333c0e23f1', 'country': 1, 'id': 1003}),
    Data(**{'date': datetime.datetime(2016, 4, 29, 0, 0), 'clinic_type': 'Refugee', 'district': 5, 'region': 2, 'clinic': 7, 'variables': {'ref_1': 1, 'ref_2': 1, 'ref_3': 1, 'ref_4': 1, 'ref_5': 1, 'ref_6': 1, 'ref_7': 1, 'ref_8': 1, 'ref_9': 1, 'ref_10': 1, 'ref_11': 1, 'ref_12': 1, 'ref_14': 1}, 'geolocation': '0,0', 'uuid': 'uuid:c35445a9-eabc-4609-bcb7-4a333c0e23f2', 'country': 1, 'id': 1004})
]


year = datetime.datetime.now().year
frontpage = [
    # Registers, total cases = 15
    Data(**{'uuid': 'uuid:b59474ed-29e7-490b-a947-558babdf80a5', 'clinic_type': 'Primary', 'district': 4, 'variables': { 'reg_1': 1, 'reg_2': 15 }, 'clinic': 8, 'geolocation': '0.2,0.2', 'id': 1, 'region': 2, 'country': 1, 'date': datetime.datetime(year, 4, 30, 11, 32, 51, 80545)}),
    # Cases, total cases = 10, 3 Males, 7 females, 2 per age category, 7 Demo Nationality 3 Null
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9323', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_1": 1, "age_13": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1 }, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 2, 'region': 2, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
     Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9324', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"alert": 1, "tot_1":1, "gen_1": 1, "age_1": 1, "age_13": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1 }, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 3, 'region': 2, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)})
]


map_test = [
    # Cases, total cases = 10, 3 Males, 7 females, 2 per age category, 7 Demo Nationality 3 Null
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9321', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_1": 1, "age_13": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1 }, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 2, 'region': 2, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9372', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_1": 1, "age_13": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1, "mod_1":1, "mod_2": 1, "mod_3": 1, "mod_4": 1, "mod_5": 1 }, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 3, 'region': 2, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9373', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_2": 1, "age_8": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1 }, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 4, 'region': 2, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9374', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_2": 1, "age_8": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1 }, 'clinic': 8, 'geolocation': '-0.1,0.4', 'id': 5, 'region': 2, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9375', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_3": 1, "age_9": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1 }, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 6, 'region': 2, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9376', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_1": 1, "age_3": 1, "age_15": 1, "nat_1": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1, "smo_2": 1, "smo_1": 1 }, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 7, 'region': 2, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9377', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1 , "age_10": 1, "nat_2": 1, "sta_1": 1, "prc_1": 1, "cmd_1": 1, "icb_1": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 8, 'region': 3, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9378', 'clinic_type': 'Hospital', 'district': 5, 'variables': {"tot_1":1, "gen_2": 1, "age_4": 1 , "age_10": 1, "nat_2": 1, "sta_1": 1, "prc_2": 1, "ncd_2": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 9, 'region': 3, 'country': 1, 'date': datetime.datetime(year, 5, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9379', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_5": 1, "age_11": 1, "nat_2": 1, "sta_1": 1, "prc_2": 1 , "ncd_1": 1, "icb_47": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 10, 'region': 3, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
    Data(**{'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9380', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"tot_1":1, "gen_2": 1, "age_5": 1, "age_11": 1, "nat_1": 1, "sta_2": 1, "prc_3": 1, "icb_54": 1}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 11, 'region': 3, 'country': 1, 'date': datetime.datetime(year, 4, 30, 23, 54, 16, 49059)}),
]

epi_monitoring = [

    Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {'alert': 1, 'ale_1':'1' ,'cmd_43': 1,'cmd_48': 1, 'epi_1': 1, 'epi_2': 1, 'epi_3': 1, 'epi_4': 1, 'epi_5': 1, 'epi_6': 1, 'epi_7': 1,'icd_1': 1, 'icd_113': 1, 'icd_168': 1, 'icd_17': 1, 'icd_188': 1, 'icd_2189': 1, 'icd_2194': 1, 'icd_321': 1, 'icd_35': 1, 'icd_380': 1, 'icd_391': 1, 'icd_4177': 1, 'icd_4183': 1, 'icd_421': 1, 'icd_461': 1, 'icd_488': 1, 'icd_530': 1, 'icd_68': 1, 'icd_804': 1, 'icd_91': 1, 'icd_9225': 1, 'icd_9643': 1, 'reg_4': 1, 'mat_0': 1, 'mat_1': 1, 'mat_2': 1, 'mat_3': 1, 'mat_4': 1, 'mat_5': 1, 'mat_6': 1, 'mat_7': 1, 'mat_8': 1, 'mat_9': 1, 'dea_0': 1, 'dea_1': 1, 'dea_2': 1, 'dea_3': 1, 'dea_4': 1, 'dea_5': 1, 'dea_6': 1, 'dea_7': 1, 'dea_8': 1, 'dea_9': 1, 'mor_1':1, 'mor_2':1, 'mor_3':1, 'mor_4':1, 'mor_5':1, 'mor_6':1, 'mor_7':1, 'mor_8':1, 'mor_9':1, 'mor_10':1, 'mor_11':1, 'mor_12':1, 'mor_13':1, 'mor_14':1, 'mor_15':1, 'mor_16':1, 'mor_17':1, 'mor_18':1, 'mor_19':1, 'mor_20':1, 'mor_21':1, 'mor_22':1, 'mor_23':1, 'mor_24':1, 'mor_25':1, 'mor_26':1, 'mor_27':1}, 'geolocation': '0,0', 'uuid': 'uuid:fe301f1b-c541-4dde-a355-1552b03e6b7f', 'country': 1, 'id': 1001}),

        Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {'alert': 1, "ale_1": 1, 'cmd_43': 1,'cmd_48': 1, 'epi_1': 1, 'epi_2': 1, 'epi_3': 1, 'epi_4': 1, 'epi_5': 1, 'epi_6': 1, 'epi_7': 1, 'icd_1': 1, 'icd_113': 1, 'icd_168': 1, 'icd_17': 1, 'icd_188': 1, 'icd_2189': 1, 'icd_2194': 1, 'icd_321': 1, 'icd_35': 1, 'icd_380': 1, 'icd_391': 1, 'icd_4177': 1, 'icd_4183': 1, 'icd_421': 1, 'icd_461': 1, 'icd_488': 1, 'icd_530': 1, 'icd_68': 1, 'icd_804': 1, 'icd_91': 1, 'icd_9225': 1, 'icd_9643': 1, 'reg_4': 1, 'mat_0': 1, 'mat_1': 1, 'mat_2': 1, 'mat_3': 1, 'mat_4': 1, 'mat_5': 1, 'mat_6': 1, 'mat_7': 1, 'mat_8': 1, 'mat_9': 1, 'dea_0': 1, 'dea_1': 1, 'dea_2': 1, 'dea_3': 1, 'dea_4': 1, 'dea_5': 1, 'dea_6': 1, 'dea_7': 1, 'dea_8': 1, 'dea_9': 1, 'mor_1':1, 'mor_2':1, 'mor_3':1, 'mor_4':1, 'mor_5':1, 'mor_6':1, 'mor_7':1, 'mor_8':1, 'mor_9':1, 'mor_10':1, 'mor_11':1, 'mor_12':1, 'mor_13':1, 'mor_14':1, 'mor_15':1, 'mor_16':1, 'mor_17':1, 'mor_18':1, 'mor_19':1, 'mor_20':1, 'mor_21':1, 'mor_22':1, 'mor_23':1, 'mor_24':1, 'mor_25':1, 'mor_26':1, 'mor_27':1}, 'geolocation': '0,0', 'uuid': 'uuid:fe301f1b-c541-4dde-a355-1552b03e6b79', 'country': 1, 'id': 1002}),

]

malaria = [

    Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_1": 1, "mls_10": 1, "mls_11": 1, "mls_12": 1, "mls_13": 1, "mls_14": 1, "mls_15": 1, "mls_16": 1, "mls_17": 1, "mls_18": 1, "mls_19": 1, "mls_2": 1, "mls_20": 1, "mls_21": 1, "mls_22": 1, "mls_23": 1, "mls_24": 1, "mls_25": 1, "mls_26": 1, "mls_27": 1, "mls_28": 1, "mls_29": 1, "mls_3": 1, "mls_30": 1, "mls_31": 1, "mls_32": 1, "mls_33": 1, "mls_34": 1, "mls_35": 1, "mls_36": 1, "mls_37": 1, "mls_38": 1, "mls_39": 1, "mls_4": 1, "mls_40": 1, "mls_41": 1, "mls_42": 1, "mls_43": 1, "mls_44": 1, "mls_45": 1, "mls_46": 1, "mls_47": 1, "mls_48": 1, "mls_49": 1, "mls_5": 1, "mls_50": 1, "mls_51": 1, "mls_52": 1, "mls_6": 1, "mls_7": 1, "mls_8": 1, "mls_9": 1, "mlp_1": 1, "mlp_2": 1, "mlp_3": 1, "mlp_4": 1, "mlp_5": 1, "mlp_6": 1, "mlp_7": 1, "mlp_8": 1, "mlp_9": 1}, 'geolocation': '0,0', 'uuid': 'uuid:fe301f1b-c541-4dde-a355-1552b03e6b7f', 'country': 1, 'id': 1001}),

        Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_1": 1, "mls_10": 1, "mls_11": 1, "mls_12": 1, "mls_13": 1, "mls_14": 1, "mls_15": 1, "mls_16": 1, "mls_17": 1, "mls_18": 1, "mls_19": 1, "mls_2": 1, "mls_20": 1, "mls_21": 1, "mls_22": 1, "mls_23": 1, "mls_24": 1, "mls_25": 1, "mls_26": 1, "mls_27": 1, "mls_28": 1, "mls_29": 1, "mls_3": 1, "mls_30": 1, "mls_31": 1, "mls_32": 1, "mls_33": 1, "mls_34": 1, "mls_35": 1, "mls_36": 1, "mls_37": 1, "mls_38": 1, "mls_39": 1, "mls_4": 1, "mls_40": 1, "mls_41": 1, "mls_42": 1, "mls_43": 1, "mls_44": 1, "mls_45": 1, "mls_46": 1, "mls_47": 1, "mls_48": 1, "mls_49": 1, "mls_5": 1, "mls_50": 1, "mls_51": 1, "mls_52": 1, "mls_6": 1, "mls_7": 1, "mls_8": 1, "mls_9": 1, "mlp_1": 1, "mlp_2": 1, "mlp_3": 1, "mlp_4": 1, "mlp_5": 1, "mlp_6": 1, "mlp_7": 1, "mlp_8": 1, "mlp_9": 1}, 'geolocation': '0,0', 'uuid': 'uuid:fe301f1b-c541-4dde-a355-1552b03e6b79', 'country': 1, 'id': 1002}),

]


alerts = [

    Data(**{'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9341', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"alert": 1, "alert_id": "ce9341", "alert_reason": "cmd_11", "alert_gender": "female", "alert_age": '33', "ale_1": 1,"ale_2":1, "ale_6": 1, "ale_7": 1}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 1, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    
    Data(**{'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9342', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"alert": 1, "alert_id": "ce93s1", "alert_reason": "cmd_1", "alert_gender": "female", "alert_age": '33'}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 2, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    
    Data(**{'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9343', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"alert": 1, "alert_id": "ce93s1", "alert_reason": "cmd_2", "alert_gender": "female", "alert_age": '33'}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 3, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    
    Data(**{'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9344', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"alert": 1, "alert_id": "ce93s1", "alert_reason": "cmd_2", "alert_gender": "female", "alert_age": '33', "ale_1": 1, "ale_4": 1}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 4, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}) ,
    
    DisregardedData(**{'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9345', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"alert": 1, "alert_id": "ce93s1", "alert_reason": "cmd_11", "alert_gender": "female", "alert_age": '33', "ale_1": 1213, "ale_3": 1}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 5, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}) ,
    
    Data(**{'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9346', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"alert": 1, "alert_id": "ce93s1", "alert_reason": "cmd_11", "alert_gender": "female", "alert_age": '33', }, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 6, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 3, 4, 23, 54, 16, 49059)}) ,
    
    Data(**{'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9347', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"alert": 1, "alert_id": "ce93s1", "alert_reason": "cmd_11", "alert_gender": "female", "alert_age": '33',}, 'clinic': 7, 'geolocation': '-0.1,0.4', 'id': 7, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}) ,
    
    Data(**{'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9348', 'clinic_type': 'Hospital', 'district': 6, 'variables': {"alert": 1, "alert_id": "ce93s1", "alert_reason": "cmd_19", "alert_gender": "female", "alert_age": '33'}, 'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 8, 'region': 3, 'country': 1, 'date': datetime.datetime(2015, 4, 20, 23, 54, 16, 49059)}) 
]


cd_report = [
    Data(**{"variables":{"alert": 1, "alert_reason": "cmd_11", "ale_1": 1, "ale_2": 1},  'clinic': 7, 'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9341', 'date': datetime.datetime(2015, 5, 1, 0, 0), 'id': '1', 'region': 2}),
    Data(**{"variables":{"alert": 1, "alert_reason": "cmd_11"},  'clinic': 7, 'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9342', 'date': datetime.datetime(2015, 5, 2, 0, 0), 'id': '2', 'region': 2}),
    # Data(**{ "variables":{"alert": 1, "alert_reason": "cmd_11"}, 'clinic': 7, 'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9343', 'date': datetime.datetime(2015, 5, 3, 0, 0), 'id': '3', 'region': 2}),
    Data(**{ "variables":{"alert": 1, "alert_reason": "cmd_11"}, 'clinic': 7, 'uuid': 'uuid:b013c24a-4790-43d6-8b43-4d28a4ce9344', 'date': datetime.datetime(2015, 5, 3, 0, 0), 'id': '4', 'region': 2}),
    Data(**{ "variables":{"alert": 1, "alert_reason": "cmd_1"}, 'clinic': 10, 'uuid': 'uuid:20b2022f-fbe7-43cb-8467-c569397f3f68', 'date': datetime.datetime(2015, 4, 18, 0, 0), 'id': '5', 'region': 2}),
    Data(**{"variables":{"alert": 1, "alert_reason": "cmd_2"}, 'clinic': 7, 'uuid': 'uuid:c51ea7a2-5e2d-4c83-a9a9-85cce0928509', 'date': datetime.datetime(2015, 3, 2, 0, 0), 'id': '6', 'region': 2}),
    Data(**{"variables":{"alert": 1, "alert_reason": "cmd_2"}, 'clinic': 7, 'uuid': 'uuid:c51ea7a2-5e2d-4c83-a9a9-85cce0928510', 'date': datetime.datetime(2015, 5, 2, 0, 0), 'id': '7', 'region': 2}),
    Data(**{"variables":{"alert": 1, "alert_reason": "cmd_19"}, 'clinic': 11, 'uuid': 'uuid:e4e92687-e7e1-4eff-9ec3-4f45421c1e93', 'date': datetime.datetime(2016, 4, 20, 0, 0), 'id': '8', 'region': 3})
]

vaccination_report = [
    Data(**{
        'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9377', 'clinic_type': 'Hospital', 'district': 6,
        "variables":{"vac_ses":0,"vac_pw_vat1":0,"vac_pw_vat2":0,"vac_pw_vat3":0,"vac_pw_vat4":0,"vac_pw_vat5":0,"vac_i0_bcg":0,"vac_i0_vpi":0,"vac_i12_bcg":0,"vac_i0_dtc1":0,"vac_i0_dtc2":0,"vac_i0_dtc3":0,"vac_i0_pcv1":0,"vac_i0_pcv2":0,"vac_i0_pcv3":0,"vac_i12_vpi":0,"vac_i0_vpo0":0,"vac_i0_vpo1":0,"vac_i0_vpo2":0,"vac_i0_vpo3":0,"vac_notpw_vat1":0,"vac_notpw_vat2":0,"vac_notpw_vat3":0,"vac_notpw_vat4":0,"vac_notpw_vat5":0,"vac_i12_dtc1":0,"vac_i12_dtc2":0,"vac_i12_dtc3":0,"vac_i12_pcv1":0,"vac_i12_pcv2":0,"vac_i12_pcv3":0,"vac_i0_rota1":0,"vac_i0_rota2":0,"vac_i0_rota3":0,"vac_i12_vpo0":0,"vac_i12_vpo1":0,"vac_i12_vpo2":0,"vac_i12_vpo3":0,"vac_i12_rota1":0,"vac_i12_rota2":0,"vac_i12_rota3":0
        },'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 1, 'region': 2, 'country': 1, 'date': datetime.datetime(2015, 4, 30, 23, 54, 16, 49059)}),
    Data(**{
        'uuid': 'uuid:2d14ec68-c5b3-47d5-90db-eee510ee9378', 'clinic_type': 'Hospital', 'district': 6,
        "variables":{"vac_ses":1,"vac_pw_vat1":1,"vac_pw_vat2":1,"vac_pw_vat3":1,"vac_pw_vat4":1,"vac_pw_vat5":1,"vac_i0_bcg":1,"vac_i0_vpi":1,"vac_i12_bcg":1,"vac_i0_dtc1":1,"vac_i0_dtc2":1,"vac_i0_dtc3":1,"vac_i0_pcv1":1,"vac_i0_pcv2":1,"vac_i0_pcv3":1,"vac_i12_vpi":1,"vac_i0_vpo0":1,"vac_i0_vpo1":1,"vac_i0_vpo2":1,"vac_i0_vpo3":1,"vac_notpw_vat1":1,"vac_notpw_vat2":1,"vac_notpw_vat3":1,"vac_notpw_vat4":1,"vac_notpw_vat5":1,"vac_i12_dtc1":1,"vac_i12_dtc2":1,"vac_i12_dtc3":1,"vac_i12_pcv1":1,"vac_i12_pcv2":1,"vac_i12_pcv3":1,"vac_i0_rota1":1,"vac_i0_rota2":1,"vac_i0_rota3":1,"vac_i12_vpo0":1,"vac_i12_vpo1":1,"vac_i12_vpo2":1,"vac_i12_vpo3":1,"vac_i12_rota1":1,"vac_i12_rota2":1,"vac_i12_rota3":1
        },'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 2, 'region': 2, 'country': 1, 'date': datetime.datetime(2016, 4, 30, 23, 54, 16, 49059)}),

]

date = datetime.date.today()
start = datetime.datetime(date.year, 1, 1)

offset = date.weekday() - start.weekday()

if offset < 0:
    offset = 7 + offset
completeness = [
    Data(**{'uuid': 'uuid:b59474ed-29e7-490b-a947-558babdf80a1', 'clinic_type': 'Primary', 'district': 4, 'variables': { 'reg_1': 1}, 'clinic': 7, 'geolocation': '0.2,0.2', 'id': 1, 'region': 2, 'country': 1, 'date': date - datetime.timedelta(days=1 + offset)}),
    Data(**{'uuid': 'uuid:b59474ed-29e7-490b-a947-558babdf80a2', 'clinic_type': 'Primary', 'district': 4, 'variables': { 'reg_1': 1}, 'clinic': 7, 'geolocation': '0.2,0.2', 'id': 2, 'region': 2, 'country': 1, 'date': date - datetime.timedelta(days=2 + offset)}),
    Data(**{'uuid': 'uuid:b59474ed-29e7-490b-a947-558babdf80a3', 'clinic_type': 'Primary', 'district': 4, 'variables': { 'reg_1': 1}, 'clinic': 7, 'geolocation': '0.2,0.2', 'id': 3, 'region': 2, 'country': 1, 'date': date - datetime.timedelta(days=3 + offset)}),
    Data(**{'uuid': 'uuid:b59474ed-29e7-490b-a947-558babdf80a4', 'clinic_type': 'Primary', 'district': 4, 'variables': { 'reg_1': 1}, 'clinic': 7, 'geolocation': '0.2,0.2', 'id': 4, 'region': 2, 'country': 1, 'date': date - datetime.timedelta(days=8 + offset)}),
    Data(**{'uuid': 'uuid:b59474ed-29e7-490b-a947-558babdf80a5', 'clinic_type': 'Primary', 'district': 4, 'variables': { 'reg_1': 1}, 'clinic': 8, 'geolocation': '0.2,0.2', 'id': 5, 'region': 2, 'country': 1, 'date': date - datetime.timedelta(days=1 + offset)}),
    Data(**{'uuid': 'uuid:b59474ed-29e7-490b-a947-558babdf80a6', 'clinic_type': 'Primary', 'district': 4, 'variables': { 'reg_1': 1}, 'clinic': 8, 'geolocation': '0.2,0.2', 'id': 6, 'region': 2, 'country': 1, 'date': date - datetime.timedelta(days=1 + offset)}) # Same day should not count,
]
