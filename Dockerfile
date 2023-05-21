# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y \
        w3c-sgml-lib \
        dwdiff \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
#        python3-flask \
#        python3-lxml \
#        python3-roman \
#        python3-cssselect \
#        python3-pip \
#        python3-dev \
#        git \

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
#COPY requirements.txt .
#RUN python -m pip install -r requirements.txt
RUN python -m pip install lxml cssselect roman flask flask-wtf tinycss html5lib
RUN python -m pip install gunicorn

WORKDIR /app
COPY . /app

WORKDIR /app/dchars
RUN python setup.py install --record install.txt

WORKDIR /app
RUN mkdir -p projects temp/uploads

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

WORKDIR /app/wsgi
# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "pptools:app"]
