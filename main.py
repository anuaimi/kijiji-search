import asyncio
import json
import logging
import os
import sqlite3

from pyppeteer import launch
from mailjet_rest import Client

# desired search
KIJIJI_HOST = "https://kijiji.ca"

QUERY = "/b-boat-watercraft/barrie/canoe/k0c29l1700006"
PARAM = "?ll=44.327238%2C-80.106186&address=Creemore%2C+ON&radius=100.0"

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

URL = KIJIJI_HOST + QUERY + PARAM
    
logging.basicConfig(filename='messages.log', format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger('__name__')
logger.setLevel(logging.INFO)


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

def is_valid_config(config):
    print(config['mj_api_key'])
    if not ('mj_api_key' in config):
        msg = "mailjet api key not set"
        logger.error(msg)
        print(msg)
        return False

    if not ('mj_api_secret' in config):
        msg = "mailjet api secret not set"
        logger.error(msg)
        print(msg)
        return False

    return True

def setup_mailjet(api_key, api_secret):
    if (len(api_key) == 0):
        logger.error("MJ_API_KEY not setup in config")
        return None
    if (len(api_secret) == 0):
        logger.error("MJ_API_SECRET not setup in config")
        return None
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    return mailjet

def setup_db():

    conn = sqlite3.connect("kijiji.db") 
    cursor = conn.cursor()

    cursor.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='listings' ''')

    #if the count is 1, then table exists
    if cursor.fetchone()[0]!=1 :
        logger.info('setting up database')
		
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

def is_new_listing( id, url):

    found = False

    conn = sqlite3.connect("kijiji.db") 
    cursor = conn.cursor()

    # see if listing already in db
    query_for_listing_sql = ''' SELECT id FROM 'listings' WHERE listing_id = ?; '''
    cursor.execute( query_for_listing_sql, (id,))
    records = cursor.fetchall()

    # if not, add it
    # TODO: add timestamp for when added
    if len(records) == 0:
        insert_listing_sql = ''' INSERT INTO 'listings' ('listing_id', 'url') VALUES (?,?); '''
        data_tuple = ( id, url)
        cursor.execute( insert_listing_sql, data_tuple)
        conn.commit()
        # print("inserted new listing",id)
    else:
        found = True

    conn.close()
    return found

async def get_listing_details(browser, id, url):
    # build url 
    full_url = "http://kijiji.ca" + url
    logger.debug(full_url)

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
        title_nodes = document.querySelectorAll('[itemProp="name"]')
        if (title_nodes.length > 0) {
            title = title_nodes[0].textContent
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
        }
    }''')

    # TODO fix title - is prov not title right now

    print(results['title'])
    # print(results['price'])
    # print(results['description'])
    # address
    # posted time
    
    # TODO add clickable link in email
    # TODO build message body to include price and clickable link

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
                "TextPart" : results['description'],
            }
        ]
    }
    send_result = mailjet.send.create(data=data)
    print(send_result.status_code)
    print(send_result.json())

    # page.close()

    # return details to caller
    return True

async def search():
    browser = await launch()
    # browser = await launch(headless=False)
    page = await browser.newPage()
    page.setDefaultNavigationTimeout(60000)    # seconds rather than 30

    # do a search
    await page.goto(URL, {'waitUntil': 'load'})

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
            print("new listing: ", listing['id'], "  ", listing['url'])
            await get_listing_details( browser, listing['id'], listing['url'])

    await browser.close()


# START HERE

# read config values
config = load_config()
if config is None:
    exit()

mailjet = setup_mailjet(config['mj_api_key'], config['mj_api_secret'])
if mailjet is None:
    exit()

setup_db()


exit()

# TODO figure how to deploy to run every x minutes (from config)
# TODO deploy using docker or something else? docker bad if want to change search
#      or do I ssh in and change config file?

# search on kijiji
asyncio.get_event_loop().run_until_complete(search())

logger.info("completed search")