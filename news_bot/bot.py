
from db_conf import *
from settings import *
from imports import *





bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())

engine = ENGINE
Session = sessionmaker(engine)
session = Session()
inspector = inspect(engine)



class UserStates(Helper):
    mode = HelperMode.snake_case

    INPUT = ListItem()
    OUTPUT = ListItem()
    ADMIN = ListItem()
    GET_NEWS = ListItem()
    BANNED = ListItem()





@dp.message_handler(state=UserStates.BANNED)
async def save_new(message: types.Message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, "😳Вас забанено адміністратором!")


#
#  get user status on startup
#

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    chat_id = message.chat.id
    state = dp.current_state(user=chat_id)


    startup_markup = InlineKeyboardMarkup(row_width=2)
    startup_markup.row(InlineKeyboardButton(text = "🕵️Поповнюю запас новин", callback_data = "input"),
                                            InlineKeyboardButton(text = "🧑‍🏫Роблю пости", callback_data = "output"))
    

    all_ids = []
    members = None
    all_users = None
    with engine.connect() as con:
        all_users = con.execute("SELECT * FROM users").fetchall()
        for user in all_users:
            all_ids.append(user.id)
    if chat_id in all_ids:
        print(f"{message.date}: {message.from_user.username} is trying to connect")
        for user in all_users:
            if int(chat_id) == int(user.id):
                print(f"{message.date}: {message.from_user.username} come back and has {user.role} role")
                if user.is_banned:
                    await state.set_state(UserStates.BANNED[0])
                    await bot.send_message(chat_id, "😳Вас забанено адміністратором!")
                elif user.role == "input":
                    await state.set_state(UserStates.INPUT[0])
                    await bot.send_message(chat_id, "🇺🇦Раді вас вітати, наша база чекає на поповнення!\n\n✍️Нагадуємо, щоб додати новини, введіть команду /add та надішліть новину<b>(максимільна кількість повідомлень - 5)</b>\n\n👌Піcля вводу новини напишіть команду /end", parse_mode="html")
                elif user.role == "output":
                    await state.set_state(UserStates.OUTPUT[0])
                    await bot.send_message(chat_id, "🇺🇦Раді вас вітати, свіжі новини вже чекають на вас!\n\n🤲Нагадуємо, щоб отримати сет новини, введіть команду /get\n\n👌Після опрацювання новини підтвердіть свої дії натиснувши на відповідну кнопку")
        
                elif user.role == "admin":
                    await state.set_state(UserStates.ADMIN[0])
                    await bot.send_message(chat_id, f"🇺🇦Раді вас вітати, {message.from_user.first_name}!")
                break    

    else:
        await bot.send_message(chat_id, "🇺🇦Вітаємо в боті з агрегації проукраїнскьких новин! Оберіть свою роль", reply_markup=startup_markup)
    



#
#  news give away 
#

@dp.message_handler(state=UserStates.OUTPUT, commands=['get'])
async def getting_news(message: types.Message):
    chat_id = message.chat.id
    state = dp.current_state(user=message.from_user.id) 
    
    all_news = None
    with engine.connect() as con:
        all_news = con.execute("SELECT * FROM news WHERE proсessing_by IS NULL and is_approved=True").fetchall()

    try:
        for i in range(5):


            news_markup = InlineKeyboardMarkup(row_width=2)
            news_markup.row(InlineKeyboardButton(text = "✌️Зробив допис", callback_data = all_news[i].first_msg_id + "sent"))

            cur_new = session.query(Post).filter(Post.id == all_news[i].id).first()
            cur_new.proсessing_by = message.from_user.username
            session.commit()

            news_group = all_news[i].id.split("|")
            for post in news_group:
                msg_id = post.split(" ")[0]
                from_chat_id = post.split(" ")[1]
                await bot.forward_message(chat_id, from_chat_id=from_chat_id, message_id=msg_id)

            await bot.send_message(chat_id, "🤞Натиснувши цю кнопку ви підтверджуєте, що зробили допис\n🧹Новина буде видалена з цього чату", reply_markup=news_markup)
    except IndexError:
       await bot.send_message(chat_id, "🤝Наразі новини зкінчились, зверніться пізніше)")

    print(f"{message.date}: {message.from_user.username} has just recieved set of {len(all_news)} news")





#
#  add user to the database
#

@dp.callback_query_handler(lambda c: c.data, state=[UserStates.OUTPUT[0], UserStates.INPUT[0], UserStates.ADMIN[0], UserStates.GET_NEWS[0]])
async def set_role(callback_query: types.CallbackQuery):
    
    call = callback_query.data
    chat_id = callback_query.message.chat.id
    state = dp.current_state(user=chat_id)

    all_admins = None
    with engine.connect() as con:
        all_admins = con.execute("SELECT * FROM users WHERE role='admin'").fetchall()
        
        
   
    if call == 'input':
        startup_markup = InlineKeyboardMarkup(row_width=2)
        startup_markup.row(InlineKeyboardButton(text = "🕵️Поповнюю запас новин", callback_data = "input"),
                                            InlineKeyboardButton(text = "🧑‍🏫Роблю пости", callback_data = "output"))

        new_user = User(id=callback_query.from_user.id, 
                        first_name=callback_query.from_user.first_name, 
                        second_name=callback_query.from_user.last_name, 
                        tg_name=callback_query.from_user.username, 
                        role='input',
                        in_editing=None,
                        is_banned=False)
        session.add(new_user)
        session.commit()

        await bot.send_message(chat_id, "🕵️Вас успішно додано!\n\n✍️Щоб додати новини, введіть команду /add та надішліть новину<b>(максимільна кількість повідомлень - 5)</b>\n\n👌Піcля вводу новини напишіть команду /end", parse_mode="html")
        for admin in all_admins:
            await bot.send_message(admin.id, f"🕵️<b>{callback_query.from_user.username}</b> починає збирати новини", parse_mode="html")

        print(f"{callback_query.message.date}: {callback_query.from_user.username} has just authorized and chose input role")
        await state.set_state(UserStates.INPUT[0])


    elif call == 'output':
        new_user = User(id=callback_query.from_user.id, 
                        first_name=callback_query.from_user.first_name, 
                        second_name=callback_query.from_user.last_name, 
                        tg_name=callback_query.from_user.username, 
                        role='output',
                        in_editing=None,
                        is_banned=False)
        session.add(new_user)
        session.commit()


        await bot.send_message(chat_id, "🧑‍🏫 Вас успішно додано!\n\n🤲Щоб отримати сет новини, введіть команду /get\n\n👌Після опрацювання новини підтвердіть свої дії натиснувши на відповідну кнопку")
        for admin in all_admins:
            await bot.send_message(admin.id, f"🧑‍🏫<b>{callback_query.from_user.username}</b> починає розслилати новини", parse_mode="html")

        print(f"{callback_query.message.date}: {callback_query.from_user.username} has just authorized and chose output role")
        await state.set_state(UserStates.OUTPUT[0])


    #  post confirmation
    #
    elif call.find("sent") != -1:
        cur_news = session.query(Post).filter(Post.first_msg_id == call[:len(call) - 4]).first()
        cur_news.is_posted = True
        session.commit()   
        
        for i in range(cur_news.msgs_number + 1):
            await bot.delete_message(chat_id, callback_query.message.message_id - i)

        print(f"{callback_query.message.date}: {callback_query.from_user.username} has just made a post with help of {cur_news.msgs_number} message(s)")
    
    elif call.find("approved") != -1:
        cur_news = session.query(Post).filter(Post.first_msg_id == call[:len(call) - 8]).first()
        cur_news.is_approved = True
        session.commit()   
        
        for i in range(cur_news.msgs_number + 1):
            await bot.delete_message(chat_id, callback_query.message.message_id - i)
        
        print(f"{callback_query.message.date}: {callback_query.from_user.username} has just approved news, given with {cur_news.msgs_number} message(s)")

    elif call == "set_input" or call == "set_output" or call == "set_admin":

        await bot.delete_message(chat_id, callback_query.message.message_id - 1)
        await bot.delete_message(chat_id, callback_query.message.message_id)

        user_to_edit_name = session.query(User).filter(User.id == chat_id).first().in_editing
        user_to_edit = session.query(User).filter(User.tg_name == user_to_edit_name).first()
        user_to_edit.role = call[4:]

        session.commit()
        target_state = dp.current_state(user=user_to_edit.id) 
            
        if call == "set_input":
            await target_state.set_state(UserStates.INPUT[0])
            await bot.send_message(user_to_edit.id, "🕵️Вас переведено адміністратором на збір новин!", parse_mode="html")
            await bot.send_message(chat_id, f"🕵️Користувача <b>{user_to_edit.tg_name}</b> успішно переведено на збір новин!")

            print(f"{callback_query.message.date}: {user_to_edit.tg_name} is sent to intput by {callback_query.from_user.username}")
        if call == "set_output":
            await target_state.set_state(UserStates.OUTPUT[0])
            await bot.send_message(user_to_edit.id, "🧑‍🏫Вас переведено адміністратором на розсилку новин!", parse_mode="html")
            await bot.send_message(chat_id, f"🧑‍🏫Користувача <b>{user_to_edit.tg_name}</b> успішно переведено на розсилку новин!")

            print(f"{callback_query.message.date}: {user_to_edit.tg_name} is sent to output by {callback_query.from_user.username}")
        if call == "set_admin":
            await target_state.set_state(UserStates.ADMIN[0])
            await bot.send_message(user_to_edit.id, "🧑‍💻Вас переведено до адміністрації!")
            await bot.send_message(chat_id, f"🧑‍💻Користувача <b>{user_to_edit.tg_name}</b> успішно переведено до адміністрації!", parse_mode="html")

            print(f"{callback_query.message.date}: {user_to_edit.tg_name} is promoted to admin by {callback_query.from_user.username}")
        
    
    elif call == "ban":

        await bot.delete_message(chat_id, callback_query.message.message_id - 1)
        await bot.delete_message(chat_id, callback_query.message.message_id)
        
        user_to_edit_name = session.query(User).filter(User.id == chat_id).first().in_editing
        user_to_edit = session.query(User).filter(User.tg_name == user_to_edit_name).first()
        print(user_to_edit)
        user_to_edit.is_banned = True
        session.commit()

        target_state = dp.current_state(user=user_to_edit.id) 
        await target_state.set_state(UserStates.BANNED[0])
        await bot.send_message(user_to_edit.id, "💔Вас було забанено..")
        await bot.send_message(chat_id, f"💔Користувача {user_to_edit.tg_name} успішно забанено!")

        print(f"{callback_query.message.date}: {user_to_edit.tg_name} is banned by {callback_query.from_user.username}")
            
    elif call == "ban_off":

        await bot.delete_message(chat_id, callback_query.message.message_id - 1)
        await bot.delete_message(chat_id, callback_query.message.message_id)
        
        user_to_edit_name = session.query(User).filter(User.id == chat_id).first().in_editing
        user_to_edit = session.query(User).filter(User.tg_name == user_to_edit_name).first()
        user_to_edit.is_banned = False
        session.commit()
        
        await bot.send_message(user_to_edit.id, "❤️Вітаємо, вас було розбанено! Перезапустіть бота для початку роботи")
        await bot.send_message(chat_id, f"❤️Користувача {user_to_edit.tg_name} успішно розбанено!")
           
        print(f"{callback_query.message.date}: {user_to_edit.tg_name} is got out of ban by {callback_query.from_user.username}")



#
#  obtain news
#


@dp.message_handler(state=UserStates.GET_NEWS, commands=["end"])
async def save_new(message: types.Message):
    chat_id = message.chat.id
    state = dp.current_state(user=message.from_user.id) 
    
    user = session.query(User).filter(User.id == chat_id).first()
    user.news_in_process = None
    session.commit()

    await state.set_state(UserStates.INPUT[0])
    await bot.send_message(chat_id, "👏Новина записана, з нетерпінням чекаю натупну!")

    print(f"{message.date}: {message.from_user.username} has just added some news")




    
    

@dp.message_handler(state=UserStates.GET_NEWS, content_types=['text', 'photo', 'video', 'document'])
async def save_new(message: types.Message):
    chat_id = message.chat.id
    state = dp.current_state(user=message.from_user.id) 
    
    user = session.query(User).filter(User.id == chat_id).first()
    if user.news_in_process == None:
        news_to_write = Post(id=str(message.message_id) + " " + str(chat_id),
                                first_msg_id=str(message.message_id) + " " + str(chat_id),
                                is_posted=False, 
                                proсessing_by=None,
                                posted_by=None,
                                on_approval=False,
                                is_approved=False,
                                msgs_number=1)
        session.add(news_to_write)
        user.news_in_process = ""
        user.news_in_process += str(message.message_id) + " " + str(chat_id)
        session.commit()
    else:
        cur_news = session.query(Post).filter(Post.id == user.news_in_process).first()
        if cur_news.msgs_number == 4:
            user = session.query(User).filter(User.id == chat_id).first()
            user.news_in_process = None

            cur_news.id += "|" + str(message.message_id) + " " + str(chat_id)
            cur_news.msgs_number += 1
            session.commit()

            print(f"{message.from_user.username} has just added some news and reached the limit")
            await state.set_state(UserStates.INPUT[0])
            await bot.send_message(chat_id, "✋Перевищино ліміт на кількісіть повідомленнь у пості\n👌Останнє повідомлення було збережене\n\n<b>Можливо ви забули ввести команду /en</b>", parse_mode="html")
        else:
            cur_news.id += "|" + str(message.message_id) + " " + str(chat_id)
            cur_news.msgs_number += 1
            user.news_in_process = cur_news.id
            session.commit()
    
    
   







#
#  prep before news obtaining
#

@dp.message_handler(state=UserStates.INPUT, commands=['add'])
async def getting_news(message: types.Message):
    chat_id = message.chat.id
    state = dp.current_state(user=message.from_user.id) 

    await state.set_state(UserStates.GET_NEWS[0])
    await bot.send_message(chat_id, "Готовий прийняти новину ")

    print(f"{message.date}: {message.from_user.username} is preparing for news adding")









@dp.message_handler(state=UserStates.ADMIN, commands=['users'])
async def getting_news(message: types.Message):
    chat_id = message.chat.id
    state = dp.current_state(user=message.from_user.id) 
    
    admins_list = "🧑‍💻<b>Адміністратори</b>"
    input_list = "🕵️<b>Додавачі</b>"
    output_list = "🧑‍🏫<b>Розсилачі</b>"
    with engine.connect() as con:
        all_users= con.execute("SELECT * FROM users").fetchall()
        for user in all_users:
            if user.role == 'admin':
                admins_list += f"\n  {user.tg_name}"
            if user.role == 'input':
                input_list += f"\n  {user.tg_name}"
            if user.role == 'output':
                output_list += f"\n  {user.tg_name}"

    text = f"{admins_list}\n{input_list}\n{output_list}\n"
    await bot.send_message(chat_id, text, parse_mode="html")

    print(f"{message.date}: {message.from_user.username} got a list of users")


@dp.message_handler(state=UserStates.ADMIN, commands=['edit'])
async def getting_news(message: types.Message):
    
    editing_keyboard = InlineKeyboardMarkup(row_width=2)
    editing_keyboard.row(InlineKeyboardButton(text = "🕵️Зробити додавачем", callback_data = "set_input"),
                                            InlineKeyboardButton(text = "🧑‍🏫Зробити розсилачем", callback_data = "set_output"))
    editing_keyboard.row(InlineKeyboardButton(text = "🧑‍💻Зробити адміністратором", callback_data = "set_admin"))
    
    chat_id = message.chat.id
    state = dp.current_state(user=message.from_user.id) 
    args = message.get_args()
    
    user = session.query(User).filter(User.id == chat_id).first()
    user.in_editing = args
    session.commit()   

    target_user = session.query(User).filter(User.tg_name == args).first()
    
    try:
        if not target_user.is_banned:
            editing_keyboard.row(InlineKeyboardButton(text = "💔Забанити", callback_data = "ban"))                                
        else:
            editing_keyboard.row(InlineKeyboardButton(text = "❤️Розбанити", callback_data = "ban_off"))
    except AttributeError:
            await bot.send_message(chat_id, "❌Невірно вказаний нік людини!")
    else:
        await bot.send_message(chat_id, f"Зміна статусу користувача: {args}", reply_markup=editing_keyboard)


@dp.message_handler(state=UserStates.ADMIN, commands=['factcheck'])
async def getting_news(message: types.Message):
    chat_id = message.chat.id
    state = dp.current_state(user=message.from_user.id) 
    
    all_news = None
    with engine.connect() as con:
        all_news = con.execute("SELECT * FROM news WHERE on_approval=False ").fetchall()

    try:
        for i in range(5):
            news_markup = InlineKeyboardMarkup(row_width=2)
            news_markup.row(InlineKeyboardButton(text = "✌️Передаю на розсилку", callback_data = all_news[i].first_msg_id + "approved"))

            cur_new = session.query(Post).filter(Post.id == all_news[i].id).first()
            cur_new.on_approval = True
            session.commit()

            news_group = all_news[i].id.split("|")
            for post in news_group:
                msg_id = post.split(" ")[0]
                from_chat_id = post.split(" ")[1]
                await bot.forward_message(chat_id, from_chat_id=from_chat_id, message_id=msg_id)

           
            await bot.send_message(chat_id, "👍Натиснувши цю кнопку ви підтверджуєте, що відправили новину на розсилку \n🧹Новина буде видалена з цього чату", reply_markup=news_markup)
    except IndexError:
       await bot.send_message(chat_id, "🤝Наразі новини для перевірки зкінчились, зверніться пізніше)")
    
    print(f"{message.date}: admin {message.from_user.username} has just recieved some news for approval")
    
   








    




if __name__ == '__main__':
    executor.start_polling(dp)
'''
async def on_startup(dp):
    logging.warning(
        'Starting connection. ')
    await bot.set_webhook(WEBHOOK_URL,drop_pending_updates=True)


async def on_shutdown(dp):
    logging.warning('Bye! Shutting down webhook connection')

def main():
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
'''