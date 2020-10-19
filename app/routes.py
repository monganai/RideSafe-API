from flask import render_template, flash, redirect, url_for, request, Response
from app.forms import LoginForm, RegistrationForm
from flask_login import logout_user, current_user, login_user, login_required
from werkzeug.urls import url_parse
from app.models import User, CrashLocationPoint, CrashDataPoint
from ddtrace import tracer, config, patch_all; patch_all(logging = True)
from datadog import initialize, statsd
import redis, os, json, logging
from app import app, db
import ddtrace.profiling.auto
from datetime import time
import requests 

# ############## Environment Variables #####################

clientToken = os.environ["DD_CLIENT_TOKEN"]
applicationId = os.environ["DD_APPLICATION_ID"]
host = os.environ["DD_AGENT_HOST"]
redis_port = 30001
tomcat_port = 30002

############# DogStatsD & Tracer Configuration ###############

options = {
    'statsd_host': host,
    'statsd_port':8125
}
initialize(**options)

# Global config - Tracer
config.trace_headers([
    'user-agent', 
    'transfer-encoding', 
])

############## Log Configuration ########################

werkzeug = logging.getLogger('werkzeug')
if len(werkzeug.handlers) == 1:
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
          '- %(message)s')
    werkzeug.handlers[0].setFormatter(formatter)


FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.service=%(dd.service)s dd.env=%(dd.env)s dd.version=%(dd.version)s dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
          '- %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)
log.level = logging.INFO

############ Backend Methods ###############################
@tracer.wrap()
def getCrashDataPoints():
    glist = []
    rlist = []
    points = CrashDataPoint.query.all()
    for point in points:
        glist.append(point.gforce)
        rlist.append(point.rotation)
    statsd.gauge('RideSafe.crashDataCount.gauge', len(glist), tags=["app:flapi"])
    return glist, rlist

@tracer.wrap()
def getCrashLocationPoints():
    latList = []
    longList = []
    points = CrashDataPoint.query.all()
    for point in points:
        latList.append(point.gfo)
        longList.append(point.rotation)
    statsd.gauge('RideSafe.crashLocationCount.gauge', len(latList), tags=["app:flapi"]) 
    return latList, longList


#################### Ui Endpoints ##########################

# Index page
@app.route('/', methods = ['GET'])
@tracer.wrap()
def index(): 
    glist, rlist = getCrashDataPoints()
    return render_template('index.html', title = 'Home', applicationId = applicationId, clientToken = clientToken, glist = glist, rlist = rlist)

# Gallery
@app.route('/gallery', methods = ['GET'])
@tracer.wrap()
def gallery():
    log.info('Gallery Accessed')
    return render_template('gallery.html', title = 'App Gallery', applicationId = applicationId, clientToken = clientToken)

# Login
@app.route('/login', methods = ['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember = form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', title = 'Sign In', form = form)

# Logout
@app.route('/logout', methods = ['GET'])
def logout():
    logout_user()
    return redirect(url_for('index'))

# Register
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username = form.username.data, email = form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title = 'Register', form = form)

##################### charts ##################################

# Line Chart
@app.route("/chart/wip", methods = ['GET'])
def chart():
    glist = []
    rlist = []
    points = CrashLocationPoint.query.all()
    for point in points:
        glist.append(point.gforce)
        rlist.append(point.longitude)
    legend = 'Gforce vs Rotation'

    return render_template('scatter.html', values = glist, labels = rlist, legend = legend, applicationId = applicationId, clientToken = clientToken)


# ################## API Endpoints #############################


# Load training Data into Database
@app.route('/loadtd', methods = ['GET'])
def loadtd():
    CrashDataPoint.query.delete()
    basedir = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(basedir, 'TrainingData.txt')
    with open(filepath) as fp:
        while fp.readline():
            line = fp.readline()
            list = line.split()
            point = CrashDataPoint()
            point.gforce = list[0]
            point.rotation = list[1]
            point.classification = list[2]
            db.session.add(point)
        db.session.commit()

    return Response(status = 200, mimetype = 'application/json')


# Return all crashpoints as JSON - Redis interaction - Not in use 
@app.route('/crashPoint/redis', methods = ['GET'])
@tracer.wrap()
def get_all_pointsre():
    dict = {}
    i = 0
    s1 = 'latitude '
    s2 = 'longitude '
    points = CrashLocationPoint.query.all()
    try:
        r = redis.Redis(host = host, port = redis_port)
        r.set("crashpoint-redis", "working")
        msg = r.keys() 
        log.info('Connection to redis suceeded')
    except Exception as e:
        print(e)
        log.info('Connection to redis failled')
        root_span = tracer.current_root_span()
        root_span.set_tag('error', 'true')
        root_span.set_tag('error.message', 'connection to redis failed')

    for point in points:
        t1 = s1 + str(i)
        t2 = s2 + str(i)
        dict[t1] = point.latitude
        dict[t2] = point.longitude
        i = i + 1
        r.set("key", "value")
        msg = r.get("key") 
    jdict = json.dumps(dict)

    return Response(jdict, status = 200, mimetype = 'application/json')


# Returns all Crashpoints as JSON - RidesafeMTB Application
@app.route('/crashPoint/getAll', methods = ['GET'])
@tracer.wrap()
def get_all_points():
    dict = {}
    i = 0
    s1 = 'latitude '
    s2 = 'longitude '
    points = CrashLocationPoint.query.all()
    for point in points:
        t1 = s1 + str(i)
        t2 = s2 + str(i)
        dict[t1] = point.latitude
        dict[t2] = point.longitude
        i = i + 1
    jdict = json.dumps(dict)

    return Response(jdict, status = 200, mimetype = 'application/json')

# Add a crashpoint to the Database - RidesafeMTB Application
# Example Request: curl  -H "Content-Type: application/json" -d '{"username":"john","latitude":"56.66785675","longitude":"65.4344"}' 127.0.0.1:8000/crashPoint/add

@app.route('/crashPoint/add', methods = ['POST'])
def add_crash_location_point():
    point = CrashLocationPoint()
    incoming = request.get_json()
    point.latitude = incoming['latitude']
    point.longitude = incoming['longitude']
    point.user_id = incoming['username']
    db.session.add(point)
    db.session.commit()
    log.info('point created by %s added', point.user_id)

    return Response("{'latitude': incoming['latitude']}", status = 200, mimetype = 'application/json')

@app.route('/crash/verify', methods = ['POST'])
def verify_crash_point():
    incoming = request.get_json()
    g = incoming['g']
    x = incoming['x']
    y = incoming['y']
    z = incoming['z']
   
    API_ENDPOINT ='http://' + str(host) + ':' + str(tomcat_port) + '/regression/classify'
    # data to be sent to ridesafe-learning
    data = {'g': g, 
            'x': x, 
            'y': y, 
            'z': z } 
    # sending post request and saving response as response object 
    r = requests.post(url = API_ENDPOINT, data = data)   
    # extracting response text  
    reply = r.text 
    status = 'false'
    if(float(reply) > 0.7):
        status = 'true'
    log.info('crash detected status: %s ', status)

    return Response("{'crash status':" + status + "}", status = 200, mimetype = 'application/json')

# Example Request: curl  -H "Content-Type: application/json" -d '{"g": 45,"x": 0.8676,"x":0.7676,"z": 0.77676767}' localhost:30000/crash/verify



