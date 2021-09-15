import requests

# PREDICT_SERVICE_URL = 'http://localhost:8080/2015-03-31/functions/function/invocations'
from config import PREDICT_SERVICE_URL


def process(inputs, params):
    res = requests.post(PREDICT_SERVICE_URL, json={'inputs': inputs, 'params': params}, timeout=120)
    res = res.json()

    return res
