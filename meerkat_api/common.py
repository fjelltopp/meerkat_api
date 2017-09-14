"""
common.py

Shared functions for meerkat_api.
"""
from flask import abort, current_app
from meerkat_api.authentication import auth
import requests
import json


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
    if(current_app.config['TESTING']):
        return {}
    else:
        api_request = ''.join([current_app.config['INTERNAL_DEVICE_API_ROOT'], url])
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
