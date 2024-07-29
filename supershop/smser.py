import os

import requests
import random

from django.utils import timezone

from authentication.models import TelNoCode


def send_sms(phone_number, message):
    api_key = os.getenv('SMS_API_ID')
    url = 'https://sms.ru/sms/send'

    params = {
        'api_id': api_key,
        'to': phone_number,
        'msg': message,
        'json': 1
    }

    response = requests.get(url, params=params)
    result = response.json()

    if result['status'] == 'OK':
        print('SMS успешно отправлено')
    else:
        print('phone_number', phone_number)
        print('Ошибка отправки SMS:', result['status_text'])


def send_verification_code(phone_number):
    code = random.randint(1000, 9999)
    print('phone_number:', phone_number)
    try:
        db_code = TelNoCode.objects.get(telNo=phone_number)
    except TelNoCode.DoesNotExist:
        db_code = TelNoCode.objects.create(code=code, telNo=phone_number)
    print('db_code:', db_code)
    if db_code.expires > timezone.now():
        db_code.delete()
        db_code = TelNoCode.objects.create(code=code, telNo=phone_number)
        print('db_code:', db_code)
        print('vnutri')
    db_code.expires = timezone.now() + timezone.timedelta(minutes=5)
    db_code.save()
    code = db_code.code
    print('saved db_code')
    message = f"Ваш код подтверждения: {code}"
    send_sms(phone_number, message)




