from app import app,db
from flask import render_template,flash,redirect,url_for,request,Response
from app.forms import LoginForm, RegistrationForm
from flask_login import logout_user,current_user, login_user,login_required
from werkzeug.urls import url_parse
from app.models import User,Post, CrashLocationPoint, CrashDataPoint
import logging
import json
from ddtrace import patch_all; patch_all(logging=True)
from ddtrace import tracer
from datadog import initialize, statsd
import os

FORMAT = ('%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] '
          '[dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] '
          '- %(message)s')

logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)
log.level = logging.INFO

#options = {
 #   'statsd_host':'127.0.0.1',
  #  'statsd_port':8125
#}

#initialize(**options)
logging.basicConfig()
app.logger.addHandler(logging.StreamHandler())
app.logger.setLevel(logging.INFO)

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
            point.gforce=list[0]
            point.rotation=list[1]
            point.classification=list[2]
            db.session.add(point)
            db.session.commit()


    return Response(status=200, mimetype = 'application/json')

@app.route('/')
@app.route('/index')
@login_required
@tracer.wrap()
def index():
    users = Post.query.all()
    log.info('Index Get')
    return render_template('index.html',title='Home', posts=users)

@app.route('/crashPoint/getAll', methods=['GET'])
@tracer.wrap()
def getAllPoints():
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
 #       statsd.set('point_loop_i', i, tags=["environment:laptop"])
    jdict = json.dumps(dict)
    app.logger.info('crashpoint/getall returned')

    return Response(jdict, status=200, mimetype = 'application/json')


@app.route('/crashPoint/add', methods=['POST'])
#curl  -H "Content-Type: application/json" -d '{"username":"john","latitude":"56.66785675","longitude":"65.4344"}' 127.0.0.1:8000/crashPoint/add

#@login_required
def addCrashLocationPoint():
    point = CrashLocationPoint()
    incoming = request.get_json()
    point.latitude = incoming['latitude']
    point.longitude = incoming['longitude']
    point.user_id = incoming['username']
    db.session.add(point)
    db.session.commit()
    app.logger.info('point created by %s added',point.user_id)

    return Response("{'latitude': incoming['latitude']}", status=200, mimetype = 'application/json')


@app.route('/post/add', methods=['POST'])
# curl  -H "Content-Type: application/json" -d '{"username":"john","body":"whats up, alri"}' 127.0.0.1:8000/post/add
#@login_required
def addPost():
    post = Post()
    incoming = request.get_json()
    post.body = incoming['body']
    post.user_id = incoming['username']
    db.session.add(post)
    db.session.commit()
    app.logger.info('post created by %s added',post.user_id)

    return render_template('post.html',title='Home', post=post)

@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)
