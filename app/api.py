from app import app,db
from ddtrace import patch_all,tracer
import logging
patch_all()

tracer.configure(
    hostname='datadog-agent',
    port=8126,
)

from app.models import User, Post

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'CrashLocationPoint' : CrashLocationPoint}
