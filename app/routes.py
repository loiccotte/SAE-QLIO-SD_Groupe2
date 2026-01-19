from flask import Blueprint, render_template
from .services import calculate_lead_time

bp = Blueprint('main', __name__)

@app.route('/')
def index():
    lt = calculate_lead_time()
    return render_template('index.html', lead_time=round(lt, 2))