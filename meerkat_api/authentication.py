from flask import request, current_app
from functools import wraps
from meerkat_libs.auth_client import auth
import logging


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
