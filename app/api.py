from app import app, db
from ddtrace import patch_all, tracer
import logging
import os
from app.models import User

patch_all()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'CrashLocationPoint' : CrashLocationPoint, 'CrashDataPoint' : CrashDataPoint}
