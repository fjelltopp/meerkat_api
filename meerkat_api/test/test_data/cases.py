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
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_1":1}, 'geolocation': '0,0', 'uuid': 'uuid:1', 'country': 1, 'id': 1}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_4":1}, 'geolocation': '0,0', 'uuid': 'uuid:2', 'country': 1, 'id': 2}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_5":1}, 'geolocation': '0,0', 'uuid': 'uuid:3', 'country': 1, 'id': 3}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_6":1}, 'geolocation': '0,0', 'uuid': 'uuid:4', 'country': 1, 'id': 4}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_7":1}, 'geolocation': '0,0', 'uuid': 'uuid:5', 'country': 1, 'id': 5}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_8":1}, 'geolocation': '0,0', 'uuid': 'uuid:6', 'country': 1, 'id': 6}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_9":1}, 'geolocation': '0,0', 'uuid': 'uuid:7', 'country': 1, 'id': 7}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_10":1}, 'geolocation': '0,0', 'uuid': 'uuid:8', 'country': 1, 'id': 8}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_11":1}, 'geolocation': '0,0', 'uuid': 'uuid:9', 'country': 1, 'id': 9}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_12":1}, 'geolocation': '0,0', 'uuid': 'uuid:10', 'country': 1, 'id': 10}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_13":1}, 'geolocation': '0,0', 'uuid': 'uuid:11', 'country': 1, 'id': 11}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_15":1}, 'geolocation': '0,0', 'uuid': 'uuid:12', 'country': 1, 'id': 12}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_16":1}, 'geolocation': '0,0', 'uuid': 'uuid:13', 'country': 1, 'id': 13}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_18":1}, 'geolocation': '0,0', 'uuid': 'uuid:14', 'country': 1, 'id': 14}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_19":1}, 'geolocation': '0,0', 'uuid': 'uuid:15', 'country': 1, 'id': 15}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_20":1}, 'geolocation': '0,0', 'uuid': 'uuid:16', 'country': 1, 'id': 16}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_23":1}, 'geolocation': '0,0', 'uuid': 'uuid:17', 'country': 1, 'id': 17}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_24":1}, 'geolocation': '0,0', 'uuid': 'uuid:18', 'country': 1, 'id': 18}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_25":1}, 'geolocation': '0,0', 'uuid': 'uuid:19', 'country': 1, 'id': 19}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_26":1}, 'geolocation': '0,0', 'uuid': 'uuid:20', 'country': 1, 'id': 20}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_27":1}, 'geolocation': '0,0', 'uuid': 'uuid:21', 'country': 1, 'id': 21}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_28":1}, 'geolocation': '0,0', 'uuid': 'uuid:22', 'country': 1, 'id': 22}),

        Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {'alert': 1, "ale_1": 1, 'cmd_43': 1,'cmd_48': 1, 'epi_1': 1, 'epi_2': 1, 'epi_3': 1, 'epi_4': 1, 'epi_5': 1, 'epi_6': 1, 'epi_7': 1, 'icd_1': 1, 'icd_113': 1, 'icd_168': 1, 'icd_17': 1, 'icd_188': 1, 'icd_2189': 1, 'icd_2194': 1, 'icd_321': 1, 'icd_35': 1, 'icd_380': 1, 'icd_391': 1, 'icd_4177': 1, 'icd_4183': 1, 'icd_421': 1, 'icd_461': 1, 'icd_488': 1, 'icd_530': 1, 'icd_68': 1, 'icd_804': 1, 'icd_91': 1, 'icd_9225': 1, 'icd_9643': 1, 'reg_4': 1, 'mat_0': 1, 'mat_1': 1, 'mat_2': 1, 'mat_3': 1, 'mat_4': 1, 'mat_5': 1, 'mat_6': 1, 'mat_7': 1, 'mat_8': 1, 'mat_9': 1, 'dea_0': 1, 'dea_1': 1, 'dea_2': 1, 'dea_3': 1, 'dea_4': 1, 'dea_5': 1, 'dea_6': 1, 'dea_7': 1, 'dea_8': 1, 'dea_9': 1, 'mor_1':1, 'mor_2':1, 'mor_3':1, 'mor_4':1, 'mor_5':1, 'mor_6':1, 'mor_7':1, 'mor_8':1, 'mor_9':1, 'mor_10':1, 'mor_11':1, 'mor_12':1, 'mor_13':1, 'mor_14':1, 'mor_15':1, 'mor_16':1, 'mor_17':1, 'mor_18':1, 'mor_19':1, 'mor_20':1, 'mor_21':1, 'mor_22':1, 'mor_23':1, 'mor_24':1, 'mor_25':1, 'mor_26':1, 'mor_27':1}, 'geolocation': '0,0', 'uuid': 'uuid:fe301f1b-c541-4dde-a355-1552b03e6b79', 'country': 1, 'id': 1002}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_1":1}, 'geolocation': '0,0', 'uuid': 'uuid:101', 'country': 1, 'id': 101}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_4":1}, 'geolocation': '0,0', 'uuid': 'uuid:102', 'country': 1, 'id': 102}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_5":1}, 'geolocation': '0,0', 'uuid': 'uuid:103', 'country': 1, 'id': 103}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_6":1}, 'geolocation': '0,0', 'uuid': 'uuid:104', 'country': 1, 'id': 104}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_7":1}, 'geolocation': '0,0', 'uuid': 'uuid:105', 'country': 1, 'id': 105}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_8":1}, 'geolocation': '0,0', 'uuid': 'uuid:106', 'country': 1, 'id': 106}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_9":1}, 'geolocation': '0,0', 'uuid': 'uuid:107', 'country': 1, 'id': 107}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_10":1}, 'geolocation': '0,0', 'uuid': 'uuid:108', 'country': 1, 'id': 108}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_11":1}, 'geolocation': '0,0', 'uuid': 'uuid:109', 'country': 1, 'id': 109}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_12":1}, 'geolocation': '0,0', 'uuid': 'uuid:110', 'country': 1, 'id': 110}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_13":1}, 'geolocation': '0,0', 'uuid': 'uuid:111', 'country': 1, 'id': 111}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_15":1}, 'geolocation': '0,0', 'uuid': 'uuid:112', 'country': 1, 'id': 112}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_16":1}, 'geolocation': '0,0', 'uuid': 'uuid:113', 'country': 1, 'id': 113}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_18":1}, 'geolocation': '0,0', 'uuid': 'uuid:114', 'country': 1, 'id': 114}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_19":1}, 'geolocation': '0,0', 'uuid': 'uuid:115', 'country': 1, 'id': 115}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_20":1}, 'geolocation': '0,0', 'uuid': 'uuid:116', 'country': 1, 'id': 116}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_23":1}, 'geolocation': '0,0', 'uuid': 'uuid:117', 'country': 1, 'id': 117}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_24":1}, 'geolocation': '0,0', 'uuid': 'uuid:118', 'country': 1, 'id': 118}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_25":1}, 'geolocation': '0,0', 'uuid': 'uuid:119', 'country': 1, 'id': 119}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_26":1}, 'geolocation': '0,0', 'uuid': 'uuid:120', 'country': 1, 'id': 120}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_27":1}, 'geolocation': '0,0', 'uuid': 'uuid:121', 'country': 1, 'id': 121}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_28":1}, 'geolocation': '0,0', 'uuid': 'uuid:122', 'country': 1, 'id': 122}),

]

malaria = [
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mlp_1": 1}, 'geolocation': '0,0', 'uuid': 'uuid:1', 'country': 1, 'id': 1}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mlp_2": 1}, 'geolocation': '0,0', 'uuid': 'uuid:2', 'country': 1, 'id': 2}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mlp_3": 1}, 'geolocation': '0,0', 'uuid': 'uuid:3', 'country': 1, 'id': 3}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mlp_4": 1}, 'geolocation': '0,0', 'uuid': 'uuid:4', 'country': 1, 'id': 4}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mlp_5": 1}, 'geolocation': '0,0', 'uuid': 'uuid:5', 'country': 1, 'id': 5}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mlp_6": 1}, 'geolocation': '0,0', 'uuid': 'uuid:6', 'country': 1, 'id': 6}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mlp_7": 1}, 'geolocation': '0,0', 'uuid': 'uuid:7', 'country': 1, 'id': 7}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mlp_8": 1}, 'geolocation': '0,0', 'uuid': 'uuid:8', 'country': 1, 'id': 8}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mlp_9": 1}, 'geolocation': '0,0', 'uuid': 'uuid:9', 'country': 1, 'id': 9}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_1": 1}, 'geolocation': '0,0', 'uuid': 'uuid:10', 'country': 1, 'id': 10}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_2": 1}, 'geolocation': '0,0', 'uuid': 'uuid:11', 'country': 1, 'id': 11}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_3": 1}, 'geolocation': '0,0', 'uuid': 'uuid:12', 'country': 1, 'id': 12}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_4": 1}, 'geolocation': '0,0', 'uuid': 'uuid:13', 'country': 1, 'id': 13}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_5": 1}, 'geolocation': '0,0', 'uuid': 'uuid:14', 'country': 1, 'id': 14}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_6": 1}, 'geolocation': '0,0', 'uuid': 'uuid:15', 'country': 1, 'id': 15}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_7": 1}, 'geolocation': '0,0', 'uuid': 'uuid:16', 'country': 1, 'id': 16}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_8": 1}, 'geolocation': '0,0', 'uuid': 'uuid:17', 'country': 1, 'id': 17}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_9": 1}, 'geolocation': '0,0', 'uuid': 'uuid:18', 'country': 1, 'id': 18}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_10": 1}, 'geolocation': '0,0', 'uuid': 'uuid:19', 'country': 1, 'id': 19}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_11": 1}, 'geolocation': '0,0', 'uuid': 'uuid:20', 'country': 1, 'id': 20}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_12": 1}, 'geolocation': '0,0', 'uuid': 'uuid:21', 'country': 1, 'id': 21}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_13": 1}, 'geolocation': '0,0', 'uuid': 'uuid:22', 'country': 1, 'id': 22}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_14": 1}, 'geolocation': '0,0', 'uuid': 'uuid:23', 'country': 1, 'id': 23}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_15": 1}, 'geolocation': '0,0', 'uuid': 'uuid:24', 'country': 1, 'id': 24}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_16": 1}, 'geolocation': '0,0', 'uuid': 'uuid:25', 'country': 1, 'id': 25}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_17": 1}, 'geolocation': '0,0', 'uuid': 'uuid:26', 'country': 1, 'id': 26}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_18": 1}, 'geolocation': '0,0', 'uuid': 'uuid:27', 'country': 1, 'id': 27}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_19": 1}, 'geolocation': '0,0', 'uuid': 'uuid:28', 'country': 1, 'id': 28}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_20": 1}, 'geolocation': '0,0', 'uuid': 'uuid:29', 'country': 1, 'id': 29}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_21": 1}, 'geolocation': '0,0', 'uuid': 'uuid:30', 'country': 1, 'id': 30}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_22": 1}, 'geolocation': '0,0', 'uuid': 'uuid:31', 'country': 1, 'id': 31}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_23": 1}, 'geolocation': '0,0', 'uuid': 'uuid:32', 'country': 1, 'id': 32}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_24": 1}, 'geolocation': '0,0', 'uuid': 'uuid:33', 'country': 1, 'id': 33}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_25": 1}, 'geolocation': '0,0', 'uuid': 'uuid:34', 'country': 1, 'id': 34}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_26": 1}, 'geolocation': '0,0', 'uuid': 'uuid:35', 'country': 1, 'id': 35}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_27": 1}, 'geolocation': '0,0', 'uuid': 'uuid:36', 'country': 1, 'id': 36}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_28": 1}, 'geolocation': '0,0', 'uuid': 'uuid:37', 'country': 1, 'id': 37}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_29": 1}, 'geolocation': '0,0', 'uuid': 'uuid:38', 'country': 1, 'id': 38}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_30": 1}, 'geolocation': '0,0', 'uuid': 'uuid:39', 'country': 1, 'id': 39}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_31": 1}, 'geolocation': '0,0', 'uuid': 'uuid:40', 'country': 1, 'id': 40}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_32": 1}, 'geolocation': '0,0', 'uuid': 'uuid:41', 'country': 1, 'id': 41}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_33": 1}, 'geolocation': '0,0', 'uuid': 'uuid:42', 'country': 1, 'id': 42}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_34": 1}, 'geolocation': '0,0', 'uuid': 'uuid:43', 'country': 1, 'id': 43}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_35": 1}, 'geolocation': '0,0', 'uuid': 'uuid:44', 'country': 1, 'id': 44}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_36": 1}, 'geolocation': '0,0', 'uuid': 'uuid:45', 'country': 1, 'id': 45}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_37": 1}, 'geolocation': '0,0', 'uuid': 'uuid:46', 'country': 1, 'id': 46}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_38": 1}, 'geolocation': '0,0', 'uuid': 'uuid:47', 'country': 1, 'id': 47}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_39": 1}, 'geolocation': '0,0', 'uuid': 'uuid:48', 'country': 1, 'id': 48}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_40": 1}, 'geolocation': '0,0', 'uuid': 'uuid:49', 'country': 1, 'id': 49}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_41": 1}, 'geolocation': '0,0', 'uuid': 'uuid:50', 'country': 1, 'id': 50}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_42": 1}, 'geolocation': '0,0', 'uuid': 'uuid:51', 'country': 1, 'id': 51}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_43": 1}, 'geolocation': '0,0', 'uuid': 'uuid:52', 'country': 1, 'id': 52}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_44": 1}, 'geolocation': '0,0', 'uuid': 'uuid:53', 'country': 1, 'id': 53}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_45": 1}, 'geolocation': '0,0', 'uuid': 'uuid:54', 'country': 1, 'id': 54}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_46": 1}, 'geolocation': '0,0', 'uuid': 'uuid:55', 'country': 1, 'id': 55}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_47": 1}, 'geolocation': '0,0', 'uuid': 'uuid:56', 'country': 1, 'id': 56}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_48": 1}, 'geolocation': '0,0', 'uuid': 'uuid:57', 'country': 1, 'id': 57}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_49": 1}, 'geolocation': '0,0', 'uuid': 'uuid:58', 'country': 1, 'id': 58}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_50": 1}, 'geolocation': '0,0', 'uuid': 'uuid:59', 'country': 1, 'id': 59}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_51": 1}, 'geolocation': '0,0', 'uuid': 'uuid:60', 'country': 1, 'id': 60}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_52": 1}, 'geolocation': '0,0', 'uuid': 'uuid:61', 'country': 1, 'id': 61}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_53": 1}, 'geolocation': '0,0', 'uuid': 'uuid:62', 'country': 1, 'id': 62}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_54": 1}, 'geolocation': '0,0', 'uuid': 'uuid:63', 'country': 1, 'id': 63}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_55": 1}, 'geolocation': '0,0', 'uuid': 'uuid:64', 'country': 1, 'id': 64}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_56": 1}, 'geolocation': '0,0', 'uuid': 'uuid:65', 'country': 1, 'id': 65}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_57": 1}, 'geolocation': '0,0', 'uuid': 'uuid:66', 'country': 1, 'id': 66}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_58": 1}, 'geolocation': '0,0', 'uuid': 'uuid:67', 'country': 1, 'id': 67}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_59": 1}, 'geolocation': '0,0', 'uuid': 'uuid:68', 'country': 1, 'id': 68}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_60": 1}, 'geolocation': '0,0', 'uuid': 'uuid:69', 'country': 1, 'id': 69}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_61": 1}, 'geolocation': '0,0', 'uuid': 'uuid:70', 'country': 1, 'id': 70}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_62": 1}, 'geolocation': '0,0', 'uuid': 'uuid:71', 'country': 1, 'id': 71}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_63": 1}, 'geolocation': '0,0', 'uuid': 'uuid:72', 'country': 1, 'id': 72}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_64": 1}, 'geolocation': '0,0', 'uuid': 'uuid:73', 'country': 1, 'id': 73}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_65": 1}, 'geolocation': '0,0', 'uuid': 'uuid:74', 'country': 1, 'id': 74}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_66": 1}, 'geolocation': '0,0', 'uuid': 'uuid:75', 'country': 1, 'id': 75}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 11, 'variables': {"cmd_17": 1, "mls_67": 1}, 'geolocation': '0,0', 'uuid': 'uuid:76', 'country': 1, 'id': 76}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mlp_1": 1}, 'geolocation': '0,0', 'uuid': 'uuid:77', 'country': 1, 'id': 77}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mlp_2": 1}, 'geolocation': '0,0', 'uuid': 'uuid:78', 'country': 1, 'id': 78}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mlp_3": 1}, 'geolocation': '0,0', 'uuid': 'uuid:79', 'country': 1, 'id': 79}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mlp_4": 1}, 'geolocation': '0,0', 'uuid': 'uuid:80', 'country': 1, 'id': 80}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mlp_5": 1}, 'geolocation': '0,0', 'uuid': 'uuid:81', 'country': 1, 'id': 81}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mlp_6": 1}, 'geolocation': '0,0', 'uuid': 'uuid:82', 'country': 1, 'id': 82}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mlp_7": 1}, 'geolocation': '0,0', 'uuid': 'uuid:83', 'country': 1, 'id': 83}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mlp_8": 1}, 'geolocation': '0,0', 'uuid': 'uuid:84', 'country': 1, 'id': 84}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mlp_9": 1}, 'geolocation': '0,0', 'uuid': 'uuid:85', 'country': 1, 'id': 85}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_1": 1}, 'geolocation': '0,0', 'uuid': 'uuid:86', 'country': 1, 'id': 86}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_2": 1}, 'geolocation': '0,0', 'uuid': 'uuid:87', 'country': 1, 'id': 87}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_3": 1}, 'geolocation': '0,0', 'uuid': 'uuid:88', 'country': 1, 'id': 88}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_4": 1}, 'geolocation': '0,0', 'uuid': 'uuid:89', 'country': 1, 'id': 89}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_5": 1}, 'geolocation': '0,0', 'uuid': 'uuid:90', 'country': 1, 'id': 90}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_6": 1}, 'geolocation': '0,0', 'uuid': 'uuid:91', 'country': 1, 'id': 91}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_7": 1}, 'geolocation': '0,0', 'uuid': 'uuid:92', 'country': 1, 'id': 92}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_8": 1}, 'geolocation': '0,0', 'uuid': 'uuid:93', 'country': 1, 'id': 93}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_9": 1}, 'geolocation': '0,0', 'uuid': 'uuid:94', 'country': 1, 'id': 94}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_10": 1}, 'geolocation': '0,0', 'uuid': 'uuid:95', 'country': 1, 'id': 95}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_11": 1}, 'geolocation': '0,0', 'uuid': 'uuid:96', 'country': 1, 'id': 96}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_12": 1}, 'geolocation': '0,0', 'uuid': 'uuid:97', 'country': 1, 'id': 97}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_13": 1}, 'geolocation': '0,0', 'uuid': 'uuid:98', 'country': 1, 'id': 98}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_14": 1}, 'geolocation': '0,0', 'uuid': 'uuid:99', 'country': 1, 'id': 99}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_15": 1}, 'geolocation': '0,0', 'uuid': 'uuid:100', 'country': 1, 'id': 100}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_16": 1}, 'geolocation': '0,0', 'uuid': 'uuid:101', 'country': 1, 'id': 101}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_17": 1}, 'geolocation': '0,0', 'uuid': 'uuid:102', 'country': 1, 'id': 102}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_18": 1}, 'geolocation': '0,0', 'uuid': 'uuid:103', 'country': 1, 'id': 103}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_19": 1}, 'geolocation': '0,0', 'uuid': 'uuid:104', 'country': 1, 'id': 104}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_20": 1}, 'geolocation': '0,0', 'uuid': 'uuid:105', 'country': 1, 'id': 105}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_21": 1}, 'geolocation': '0,0', 'uuid': 'uuid:106', 'country': 1, 'id': 106}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_22": 1}, 'geolocation': '0,0', 'uuid': 'uuid:107', 'country': 1, 'id': 107}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_23": 1}, 'geolocation': '0,0', 'uuid': 'uuid:108', 'country': 1, 'id': 108}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_24": 1}, 'geolocation': '0,0', 'uuid': 'uuid:109', 'country': 1, 'id': 109}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_25": 1}, 'geolocation': '0,0', 'uuid': 'uuid:110', 'country': 1, 'id': 110}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_26": 1}, 'geolocation': '0,0', 'uuid': 'uuid:111', 'country': 1, 'id': 111}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_27": 1}, 'geolocation': '0,0', 'uuid': 'uuid:112', 'country': 1, 'id': 112}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_28": 1}, 'geolocation': '0,0', 'uuid': 'uuid:113', 'country': 1, 'id': 113}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_29": 1}, 'geolocation': '0,0', 'uuid': 'uuid:114', 'country': 1, 'id': 114}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_30": 1}, 'geolocation': '0,0', 'uuid': 'uuid:115', 'country': 1, 'id': 115}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_31": 1}, 'geolocation': '0,0', 'uuid': 'uuid:116', 'country': 1, 'id': 116}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_32": 1}, 'geolocation': '0,0', 'uuid': 'uuid:117', 'country': 1, 'id': 117}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_33": 1}, 'geolocation': '0,0', 'uuid': 'uuid:118', 'country': 1, 'id': 118}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_34": 1}, 'geolocation': '0,0', 'uuid': 'uuid:119', 'country': 1, 'id': 119}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_35": 1}, 'geolocation': '0,0', 'uuid': 'uuid:120', 'country': 1, 'id': 120}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_36": 1}, 'geolocation': '0,0', 'uuid': 'uuid:121', 'country': 1, 'id': 121}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_37": 1}, 'geolocation': '0,0', 'uuid': 'uuid:122', 'country': 1, 'id': 122}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_38": 1}, 'geolocation': '0,0', 'uuid': 'uuid:123', 'country': 1, 'id': 123}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_39": 1}, 'geolocation': '0,0', 'uuid': 'uuid:124', 'country': 1, 'id': 124}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_40": 1}, 'geolocation': '0,0', 'uuid': 'uuid:125', 'country': 1, 'id': 125}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_41": 1}, 'geolocation': '0,0', 'uuid': 'uuid:126', 'country': 1, 'id': 126}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_42": 1}, 'geolocation': '0,0', 'uuid': 'uuid:127', 'country': 1, 'id': 127}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_43": 1}, 'geolocation': '0,0', 'uuid': 'uuid:128', 'country': 1, 'id': 128}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_44": 1}, 'geolocation': '0,0', 'uuid': 'uuid:129', 'country': 1, 'id': 129}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_45": 1}, 'geolocation': '0,0', 'uuid': 'uuid:130', 'country': 1, 'id': 130}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_46": 1}, 'geolocation': '0,0', 'uuid': 'uuid:131', 'country': 1, 'id': 131}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_47": 1}, 'geolocation': '0,0', 'uuid': 'uuid:132', 'country': 1, 'id': 132}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_48": 1}, 'geolocation': '0,0', 'uuid': 'uuid:133', 'country': 1, 'id': 133}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_49": 1}, 'geolocation': '0,0', 'uuid': 'uuid:134', 'country': 1, 'id': 134}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_50": 1}, 'geolocation': '0,0', 'uuid': 'uuid:135', 'country': 1, 'id': 135}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_51": 1}, 'geolocation': '0,0', 'uuid': 'uuid:136', 'country': 1, 'id': 136}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_52": 1}, 'geolocation': '0,0', 'uuid': 'uuid:137', 'country': 1, 'id': 137}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_53": 1}, 'geolocation': '0,0', 'uuid': 'uuid:138', 'country': 1, 'id': 138}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_54": 1}, 'geolocation': '0,0', 'uuid': 'uuid:139', 'country': 1, 'id': 139}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_55": 1}, 'geolocation': '0,0', 'uuid': 'uuid:140', 'country': 1, 'id': 140}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_56": 1}, 'geolocation': '0,0', 'uuid': 'uuid:141', 'country': 1, 'id': 141}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_57": 1}, 'geolocation': '0,0', 'uuid': 'uuid:142', 'country': 1, 'id': 142}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_58": 1}, 'geolocation': '0,0', 'uuid': 'uuid:143', 'country': 1, 'id': 143}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_59": 1}, 'geolocation': '0,0', 'uuid': 'uuid:144', 'country': 1, 'id': 144}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_60": 1}, 'geolocation': '0,0', 'uuid': 'uuid:145', 'country': 1, 'id': 145}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_61": 1}, 'geolocation': '0,0', 'uuid': 'uuid:146', 'country': 1, 'id': 146}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_62": 1}, 'geolocation': '0,0', 'uuid': 'uuid:147', 'country': 1, 'id': 147}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_63": 1}, 'geolocation': '0,0', 'uuid': 'uuid:148', 'country': 1, 'id': 148}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_64": 1}, 'geolocation': '0,0', 'uuid': 'uuid:149', 'country': 1, 'id': 149}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_65": 1}, 'geolocation': '0,0', 'uuid': 'uuid:150', 'country': 1, 'id': 150}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_66": 1}, 'geolocation': '0,0', 'uuid': 'uuid:151', 'country': 1, 'id': 151}),
Data(**{'date': datetime.datetime(2015, 1, 1, 0, 0), 'clinic_type': 'Hospital', 'district': 6, 'region': 3, 'clinic': 7, 'variables': {"cmd_17": 1, "mls_67": 1}, 'geolocation': '0,0', 'uuid': 'uuid:152', 'country': 1, 'id': 152})]


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
        },'clinic': 11, 'geolocation': '-0.1,0.4', 'id': 2, 'region': 2, 'country': 1, 'date': datetime.datetime(2016, 4, 30, 23, 54, 16, 49059)})

]


#Freeze date of test 24th Dec 2016
#id 1,
#comp_week - completeness in the recent week, 25, only clinic A reported every day.
#clinic_num - 4 health facilities
#!!!comp_year = approx 1.9. In last 51 weeks in total we had completeness 100& only one week.
#dea_0 - reported deaths, it is 7 this week in clinic A.
# dea_0 ale_1 - deaths from community (5)
# cmd_21 - maternal, ale_1 maternal investigated
# cmd_22 - neonatal, ale_1 investigated

afro_report = [
    #completeness, Districts Blue, Red and Green
    Data(**{"id":10,"uuid":"10","type":"case","date":"2016-12-20T00:00:00","country":1,"region":2,"district":4,"clinic":7,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "reg_1":1,
                "reg_5":1
            },"geolocation":"0,0"}),
    Data(**{"id":100,"uuid":"100","type":"case","date":"2016-12-20T00:00:00","country":1,"region":2,"district":4,"clinic":8,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "reg_1":1,
                "reg_5":1
            },"geolocation":"0,0"}),
    Data(**{"id":101,"uuid":"101","type":"case","date":"2016-12-19T00:00:00","country":1,"region":2,"district":5,"clinic":9,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "reg_1":2,
                "reg_5":2
            },"geolocation":"0,0"}),
    # Data(**{"id":102,"uuid":"102","type":"case","date":"2016-12-21T00:00:00","country":1,"region":2,"district":5,"clinic":9,"clinic_type":"test","links":{},"tags":[],
    #         "variables":{
    #             "reg_1":5,
    #             "reg_5":5
    #         },"geolocation":"0,0"}),
    Data(**{"id":11,"uuid":"11","type":"case","date":"2016-11-20T00:00:00","country":1,"region":2,"district":5,"clinic":9,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "reg_1":1,
                "reg_5":1
            },"geolocation":"0,0"}),
    Data(**{"id":12,"uuid":"12","type":"case","date":"2016-12-20T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "reg_1":4,
                "reg_5":4
            },"geolocation":"0,0"}),

    #Completeness in the week after date of the report. Shouldn't change the weekly completeness
    #4 daily registers means that completeness in this week is 100
    Data(**{"id":112,"uuid":"112","type":"case","date":"2016-12-29T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "reg_1":4,
                "reg_5":4
            },"geolocation":"0,0"}),

    #50 deaths and 50 cases of sever malnutrition `dea_0` and `cmd_24` in a week after the report. Shouldn't appear in weekly highlights
    Data(**{"id":113,"uuid":"113","type":"case","date":"2016-12-29T00:00:00","country":1,"region":2,"district":4,"clinic":7,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "dea_0":50,
                "cmd_24":50,
            },"geolocation":"0,0"}),

    #THIS WEEK
    #Clinic A
    #14 deaths (dea_0) in this week, half of them (ale_1) from community
    #21 cases of severe malnutrition `cmd_24` in Region Major and 11 of moderate (`cmd_23`)
    #120 cases of fever (mls_2) and 40 cases tested (mls_3)
    #MALARIA data
    #10 deaths from malaria (mls_36)
    #30 positively tested cases of malaria (cmd_17), it is 30/40 of tested (mls_3)
    #10 simple (mls_12) and 20 sever (mls_24), 15 (mls_48) treated with ACT 
    Data(**{"id":1,"uuid":"1","type":"case","date":"2016-12-20T00:00:00","country":1,"region":2,"district":4,"clinic":7,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "mls_2":120,
                "mls_3":40,
                "mls_12":10,
                "mls_24":20,
                "mls_48":15,
                "dea_0":7,
                "mls_36":10,
                "cmd_17":30
            },"geolocation":"0,0"}),
    Data(**{"id":2,"uuid":"2","type":"case","date":"2016-12-20T00:00:00","country":1,"region":2,"district":4,"clinic":7,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "dea_0":7,
                "ale_1":1
            },"geolocation":"0,0"}),
    Data(**{"id":3,"uuid":"3","type":"case","date":"2016-10-24T00:00:00","country":1,"region":2,"district":4,"clinic":7,"clinic_type":"test","links":{},"tags":[],
            "variables":{

            },"geolocation":"0,0"}),
    #Measles for WEEKLY HIGHLIGHTS
    #125 cases in total (cmd_15)
    #40 suspected but not tested
    #ale_1 investigated (50)
    #ale_2 confirmed (25)
    #age_1 10 among children <5
    Data(**{"id":13,"uuid":"13","type":"case","date":"2016-12-21T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_15":40
            },"geolocation":"0,0"}),
    Data(**{"id":14,"uuid":"14","type":"case","date":"2016-12-21T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_15":10,
                "age_1":1
            },"geolocation":"0,0"}),
    Data(**{"id":15,"uuid":"15","type":"case","date":"2016-12-21T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_15":50,
                "ale_1":1
            },"geolocation":"0,0"}),
    Data(**{"id":16,"uuid":"16","type":"case","date":"2016-12-21T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_15":25,
                "ale_2":1
            },"geolocation":"0,0"}),
    #Acute flaccid paralysis for WEEKLY HIGHLIGHTS
    #99 cases suspected (cmd_10)
    #ale_2 investigated (33) TODO: cofirm it is not ale_1
    Data(**{"id":17,"uuid":"17","type":"case","date":"2016-12-21T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_10":66,
                "mor_11":33
            },"geolocation":"0,0"}),
    Data(**{"id":18,"uuid":"18","type":"case","date":"2016-12-21T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_10":33,
                "ale_2":1
            },"geolocation":"0,0"}),
    #Malnutrition for WEEKLY HIGHLIGHTS
    #severe malnutrition `cmd_24` : 40, moderate `cmd_23`, 20, 40 from Major and 20 from minor
    #major
    Data(**{"id":20,"uuid":"20","type":"case","date":"2016-12-21T00:00:00","country":1,"region":2,"district":4,"clinic":7,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_24":21,
                "cmd_23":19,
            },"geolocation":"0,0"}),
    #minor
    Data(**{"id":21,"uuid":"21","type":"case","date":"2016-12-21T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_24":19,
                "cmd_23":1,
            },"geolocation":"0,0"}),
    #All cases in clinc C,
    # REPORTED only
    #Diarrhoea.
    #15 `cmd_1` acute and `mor_18` 10 deaths
    #22 `cmd_4` bloody (dysentery)
    #12 `cmd_2` watery (cholera)
    #40 cases `cmd_25` ARTI (Acute respiratory tract infection)
    #23 cases `cmd_18`influenza like ilness
    #100 cases `cmd_27` of animal bites
    #20 UNCOMFIRMED cases of Rabies `cmd_11`
    #99 UNCOMFIRMED cases of Plague `cmd_7`
    Data(**{"id":22,"uuid":"22","type":"case","date":"2016-12-22T00:00:00","country":1,"region":2,"district":5,"clinic":9,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_1":15,
                "mor_18":10,
                "cmd_4":22,
                "cmd_2":12,
                "cmd_25":40,
                "cmd_18":23,
                "cmd_27":100,
                "cmd_11":20,
                "cmd_7":99
            },"geolocation":"0,0"}),
    #clinic C cases INVESTIGATED `ale_1`
    #76 investigated cases of Plague `cmd_7` with `ale_1`
    Data(**{"id":23,"uuid":"23","type":"case","date":"2016-12-23T00:00:00","country":1,"region":2,"district":5,"clinic":9,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_7":76,
                "ale_1":1,
            },"geolocation":"0,0"}),

    #clinic C cases CONFIRMED
    #Confirmed Rabies
    #15 confirmed cases of Rabies `cmd_11` with `ale_2`
    #16 confirmed cases of Plague `cmd_7` with `ale_2`
    Data(**{"id":24,"uuid":"24","type":"case","date":"2016-12-21T00:00:00","country":1,"region":2,"district":5,"clinic":9,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_11":15,
                "cmd_7":16,
                "ale_2":1,
            },"geolocation":"0,0"}),

    #Clinic B, District Blue, Region Major.
    #14 Maternal deaths and 10 neonatal NOT investigated
    Data(**{"id":6,"uuid":"6","type":"case","date":"2016-12-24T00:00:00","country":1,"region":2,"district":4,"clinic":8,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_21":14,
                "cmd_22":10,
            },"geolocation":"0,0"}),
    #5 Maternal deaths and 2 neonatal *investigated*
    Data(**{"id":7,"uuid":"7","type":"case","date":"2016-12-24T00:00:00","country":1,"region":2,"district":5,"clinic":9,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_21":5,
                "cmd_22":2,
                "ale_1":1
            },"geolocation":"0,0"}),
    # # 1 maternal death and 1 neonatal investiaged in District Green
    Data(**{"id":70,"uuid":"70","type":"case","date":"2016-12-24T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_21":1,
                "cmd_22":1,
                "ale_1":1
            },"geolocation":"0,0"}),


    #
    #
    # PREVIOUS WEEKS
    # SHOULDN'T be in Weekly Highlights
    #
    #



    #Clinic B, District Blue, Region Major.
    #17 Maternal deaths and 17 neonatal NOT investigated
    Data(**{"id":31,"uuid":"31","type":"case","date":"2016-10-24T00:00:00","country":1,"region":2,"district":4,"clinic":8,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_21":17,
                "cmd_22":17,
            },"geolocation":"0,0"}),

    #Malaria map takes cases of `epi_1` and `epi_2`
    #malaria map by type `mls_12`, `mls_24`, `mls_3`
    #clinic C in region major of population 750
    Data(**{"id":32,"uuid":"32","type":"case","date":"2016-11-20T00:00:00","country":1,"region":2,"district":5,"clinic":9,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "epi_1":7,
                "epi_2":25,
                "mls_12":14,
                "mls_24":22,
                "mls_3":100
            },"geolocation":"0,0"}),
    #clinic D in region minor of population 250
    Data(**{"id":33,"uuid":"33","type":"case","date":"2016-11-24T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "epi_1":25,
                "epi_2":75,
                "mls_12":4,
                "mls_24":2,
                "mls_3":10
            },"geolocation":"0,0"}),

    #Measles over 5 yo
    # 13 cases
    Data(**{"id":34,"uuid":"34","type":"case","date":"2016-11-24T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_15":13,
                "mor_13":5,
                "age_3":1
            },"geolocation":"0,0"}),
    Data(**{"id":35,"uuid":"35","type":"case","date":"2016-11-11T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_15":7,
                "age_5":5
            },"geolocation":"0,0"}),

    #Severe malnutrition under 5yo
    #It is from epi code 8
    # 5 cases in week in September of malnutrition in clinicD
    Data(**{"id":36,"uuid":"36","type":"case","date":"2016-09-11T00:00:00","country":1,"region":3,"district":6,"clinic":10,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "epi_8":5
            },"geolocation":"0,0"}),

    #Table priority diseases cumulative information
    #Acute diarrhoea case from previous week (july) to alter cumulative
    Data(**{"id":37,"uuid":"37","type":"case","date":"2016-07-22T00:00:00","country":1,"region":2,"district":5,"clinic":9,"clinic_type":"test","links":{},"tags":[],
            "variables":{
                "cmd_1":80,
                "mor_18":70,
            },"geolocation":"0,0"}),
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
