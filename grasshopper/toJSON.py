"""Pretty-print some data
    Inputs:
        data: The data to print
    Output:
        json: The a output variable
"""

__author__ = "mark@procedural.build"
__version__ = "2020.04.07"

import json as jsonlib

print(jsonlib.dumps(data, indent=4))
