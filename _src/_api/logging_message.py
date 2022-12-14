import os
from pathlib import Path
from datetime import datetime

def remove_message(path = None):
    os.remove(path) if Path(path).exists() else None
    return None

def input_message(path = None, message = None):
    now = str(datetime.now())[0:19]
    f = open(path,'a')
    f.write(now+' '+message+'\n')
    f.close()
    return None