"""
common.py

Shared functions for meerkat_api.
"""
from datetime import datetime, timedelta
from dateutil.parser import parse
from flask import abort
from meerkat_api import app
import authorise as auth
import requests
import logging
import json
import os


def device_api(url, data, api_key=False, params=None):
    """
    Returns JSON data from API request.
    Args:
        url (str): The Meerkat API url from which data is requested
        api_key (optional bool): Whethe or not we should include the api
        key. Defaults to False.
    Returns:
        dict: A python dictionary formed from the API reponse json string.
    """
    if(app.config['TESTING']):
        return {}
    else:
        api_request = ''.join([app.config['INTERNAL_DEVICE_API_ROOT'], url])
        try:
            if api_key:
                r = requests.post(
                        api_request,
                        headers={
                            'authorization': 'Bearer ' + auth.get_token(),
                            'Content-Type': 'application/json'
                        },
                        params=params,
                        data=data
                    )

            else:
                r = requests.post(
                    api_request,
                    headers={
                        'Content-Type': 'application/json'
                    },
                    params=params,
                    data=data
                )
        except requests.exceptions.RequestException as e:
            abort(500, e)
        try:
            output = r.json()
        except Exception as e:
            abort(500, r)
        return output
