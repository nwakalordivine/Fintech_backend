import requests
import base64
from django.conf import settings

def get_monnify_token():
    api_key = settings.MONNIFY_API_KEY
    secret_key = settings.MONNIFY_SECRET_KEY
    auth_str = f"{api_key}:{secret_key}".encode()
    encoded = base64.b64encode(auth_str).decode()

    headers = {"Authorization": f"Basic {encoded}"}
    res = requests.post("https://sandbox.monnify.com/api/v1/auth/login", headers=headers)

    if res.status_code == 200:
        return res.json()['responseBody']['accessToken']
    else:
        raise Exception("Failed to authenticate with Monnify: " + res.text)
