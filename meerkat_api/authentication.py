from flask import request, current_app, g
from functools import wraps
from meerkat_api.util import is_child
from meerkat_libs.auth_client import Authorise as libs_auth
from meerkat_abacus.util import get_locations
import logging
from meerkat_api import db

allowed_locations_locs = None


def is_allowed_location(location, allowed_location):
    """"
    Returns true if the location is allowed_location

    Args:
        location: location id
        allowed_location: allowed_location
    Returns:
        is_allowed(bool): Is location allowed.

    """
    if location == 1:
        return True
    global allowed_locations_locs
    if allowed_locations_locs is None:
        allowed_locations_locs = get_locations(db.session)
    if is_child(allowed_location, int(location), allowed_locations_locs):
        return True
    return False


# Extend the Authorise object so that we can restrict access to location
class Authorise(libs_auth):
    """
    Extension of the meerkat_libs auth_client Authorise class. We override one
    of its functions so that it works smoothly in meerkat_auth.
    """
    # Override the check_auth method
    def check_auth(self, access, countries, logic='OR'):
        # First check that the user has required access levels.
        libs_auth.check_auth(self, access, countries, logic)

        # Continue by checking if the user has restrcited access to location
        # Cycle through each location restriction level
        # If the restriction level is in the users access, set the allowed loc
        allowed_location = 9999
        for level, loc in current_app.config.get('LOCATION_AUTH', {}).items():
            access = Authorise.check_access(
                [level],
                [current_app.config['COUNTRY']],
                g.payload['acc']
            )
            if access and loc < allowed_location:  # Prioritise small loc id
                allowed_location = loc

        # If no restriction set, then default to the whole country.
        if allowed_location is 9999:
            allowed_location = 1

        # Set the allowed location root in the global request g object
        g.allowed_location = allowed_location


# The extended authorise object used across this flask app to restrict access
auth = Authorise()


def authenticate(f):
    """
    Decorator to require api authentication

    Args:
        f: flask function
    Returns:
       function: decorated function or abort(401)
    """
    @wraps(f)
    def decorated(*args, **kwargs):

        # Load the authentication rule from configs,
        # based on the request url_rule.
        auth_rule = current_app.config['AUTH'].get(
            str(request.path),
            None
            # Default rule when no specific rule
        )
        if not auth_rule:
            auth_rule = current_app.config['AUTH'].get(
                str(request.url_rule),
                current_app.config['AUTH'].get('default', [['BROKEN'], ['']])
                # Default rule when no specific rule
            )
        logging.warning("Url requires access: {}".format(auth_rule))

        auth.check_auth(*auth_rule)

        return f(*args, **kwargs)
    return decorated
