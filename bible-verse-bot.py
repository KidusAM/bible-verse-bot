from telegram.ext import *
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import os
from utils import *
from bible.bible_utils import *
from collections import OrderedDict
import pdb
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

with open("token.txt") as token_file:
    bot_token = token_file.read().strip() 

en_books = index_books_en(os.path.join("bible", "books_en.txt"))

next_verse = "Next verse " + chr(128213)
show_verse = "Show verse " + chr(128214)

def start(update, context):
    hello_message = "Hello There, welcome to Sword Bot."
    usage_message = "Do /train to train verses and /add Book Chapter:Verse to add verses to your personal training set" 
    add_user(update.effective_user.id)
    message(context, update, hello_message)
    message(context, update, usage_message)
    

def add(update, context, arg=None):
    argument = arg if arg else ' '.join(context.args)
    if update.message.reply_to_message and not arg:
        for line in update.message.reply_to_message.text.split("\n"):
            add(update,context, arg=line)
        return
    # pdb.set_trace()
    try: 
        
        verse = get_verse(argument, en_books, update.effective_user.id)
        keyboard = [
        [InlineKeyboardButton("Amharic", callback_data="am"), 
         InlineKeyboardButton("English", callback_data="en")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if add_verse(update.effective_user.id, argument.title()):
            message(context, update, "This verse is already in your list.")
        else:
            message(context, update, "Successfully added " + argument.title() + " :")
            message(context, update, verse, reply_markup)
        
    except Exception as e: 
        if not arg: handle_verse_exception(e, update, context); return;
        else: message(context, update, f"'{arg}' " + " is not a valid verse")

    
    

def remove(update, context):
    argument = ' '.join(context.args)
    try: 
        get_verse(argument, en_books, update.effective_user.id)
        remove_verse(update.effective_user.id, argument.title())
        message(context, update, "Successfully removed " + argument.title())
        
    except NoSuchVerseException: message(context, update, "This verse is not in your list.")
    except Exception as e: handle_verse_exception(e, update, context)
    

def get_all(update, context):
    all_messages = get_all_verses(update.effective_user.id)
    if not len(all_messages): message(context, update, "You haven't added any verses yet."); return;
    message(context, update, "Your verses:")
    message(context, update, all_messages)

def get(update, context):
    argument = ' '.join(context.args)
    try:    
        verse = get_verse(argument, en_books, update.effective_user.id)
        keyboard = [
        [InlineKeyboardButton("Amharic", callback_data="am"),
         InlineKeyboardButton("English", callback_data="en")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message(context, update, verse, reply_markup)
    except Exception as e:
        handle_verse_exception(e, update, context)

def choose_lang(update, context):
    query = update.callback_query

    query.answer()
    change_lang(update.effective_user.id, query.data)
    # query.edit_message_text()


def handle_verse_exception(e, update, context):
    try:
        raise e
    except InvalidFormatException:
        message(context, update, 'Invalid Format. Please use "Book Verse:Chapter". You can do /example to see examples.')
    except InvalidBookException:
        message(context, update, 'Invalid Book. That is not a valid book in the bible. You can do /books to see all the books.')
    except InvalidVerseException:
        message(context, update, 'Invalid Chapter/Verse. Remember, you can do "Book Chapter" to see a whole chapter')
    except Exception as e:
        print(e)

        
def example(update, context):
    examples = "John 3:16\n" + \
                "Psalms 23:1-6\n" + \
                "Isaiah 53"
    message(context, update, examples)
    
def books(update, context):
    final = str()
    books = en_books.keys()
    for book in books:
        final += book + "\n"
    message(context, update, final)


def begin_train(update, context):
    if get_status(update.effective_user.id) == 1:
        message(context, update, "You are already in training mode. Do /end_training to\
                exit out of training mode")
    else:
        update_state(update.effective_user.id, 1)
        send_keyboard(update, context, "You are now in training mode", next_verse)

def end_train(update, context):
    if get_status(update.effective_user.id) == 0:
        message(context, update, "You are not in training mode.")
    else:
        update_state(update.effective_user.id, 0)
        clear_training(update.effective_user.id)
    
def send_keyboard(update, context, message , *args, otk=True):
    keyboard = [[message] for message in args]

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=otk)
    
    context.bot.send_message(chat_id=update.effective_chat.id,
        text=message,
        reply_markup=reply_markup)
    


def add_command(command, func, disp):
    handler = CommandHandler(command, func)
    disp.add_handler(handler)


def message(ctx, upd, message, reply_mark=None):
    ctx.bot.send_message(chat_id=upd.effective_chat.id, text=message, 
                         reply_markup = reply_mark)

def language(update, context):
    keyboard = [
        [InlineKeyboardButton("Amharic", callback_data="am"),
         InlineKeyboardButton("English", callback_data="en")]
        ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message(context, update, "Please choose your language", reply_markup)
    
    
def msg_handler(update, context):
    user_id = update.effective_user.id

    if not get_status(user_id):
        message(context, update, "You are not in training mode. Do /begin_train to enter")
        return
    try:
        verse = get_next_verse(user_id)
        if show_verse in update.message.text:
            send_keyboard(update, context, verse, next_verse)
            
        elif next_verse in update.message.text:
            send_keyboard(update, context, verse, show_verse)
    
    except NoVersesException:
        message(context, update, "You don't have any verses in your list." + 
                "Do /add to add some.")
            
    
    
    
    
def main():
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher
    
    general_msg_handler = MessageHandler(Filters.text & (~Filters.command), msg_handler)
    dispatcher.add_handler(general_msg_handler)
    
    def end_now_all(update, context):
        '''
            Stop the bot in case of an emergency
        '''
        print("Am here")
        print(context.args[0])
        if(context.args[0] == "thisIsThePasscOde"):
            print("Also here")
            updater.stop()
            exit(1)
        
    updater.dispatcher.add_handler(CallbackQueryHandler(choose_lang))
    add_command('end_now_all', end_now_all, dispatcher)
    
    add_command('start', start, dispatcher)
    
    add_command('add', add, dispatcher)    
    add_command('get', get, dispatcher)
    add_command('example', example, dispatcher)
    add_command('books', books, dispatcher)
    add_command('remove', remove, dispatcher)
    add_command('all', get_all, dispatcher)
    add_command('begin_train', begin_train, dispatcher)    
    add_command('end_train', end_train, dispatcher)
    add_command('language', language, dispatcher)
    
    updater.start_polling()
    updater.idle()
    
    
    # time.sleep(10)
    
    updater.stop()
    
    
    
    



if __name__ == '__main__': main()
