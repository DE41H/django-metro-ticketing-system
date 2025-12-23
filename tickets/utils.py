import random
from decimal import Decimal
from threading import Thread
from functools import wraps
from django.conf import settings
from django.core.mail import send_mail
from stations.utils import calculate_route
from stations.models import Station

def calculate_ticket_price(start: Station, stop: Station) -> Decimal:
    if start == stop:
        return Decimal('0.00')
    path = calculate_route(start, stop)
    length = len(path) - 1
    return Decimal(length) * Decimal(10.0)

def _parallel(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        
    return wrapper

@_parallel
def send_email(user_email: str, subject: str, message: str) -> None:
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=False
    )

def generate_otp() -> str:
    choices = random.choices(range(10), k=6)
    choices = map(str, choices)
    choices = ''.join(choices)
    return choices
