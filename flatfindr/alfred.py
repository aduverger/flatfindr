#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import random
import os
import re
from time import sleep

from geopy.geocoders import Nominatim
from flatfindr import facebook
from flatfindr.logins import LOGINS
from telegram import ParseMode, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

LOCATION, RADIUS, MIN_PRICE, MAX_PRICE, MIN_BEDROOMS = range(5)

INFOS = {}


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about its prefered position."""
    update.message.reply_text(
        "Hi! My name is Alfred. I will help you find your next apartment. "
        "Send /cancel to stop talking to me.\n\n"
        "What is the position around which you are looking for an apartment? "
        "Use the `share position` function from Telegram"
    )

    return LOCATION


def location(update: Update, context: CallbackContext) -> int:
    """Stores the location and asks for the radius."""
    user = update.message.from_user
    user_location = update.message.location
    logger.info(
        f"Location of {user.first_name}: {user_location.latitude} / {user_location.longitude}"
    )
    INFOS["lat"] = user_location.latitude
    INFOS["lng"] = user_location.longitude
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(f"{user_location.latitude},{user_location.longitude}")
    update.message.reply_text(
        f"Wooo I love {location.raw.get('address', {}).get('city', 'suburb')}! "
        "What is the radius (in km) around this position?"
    )

    return RADIUS


def radius(update: Update, context: CallbackContext) -> int:
    """Stores the radius and asks for the minimum price."""
    user = update.message.from_user
    radius = re.findall(r"\d+", update.message.text)[0]
    logger.info(f"Radius of {user.first_name}: {radius}")
    INFOS["radius"] = int(radius)
    update.message.reply_text("I see! What is your minimum monthly rent (in $CAD)?")

    return MIN_PRICE


def min_price(update: Update, context: CallbackContext) -> int:
    """Stores the min price and asks for max price."""
    user = update.message.from_user
    min_price = re.findall(r"\d+", update.message.text)[0]
    logger.info(f"min_price of {user.first_name}: {min_price}")
    INFOS["min_price"] = int(min_price)
    update.message.reply_text(
        "Wonderful! Now, what is your maximum monthly rent (in $CAD)?"
    )

    return MAX_PRICE


def max_price(update: Update, context: CallbackContext) -> int:
    """Stores the max price and asks for the min bedrooms."""
    user = update.message.from_user
    max_price = re.findall(r"\d+", update.message.text)[0]
    logger.info(f"max_price of {user.first_name}: {max_price}")
    INFOS["max_price"] = int(max_price)
    update.message.reply_text(
        "Gorgeous! Now, tell me the minimum number of bedrooms you need."
    )

    return MIN_BEDROOMS


def min_bedrooms(update: Update, context: CallbackContext) -> int:
    """Stores the max price and ends the conversation / run the script."""
    user = update.message.from_user
    min_bedrooms = re.findall(r"\d+", update.message.text)[0]
    logger.info(f"min_bedrooms of {user.first_name}: {min_bedrooms}")
    INFOS["min_bedrooms"] = int(min_bedrooms)
    update.message.reply_text("Thank you! Now let me find one flat that match..")

    """Run the flatfindr script for 1 item"""
    ads_to_display = facebook.main(
        headless=True,
        to_html=True,
        min_price=INFOS.get("min_price", 0),
        max_price=INFOS.get("max_price", 5000),
        min_bedrooms=INFOS.get("min_bedrooms", 1),
        lat=INFOS.get("lat", 45.5254),
        lng=INFOS.get("lng", -73.5724),
        radius=INFOS.get("radius", 2),
        scroll=0,
        max_items=1,
    )
    if len(ads_to_display):
        update.message.reply_text(ads_to_display[0], parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text(
            "Unfortunately, there is nothing on the marketplace for now!"
        )

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def run(update, context):
    """Run the flatfindr script"""
    while True:
        ads_to_display = facebook.main(headless=True, to_html=True)
        for ad in ads_to_display:
            update.message.reply_text(ad, parse_mode=ParseMode.HTML)
        sleep(random.uniform(25, 35) * 60)


def test(update, context):
    fb = facebook.Facebook(headless=True)
    fb.quit_driver()
    item_details = {
        "url": "https://www.facebook.com/marketplace/item/296710065762366/",
        "state": "new",
        "published": "2022-01-20",
        "price": 1600,
        "bedrooms": 2,
        "surface": 70,
        "address": "2212 Rue d'Iberville",
        "furnished": "Non meublé",
        "images": [],
        "description": "Superbe 4 1/2 mise \u00e0 neuf, moderne et au go\u00fbt du jour dans le magnifique quartier de Centre-Sud-Ville-Marie.",
    }
    update.message.reply_text(
        fb.item_details_to_html(item_details), parse_mode=ParseMode.HTML
    )


def help(update, context):
    update.message.reply_text(
        "/start - start a custom flat search"
        "/run - run the default flat search for Montréal"
    )


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(LOGINS["telegram"], use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LOCATION: [MessageHandler(Filters.location, location)],
            RADIUS: [MessageHandler(Filters.regex(r"\d+"), radius)],
            MIN_PRICE: [MessageHandler(Filters.regex(r"\d+"), min_price)],
            MAX_PRICE: [MessageHandler(Filters.regex(r"\d+"), max_price)],
            MIN_BEDROOMS: [
                MessageHandler(Filters.regex(r"\d+") & ~Filters.command, min_bedrooms)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("run", run))
    dp.add_handler(CommandHandler("test", test))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == "__main__":
    main()
