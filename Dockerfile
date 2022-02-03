# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.8-buster

# Install manually all the missing libraries
RUN apt-get update
RUN apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libnss3 lsb-release xdg-utils
RUN apt-get install -y libappindicator1; apt-get -fy install

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .

RUN pip install -e .

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
CMD python3.8 flatfindr/alfred.py --bind :$PORT --workers 1 --threads 4 main:app