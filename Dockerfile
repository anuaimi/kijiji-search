FROM python:3.9-alpine

# install chromium
RUN apk update && apk upgrade && \
    apk add --update ca-certificates && \
    apk add chromium --update-cache && \
    rm -fr /var/cache/apk/*

# install python packages needed
RUN pip install pipenv
COPY Pipfile* ./
RUN pipenv install 

# RUN mkdir /data
# COPY config.json queries.json /data/

# setup main app
COPY main.py /
# COPY config.json queries.json /

CMD [ "pipenv", "run", "python", "main.py"]
