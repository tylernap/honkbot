FROM python:3.6
COPY . /usr/src/app/
COPY requirements.txt /usr/src/app/
RUN pip3 install -r /usr/src/app/requirements.txt
CMD [ "python3", "/usr/src/app/startup.py" ]
