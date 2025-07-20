import asyncio
import logging
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, BotCommand
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiohttp import web
from aiogram.webhook.aiohttp_server import setup_application
from config import BOT_TOKEN, ADMIN_ID, WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
import db

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set: {WEBHOOK_URL}")

def startup():
    db.init_db()

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("Webhook deleted")

# --- STATES ---
class AdminStates(StatesGroup):
    add_car = State()
    del_car = State()
    add_route = State()
    del_route = State()

class Form(StatesGroup):
    direction = State()
    date = State()
    phone = State()
    trip_type = State()
    car = State()
    address = State()
    comment = State()
    confirm = State()

# --- KEYBOARDS ---
def get_direction_kb():
    routes = db.get_routes()
    if not routes:
        # Default routes if db is empty
        routes = ["Xorazmdan Buxoroga", "Buxorodan Xorazmga"]
        for r in routes:
            db.add_route(r)
    buttons = [InlineKeyboardButton(text=route, callback_data=route) for route in routes]
    return InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons])

def get_trip_type_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Odam", callback_data="person"),
             InlineKeyboardButton(text="Pochta", callback_data="cargo")]
        ]
    )

def get_car_kb():
    cars = db.get_cars()
    if not cars:
        # Default cars if db is empty
        cars = ["Kaptiva", "Malibu", "Cobalt", "Gentra", "Largus", "Lasetti"]
        for c in cars:
            db.add_car(c)
    rows = []
    for i in range(0, len(cars), 2):
        row = []
        for j in range(2):
            if i + j < len(cars):
                row.append(InlineKeyboardButton(text=cars[i + j], callback_data=cars[i + j]))
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_confirm_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="confirm")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
        ]
    )

def get_admin_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Mashina qo'shish", callback_data="admin_add_car")],
            [InlineKeyboardButton(text="➖ Mashina o'chirish", callback_data="admin_del_car")],
            [InlineKeyboardButton(text="🚗 Mashinalar ro'yxati", callback_data="admin_list_car")],
            [InlineKeyboardButton(text="➕ Marshrut qo'shish", callback_data="admin_add_route")],
            [InlineKeyboardButton(text="➖ Marshrut o'chirish", callback_data="admin_del_route")],
            [InlineKeyboardButton(text="🛣 Marshrutlar ro'yxati", callback_data="admin_list_route")]
        ]
    )

# --- VALIDATORS ---
def is_valid_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def is_valid_phone(phone):
    return re.match(r"^(\+998|998)?\d{9}$", phone)

# --- COMMANDS ---
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    logging.info(f"/start from user_id={getattr(message.from_user, 'id', None)}")
    await state.clear()
    if message.from_user and hasattr(message.from_user, 'id') and hasattr(message.from_user, 'full_name'):
        db.add_user(message.from_user.id, message.from_user.full_name)
        logging.info(f"User registered: {message.from_user.id} {message.from_user.full_name}")
    await message.answer(
        "Assalomu alaykum!\n\nBuyurtma berish uchun yo'nalishni tanlang ",
        reply_markup=get_direction_kb()
    )
    await state.set_state(Form.direction)

@dp.message(Command("help"))
async def help_cmd(message: Message, state: FSMContext):
    logging.info(f"/help from user_id={getattr(message.from_user, 'id', None)}")
    await message.answer(
        "Bot yordamchisi:\n\n"
        "/start — Buyurtma berishni boshlash\n"
        "/cancel — Jarayonni bekor qilish\n"
        "/help — Yordam\n\n"
        "Buyurtma bosqichlarida tugmalardan foydalaning va ma'lumotlarni to'g'ri kiriting."
    )

@dp.message(Command("cancel"))
async def cancel_cmd(message: Message, state: FSMContext):
    logging.info(f"/cancel from user_id={getattr(message.from_user, 'id', None)}")
    await state.clear()
    await message.answer("Buyurtma bekor qilindi. /start orqali yangidan boshlang.")

@dp.message(Command("stats"))
async def stats_cmd(message: Message):
    logging.info(f"/stats from user_id={getattr(message.from_user, 'id', None)}")
    if message.from_user and hasattr(message.from_user, 'id') and message.from_user.id == ADMIN_ID:
        orders = db.get_orders()
        await message.answer(f"Jami buyurtmalar: {len(orders)}")
    else:
        await message.answer("Bu buyruq faqat admin uchun.")

@dp.message(Command("adminhelp"))
async def admin_help(message: Message):
    logging.info(f"/adminhelp from user_id={getattr(message.from_user, 'id', None)}")
    if message.from_user and hasattr(message.from_user, 'id') and message.from_user.id == ADMIN_ID:
        await message.answer(
            "Admin uchun buyruqlar:\n"
            "/admin — Admin panel\n"
            "/adminhelp — Admin uchun yordam\n"
            "/stats — Buyurtmalar statistikasi\n"
            "/users — Foydalanuvchilar soni\n\n"
            "Panelda: Mashina va marshrutlarni qo'shish/o'chirish/ko'rish."
        )
    else:
        await message.answer("Bu buyruq faqat admin uchun.")

@dp.message(Command("users"))
async def users_count(message: Message):
    logging.info(f"/users from user_id={getattr(message.from_user, 'id', None)}")
    if message.from_user and hasattr(message.from_user, 'id') and message.from_user.id == ADMIN_ID:
        count = db.get_users_count() if hasattr(db, 'get_users_count') else 0
        await message.answer(f"Jami foydalanuvchilar: {count}")
    else:
        await message.answer("Bu buyruq faqat admin uchun.")

# --- ADMIN PANEL ---
@dp.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    logging.info(f"/admin from user_id={getattr(message.from_user, 'id', None)}")
    if message.from_user and hasattr(message.from_user, 'id') and message.from_user.id != ADMIN_ID:
        await message.answer("Bu bo'lim faqat admin uchun.")
        return
    await message.answer("Admin paneliga xush kelibsiz!", reply_markup=get_admin_kb())

@dp.callback_query(F.data.startswith("admin_"))
async def admin_actions(callback: CallbackQuery, state: FSMContext):
    logging.info(f"Admin action: {callback.data} from user_id={getattr(callback.from_user, 'id', None)}")
    if not callback.from_user or not hasattr(callback.from_user, 'id') or callback.from_user.id != ADMIN_ID:
        await callback.answer("Faqat admin uchun!", show_alert=True)
        return
    user_id = callback.from_user.id if callback.from_user and hasattr(callback.from_user, 'id') else None
    async def safe_answer(text, reply_markup=None):
        if callback.message:
            return await callback.message.answer(text, reply_markup=reply_markup)
        elif user_id:
            return await bot.send_message(user_id, text, reply_markup=reply_markup)
        else:
            return await asyncio.sleep(0)
    if callback.data == "admin_add_car":
        await safe_answer("Yangi mashina nomini kiriting:")
        await state.set_state(AdminStates.add_car)
    elif callback.data == "admin_del_car":
        cars = db.get_cars()
        if not cars:
            await safe_answer("Mashinalar ro'yxati bo'sh.")
            return
        text = "O'chirmoqchi bo'lgan mashina nomini kiriting (aniq nom):\n" + ", ".join(cars)
        await safe_answer(text)
        await state.set_state(AdminStates.del_car)
    elif callback.data == "admin_list_car":
        cars = db.get_cars()
        if not cars:
            await safe_answer("Mashinalar ro'yxati bo'sh.")
        else:
            await safe_answer("Mashinalar ro'yxati:\n" + ", ".join(cars))
    elif callback.data == "admin_add_route":
        await safe_answer("Yangi marshrut nomini kiriting:")
        await state.set_state(AdminStates.add_route)
    elif callback.data == "admin_del_route":
        routes = db.get_routes()
        if not routes:
            await safe_answer("Marshrutlar ro'yxati bo'sh.")
            return
        text = "O'chirmoqchi bo'lgan marshrut nomini kiriting (aniq nom):\n" + ", ".join(routes)
        await safe_answer(text)
        await state.set_state(AdminStates.del_route)
    elif callback.data == "admin_list_route":
        routes = db.get_routes()
        if not routes:
            await safe_answer("Marshrutlar ro'yxati bo'sh.")
        else:
            await safe_answer("Marshrutlar ro'yxati:\n" + ", ".join(routes))

@dp.message(AdminStates.add_car)
async def admin_add_car(message: Message, state: FSMContext):
    car = (message.text or '').strip()
    if not car:
        if message:
            await message.answer("Mashina nomi bo'sh bo'lishi mumkin emas.")
        return
    if db.add_car(car):
        if message:
            await message.answer(f"{car} mashinasi muvaffaqiyatli qo'shildi!", reply_markup=get_admin_kb())
    else:
        if message:
            await message.answer("Bu mashina allaqachon ro'yxatda mavjud.")
    await state.clear()

@dp.message(AdminStates.del_car)
async def admin_del_car(message: Message, state: FSMContext):
    car = (message.text or '').strip()
    if not car:
        if message:
            await message.answer("Mashina nomi bo'sh bo'lishi mumkin emas.")
        return
    db.remove_car(car)
    if message:
        await message.answer(f"{car} mashinasi o'chirildi!", reply_markup=get_admin_kb())
    await state.clear()

@dp.message(AdminStates.add_route)
async def admin_add_route(message: Message, state: FSMContext):
    route = (message.text or '').strip()
    if not route:
        if message:
            await message.answer("Marshrut nomi bo'sh bo'lishi mumkin emas.")
        return
    if db.add_route(route):
        if message:
            await message.answer(f"{route} marshruti muvaffaqiyatli qo'shildi!", reply_markup=get_admin_kb())
    else:
        if message:
            await message.answer("Bu marshrut allaqachon ro'yxatda mavjud.")
    await state.clear()

@dp.message(AdminStates.del_route)
async def admin_del_route(message: Message, state: FSMContext):
    route = (message.text or '').strip()
    if not route:
        if message:
            await message.answer("Marshrut nomi bo'sh bo'lishi mumkin emas.")
        return
    db.remove_route(route)
    if message:
        await message.answer(f"{route} marshruti o'chirildi!", reply_markup=get_admin_kb())
    await state.clear()

# --- USER ORDER FLOW ---
@dp.callback_query(Form.direction)
async def choose_direction(callback: CallbackQuery, state: FSMContext):
    logging.info(f"choose_direction: {callback.data} from user_id={getattr(callback.from_user, 'id', None)}")
    direction = callback.data
    await state.update_data(direction=direction)
    user_id = callback.from_user.id if callback.from_user and hasattr(callback.from_user, 'id') else None
    if callback.message and hasattr(callback.message, 'edit_text'):
        await callback.message.edit_text(f"Tanlangan yo‘nalish: {direction}")
        await callback.message.answer("Ketish sanasini yozing (masalan: 2025-06-15):")
    elif user_id:
        await bot.send_message(user_id, f"Tanlangan yo‘nalish: {direction}")
        await bot.send_message(user_id, "Ketish sanasini yozing (masalan: 2025-06-15):")
    else:
        await callback.answer(f"Tanlangan yo‘nalish: {direction}")
        await callback.answer("Ketish sanasini yozing (masalan: 2025-06-15):")
    await state.set_state(Form.date)

@dp.message(Form.direction)
async def block_text(message: Message):
    await message.answer("Iltimos, tugmalardan foydalaning.")

@dp.message(Form.date)
async def enter_date(message: Message, state: FSMContext):
    logging.info(f"enter_date: {message.text} from user_id={getattr(message.from_user, 'id', None)}")
    if not is_valid_date(message.text):
        await message.answer("Sana noto‘g‘ri formatda. To‘g‘ri format: YYYY-MM-DD (masalan: 2025-06-15)")
        return
    await state.update_data(date=message.text)
    await message.answer("Telefon raqamingizni yozing (masalan: +998901234567 yoki 998901234567):")
    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def enter_phone(message: Message, state: FSMContext):
    logging.info(f"enter_phone: {message.text} from user_id={getattr(message.from_user, 'id', None)}")
    if not is_valid_phone(message.text):
        await message.answer("Telefon raqami noto‘g‘ri formatda. To‘g‘ri format: +998901234567 yoki 998901234567")
        return
    await state.update_data(phone=message.text)
    if message.from_user and hasattr(message.from_user, 'id'):
        db.update_user_phone(message.from_user.id, message.text)
    await message.answer("Odam yuborayapsizmi yoki pochta?", reply_markup=get_trip_type_kb())
    await state.set_state(Form.trip_type)

@dp.callback_query(Form.trip_type)
async def choose_type(callback: CallbackQuery, state: FSMContext):
    logging.info(f"choose_type: {callback.data} from user_id={getattr(callback.from_user, 'id', None)}")
    trip_type = "Odam" if callback.data == "person" else "Pochta"
    await state.update_data(trip_type=trip_type)
    user_id = callback.from_user.id if callback.from_user and hasattr(callback.from_user, 'id') else None
    if callback.message and hasattr(callback.message, 'edit_text'):
        await callback.message.edit_text(f"Tanlangan: {trip_type}")
        await callback.message.answer("Mashina turini tanlang:", reply_markup=get_car_kb())
    elif user_id:
        await bot.send_message(user_id, f"Tanlangan: {trip_type}")
        await bot.send_message(user_id, "Mashina turini tanlang:", reply_markup=get_car_kb())
    else:
        await callback.answer(f"Tanlangan: {trip_type}")
        await callback.answer("Mashina turini tanlang:")
    await state.set_state(Form.car)

@dp.message(Form.trip_type)
async def block_trip_type(message: Message):
    await message.answer("Iltimos, tugmalardan foydalaning.")

@dp.callback_query(Form.car)
async def choose_car(callback: CallbackQuery, state: FSMContext):
    logging.info(f"choose_car: {callback.data} from user_id={getattr(callback.from_user, 'id', None)}")
    await state.update_data(car=callback.data)
    user_id = callback.from_user.id if callback.from_user and hasattr(callback.from_user, 'id') else None
    if callback.message and hasattr(callback.message, 'edit_text'):
        await callback.message.edit_text(f"Tanlangan mashina: {callback.data}")
        await callback.message.answer("Qayerdan olib ketish kerak? Manzilni yozing:")
    elif user_id:
        await bot.send_message(user_id, f"Tanlangan mashina: {callback.data}")
        await bot.send_message(user_id, "Qayerdan olib ketish kerak? Manzilni yozing:")
    else:
        await callback.answer(f"Tanlangan mashina: {callback.data}")
        await callback.answer("Qayerdan olib ketish kerak? Manzilni yozing:")
    await state.set_state(Form.address)

@dp.message(Form.car)
async def block_car_text(message: Message):
    await message.answer("Iltimos, tugmalardan foydalaning.")

@dp.message(Form.address)
async def enter_address(message: Message, state: FSMContext):
    logging.info(f"enter_address: {message.text} from user_id={getattr(message.from_user, 'id', None)}")
    await state.update_data(address=message.text)
    await message.answer("Izoh qoldirmoqchimisiz? (ixtiyoriy, yoki '-' deb yozing):")
    await state.set_state(Form.comment)

@dp.message(Form.comment)
async def enter_comment(message: Message, state: FSMContext):
    logging.info(f"enter_comment: {message.text} from user_id={getattr(message.from_user, 'id', None)}")
    comment = message.text.strip() if message.text and hasattr(message.text, 'strip') and message.text.strip() != "-" else "Yo‘q"
    await state.update_data(comment=comment)
    data = await state.get_data()
    text = (
        "🚕 Yangi buyurtma:\n"
        f"📍 Yo‘nalish: {data['direction']}\n"
        f"📅 Sana: {data['date']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📦 Turi: {data['trip_type']}\n"
        f"🚗 Mashina: {data['car']}\n"
        f"📍 Manzil: {data['address']}\n"
        f"📝 Izoh: {data['comment']}\n\n"
        "Tasdiqlaysizmi?"
    )
    await message.answer(text, reply_markup=get_confirm_kb())
    await state.set_state(Form.confirm)

@dp.callback_query(Form.confirm, F.data == "confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    logging.info(f"confirm_order from user_id={getattr(callback.from_user, 'id', None)}")
    data = await state.get_data()
    user_id = callback.from_user.id if callback.from_user and hasattr(callback.from_user, 'id') else None
    db.add_order(
        user_id=user_id,
        direction=data['direction'],
        date=data['date'],
        phone=data['phone'],
        trip_type=data['trip_type'],
        car=data['car'],
        address=data['address'],
        comment=data['comment']
    )
    text = (
        "🚕 Yangi buyurtma:\n"
        f"📍 Yo‘nalish: {data['direction']}\n"
        f"📅 Sana: {data['date']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📦 Turi: {data['trip_type']}\n"
        f"🚗 Mashina: {data['car']}\n"
        f"📍 Manzil: {data['address']}\n"
        f"📝 Izoh: {data['comment']}"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=text)
    if callback.message and hasattr(callback.message, 'edit_text'):
        await callback.message.edit_text("Rahmat! Buyurtmangiz yuborildi ✅")
    elif user_id:
        await bot.send_message(user_id, "Rahmat! Buyurtmangiz yuborildi ✅")
    else:
        await callback.answer("Rahmat! Buyurtmangiz yuborildi ✅")
    await state.clear()

@dp.callback_query(Form.confirm, F.data == "cancel")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    logging.info(f"cancel_order from user_id={getattr(callback.from_user, 'id', None)}")
    user_id = callback.from_user.id if callback.from_user and hasattr(callback.from_user, 'id') else None
    if callback.message and hasattr(callback.message, 'edit_text'):
        await callback.message.edit_text("Buyurtma bekor qilindi.")
    elif user_id:
        await bot.send_message(user_id, "Buyurtma bekor qilindi.")
    else:
        await callback.answer("Buyurtma bekor qilindi.")
    await state.clear()

@dp.message(Form.confirm)
async def block_confirm(message: Message):
    await message.answer("Iltimos, tugmalardan foydalaning.")

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Botni boshlash"),
        BotCommand(command="help", description="Yordam"),
        BotCommand(command="cancel", description="Buyurtmani bekor qilish"),
    ]
    await bot.set_my_commands(commands)

async def main():
    startup()
    await set_bot_commands(bot)
    app = web.Application()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    setup_application(app, dp, bot=bot)
    logging.info(f"Webhook server running at {WEBAPP_HOST}:{WEBAPP_PORT}{WEBHOOK_PATH}")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, WEBAPP_HOST, WEBAPP_PORT)
    await site.start()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main()) 