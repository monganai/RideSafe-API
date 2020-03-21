from app import app,db
from ddtrace import patch_all,tracer
import logging
import os
from app.models import User, Post

patch_all()

#tracer.configure(
#Docker tracer configuration
 #   hostname='datadog-agent',
  #  port=8126,

#kubernetes tracer configuration.
    #hostname=os.environ['DD_AGENT_HOST'],
    #port=os.environ['DD_TRACE_AGENT_PORT'],
#)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'CrashLocationPoint' : CrashLocationPoint, 'CrashDataPoint' : CrashDataPoint}
