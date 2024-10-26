from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import random
from typing import Dict, List, Any
import asyncio
from telegram.error import TimedOut
from functools import wraps

# Retry decorator to handle timeout errors
def retry_on_timeout(retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except TimedOut:
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)
                        print(f"Retrying due to timeout... (Attempt {attempt + 1})")
                    else:
                        print("All retry attempts failed due to timeout.")
                        raise
        return wrapper
    return decorator

@retry_on_timeout()
async def send_safe_message(context, chat_id, text, reply_markup=None):
    """Safe message sending with retry handling."""
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


# Game Configuration
PROFESSIONS = ["Інженер", "Лікар", "Науковець", "Вчитель", "Митець",
               "Солдат", "Пілот", "Фермер", "Кухар", "Механік",
               "Журналіст", "Бізнесмен", "Архітектор", "Спортсмен", "Еколог",
               "Адвокат", "Психолог", "Програміст", "Менеджер", "Соціолог",
               "Рятувальник", "Астроном", "Історик", "Перекладач", "Геолог",
               "Біолог", "Хімік", "Фізик", "Інструктор з виживання", "Електрик",
               "Оператор дронів", "Аналітик", "Дизайнер", "Спеціаліст з комунікацій", "Картограф"]

ITEMS = ["Радіо", "Набір інструментів", "Ноутбук", "Книга", "Мапа",
         "Ліхтарик", "Канат", "Компас", "Запальничка", "Намет",
         "Повербанк", "Камера", "Повідомлення про виживання", "Водонепроникний плащ",
         "Сокира", "Малий газовий плитка", "Спалаханка", "Спальний мішок", "Набір продуктів",
         "Великий контейнер для зберігання", "Блокнот і ручка", "Набір для шиття", "Ручний генератор",
         "Зарядний пристрій для батарейок", "Пластикові контейнери", "Швейцарський ніж", "Ручна пилка",
         "Розкладний стілець", "Кружка з фільтром для води", "Додаткові батарейки", 
         "Інфрачервоний прилад нічного бачення", "Портативна сонячна панель", "Таблетки для очищення води",
         "Протигаз", "Захисні окуляри", "Інструмент для відкривання банок", "Кухонний термометр"]

BOT_NAMES = [
    "R2-D2",
    "C-3PO",
    "HAL 9000",
    "Bumblebee",
    "Optimus Prime",
    "TARS",
    "WALL-E",
    "Sonny",
    "Marvin",
    "Data",
    "GLaDOS",
    "Baymax",
    "Bender",
    "Megatron",
    "A.L.I.E.N.",
    "BB-8"
]

TOKEN = "7227673845:AAHjCl-2QK67paml-Y2hGqloVjPGVbae2tk"

# Game State
games: Dict[int, Dict[str, Any]] = {}
votes: Dict[int, Dict[int, int]] = {}

class GameState:
    def __init__(self, chat_id: int, initiator: str):
        self.chat_id = chat_id
        self.players = {}
        self.started = False
        self.initiator = initiator
        self.discussion_time = 30  # Default time in seconds
        self.round = 0

    def add_player(self, user_id: int, name: str) -> Dict[str, str]:
        """Add a player to the game and return their role"""
        if user_id in self.players:
            return None
        
        player_data = {
            'name': name,
            'profession': random.choice(PROFESSIONS),
            'item': random.choice(ITEMS),
            'is_bot': False
        }
        self.players[user_id] = player_data
        return player_data

    def add_bots(self) -> List[Dict[str, str]]:
        """Add bots to fill the game"""
        added_bots = []
        available_bots = BOT_NAMES.copy()
        
        while len(self.players) < 5 and available_bots:
            bot_id = random.randint(10000, 99999)
            bot_name = available_bots.pop()
            bot_data = {
                'name': bot_name,
                'profession': random.choice(PROFESSIONS),
                'item': random.choice(ITEMS),
                'is_bot': True
            }
            self.players[bot_id] = bot_data
            added_bots.append(bot_data)
        
        return added_bots

    def get_player_list(self) -> str:
        """Get formatted list of players"""
        return "\n".join([
            f"🔹 {data['name']} - {data['profession']} (Предмет: {data['item']})"
            for data in self.players.values()
        ])

    def start_new_round(self) -> None:
        """Start a new round and update items"""
        self.round += 1
        for player in self.players.values():
            player['item'] = random.choice(ITEMS)

async def start(update: Update, context: CallbackContext) -> None:
    """Initialize or restart the game"""
    message = update.message or update.callback_query.message
    chat_id = message.chat.id
    
    if chat_id not in games:
        games[chat_id] = GameState(chat_id, update.effective_user.first_name)

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚪 Увійти в бункер", callback_data='join')],
        [InlineKeyboardButton("⚙️ Налаштування", callback_data='settings')]
    ])

    text = "🎉 Ласкаво просимо до гри 'Бункер'! Виберіть дію:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=buttons)
    else:
        await message.reply_text(text, reply_markup=buttons)

async def handle_join(update: Update, context: CallbackContext) -> None:
    """Handle player joining the game"""
    query = update.callback_query
    chat_id = query.message.chat.id
    user = update.effective_user
    
    if chat_id not in games:
        await query.answer("❌ Гра не знайдена.")
        return
    
    game = games[chat_id]
    
    if game.started:
        await query.answer("❌ Гра вже розпочата.")
        return

    player_data = game.add_player(user.id, user.first_name)
    if not player_data:
        await query.answer("❗️ Ви вже в грі!")
        return

    await query.answer("✅ Ви приєдналися до гри!")
    await query.message.reply_text(
        f"👤 {user.first_name} долучився до гри як {player_data['profession']} "
        f"з предметом: {player_data['item']}."
    )

    if len(game.players) >= 2:
        if len(game.players) < 5:
            await query.message.reply_text(
                "⚠️ Недостатньо гравців! Додаємо ботів для заповнення місць... 🤖"
            )
            added_bots = game.add_bots()
            for bot in added_bots:
                await query.message.reply_text(
                    f"🤖 {bot['name']} доєднався як {bot['profession']} "
                    f"з предметом: {bot['item']}."
                )

        start_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🚀 Почати раунд", callback_data='start_game')]
        ])
        await query.message.reply_text("🛠 Усі гравці готові. Почати гру?", reply_markup=start_button)

async def start_game(update: Update, context: CallbackContext) -> None:
    """Start the game round"""
    query = update.callback_query
    chat_id = query.message.chat.id
    
    if chat_id not in games:
        await query.answer("❌ Гра не знайдена.")
        return
    
    game = games[chat_id]
    if game.started:
        await query.answer("❌ Гра вже розпочата.")
        return

    game.started = True
    game.round = 1
    player_list = game.get_player_list()
    
    await query.edit_message_text(
        f"🛡 Раунд {game.round} розпочався!\n\nГравці:\n{player_list}"
    )

    await query.message.reply_text(
        f"💬 Фаза обговорення почалась. У вас є {game.discussion_time} секунд для обговорення!"
    )
    
    context.job_queue.run_once(
        end_discussion,
        game.discussion_time,
        chat_id=chat_id
    )

async def start_next_round(chat_id: int, context: CallbackContext) -> None:
    """Start the next round of the game"""
    game = games[chat_id]
    game.start_new_round()
    
    player_list = game.get_player_list()
    await context.bot.send_message(
        chat_id,
        f"🛡 Раунд {game.round} розпочався!\n\nГравці:\n{player_list}\n\n"
        f"💬 Фаза обговорення почалась. У вас є {game.discussion_time} секунд для обговорення!"
    )
    
    context.job_queue.run_once(
        end_discussion,
        game.discussion_time,
        chat_id=chat_id
    )

async def end_discussion(context: CallbackContext) -> None:
    """End discussion phase and start voting"""
    chat_id = context.job.chat_id
    game = games[chat_id]
    votes[chat_id] = {}

    vote_buttons = [
        [InlineKeyboardButton(player['name'], callback_data=f'vote_{player_id}')]
        for player_id, player in game.players.items()
    ]
    
    await context.bot.send_message(
        chat_id,
        "⏳ Час обговорення закінчився. Проголосуйте, кого виганяти!",
        reply_markup=InlineKeyboardMarkup(vote_buttons)
    )

async def vote_player(update: Update, context: CallbackContext) -> None:
    """Handle player voting"""
    query = update.callback_query
    chat_id = query.message.chat.id
    user_id = update.effective_user.id
    
    if chat_id not in games or chat_id not in votes:
        await query.answer("❌ Голосування не активне.")
        return

    game = games[chat_id]
    voted_player_id = int(query.data.split('_')[1])

    votes[chat_id][user_id] = voted_player_id
    await query.answer("✅ Ваш голос зараховано!")

    human_players = len([p for p in game.players.values() if not p['is_bot']])
    if len(votes[chat_id]) == human_players:
        await end_voting(chat_id, context)

async def end_voting(chat_id: int, context: CallbackContext) -> None:
    """Process voting results"""
    game = games[chat_id]
    vote_count = {}
    
    for voted_id in votes[chat_id].values():
        vote_count[voted_id] = vote_count.get(voted_id, 0) + 1

    kicked_id = max(vote_count, key=vote_count.get)
    kicked_player = game.players.pop(kicked_id)

    await context.bot.send_message(
        chat_id,
        f"🛑 {kicked_player['name']} ({kicked_player['profession']}) "
        f"виключений з бункера!"
    )

    if len(game.players) > 2:
        # Start next round
        await start_next_round(chat_id, context)
    else:
        # Game over
        winners = list(game.players.values())
        await context.bot.send_message(
            chat_id,
            f"🏆 Гра завершена! Переможці: {winners[0]['name']} і {winners[1]['name']}!"
        )
        del games[chat_id]
        del votes[chat_id]

async def settings(update: Update, context: CallbackContext) -> None:
    """Show settings menu"""
    query = update.callback_query
    chat_id = query.message.chat.id
    game = games[chat_id]
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⏲ {time}с {'✅' if game.discussion_time == time else ''}", 
                            callback_data=f'time_{time}')]
        for time in [30, 60, 90]
    ] + [[InlineKeyboardButton("⬅️ Назад", callback_data='back_to_main')]])
    
    await query.edit_message_text("⚙️ Налаштування гри:", reply_markup=buttons)

async def set_time(update: Update, context: CallbackContext) -> None:
    """Set discussion time"""
    query = update.callback_query
    chat_id = query.message.chat.id
    new_time = int(query.data.split('_')[1])
    
    games[chat_id].discussion_time = new_time
    await query.answer(f"⏲ Встановлено час обговорення: {new_time} секунд")
    await settings(update, context)

async def back_to_main(update: Update, context: CallbackContext) -> None:
    """Return to main menu"""
    await start(update, context)

def main() -> None:
    """Start the bot"""
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", lambda u, c: 
        u.message.reply_text("Використайте /start щоб почати нову гру!")))

    # Callback handlers
    application.add_handler(CallbackQueryHandler(handle_join, pattern='^join$'))
    application.add_handler(CallbackQueryHandler(start_game, pattern='^start_game$'))
    application.add_handler(CallbackQueryHandler(settings, pattern='^settings$'))
    application.add_handler(CallbackQueryHandler(set_time, pattern=r'^time_\d+$'))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern='^back_to_main$'))
    application.add_handler(CallbackQueryHandler(vote_player, pattern=r'^vote_\d+$'))

    application.run_polling()

if __name__ == '__main__':
    main()