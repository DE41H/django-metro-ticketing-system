from threading import Thread
from functools import wraps
from django.conf import settings
from django.core.mail import send_mail
from stations.utils import calculate_route
from stations.models import Station

def calculate_ticket_price(start: Station, stop: Station) -> float:
    return len(calculate_route(start, stop)) * 10.0

def offload_to_thread(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        
    return wrapper

@offload_to_thread
def send_email(user_email: str, subject: str, message: str):
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user_email],
        fail_silently=True
    )
