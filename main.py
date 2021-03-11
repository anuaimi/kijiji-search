import asyncio
from datetime import datetime
import json
import logging
from string import Template
import os
import sqlite3

from pyppeteer import launch
from mailjet_rest import Client


# desired search
KIJIJI_HOST = "https://kijiji.ca"
DB_NAME = 'kijiji.db'

# queries = [
#     {
#         query: "/b-boat-watercraft/barrie/canoe/k0c29l1700006",
#         param: "?ll=44.327238%2C-80.106186&address=Creemore%2C+ON&radius=100.0"
#     },
#     {
#         query: "",
#         param: ""
#     }
# ]

    
# get logging setup
logging.basicConfig(filename='messages.log', format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)


# load_config reads config file & and environment variables
def load_config():
    data = None
    try:
        with open("config.json") as json_data_file:
            data = json.load(json_data_file)
        # print(data)
    except:
        print("config.json file missing or can't be read")

    # see if environment has some config settings
    api_key = os.getenv('MJ_API_KEY')
    if api_key:
        data['mj_api_key'] = api_key
    api_secret = os.getenv('MJ_API_SECRET')
    if api_secret:
        data['mj_api_secret'] = api_secret

    # see if logging level defined
    if data['logging_level']:
        desired_level = data['logging_level'].upper()
        switcher = {
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
            'WARN' : logging.WARN,
            'ERROR' : logging.ERROR,
            'FATAL' : logging.FATAL
        }        
        logger.setLevel(switcher.get(desired_level))

    logger.info("read settings from config.json")
    return data

# load_config reads config file & and environment variables
def load_queries():
    queries = None
    try:
        with open("queries.json") as json_data_file:
            queries = json.load(json_data_file)
        # print(queries)
        logger.info("loaded " + str(len(queries)) + " queries")
    except:
        logger.error("queries.json file missing or can't be read")
        return None

    # see if environment has some config settings
    if len(queries) == 0:
        logger.warn("queries file has no queries")
        return None

    return queries

# setup_mailjet initializes mailjet object
def setup_mailjet(config):
    if not ('mj_api_key' in config):
        logger.error("MJ_API_KEY not setup in config")
        return None
    if not ('mj_api_secret' in config):
        logger.error("MJ_API_SECRET not setup in config")
        return None
    mailjet = Client(auth=(config['mj_api_key'], config['mj_api_secret']), version='v3.1')

    return mailjet

# setup_db will create sqlite database
def setup_db():

    conn = sqlite3.connect(DB_NAME) 
    cursor = conn.cursor()

    # see if table already exists
    cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='listings' ''')

    #if the count is 1, then table exists
    if cursor.fetchone()[0]!=1 :
        # ok, we need to create the database & table(s)
        logger.info('creating database')
		
        create_table_sql = """
CREATE TABLE listings (
   id INTEGER PRIMARY KEY,
   listing_id VARCHAR(10),
   url VARCHAR(50),
   date_added timestamp
);
"""
        cursor.execute(create_table_sql)
        conn.commit()
        
    conn.close()
    return True

# is_new_listing will check if we have seen that listing before
def is_new_listing( id, url):

    found = False

    conn = sqlite3.connect(DB_NAME) 
    cursor = conn.cursor()

    # see if listing already in db
    query_for_listing_sql = ''' SELECT id FROM 'listings' WHERE listing_id = ?; '''
    cursor.execute( query_for_listing_sql, (id,))
    records = cursor.fetchall()

    # if not, add it
    if len(records) == 0:
        insert_listing_sql = ''' INSERT INTO 'listings' ('listing_id', 'url', 'date_added') VALUES (?,?,?); '''
        data_tuple = ( id, url, datetime.now())
        cursor.execute( insert_listing_sql, data_tuple)
        conn.commit()
        # print("inserted new listing",id)
    else:
        found = True

    conn.close()
    return found

async def get_listing_details(browser, id, url, exclusions):
    # build url 
    full_url = "http://kijiji.ca" + url
    # logger.debug(full_url)

    # use pyppeteer to load page
    page = await browser.newPage()
    await page.goto(full_url,{'waitUntil': 'load'})
    # await page.screenshot({'path': 'listing.png'})

    # extract data we need
    results = await page.evaluate('''() => {

        details = []

        // get listing price
        price = ""
        price_nodes = document.querySelectorAll('[itemProp="price"]')
        if (price_nodes.length > 0) {
            price = price_nodes[0].textContent
        }

        description = ""
        desc_nodes = document.querySelectorAll('[itemProp="description"]')
        if (desc_nodes.length > 0) {
            description = desc_nodes[0].textContent
        }

        title = ""
        title_nodes = document.querySelectorAll('h1[class^="title"]')
        if (title_nodes.length > 0) {
            title = title_nodes[0].textContent
        }

        address = ""
        address_nodes = document.querySelectorAll('[itemProp="address"]')
        if (address_nodes.length > 0) {
            address = address_nodes[0].textContent
        }

        datePosted = ""
        date_nodes = document.querySelectorAll('[itemProp="datePosted"]')
        if (date_nodes.length > 0) {
            datePosted = date_nodes[0].textContent
        }

        //  look for data on page
        items = document.querySelectorAll('[itemProp]')
        for (i= 0; i < items.length; i++) {
            
            // name: ad title
            // datePosted (in div)
            // address (in span)

            // type = items[i].attributes['itemProp'].value
            // details.push(type)
        }
        return {
            title: title,
            price: price,
            description: description,
            address: address,
            datePosted: datePosted,
        }
    }''')

    # print(results['title'])
    # print(results['price'])
    # print(results['description'])


    # see how old it is
    #   datePosted will have one of the following: 'minutes', 'hours', 'day' 'days'

    datePosted = results['datePosted']
    if datePosted.lower().find('days') > 0:
        logger.info("skipping as was posted days ago")
        return
    if datePosted.lower().find('month') > 0:
        logger.info("skipping as was posted over a month ago")
        return

    # see if it include exclusion word in title
    #  'wanted' or 'kayak' in title
    for exclude_str in exclusions:
        title = results['title']
        if title.lower().find(exclude_str) >= 0:
            logger.info("skipping as title has " + exclude_str + " in it")
            return 

    # build message body to include price and clickable link
    kijiji_link = KIJIJI_HOST + url 
    html_template = Template("<div>$price</div><br/><div>$date_posted</div><br/><div>$desc</div><br/><div>$address</div><br/><div><a href='$url'>$url</a></div>")
    html_text = html_template.substitute({ 
                    'price' : results['price'], 
                    'desc' : results['description'], 
                    'url' : kijiji_link,
                    'address' : results['address'],
                    'date_posted': datePosted,
                })

    data = {
        'Messages': [
            {
                "From": {
                    "Email": "athir@nuaimi.com",
                    "Name" : "athir nuaimi"
                },
                "To" : [
                    {
                        "Email": "athir@nuaimi.com",
                        "Name" : "athir nuaimi"
                    }
                ],
                "Subject" : "kijiji: " + results['title'],
                "HTMLPart" : html_text,
            }
        ]
    }
    send_result = mailjet.send.create(data=data)
    if send_result.status_code == 200:
        logger.info("sent email notification")
    else:
        logger.error("could not send email: " + send_result.status_code)
    # print(send_result.status_code)
    # print(send_result.json())

    # page.close()

    # return details to caller
    return

async def search(query_details):

    browser = await launch()
    # browser = await launch(headless=False)
    page = await browser.newPage()
    page.setDefaultNavigationTimeout(60000)    # seconds rather than 30

    kijiji_url = KIJIJI_HOST + query_details['query'] + query_details['parameters']


    # TODO set URL to query_details['query'] and parameters

    # do a search
    await page.goto(kijiji_url, {'waitUntil': 'load'})

    results = await page.evaluate('''() => {

        listings = []

        //  look for class = 'search-item'
        items = document.querySelectorAll('.search-item')
        for (i= 0; i < items.length; i++) {
            
            listing_id = items[i].attributes['data-listing-id'].value
            listing_url = items[i].attributes['data-vip-url'].value

            listing = { id: listing_id, url: listing_url}
            listings.push(listing)
        }
        return {
           listings
        }
    }''')

    # dump results to view
    # print(results['listings'])
    # print(len(results['listings']))

    # go through results and see if any new
    listings = results['listings']
    for listing in listings:
        # print(listing['id'], listing['url'])
        found = is_new_listing(listing['id'], listing['url'])
        if found == False:
            message = "found listing: " + listing['id'] + " (" + listing['url'] + ")"
            logger.info(message)
            await get_listing_details( browser, listing['id'], listing['url'], query_details['exclude'])

    await browser.close()


# START HERE

# read config values
config = load_config()
if config is None:
    exit()

# get searches we need to run
queries = load_queries()
if queries is None:
    exit()

mailjet = setup_mailjet(config)
if mailjet is None:
    exit()

setup_db()


# time to get to work
# ready to search kijiji for what we're looking for

# TODO figure how to deploy to run every x minutes (from config)
# TODO deploy using docker or something else? docker bad if want to change search
#      or do I ssh in and change config file?


# search on kijiji
for query in queries:
    logger.info("starting search for " + query['name'])
    asyncio.get_event_loop().run_until_complete(search(query))
    logger.info("completed search")

