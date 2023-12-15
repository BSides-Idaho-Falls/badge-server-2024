FROM python:3.8-buster

RUN apt-get update
WORKDIR /root
COPY requirements.txt /root/requirements.txt
COPY . /root
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

CMD ["python3", "-u", "main.py"]