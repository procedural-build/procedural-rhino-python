""" Python code for login component in Grasshopper (Rhino 6) that gets and
maintains a JWT access token.  Requests to `/api/auth-jwt/` returns an
`access` and `refresh` token.  The access token is appended to the header of
each request that is made using the `User.request` method.

The `access` token has a short expiry time (~ 10 minutes) so each request that is
made checks that the access token is still valid and gets a new one using the
`refresh` token as required.

Inputs:
    server: str      - The URL to the compute server [ie. http://compute.procedural.build/]
    username: str    - Login username
    password: str    - Login password

Output:
    out: str         - Stdout/stderr messages
    user: User       - A User class instance that may be used to hit the API in other components
"""

__author__ = "mark@procedural.build"
__version__ = "2020.04.07"

from urllib import urlencode
from collections import OrderedDict
from urllib2 import urlopen, URLError
from urllib2 import Request as BaseRequest
from datetime import datetime
import base64
import json

# Dictionary for globals
from scriptcontext import sticky

# Keep a global cache of responses to POST, PUT, PATCH endpoints so that we can
# use a button to call it once and then still display the response even if the
# component expires when the button toggles off
_RESPONSE_CACHE = {}

# Default urllib2.Request with ironPython only allows GET and POST methods
# This allows all methods PUT, PATCH, DELETE, etc.
class Request(BaseRequest):

    def __init__(self, *args, **kwargs):
        if 'method' in kwargs:
            self._method = kwargs['method']
            del kwargs['method']
        else:
            self._method = None
        return BaseRequest.__init__(self, *args, **kwargs)

    def get_method(self, *args, **kwargs):
        if self._method is not None:
            return self._method
        return BaseRequest.get_method(self, *args, **kwargs)


# Class for handling user login and requests
class User():

    content_header = {"content-type": "application/json"}

    def __init__(self, username, password, host="http://localhost:8001"):
        self.host_url       = host
        self.username       = username
        self.password       = password
        self._access_token   = ""
        self._refresh_token  = ""

    @property
    def token(self):
        return self._access_token

    @property
    def jwt_payload(self):
        if not self._access_token:
            return None
        payload_bytes = self._access_token.split('.')[1].encode('utf8')
        missing_padding = len(payload_bytes) % 4
        if missing_padding:
            payload_bytes += b'=' * (4 - missing_padding)
        payload = json.loads(base64.b64decode(payload_bytes))
        return payload

    @property
    def token_exp_time(self):
        """Seconds remaining until token expiry"""
        payload = self.jwt_payload
        if payload is None:
            return None
        exp_timestamp = payload.get('exp', None)
        if not exp_timestamp:
            raise Exception('Could not get expiry timestamp from JWT token')
        now = datetime.utcnow()
        expiry = datetime.utcfromtimestamp(exp_timestamp)
        return (expiry - now).total_seconds()

    # Some common functions
    @staticmethod
    def geturl(host_url, path):
        host_url = host_url[:-1] if host_url[-1] == "/" else host_url
        return host_url + path

    @staticmethod
    def printJSON(pyObj):
        print(json.dumps(pyObj, indent=4))

    def operation_method(self, operation):
        """ Map an operation (list, read, create, update, partial_update) to
        a corresponding http method
        """
        _operation_map = {
            'list': 'GET',
            'read': 'GET',
            'create': 'POST',
            'update': 'PUT',
            'partial_update': 'PATCH'
        }
        return _operation_map.get(operation, 'GET')

    def headers(self, extra_headers=None):
        header = self.content_header
        if self.token:
            header.update({'Authorization': 'JWT %s'%(self.token)})
        if extra_headers:
            header.update(extra_headers)
        return header

    def clear_tokens(self):
        self._access_token = ""
        self._refresh_token = ""

    def get_token(self):
        self.clear_tokens()
        response_dict = self.request('POST', '/auth-jwt/get/', {'username': self.username, 'password': self.password})
        self._access_token = response_dict.get('access', None)
        self._refresh_token = response_dict.get('refresh', None)
        for token_type in ['access', 'refresh']:
            if response_dict.get(token_type, None) is None:
                raise Exception("Error getting token: %s", self.printJSON(response_dict))
        print("Got new token. Will expire in", self.token_exp_time)
        return self.token

    def refresh_token(self, time_remaining = 20):
        # Check that we have a refresh token first
        if not self._refresh_token:
            return None
        # Check if the current access token is valid
        exp_time = self.token_exp_time
        if exp_time and exp_time > time_remaining:
            print("No refresh required. Token will expire in", exp_time)
            return self.token
        # Do the refresh
        response_dict = self.request('POST', '/auth-jwt/refresh/', {'refresh': self._refresh_token})
        self._access_token = response_dict['access']
        print("Refreshed token. Will expire in", self.token_exp_time)
        return self.token

    def verify_token(self):
        response_dict = self.request('POST', '/auth-jwt/verify/', {'token': self.token})
        self._access_token = response_dict['access']
        return self.token

    def set_cached_response(self, method, url, data):
        print("Setting response cache", (method, url), data)
        self.response_cache[(method, url)] = data

    def get_cached_response(self, method, url):
        url = self.geturl(self.host_url, url)
        return self.response_cache.get((method, url), None)

    @property
    def response_cache(self):
        return _RESPONSE_CACHE

    def request(self, method, url, data=None, params=None, extra_headers=None, sendRaw=False):
        cache_response = False

        # Check if the access token needs refreshing unless we are calling an auth-jwt endpoint
        if not url.startswith('/auth-jwt/'):
            self.refresh_token()

        # Do the full request url
        url = self.geturl(self.host_url, url)
        #print("Sending request to url: %s" % url)

        # Append url parameters to the url
        url_params = urlencode(params) if params else None
        url = url + '?%s'%(url_params) if url_params else url

        # Set the data that should be sent
        if method in ('POST', 'PUT', 'PATCH') and not sendRaw:
            cache_response = True
            # Send POST requst with JSON encoded data
            # Note PUT requests send data as RAW (to handle files)
            orgData = data
            try:
                data = json.dumps(data).encode('utf8')
            except:
                pass

        # Remove data from GET requests (otherwise urllib will conver this to a POST automatically)
        if method == "GET":
            data = None

        # Get the actual request object
        r = Request(url, method=method, data=data, headers=self.headers(extra_headers))
        try:
            response = urlopen(r).read().decode('utf8')
        except URLError as err:
            print(err.code, err)
            response = err.reason  # e.read().decode('utf8')

        # Try to parse the response as JSON, otherwise just return the raw response
        response_data = {}
        try:
            response_data = json.loads(response)
        except:
            response_data = response

        # Cache the response before returning
        if cache_response:
            self.set_cached_response(method, url, response_data)

        return response_data

    def get_or_post(url, post_data):
        objs = self.request('GET', url)
        if not objs:
            print("Creating a new object")
            obj = self.request('POST', url, post_data)
        else:
            print("Found existing object")
            obj = objs[0]
        return obj

# Try to login and return the user object
server = server or "http://localhost:8001"
user = User(username, password, host=server)

# Get an access token for this user
print("User: %s, Token: %s"%(user.username, user.get_token()))
#print("User: %s, Token: ...%s"%(user.username, user.get_token()[-8:]))
