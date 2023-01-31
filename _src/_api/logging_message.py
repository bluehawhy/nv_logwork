import os
from pathlib import Path
from datetime import datetime

def remove_message(path = None):
    os.remove(path) if Path(path).exists() else None
    return None

def input_message(path = None, message = None, settime=True):
    now = str(datetime.now())[0:19]
    f = open(path,'a')
    if settime == True: 
        f.write(now+' '+message+'\n')
    if settime == False:
        f.write(message+'\n')
    f.close()
    return None