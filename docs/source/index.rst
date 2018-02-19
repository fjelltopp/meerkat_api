==================
Meerkat API
==================
Meerkat API gives access to the data processed by meerkat abacus. It is build using flask and communicates with DB setup by Abacus. The main functionality is to aggregate data over time and location and give access to all the variables and locations in the DB. The API provides all the data for Meerkat Frontend and could be accessed by other applications. Access is granted through the meerkat_auth module. 

We use flaskRESTful to create the API and flask-sqlalcemy to access the db

---------------
Structure
---------------

__init__.py: sets up the flask app and all the URLs

authentication.py: Methods for authentication

util/__init__.py: Various utility methods

resources/: Folder containing the following files: 

* locations.py: Location information including a location tree
* variables.py: Access to all the variables used in Abacus
* data.py: Aggregated data over time and locations
* alerts.py: Access to alerts and alert_investigations
* epi_week.py: Calculating epi weeks
* incidence.py: Calculating incidence rates.
* explore.py: Export various data as csv-files
* export_data.py: Gives options to look at cross tables and time-lines of data
* map.py: Mapping different data
* reports.py: Data for specified reports
* completeness.py: Calculating completeness of reporting
* links.py: Retrieve link information
* frontpage.py: High level information
  
----------
Config
----------
The API key needs to specified in a file pointed to by the environmental variable MEERKAT_API_SETTINGS. Authentication is handled by the meerkat_auth module. 

-------------------
API urls
-------------------
.. autoflask:: meerkat_api:app
   :undoc-static:

----------------
Testing
----------------
When new features for the API are developed they should be properly tested. The test are done using the python unittest library. All the tests are in the meerkat_api/test directory. For tests of indivudal function we use data inserted into the database for that specific test. The db_util.py file contains utilities for inserting data from data test_data directory. See the documentation below. We also have some general tests in the __init__.py file. We test that all urls return a 200 status code and that the authentication is set up properly. When adding new url endpoints it is important to make sure that these tests pass. Any arugments to these function needs to be given values that make sense (not nesccesary that all the functions return real results, but all urls should return status code 200). As some endpoints return csv format instead of json we need to handle them differently. Any new endpoints that return a csv format needs to be added to the csv_representations in need_csv_representations.

We also test that authentication is set up properly. We assume that all urls need authentication and the few urls that do not need authentication have to be specified in the urls_without_authentication list in the test_authentication function in __init__.py.

**Functions that are used to test all urls**

.. automodule:: meerkat_api.test
   :members: valid_urls, need_csv_representation



**DB Util**

.. automodule:: meerkat_api.test.db_util
   :members:





      
------------------
Utility Functions
------------------
The most important utility function is thi query_sum function. It counts adds up the value of the variables submitted to it between the start_date and end_date. It can be used to get either an overall total, a weekly breakdown or breakdown by location level. The variables keyword is a list of variables that are required. For the variables that have values other than just 1 or 0, we sum up the values of the first variable in the list. Setting weeks=True gives a breakdown by weeks and setting level=region,district or clinic gives a breakdown by this level.

.. automodule:: meerkat_api.util.data_query
   :members:

Other util functions: 
      
.. automodule:: meerkat_api.util
   :members:

---------------------------
Report Helper Functions
---------------------------
.. automodule:: meerkat_api.resources.reports
   :members: fix_dates, get_disease_types, make_dict, top, get_variable_id, get_variables_category, disease_breakdown, get_latest_category, refugee_disease
