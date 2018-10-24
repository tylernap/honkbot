FROM python:3.6
COPY honkbot /usr/src/app/
RUN ls -al /usr/src/app/
RUN pip3 install -r /usr/src/app/honkbot/requirements.txt && pip3 install boto3
CMD [ "python3", "./honkbot/honkbot.py" ]
