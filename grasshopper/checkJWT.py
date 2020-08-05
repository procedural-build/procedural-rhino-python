"""Provides a scripting component.
    Inputs:
        reload: bool    - A button input to just expire (reload) this component
        user: User      - An instance of the User class from the login component
        refresh: bool   - Refresh the token
    Output:
        out: str        - stdout/stderr logging
        exp_time: float - Time remaining until the access token expires
        payload: dict   - The contents of the payload of the JWT
"""

__author__ = "mark@procedural.build"
__version__ = "2020.04.07"

import json

if refresh:
    user.refresh_token()

exp_time = user.token_exp_time
payload = json.dumps(user.jwt_payload, indent=4)

print("Token expires in %s seconds" % exp_time)
print(payload)
