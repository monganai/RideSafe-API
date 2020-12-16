FROM python:latest
ENV PYTHONUNBUFFERED 1
ARG FLASK_APP=api.py
ARG FLASK_RUN_PORT=8000
ENV FLASK_APP=${FLASK_APP}
COPY . /code/
WORKDIR /code/app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENTRYPOINT ["flask"]

CMD ["run","--host=0.0.0.0","--port=8080"]
