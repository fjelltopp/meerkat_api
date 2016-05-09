from flask import abort, request, current_app
from functools import wraps


def require_api_key(f):
    """
    Decorator to require api key for authentication 
    
    Args: 
        f: flask function
    Returns:
       function: decorated function or abort(401)
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.args.get('api_key') == current_app.config["API_KEY"] or current_app.config["API_KEY"] == "":
            return f(*args, **kwargs)
        else:
            current_app.logger.warning("Unauthorized address trying to use the API: {}".format(request.remote_addr))
            abort(401)
    return decorated
