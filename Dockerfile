FROM python:3.9-alpine

RUN pip install pipenv
COPY Pipfile* ./
RUN pipenv install 

WORKDIR .

COPY main.py .
COPY config.json .

CMD [ "pipenv", "run", "python", "main.py"]
