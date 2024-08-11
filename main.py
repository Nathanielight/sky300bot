import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up bot token and channel ID
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Define the path to the JSON data store
DATA_STORE = 'data_store.json'

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Function to load data from JSON file
def load_data():
    if not os.path.exists(DATA_STORE):
        return {}
    with open(DATA_STORE, 'r') as file:
        return json.load(file)

# Function to save data to JSON file
def save_data(data):
    with open(DATA_STORE, 'w') as file:
        json.dump(data, file, indent=4)

# Function to check if a user is a member of the channel
async def check_membership(user_id, app):
    try:
        member = await app.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking membership for user {user_id}: {e}")
        return False

# Function to get a referral link for a user
def get_referral_link(user_id):
    base_link = "https://t.me/skyet300kchallengeBot?start="
    return f"{base_link}{user_id}"

# Function to store user data in the JSON file
def store_user_data(user_id, username, first_name):
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {
            'username': username,
            'first_name': first_name,
            'referrals': 0
        }
    save_data(data)
    logger.info(f"Stored data for user {user_id}: {username} ({first_name})")

# Function to increment referral count for a user
def increment_referrals(referrer_id, username, first_name):
    data = load_data()
    if str(referrer_id) in data:
        data[str(referrer_id)]['referrals'] += 1
    else:
        data[str(referrer_id)] = {
            'username': username,
            'first_name': first_name,
            'referrals': 1
        }
    save_data(data)
    logger.info(f"Incremented referrals for referrer {referrer_id}: {username} ({first_name})")

# Function to notify the referrer
async def notify_referrer(context: CallbackContext, referrer_id, new_user_first_name, new_user_username):
    if referrer_id is not None:
         
        message = (f"🎉 እንኳን ደስ አሎት!{new_user_first_name} (@{new_user_username}) "
                   f"በእርሶ ሊንክ ቻናሉን ተቀላቅሏል")
        try:
            await context.bot.send_message(chat_id=int(referrer_id), text=message)
            logger.info(f"Notified referrer {referrer_id} of new referral {new_user_username}")
        except Exception as e:
            logger.error(f"Error sending message to referrer {referrer_id}: {e}")

# Function to get the leaderboard
def get_leaderboard():
    data = load_data()
    leaderboard = [(user_id, details['username'], details['first_name'], details['referrals']) for user_id, details in data.items()]
    leaderboard.sort(key=lambda x: x[3], reverse=True)
    logger.info("Generated leaderboard")
    return leaderboard

# Start command handler
# Start command handler
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username
    first_name = user.first_name

    logger.info(f"User {username} ({first_name}) started the bot")

    # Store user data
    store_user_data(user_id, username, first_name)

    # Check if the user joined via a referral link
    args = context.args
    if args:
        referrer_id = args[0]
        increment_referrals(referrer_id, username, first_name)  # Increment referrer's count
        await notify_referrer(context, referrer_id, first_name, username)

    if await check_membership(user_id, context.application):
        data = load_data()
        user_referrals = data[str(user_id)]['referrals'] if str(user_id) in data else 0
        leaderboard = get_leaderboard()
        leader_name = f"{leaderboard[0][2]} (@{leaderboard[0][1]})" if leaderboard else "No one yet"
        leader_referrals = leaderboard[0][3] if leaderboard else 0

        # Generate the referral link
        referral_link = get_referral_link(user_id)

        message = (f"👋🏾 ሰላም  {first_name}!\n\n"
                   f"አሁን የቻናሉ አባል ኖት። ለሌሎች ሰዎች በማጋራት የስካይ 300 ቻሌንጅ አሸናፊ ይሁኑ👇\n\n"
                   f"🔗 Your referral link: {referral_link}\n\n"
                   f"🏅 እስካሁን {user_referrals} ሰዎችን ጋብዘዋል.\n\n")

        keyboard = [
            [InlineKeyboardButton("📈 Leaderboard", callback_data='leaderboard')],
            [InlineKeyboardButton("🔗 Get Referral Link", callback_data='referral_link')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=message,
                                       reply_markup=reply_markup)
    else:
        join_button = InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")
        check_button = InlineKeyboardButton("Check Membership", callback_data='check_membership')
        keyboard = [[join_button], [check_button]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"✅ ይሄንን ቦት ለመጠቀም እባክዎ አስቀድመው ይሄንን ቻናል {CHANNEL_ID[1:]} ይቀላቀሉ.",
                                       reply_markup=reply_markup)
# Callback query handler
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name

    logger.info(f"User {username} ({first_name}) triggered callback: {query.data}")

    if query.data == 'check_membership':
        if await check_membership(user_id, context.application):
            data = load_data()
            user_referrals = data[str(user_id)]['referrals'] if str(user_id) in data else 0
            leaderboard = get_leaderboard()
            leader_name = f"{leaderboard[0][2]} (@{leaderboard[0][1]})" if leaderboard else "No one yet"
            leader_referrals = leaderboard[0][3] if leaderboard else 0

            message = (f"👋🏾 ሰላም  {user.first_name}!\n\n"
                       f"አሁን የቻናሉ አባል ኖት። ለሌሎች ሰዎች በማጋራት የስካይ 300 ቻሌንጅ አሸናፊ ይሁኑ👇\n\n"
                       f"🔗 Your referral link: {referral_link}\n\n"
                       f"🏅 እስካሁን {user_referrals} ሰዎችን ጋብዘዋል.\n\n")

            keyboard = [
                [InlineKeyboardButton("📈 Leaderboard", callback_data='leaderboard')],
                [InlineKeyboardButton("🔗 Get Referral Link", callback_data='referral_link')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=query.message.chat_id,
                                           text=message,
                                           reply_markup=reply_markup)
        else:
            join_button = InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")
            check_button = InlineKeyboardButton("Check Membership", callback_data='check_membership')
            keyboard = [[join_button], [check_button]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=query.message.chat_id,
                                           text=f"❗ እስካሁን አባል አይደሉም፣ እባክዎትን @{CHANNEL_ID[1:]} ይቀላቀሉ.",
                                           reply_markup=reply_markup)
    elif query.data == 'leaderboard':
        leaderboard = get_leaderboard()
        leaderboard_text = "\n".join([f"{first_name} (@{username}): {referrals} referrals" for _, username, first_name, referrals in leaderboard])
        await context.bot.send_message(chat_id=query.message.chat_id,
                                       text=f"🏆 Leaderboard:\n{leaderboard_text}")
    elif query.data == 'referral_link':
        referral_link = get_referral_link(user_id)
        message = (
            f"🎉 እንኳን ደስ አለዎት!\n"
            f"ወደ ቻናሉ ከታች ባለው ሊንክ በመቀላቀል የገንዘብ ተሸላሚ ይሁኑ\n\n"
            f"🔗 በዚህ ሊንክ ይቀላቀሉ 👉 ({referral_link})\n\n"
            f"SKY ስፖርት ET™ - Bringing The World of sports to Ethiopia - Every Victory, Every Nation!"
        )
        await context.bot.send_message(chat_id=query.message.chat_id,
                                    text=message,
                                    parse_mode='Markdown')

# Initialize the Application
application = Application.builder().token(BOT_TOKEN).build()

# Add handlers to the application
application.add_handler(CommandHandler('start', start))
application.add_handler(CallbackQueryHandler(handle_callback))

# Run the bot
if __name__ == '__main__':
    logger.info("Starting bot")
    application.run_polling()
    logger.info("Bot stopped")
