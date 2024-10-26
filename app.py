import logging
import asyncio
from telegram import (
    Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler,
    CallbackQueryHandler, filters
)
import random

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ======== Змінні гри ========
games = {}
default_professions = [
    'Лікар', 'Інженер', 'Вчений', 'Музикант', 'Письменник',
    'Астроном', 'Пілот', 'Шеф-кухар', 'Художник', 'Програміст'
]
default_items = [
    'Ліхтарик', 'Ніж', 'Аптечка', 'Мапа', 'Радіо',
    'Телескоп', 'Ноутбук', 'Книга', 'Гітара', 'Камера'
]

# ======== Хендлери команд ========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id in games:
        await update.message.reply_text(
            "🔄 Гра вже запущена!",
            reply_to_message_id=update.message.message_id
        )
        return

    games[chat_id] = {
        'initiator': user_id,
        'players': {},
        'bots': [],
        'professions': default_professions.copy(),
        'items': default_items.copy(),
        'custom_professions': None,
        'custom_items': None,
        'phase': 'joining',
        'round_time': 30  # За замовчуванням 30 секунд
    }
    join_button = [InlineKeyboardButton("🔹 Приєднатися до гри", callback_data='join_game')]
    reply_markup = InlineKeyboardMarkup([join_button])
    await update.message.reply_text(
        "🛸 Починаємо нову гру! Натисніть кнопку нижче або використайте команду /join",
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id
    )

async def join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await join(update, context)

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id not in games or games[chat_id]['phase'] != 'joining':
        await update.effective_message.reply_text(
            "🚫 Зараз неможливо приєднатися до гри.",
            reply_to_message_id=update.effective_message.message_id
        )
        return

    game = games[chat_id]
    if user.id in game['players']:
        await update.effective_message.reply_text(
            "😎 Ви вже в грі!",
            reply_to_message_id=update.effective_message.message_id
        )
        return

    if not game['professions'] or not game['items']:
        await update.effective_message.reply_text(
            "🚫 Немає доступних професій або предметів для нових гравців.",
            reply_to_message_id=update.effective_message.message_id
        )
        return

    profession = random.choice(game['professions'])
    game['professions'].remove(profession)
    item = random.choice(game['items'])
    game['items'].remove(item)

    game['players'][user.id] = {
        'name': user.first_name,
        'profession': profession,
        'items': [item],
        'alive': True,
        'votes': 0
    }

    await update.effective_message.reply_text(
        f"👤 {user.first_name} приєднався до гри!\n"
        f"🧑‍💼 Професія: {profession}\n"
        f"🎒 Предмет: {item}",
        reply_to_message_id=update.effective_message.message_id
    )

async def bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in games:
        await update.message.reply_text(
            "🚫 Гра ще не почалася.",
            reply_to_message_id=update.message.message_id
        )
        return

    game = games[chat_id]
    if user_id != game['initiator']:
        await update.message.reply_text(
            "🚫 Тільки ініціатор може додавати ботів.",
            reply_to_message_id=update.message.message_id
        )
        return

    cmd = update.message.text.strip('/')
    if cmd.startswith('bot'):
        try:
            num_bots = int(cmd[3:])
            if num_bots == 0:
                game['bots'] = []
                await update.message.reply_text(
                    "🤖 Всі боти видалені.",
                    reply_to_message_id=update.message.message_id
                )
                return
            for i in range(num_bots):
                bot_id = f'bot_{i}'
                if not game['professions'] or not game['items']:
                    await update.message.reply_text(
                        "🚫 Немає доступних професій або предметів для ботів.",
                        reply_to_message_id=update.message.message_id
                    )
                    return
                profession = random.choice(game['professions'])
                game['professions'].remove(profession)
                item = random.choice(game['items'])
                game['items'].remove(item)
                game['bots'].append({
                    'id': bot_id,
                    'name': f'Бот {i+1}',
                    'profession': profession,
                    'items': [item],
                    'alive': True,
                    'votes': 0
                })
            await update.message.reply_text(
                f"🤖 Додано {num_bots} ботів.",
                reply_to_message_id=update.message.message_id
            )
        except ValueError:
            await update.message.reply_text(
                "🚫 Невірна команда для ботів.",
                reply_to_message_id=update.message.message_id
            )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Почати нову гру\n"
        "/join - Приєднатися до гри\n"
        "/bot1, /bot2... - Додати ботів\n"
        "/bot0 - Видалити всіх ботів\n"
        "/begin - Розпочати гру\n"
        "/help - Допомога\n"
        "/settings - Налаштування\n"
        "/roadmap - План оновлень\n"
        "/about - Про гру",
        reply_to_message_id=update.message.message_id
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = games.get(chat_id)
    if not game or game['initiator'] != update.effective_user.id:
        await update.message.reply_text(
            "🚫 Тільки ініціатор може змінювати налаштування.",
            reply_to_message_id=update.message.message_id
        )
        return

    time_buttons = []
    for t in [30, 60, 90]:
        if game['round_time'] == t:
            time_buttons.append(InlineKeyboardButton(f"✅ {t} сек", callback_data=f"time_{t}"))
        else:
            time_buttons.append(InlineKeyboardButton(f"{t} сек", callback_data=f"time_{t}"))

    keyboard = [
        time_buttons,
        [InlineKeyboardButton("📋 Переглянути професії", callback_data='view_professions')],
        [InlineKeyboardButton("🎒 Переглянути предмети", callback_data='view_items')],
        [InlineKeyboardButton("📋 Налаштувати професії", callback_data='set_professions')],
        [InlineKeyboardButton("🎒 Налаштувати предмети", callback_data='set_items')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚙️ Налаштування:",
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id
    )

async def settings_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = games.get(chat_id)

    if not game or user_id != game['initiator']:
        await query.edit_message_text("🚫 Ви не маєте доступу до налаштувань.")
        return

    if query.data.startswith('time_'):
        time = int(query.data.split('_')[1])
        game['round_time'] = time
        await query.edit_message_text(f"⏱ Час раунду встановлено на {time} секунд.")
    elif query.data == 'view_professions':
        professions = game['custom_professions'] if game['custom_professions'] else default_professions
        await query.edit_message_text(f"📋 Список професій:\n" + "\n".join(professions))
    elif query.data == 'view_items':
        items = game['custom_items'] if game['custom_items'] else default_items
        await query.edit_message_text(f"🎒 Список предметів:\n" + "\n".join(items))
    elif query.data == 'set_professions':
        game['awaiting_professions'] = True
        await query.edit_message_text("📋 Надішліть новий список професій (кожна з нового рядка).")
    elif query.data == 'set_items':
        game['awaiting_items'] = True
        await query.edit_message_text("🎒 Надішліть новий список предметів (кожен з нового рядка).")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = games.get(chat_id)

    if game and game.get('awaiting_professions') and user_id == game['initiator']:
        professions = update.message.text.strip().split('\n')
        game['custom_professions'] = professions
        game['professions'] = professions.copy()
        del game['awaiting_professions']
        await update.message.reply_text(
            "📋 Новий список професій встановлено.",
            reply_to_message_id=update.message.message_id
        )
    elif game and game.get('awaiting_items') and user_id == game['initiator']:
        items = update.message.text.strip().split('\n')
        game['custom_items'] = items
        game['items'] = items.copy()
        del game['awaiting_items']
        await update.message.reply_text(
            "🎒 Новий список предметів встановлено.",
            reply_to_message_id=update.message.message_id
        )
    else:
        # Повідомлення під час обговорення
        if game and game['phase'] == 'discussion':
            pass  # Повідомлення дозволені
        else:
            pass  # Ігнорувати або обробити інші повідомлення

async def begin_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in games:
        await update.message.reply_text(
            "🚫 Гра ще не почалася.",
            reply_to_message_id=update.message.message_id
        )
        return

    game = games[chat_id]
    if user_id != game['initiator']:
        await update.message.reply_text(
            "🚫 Тільки ініціатор може почати гру.",
            reply_to_message_id=update.message.message_id
        )
        return

    if len(game['players']) + len(game['bots']) < 3:
        await update.message.reply_text(
            "🚫 Потрібно як мінімум 3 гравці для початку гри.",
            reply_to_message_id=update.message.message_id
        )
        return

    game['phase'] = 'discussion'
    await update.message.reply_text(
        "💬 Фаза обговорення розпочалася! У вас є "
        f"{game['round_time']} секунд.",
        reply_to_message_id=update.message.message_id
    )

    await asyncio.sleep(game['round_time'])

    await update.message.reply_text(
        "🗳 Час для голосування! Кого ви хочете вигнати?",
        reply_to_message_id=update.message.message_id
    )

    game['phase'] = 'voting'
    game['votes'] = {}

    # Створити кнопки для голосування
    keyboard = []
    for player_id, player in game['players'].items():
        if player['alive']:
            keyboard.append([InlineKeyboardButton(player['name'], callback_data=f"vote_{player_id}")])
    for bot in game['bots']:
        if bot['alive']:
            keyboard.append([InlineKeyboardButton(bot['name'], callback_data=f"vote_{bot['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Натисніть на ім'я гравця, щоб проголосувати:",
        reply_markup=reply_markup
    )

async def vote_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    game = games.get(chat_id)

    if not game or game['phase'] != 'voting':
        await query.edit_message_text("🚫 Зараз не час для голосування.")
        return

    if user_id not in game['players']:
        await query.edit_message_text("🚫 Ви не берете участь у цій грі.")
        return

    if not game['players'][user_id]['alive']:
        await query.edit_message_text("🚫 Ви не можете голосувати, бо ви вибули.")
        return

    vote_target = query.data.split('_')[1]
    game['votes'][user_id] = vote_target
    await query.edit_message_text(f"✅ Ваш голос зараховано.")

    # Перевірка, чи всі проголосували
    total_alive = sum(1 for p in game['players'].values() if p['alive'])
    total_votes = len(game['votes'])

    if total_votes >= total_alive:
        await tally_votes(chat_id, context)

async def tally_votes(chat_id, context):
    game = games[chat_id]
    vote_counts = {}
    for voter, target in game['votes'].items():
        vote_counts[target] = vote_counts.get(target, 0) + 1

    # Знайти гравця з найбільшою кількістю голосів
    max_votes = max(vote_counts.values())
    eliminated = [k for k, v in vote_counts.items() if v == max_votes]

    # Якщо нічия, ніхто не вибуває
    if len(eliminated) > 1:
        await context.bot.send_message(
            chat_id=chat_id,
            text="🤷‍♂️ Нічия! Ніхто не вибуває цього раунду."
        )
    else:
        target = eliminated[0]
        # Видалити гравця
        if target.isdigit():
            game['players'][int(target)]['alive'] = False
            name = game['players'][int(target)]['name']
        else:
            for bot in game['bots']:
                if bot['id'] == target:
                    bot['alive'] = False
                    name = bot['name']
                    break
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"☠️ {name} вибуває з гри!"
        )

    # Перевірити кількість залишившихся гравців
    alive_players = sum(1 for p in game['players'].values() if p['alive'])
    alive_bots = sum(1 for b in game['bots'] if b['alive'])
    total_alive = alive_players + alive_bots

    if total_alive <= 2:
        # Гра завершується
        winners = []
        for p in game['players'].values():
            if p['alive']:
                winners.append(p['name'])
        for b in game['bots']:
            if b['alive']:
                winners.append(b['name'])
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎉 Гра завершена! Переможці: {', '.join(winners)}"
        )
        del games[chat_id]
    else:
        # Почати новий раунд
        await new_round(chat_id, context)

async def new_round(chat_id, context):
    game = games[chat_id]
    # Видати додаткові предмети
    for player_id, player in game['players'].items():
        if player['alive']:
            if game['items']:
                item = random.choice(game['items'])
                game['items'].remove(item)
                player['items'].append(item)
            else:
                continue  # Немає більше предметів
    for bot in game['bots']:
        if bot['alive']:
            if game['items']:
                item = random.choice(game['items'])
                game['items'].remove(item)
                bot['items'].append(item)
            else:
                continue  # Немає більше предметів

    game['phase'] = 'discussion'
    game['votes'] = {}
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"💬 Новий раунд розпочато! Фаза обговорення триває {game['round_time']} секунд."
    )

    await asyncio.sleep(game['round_time'])

    await context.bot.send_message(
        chat_id=chat_id,
        text="🗳 Час для голосування! Кого ви хочете вигнати?"
    )

    game['phase'] = 'voting'

    # Створити кнопки для голосування
    keyboard = []
    for player_id, player in game['players'].items():
        if player['alive']:
            keyboard.append([InlineKeyboardButton(player['name'], callback_data=f"vote_{player_id}")])
    for bot in game['bots']:
        if bot['alive']:
            keyboard.append([InlineKeyboardButton(bot['name'], callback_data=f"vote_{bot['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=chat_id,
        text="Натисніть на ім'я гравця, щоб проголосувати:",
        reply_markup=reply_markup
    )

# ======== Основна функція ========
def main():
    application = ApplicationBuilder().token('7227673845:AAHjCl-2QK67paml-Y2hGqloVjPGVbae2tk').build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('join', join))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('settings', settings))
    application.add_handler(CommandHandler('begin', begin_game))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(CallbackQueryHandler(settings_button, pattern='^(time_.*|view_professions|view_items|set_professions|set_items)$'))
    application.add_handler(CallbackQueryHandler(join_callback, pattern='^join_game$'))
    application.add_handler(CallbackQueryHandler(vote_button, pattern='^vote_.*'))

    # Динамічні команди для ботів
    for i in range(10):
        application.add_handler(CommandHandler(f'bot{i}', bot_command))

    logging.info("🤖 Бот запущений...")
    application.run_polling()

if __name__ == '__main__':
    main()
