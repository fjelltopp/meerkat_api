from flask import abort, request, current_app
from functools import wraps
import authorise as auth

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
        auth.check_auth(['registered'])
        return f(*args, **kwargs)
    return decorated
