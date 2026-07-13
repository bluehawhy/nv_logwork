import os
import sys

def callamo(refer_api = "global", *args):
    if refer_api == "global":
        sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
        from _api import loggas, configus
    if refer_api == "local":
        from _src._api import loggas, configus
