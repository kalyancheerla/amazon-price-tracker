#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import argparse
import json
import random

def get_parser():
    description='A simple price tracker app which scrapes the amazon website \
                 for price drop or availability and sends a quick message \
                 using discord webhooks'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('settings_file', type=argparse.FileType('r'),
                        help='Load JSON settings file')
    return parser

def get_product_details(headers, url):
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')
    title = soup.find(id='productTitle').get_text().strip()
    try:
        price = soup.find(id='priceblock_ourprice').get_text().strip()
    except:
        price = "Out of stock"
    return (title, price)

def convert_price_to_int(price):
    currency_symbols = ['₹', '$', '€', '£', '¥', 'HK$', '¥', ',']
    for i in currency_symbols:
        price = price.replace(i, '')
    return int(float(price))

def get_percent(budget, price):
    return (((price - budget)/budget) * 100)

def build_percent_msg(percent):
    message = "   ("
    if (percent == 0.0):
        message += "no change"
    elif (percent < 0):
        message += "{:.3f}".format(percent) + "% less"
    else:
        message += "+" + "{:.3f}".format(percent) + "% more"
    message += ")"
    return message

def build_product_msg(title, price, budget):
    message = "\nName: **" + title + "**\nPrice: **" + price
    if (price != "Out of stock"):
        int_price = convert_price_to_int(price)
        percent = get_percent(budget, int_price)
        message += build_percent_msg(percent)
    message += "**\n"
    return message

def post_discord_msg(intros, discord_url, message):
    intro = random.choice(intros)
    msg = {
        "username" : "Price",
        "content": "Hey guys,\nI'm not ready yet.. this is just a test msg!\n"
    }
    msg['content'] = intro + message
    result = requests.post(discord_url, json=msg)
    return result.status_code

def main(args=None):
    message = ""
    # Parse arguments
    parser = get_parser()
    args = parser.parse_args(args)
    # Load JSON settings file
    settings = json.load(args.settings_file)
    # Loop over all the products
    for product in settings['products']:
        title, price = get_product_details(settings['amazon_headers'], product['url'])
        message += build_product_msg(title, price, product['budget'])
    # Post the message to discord
    post_discord_msg(settings['intros'], settings['discord_webhooks'], message)

if __name__ == "__main__":
    main()