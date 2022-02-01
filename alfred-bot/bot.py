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
from time import sleep

from flatfindr.facebook import Facebook
from flatfindr.logins import LOGINS
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from telegram import ParseMode

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text("Hi!")


def run(update, context):
    """Run the flatfindr script"""
    while True:
        fb = Facebook()
        fb.log_in()
        fb.get_items_links(
            min_price=1_200,
            max_price=1_750,
            min_bedrooms=2,
            lat=45.5254,
            lng=-73.5724,
            radius=2,
            scroll=10,
        )
        ads_to_display = fb.get_items_details(for_alfred=True)
        fb.quit_driver()
        for ad in ads_to_display:
            update.message.reply_text(ad, parse_mode=ParseMode.HTML)
        sleep(random.uniform(25, 35) * 60)


def test(update, context):
    fb = Facebook()
    item_data = {
        "url": "https://www.facebook.com/marketplace/item/296710065762366/",
        "state": "new",
        "published": "2022-01-20",
        "price": 1600,
        "bedrooms": 2,
        "surface": 70,
        "address": "2212 Rue d'Iberville",
        "furnished": "Non meublé",
        "images": [],
        "description": "Superbe 4 1/2 mise \u00e0 neuf, moderne et au go\u00fbt du jour dans le magnifique quartier de Centre-Sud-Ville-Marie. Situ\u00e9 \u00e0 5 minutes \u00e0 pied du parc Lafontaine et multiples \u00e9piceries. Parc pour enfant et chien situ\u00e9e au bout de la rue. Unit\u00e9 disponible pour le 1ER MARS 2022.\nVoici ce que cette unit\u00e9 inclut:\n- 1er \u00e9tage avec entr\u00e9e ind\u00e9pendante \n- 2 chambres ferm\u00e9es (peuvent \u00e9galement servir de bureau)\n- 1 salle de bain enti\u00e8rement r\u00e9nov\u00e9\n- 1 Stationnement int\u00e9rieur avec rangement unique\n- TOUT INCLU: wifi haute vitesse illimit\u00e9 60Mbit/s ind\u00e9pendants, \u00e9lectricit\u00e9\n- Air climatis\u00e9 mural dans la chambre \u00e0 coucher assez fort pour climatiser tout l'appartement\n-Laveuse/S\u00e9cheuse dans la salle de bain avec rangement\n-\u00c9lectrom\u00e9nagers et meubles INCLUS selon ce que vous souhaitez avoir et ne pas avoir\nUne enqu\u00eate de cr\u00e9dit sera requise pour toutes personnes qui voudront faire une application.\nPour plus d'informations, SVP me contacter Patrice-Alain Fran\u00e7ois [hidden information] ou par courriel au [hidden information] ",
    }
    update.message.reply_text(
        fb.item_details_to_html(item_data), parse_mode=ParseMode.HTML
    )


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


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

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("run", run))
    dp.add_handler(CommandHandler("test", test))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

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
