FROM python:3.8-buster

RUN apt-get update
WORKDIR /root
COPY requirements.txt /root/requirements.txt
COPY . /root
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# need to figure out multiprocessing for CollectorRegistry() for prometheus
# Need to figure out worker timeouts
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app", "--workers", "8"]

# Supposedly slower but metrics work.
# No timeouts on worker threads either.
# Can process ~20k requests per minute / ~330 requests per second which should be fine
#CMD ["python3", "main.py"]