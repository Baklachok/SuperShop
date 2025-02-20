import os
import logging
import requests
import random
from django.utils import timezone
from authentication.models import TelNoCode

# Настройка логирования
logger = logging.getLogger(__name__)

def send_sms(phone_number, message):
    api_key = os.getenv('SMS_API_ID')

    if not api_key:
        logger.error("API-ключ для SMS-сервиса отсутствует!")
        return

    url = 'https://sms.ru/sms/send'
    params = {
        'api_id': api_key,
        'to': phone_number,
        'msg': message,
        'json': 1
    }

    try:
        response = requests.get(url, params=params)
        result = response.json()

        if result['status'] == 'OK':
            logger.info(f"SMS успешно отправлено на {phone_number}")
        else:
            logger.error(f"Ошибка отправки SMS на {phone_number}: {result.get('status_text', 'Неизвестная ошибка')}")
    except requests.RequestException as e:
        logger.exception(f"Ошибка при отправке запроса в SMS-сервис: {e}")


def send_verification_code(phone_number):
    code = random.randint(1000, 9999)
    logger.info(f"Начало генерации кода для {phone_number}")

    try:
        db_code = TelNoCode.objects.get(telNo=phone_number)
        logger.info(f"Найден существующий код для {phone_number}: {db_code.code}")
    except TelNoCode.DoesNotExist:
        db_code = TelNoCode.objects.create(code=code, telNo=phone_number)
        logger.info(f"Создан новый код {code} для {phone_number}")

    if db_code.expires > timezone.now():
        logger.warning(f"Старый код для {phone_number} ещё не истёк, создаю новый...")
        db_code.delete()
        db_code = TelNoCode.objects.create(code=code, telNo=phone_number)
        logger.info(f"Создан новый код {code} после удаления старого для {phone_number}")

    db_code.expires = timezone.now() + timezone.timedelta(minutes=5)
    db_code.save()
    logger.info(f"Код {db_code.code} сохранён в БД для {phone_number}, истекает в {db_code.expires}")

    message = f"Ваш код подтверждения: {db_code.code}"
    send_sms(phone_number, message)
