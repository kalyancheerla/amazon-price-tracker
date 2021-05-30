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
        price = -1
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

def build_product_title_msg(title):
    return ("\nName: **" + title + "**")

def build_price_outofstock_msg():
    return ("\nPrice: **Out of stock**\n")

def build_price_normal_msg(price, budget):
    message = "\nPrice: **" + price
    int_price = convert_price_to_int(price)
    percent = get_percent(budget, int_price)
    message += build_percent_msg(percent)
    message += "**\n"
    return message

def build_product_normal_msg(title, price, budget):
    message = build_product_title_msg(title)
    if (price == -1):
        message += build_price_outofstock_msg()
    else:
        message += build_price_normal_msg(price, budget)
    return message

def build_product_onlow_msg(title, price, budget):
    message = ""
    int_price = convert_price_to_int(price)
    if (int_price < budget):
        message += build_product_title_msg(title)
        message += build_price_normal_msg(price, budget)
    return message

def build_product_onhigh_msg(title, price, budget):
    message = ""
    int_price = convert_price_to_int(price)
    if (int_price > budget):
        message += build_product_title_msg(title)
        message += build_price_normal_msg(price, budget)
    return message

def build_product_onchange_msg(title, price, budget):
    message = ""
    int_price = convert_price_to_int(price)
    if (int_price != budget):
        message += build_product_title_msg(title)
        message += build_price_normal_msg(price, budget)
    return message

def build_product_msg(title, price, product):
    try:
        report = product['report']
    except:
        report = "normal"
    if (report == "on_low" and price != -1):
        message = build_product_onlow_msg(title, price, product['budget'])
    elif (report == "on_high" and price != -1):
        message = build_product_onhigh_msg(title, price, product['budget'])
    elif (report == "on_change" and price != -1):
        message = build_product_onchange_msg(title, price, product['budget'])
    else:
        message = build_product_normal_msg(title, price, product['budget'])
    return message

def post_discord_msg(settings, message):
    intro = random.choice(settings['intros'])
    msg = {
        "username" : "price bot",
        "content": "Hey guys,\nI'm not ready yet.. this is just a test msg!\n"
    }
    msg['username'] = settings['botname']
    if (message != ""):
        msg['content'] = intro + message
    else:
        msg['content'] = intro + "Oops! no updates for today."
    result = requests.post(settings['discord_webhooks'], json=msg)
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
        message += build_product_msg(title, price, product)
    # Post the message to discord
    post_discord_msg(settings['discord_setup'], message)

if __name__ == "__main__":
    main()