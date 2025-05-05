import pickle
import requests
import time
import re

def load_obj(filename):
    with open(filename+'.pkl', 'rb') as file:
        loaded_data = pickle.load(file)
        return loaded_data

def save_obj(data,filename):
    with open(filename+'.pkl', 'wb') as file:
        pickle.dump(data, file)

def _get_file(url):
    fname=url.split('/')[-1]
    if 'pdf' in fname:
        folder='../files/pdf_files'
    else:
        folder='../files/raw_files'
    r = requests.get(url, stream=True)
    if 'pdf' in url:
        with open(folder+'/'+fname, 'wb+') as f:
            for chunk in r.iter_content():
                f.write(chunk)
    else:
        if r.status_code == 200:
            with open(folder+'/'+fname, 'wb+') as f:
                f.write(r.raw.read())

