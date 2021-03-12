FROM python:3.9-alpine

RUN apk update && \
    apk upgrade && \
    apk add --update ca-certificates && \
    apk add chromium --update-cache && \
    rm -fr /var/cache/apk/*


RUN pip install pipenv
COPY Pipfile* ./
RUN pipenv install 

COPY main.py /
COPY config.json queries.json /

CMD [ "pipenv", "run", "python", "main.py"]
