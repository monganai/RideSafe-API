FROM python:3.7

ENV PYTHONUNBUFFERED 1
ARG FLASK_APP=api.py
ARG FLASK_RUN_PORT=8000

ENV FLASK_APP=${FLASK_APP}


COPY . /code/
WORKDIR /code/app

RUN pip install -r requirements.txt


ENTRYPOINT ["flask"]

CMD ["run","--host=0.0.0.0","--port=8080"]

LABEL "com.datadoghq.ad.logs"='[{"source":"Flask", "service": "Flapi" }]'
