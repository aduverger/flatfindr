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
from time import sleep

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

LOCATION, GENDER, PHOTO, BIO = range(4)

INFOS = {}


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about their gender."""
    update.message.reply_text(
        "Hi! My name is Alfred. I will help you find your next apartment."
        "Send /cancel to stop talking to me.\n\n"
        "What is the position around which you are looking for an apartment?"
        "Use the `share position` function from Telegram"
    )

    return LOCATION


def location(update: Update, context: CallbackContext) -> int:
    """Stores the location and asks for some info about the user."""
    user = update.message.from_user
    user_location = update.message.location
    logger.info(
        f"Location of {user.first_name}: {user_location.latitude} / {user_location.longitude}"
    )
    update.message.reply_text(
        f"Maybe I can visit you sometime ! At last, tell me something about yourself."
    )

    return BIO


def gender(update: Update, context: CallbackContext) -> int:
    """Stores the selected gender and asks for a photo."""
    user = update.message.from_user
    logger.info("Gender of %s: %s", user.first_name, update.message.text)
    INFOS["gender"] = update.message.text
    update.message.reply_text(
        "I see! Please send me a photo of yourself, "
        "so I know what you look like, or send /skip if you don't want to.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return PHOTO


def photo(update: Update, context: CallbackContext) -> int:
    """Stores the photo and asks for a location."""
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    photo_file.download("user_photo.jpg")
    logger.info("Photo of %s: %s", user.first_name, "user_photo.jpg")
    update.message.reply_text(
        "Gorgeous! Now, send me your location please, or send /skip if you don't want to."
    )

    return LOCATION


def skip_photo(update: Update, context: CallbackContext) -> int:
    """Skips the photo and asks for a location."""
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    update.message.reply_text(
        "I bet you look great! Now, send me your location please, or send /skip."
    )

    return LOCATION


def bio(update: Update, context: CallbackContext) -> int:
    """Stores the info about the user and ends the conversation."""
    user = update.message.from_user
    logger.info("Bio of %s: %s", user.first_name, update.message.text)
    update.message.reply_text("Thank you! I hope we can talk again some day.")

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def run_default(update, context):
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


def echo(update, context):
    """Echo the user message."""
    if update.message.text.lower().strip() == "jeffrey":
        update.message.reply_text("Remets nous des glaçons")


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
            PHOTO: [
                MessageHandler(Filters.photo, photo),
                CommandHandler("skip", skip_photo),
            ],
            LOCATION: [MessageHandler(Filters.location, location),],
            BIO: [MessageHandler(Filters.text & ~Filters.command, bio)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    dp.add_handler(conv_handler)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("run_default", run_default))
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
