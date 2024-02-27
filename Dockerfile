FROM python:3.8-buster

RUN apt-get update
WORKDIR /root
COPY requirements.txt /root/requirements.txt
COPY . /root
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]