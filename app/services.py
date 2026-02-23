from .models import Order
from datetime import timedelta

def calculate_lead_time():
    orders = Order.query.filter(Order.End.isnot(None)).all()
    if not orders: return 0
    total_time = sum([(o.End - o.Start).total_seconds() for o in orders])
    return total_time / len(orders) / 60  # Retourne en minutes