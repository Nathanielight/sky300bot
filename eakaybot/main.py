import logging
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, ChatMemberHandler
from telegram.utils.request import Request

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionary to store user referrals
user_referrals = {}

CHANNEL_ID = '@skysport_ethiopia'  # Replace with your channel's ID or username

def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    if user_id not in user_referrals:
        # Generate a unique private invite link for the user with their username as the name of the link
        invite_link = context.bot.create_chat_invite_link(chat_id=CHANNEL_ID, name=username).invite_link

        # Save the invite link information
        user_referrals[user_id] = {'username': username, 'invite_link': invite_link, 'referrals': 0}
    else:
        invite_link = user_referrals[user_id]['invite_link']

    # Send the invite link to the user privately
    update.message.reply_text(f"ሰላም {username}! ይሔንን ሊንክ በማጋራት የስካይ 300 ቻሌንጅ አሸናፊ ይሁኑ፣ የሽልማቱም ተቋዳሽ ይሁኑ: {invite_link}")

def track_joins(update: Update, context: CallbackContext) -> None:
    channel_username = "skysport_Ethiopia"
    
    # Check if the update is for the specified channel
    if update.chat_member.chat.username == channel_username:
        new_chat_member = update.chat_member.new_chat_member
        if new_chat_member:
            new_member_id = new_chat_member.user.id
            user_status = new_chat_member.status

            if user_status == "member":
                # Log the invite link and user info
                logger.info(f"New member joined: {new_member_id} via {new_chat_member.invite_link.invite_link if new_chat_member.invite_link else 'unknown link'}")

                # Check which user's invite link was used
                if new_chat_member.invite_link:
                    for user_id, data in user_referrals.items():
                        if data['invite_link'] == new_chat_member.invite_link.invite_link:
                            # Increment the referral count for the user who owns the invite link
                            user_referrals[user_id]['referrals'] += 1
                            logger.info(f"Referral count updated for user {user_id} ({data['username']}): {data['referrals']} referrals")
                            break

def leaderboard(update: Update, context: CallbackContext) -> None:
    sorted_referrals = sorted(user_referrals.values(), key=lambda x: x['referrals'], reverse=True)
    leaderboard_text = "Leaderboard:\n\n"
    for rank, data in enumerate(sorted_referrals, start=1):
        leaderboard_text += f"{rank}. {data['username']}: {data['referrals']} referrals\n"
    
    update.message.reply_text(leaderboard_text)

def main() -> None:
    # Your bot token here
    TOKEN = '7364132452:AAE2wF52JrS4LqxXwSxx3E9XIGLlxNnYBDM'

    # Create the Updater and pass it your bot's token.
    request = Request(con_pool_size=8)
    bot = Bot(token=TOKEN, request=request)
    updater = Updater(bot=bot, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(CommandHandler("start", start))
    #dispatcher.add_handler(CommandHandler("leaderboard", leaderboard))
    dispatcher.add_handler(ChatMemberHandler(track_joins, ChatMemberHandler.MY_CHAT_MEMBER))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
