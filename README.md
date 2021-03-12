# KIJIJI SEARCH MONITOR

## Overview

This will run a search against Kijiji's websetup regularly and notify you by email if there are any new listings.  It does this by using pyppeteer (which uses a real browser) and doing the search the same way that a user would.

You need to generate the query yourself in a real browser and copy the results to `queries.json`.  The file can have multiple queries in it and all of them will be run each cycle.

## TODO

- validate that hand built approach works with dockerfile
- make it work locally as well as in docker (which chrome)
  - would this problem go away if not alpine?
- deploy to cloud and see if still works
- docker should store db in underlying filesystem so if stop/start, don't lose
- do we want to backup db?
- ship database and make sure db is shared between containers?
- run every hour
- monitor (through liveness probe?)
- need some way to make sure it is still working??
  - email log file (errors only) once a day
- providate a way to update search details without a new deploy??
  - have config in seperate directory that is shared with base filesystem

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

## Running

with secrets

```bash
export MY_API_KEY=""
export MY_API_SECRET=""
docker run -it -n kijiji-search -e MJ_API=$MJ_API_KEY -e MJ_SECRET=$MY_API_SECRET kijiji-search
```

## Debugging

You can debug docker issues by starting a python container and running the various command in the docker file.  Also you can use the following to debug pyppeteer issues

```python
from pyppeteer.launcher import Launcher
' '.join(Launcher().cmd)
```
