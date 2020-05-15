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

# Global config - Tracer
config.trace_headers([
    'user-agent', 
    'transfer-encoding', 
])

# ############ Log Configuration ########################

FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.trace_id = %(dd.trace_id)s dd.span_id = %(dd.span_id)s] '
          '- %(message)s')

logging.basicConfig(format = FORMAT)
log = logging.getLogger(__name__)
log.level = logging.INFO
logging.basicConfig()
app.logger.addHandler(logging.StreamHandler())
app.logger.setLevel(logging.INFO)

# ############## User Interface Endpoints #####################

# Index page
@app.route('/')
@app.route('/index')
# @login_required
@tracer.wrap()
def index():
    API_KEY = os.environ["DD_PROFILING_API_KEY"]
    clientToken = os.environ["DD_CLIENT_TOKEN"]
    applicationId = os.environ["DD_APPLICATION_ID"]
    
    
    
    return render_template('index.html', title = 'Home', applicationId = applicationId, clientToken = clientToken)


@app.route('/gallery')
@tracer.wrap()
def gallery():
    log.info('Gallery Accessed')
    return render_template('gallery.html', title = 'App Gallery')



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


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

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

# ################### charts ##################################

@app.route("/line_chart")
def line_chart():
    clientToken = os.environ["DD_CLIENT_TOKEN"]
    applicationId = os.environ["DD_APPLICATION_ID"]
    legend = 'Temperatures'
    temperatures = [73.7, 73.4, 73.8, 72.8, 68.7, 65.2, 
                    61.8, 58.7, 58.2, 58.3, 60.5, 65.7, 
                    70.2, 71.4, 71.2, 70.9, 71.3, 71.1]
    times = ['12:00PM', '12:10PM', '12:20PM', '12:30PM', '12:40PM', '12:50PM', 
             '1:00PM', '1:10PM', '1:20PM', '1:30PM', '1:40PM', '1:50PM', 
             '2:00PM', '2:10PM', '2:20PM', '2:30PM', '2:40PM', '2:50PM']
    return render_template('line_chart.html', values = temperatures, labels = times, legend = legend, applicationId = applicationId, clientToken = clientToken)


@app.route("/chart")
def chart():
    clientToken = os.environ["DD_CLIENT_TOKEN"]
    applicationId = os.environ["DD_APPLICATION_ID"]
    glist = []
    rlist = []
    points = CrashLocationPoint.query.all()
    for point in points:
        glist.append(point.gforce)
        rlist.append(point.longitude)
    legend = 'Gforce vs Rotation'

    return render_template('line_chart.html', values = glist, labels = rlist, legend = legend, applicationId = applicationId, clientToken = clientToken)


# ################## API Endpoints #############################


# Load training Data into Database
@app.route('/loadtd')
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
    try:
        host = os.environ["DD_AGENT_HOST"]
        redis_port = 30001
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

    dict = {}
    i = 0
    s1 = 'latitude '
    s2 = 'longitude '
    points = CrashLocationPoint.query.all()
    for point in points:
        lat = point.latitude
        long = point.longitude
        #print(lat)
        t1 = s1 + str(i)
        t2 = s2 + str(i)
        dict[t1] = lat
        dict[t2] = long
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
        lat = point.latitude
        long = point.longitude
        #print(lat)
        t1 = s1 + str(i)
        t2 = s2 + str(i)
        dict[t1] = lat
        dict[t2] = long
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
    app.logger.info('point created by %s added', point.user_id)

    return Response("{'latitude': incoming['latitude']}", status = 200, mimetype = 'application/json')




