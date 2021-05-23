from flask import Flask, render_template, url_for, flash, redirect, request
from forms import BookingForm
from flask_mqtt import Mqtt
import redis
import json
import time
import sys

# Initialize flask server
app = Flask(__name__)
app.config['SECRET_KEY'] = '8fd4b5b09d72052a2ef9e200dc3a990e'
app.config['MQTT_BROKER_URL'] = '192.168.178.17'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 60
app.config['MQTT_TLS_ENABLED'] = False

# Initialize redis database
cache = redis.Redis(host='redis', port=6379, charset="utf-8", decode_responses=True)

# Initialize mqtt client
mqtt = Mqtt(app)

# Default page
@app.route('/', methods=['GET', 'POST'])
def home():
    form = BookingForm()
    bookings = get_bookings()
    if request.method == 'POST':
        if form.validate_on_submit():
            set_bookings(form)
            mqtt.publish('booking/new', json.dumps(format_input_data(form)))
            flash(f'Reservation submitted for {form.firstname.data} {form.lastname.data}.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid input. Look below for more information.', 'danger')
    return render_template('home.html', bookings=bookings, form=form)

def get_bookings():
    weeks = []
    for week in range(7):
        slots = []
        for slot in range(4):
            value = cache.get(f'week-{week}-slot-{slot}')
            if value is None:
                value = 0
            slots.append(10 - int(value))
        weeks.append(slots)
    return weeks

def set_bookings(form):
    bookings = format_table(form)
    for booking in bookings:
        try:
            cache.incr(f'week-{booking.get("week")}-slot-{booking.get("slot")}')
        except redis.exceptions.ConnectionError as exc:
            raise exc

# Returning formatted form data
def format_input_data(form):
    return {
        "firstname": form.firstname.data,
        "lastname": form.lastname.data,
        "email": form.email.data,
        "bookings": format_table(form)
    }

# Converting table form into booking list
def format_table(form):
    # Put all form data into 2-dimensional array
    table = [
        [form.m1.data, form.m2.data, form.m3.data, form.m4.data],
        [form.t1.data, form.t2.data, form.t3.data, form.t4.data],
        [form.w1.data, form.w2.data, form.w3.data, form.w4.data],
        [form.th1.data, form.th2.data, form.th3.data, form.th4.data],
        [form.f1.data, form.f2.data, form.f3.data, form.f4.data],
        [form.s1.data, form.s2.data, form.s3.data, form.s4.data],
        [form.su1.data, form.su2.data, form.su3.data, form.su4.data],
    ]
    # iterate over array and push booked entries on list
    bookings = []
    for week_index, week in enumerate(table):
        for slot_index, slot in enumerate(week):
            if slot == True:
                bookings.append({
                    "week": week_index,
                    "slot": slot_index
                })
    return bookings
