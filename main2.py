import os
import json
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
    member = await app.bot.get_chat_member(CHANNEL_ID, user_id)
    return member.status in ['member', 'administrator', 'creator']

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

# Function to notify the referrer
async def notify_referrer(context: CallbackContext, referrer_id, new_user_first_name, new_user_username):
    if referrer_id is not None:
        message = (f"🎉 Congratulations! {new_user_first_name} (@{new_user_username}) "
                   f"has joined the channel using your referral link.")
        try:
            await context.bot.send_message(chat_id=int(referrer_id), text=message)
        except Exception as e:
            print(f"Error sending message to referrer: {e}")

# Function to get the leaderboard
def get_leaderboard():
    data = load_data()
    leaderboard = [(details['username'], details['first_name'], details['referrals']) for details in data.values()]
    leaderboard.sort(key=lambda x: x[2], reverse=True)
    return leaderboard

# Start command handler
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    username = user.username
    first_name = user.first_name

    # Store user data
    store_user_data(user_id, username, first_name)

    # Check if the user joined via a referral link
    args = context.args
    if args:
        referrer_id = args[0]
        increment_referrals(referrer_id, username, first_name)  # Increment referrer's count
        await notify_referrer(context, referrer_id, first_name, username)

    if await check_membership(user_id, context.application):
        keyboard = [
            [InlineKeyboardButton("📈 Leaderboard", callback_data='leaderboard')],
            [InlineKeyboardButton("🔗 Get Referral Link", callback_data='referral_link')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"👋 Welcome {first_name}!\nYou are a member of the channel. Refer others and become a winner of the Sky 300k challenge!\n\n",
                                       reply_markup=reply_markup)
    else:
        join_button = InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")
        keyboard = [[join_button]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"✅ Please join @{CHANNEL_ID[1:]} first to use the bot.",
                                       reply_markup=reply_markup)

# Callback query handler
async def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name

    # Re-check membership status
    if not await check_membership(user_id, context.application):
        join_button = InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_ID[1:]}")
        keyboard = [[join_button]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=query.message.chat_id,
                                       text=f"✅ Please join @{CHANNEL_ID[1:]} first to use the bot.",
                                       reply_markup=reply_markup)
        return

    if query.data == 'leaderboard':
        leaderboard = get_leaderboard()
        leaderboard_text = "\n".join([f"{first_name} (@{username}): {referrals} referrals" for username, first_name, referrals in leaderboard])
        await context.bot.send_message(chat_id=query.message.chat_id,
                                       text=f"🏆 Leaderboard:\n{leaderboard_text}")
    elif query.data == 'referral_link':
        referral_link = get_referral_link(user_id)
        await context.bot.send_message(chat_id=query.message.chat_id,
                                       text=f"🔗 Share this link to win the Sky 300k challenge: {referral_link}")

# Initialize the Application
application = Application.builder().token(BOT_TOKEN).build()

# Add handlers to the application
application.add_handler(CommandHandler('start', start))
application.add_handler(CallbackQueryHandler(handle_callback))

# Run the bot
if __name__ == '__main__':
    application.run_polling()
