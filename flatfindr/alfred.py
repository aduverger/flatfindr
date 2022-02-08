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
import re
import os

from geopy.geocoders import Nominatim
from flatfindr.facebook import Facebook
from flatfindr.logins import LOGINS
from telegram import ParseMode, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
    PicklePersistence,
)


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

LOCATION, RADIUS, MIN_PRICE, MAX_PRICE, MIN_BEDROOMS = range(5)


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
    context.user_data["lat"] = user_location.latitude
    context.user_data["lng"] = user_location.longitude
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(f"{user_location.latitude},{user_location.longitude}")
    update.message.reply_text(
        f"Wooo I love {location.raw.get('address', {}).get('city', location.raw.get('address', {}).get('suburb', 'nowhere'))}! "
        "What is the radius (in km) around this position?"
    )

    return RADIUS


def radius(update: Update, context: CallbackContext) -> int:
    """Stores the radius and asks for the minimum price."""
    user = update.message.from_user
    radius = re.findall(r"\d+", update.message.text)[0]
    logger.info(f"Radius of {user.first_name}: {radius}")
    context.user_data["radius"] = int(radius)
    update.message.reply_text("I see! What is your minimum monthly rent (in $CAD)?")

    return MIN_PRICE


def min_price(update: Update, context: CallbackContext) -> int:
    """Stores the min price and asks for max price."""
    user = update.message.from_user
    min_price = re.findall(r"\d+", update.message.text)[0]
    logger.info(f"min_price of {user.first_name}: {min_price}")
    context.user_data["min_price"] = int(min_price)
    update.message.reply_text(
        "Wonderful! Now, what is your maximum monthly rent (in $CAD)?"
    )

    return MAX_PRICE


def max_price(update: Update, context: CallbackContext) -> int:
    """Stores the max price and asks for the min bedrooms."""
    user = update.message.from_user
    max_price = re.findall(r"\d+", update.message.text)[0]
    logger.info(f"max_price of {user.first_name}: {max_price}")
    context.user_data["max_price"] = int(max_price)
    update.message.reply_text(
        "Gorgeous! Now, tell me the minimum number of bedrooms you need."
    )

    return MIN_BEDROOMS


def min_bedrooms(update: Update, context: CallbackContext) -> int:
    """Stores the max price and ends the conversation / run the script."""
    chat_id = update.message.chat_id
    user = update.message.from_user
    min_bedrooms = re.findall(r"\d+", update.message.text)[0]
    logger.info(f"min_bedrooms of {user.first_name}: {min_bedrooms}")
    context.user_data["min_bedrooms"] = int(min_bedrooms)
    update.message.reply_text(
        "Thank you! 🚀 Launching now the apartment search with these parameters:\n"
        + get_params(context)
        + "\n\nNext time, you can directly run the same search by using /run instead of /start.\n"
        "The active search can be canceled at any time using /stop. Type /help for a list of all commands."
    )
    context.job_queue.run_repeating(
        run_once,
        interval=random.uniform(25, 35) * 60,
        first=1,
        context=chat_id,
        name=str(chat_id),
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
    chat_id = update.message.chat_id
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=(
            "🚀 Launching the apartment search with these parameters:\n"
            + get_params(context)
        ),
    )
    context.job_queue.run_repeating(
        run_once,
        interval=random.uniform(25, 35) * 60,
        first=1,
        context=(context, chat_id),
        name=str(chat_id),
    )


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def stop(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = (
        "Flat search successfully cancelled!"
        if job_removed
        else "You have no active flat search."
    )
    update.message.reply_text(text)


def run_once(context):
    chat_id = context.job.context[1]
    job_context = context.job.context[0]
    ads_to_display = Facebook(headless=True).run(
        to_html=True,
        min_price=job_context.user_data.get("min_price", 1200),
        max_price=job_context.user_data.get("max_price", 1750),
        min_bedrooms=job_context.user_data.get("min_bedrooms", 2),
        lat=job_context.user_data.get("lat", 45.5254),
        lng=job_context.user_data.get("lng", -73.5724),
        radius=job_context.user_data.get("radius", 2),
    )
    for ad in ads_to_display:
        context.bot.send_message(chat_id=chat_id, text=ad, parse_mode=ParseMode.HTML)


def test(update, context):
    fb = Facebook(headless=True)
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
        "description": "Superbe 4 1/2 mise à neuf, moderne et au goût du jour dans le magnifique quartier de Centre-Sud-Ville-Marie.",
    }
    update.message.reply_text(
        fb.item_details_to_html(item_details), parse_mode=ParseMode.HTML
    )


def params(update, context):
    update.message.reply_text(get_params(context))


def get_params(context):
    return (
        f"- Min price: {context.user_data.get('min_price', 1200)} $CAD\n"
        f"- Max price: {context.user_data.get('max_price', 1750)} $CAD\n"
        f"- Min bedrooms: {context.user_data.get('min_bedrooms', 2)}\n"
        f"- Lat, Long: {round(context.user_data.get('lat', 45.5254), 2)}, {round(context.user_data.get('lng', -73.5724), 2)}\n"
        f"- Radius: {context.user_data.get('radius', 2)} km"
    )


def help(update, context):
    update.message.reply_text(
        "/start - set your search parameters\n"
        "/run - run the flat search\n"
        "/stop - stop the current flat search\n"
        "/params - display the current search parameters\n"
        "/test - test the display of a flat ad"
    )


def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("Sorry, I didn't understand that answer.")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    persistence = PicklePersistence(
        filename=os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            os.path.join("raw_data", "alfred"),
        )
    )
    updater = Updater(LOGINS["telegram"], use_context=True, persistence=persistence)

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
            MIN_BEDROOMS: [MessageHandler(Filters.regex(r"\d+"), min_bedrooms)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    dp.add_handler(conv_handler)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("run", run))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("test", test))
    dp.add_handler(CommandHandler("params", params))
    dp.add_handler(MessageHandler(Filters.text | Filters.command, unknown))
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
