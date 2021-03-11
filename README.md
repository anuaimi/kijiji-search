# KIJIJI SEARCH MONITOR

## Overview

This will run a search against Kijiji's websetup every hour and notify you by email if there are any new listings.

## TODO

- if deploy using docker, should be able to put api keys in env variable
- don't send emails for listing that are old
- don't send a ton of emails when a search starts up.  only go back x days
- support multiple searches
- deploy to cloud and see if still works
- run every hour
- monitor (through liveness probe?)
- need some way to make sure it is still working??
  - email log file (errors only) once a day
- providate a way to update search details without a new deploy??

## Setup

```bash
pip install pipenv
pipenv shell
pipenv --venv
# add above to python.pythonPath in .vscode/settings.json
```

To be able to send email, the code needs a MailJet api key and secret. You can set them as environment variables or add them to the config file (see `config-sample.json`)

```bash
export MJ_API_KEY="--api-key--"
export MJ_API_SECRET="--api-secret--"
```

## Build

```bash
docker build -t kijiji-search .
docker run -it -n kijiji-search kijiji-search
# docker kill kijiji-search
# docker rm kijiji-search
```

with secrets

```bash
docker run -it -n kijiji-search -e MJ_API='' -e MJ_SECRET='' kijiji-search
```

<!-- 
individual page
-----
-title in class'itemTitleWrapper' div div h1
- description in class='showMoreWrapper' div div div'itemProp=description'
- page also has itemprop='price' which in <span>
- itemprop='dataPosted'
- itemprop='address'
- itemprop='image' -->
