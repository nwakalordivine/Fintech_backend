import requests
import base64
from django.conf import settings

def get_monnify_token():
    api_key = settings.MONNIFY_API_KEY
    secret_key = settings.MONNIFY_SECRET_KEY
    auth_str = f"{api_key}:{secret_key}".encode()
    encoded = base64.b64encode(auth_str).decode()

    headers = {"Authorization": f"Basic {encoded}"}
    res = requests.post(f"{settings.MONNIFY_BASE_URL}api/v1/auth/login", headers=headers)

    if res.status_code == 200:
        return res.json()['responseBody']['accessToken']
    else:
        raise Exception("Failed to authenticate with Monnify: " + res.text)


def get_bank_code(bank_name):
    access_token = get_monnify_token()
    if not access_token:
        return None

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(f"{settings.MONNIFY_BASE_URL}api/v1/banks", headers=headers)
    if response.status_code == 200:
        for bank in response.json().get("responseBody", []):
            if bank_name.lower() == bank["name"].lower():
                print(f"Bank code for {bank_name}: {bank['code']}")
                return bank["code"]
    return None

def initiate_transfer(amount, reference, bank_name, description, destination, bank_code):
    payload = {
        "amount": float(amount),
        "reference": reference,
        "narration": description,
        "destinationBankCode": bank_code,
        "destinationAccountNumber": destination,
        "currency": "NGN",
        "sourceAccountNumber": '5576981465',
        "destinationAccountName": bank_name
    }

    access_token = get_monnify_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{settings.MONNIFY_BASE_URL}api/v2/disbursements/single",
        json=payload,
        headers=headers
    )
    print(response.json())
    return response