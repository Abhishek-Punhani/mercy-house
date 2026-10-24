import json
import os
from pathlib import Path

def clean(value):
    text=json.dumps(value,ensure_ascii=False)
    for name in ('API_KEY','NPC_API_KEY'):
        secret=os.getenv(name,'')
        if secret:text=text.replace(secret,'[REDACTED]')
    return text

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(clean(value)+'\n')

def append_log(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as file:file.write(clean(value)+'\n')

def trim(messages):
    while len(json.dumps(messages))>140000 and len(messages)>4:
        end=3
        while end<len(messages) and messages[end]['role']=='tool':end+=1
        del messages[2:end]
