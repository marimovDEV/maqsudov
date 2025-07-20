from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
import asyncio

TOKEN = "7706560271:AAHXKJy1qd1EKyYoQjunhdo_cvrFHkkprrw"
ADMIN_ID = 412216093

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Holatlar
class Form(StatesGroup):
    direction = State()
    date = State()
    phone = State()
    trip_type = State()
    car = State()
    address = State()
    comment = State()

# Tugmalar
direction_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Xorazmdan Buxoroga", callback_data="xb"),
            InlineKeyboardButton(text="Buxorodan Xorazmga", callback_data="bx")
        ]
    ]
)

trip_type_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Odam", callback_data="person"),
            InlineKeyboardButton(text="Pochta", callback_data="cargo")
        ]
    ]
)

car_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Kaptiva", callback_data="Kaptiva"),
         InlineKeyboardButton(text="Malibu", callback_data="Malibu")],
        [InlineKeyboardButton(text="Cobalt", callback_data="Cobalt"),
         InlineKeyboardButton(text="Gentra", callback_data="Gentra")],
        [InlineKeyboardButton(text="Largus", callback_data="Largus"),
         InlineKeyboardButton(text="Lasetti", callback_data="Lasetti")],
    ]
)

# START
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await message.answer("Yo‘nalishni tanlang:", reply_markup=direction_kb)
    await state.set_state(Form.direction)

# Yo‘nalish
@dp.callback_query(Form.direction)
async def choose_direction(callback: CallbackQuery, state: FSMContext):
    direction = "Xorazmdan Buxoroga" if callback.data == "xb" else "Buxorodan Xorazmga"
    await state.update_data(direction=direction)
    await callback.message.edit_text(f"Tanlangan yo‘nalish: {direction}")
    await callback.message.answer("Ketish sanasini yozing (masalan: 2025-06-15):")
    await state.set_state(Form.date)

@dp.message(Form.direction)
async def block_text(message: Message):
    await message.answer("Iltimos, tugmalardan foydalaning.")

# Sana
@dp.message(Form.date)
async def enter_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer("Telefon raqamingizni yozing:")
    await state.set_state(Form.phone)

# Telefon
@dp.message(Form.phone)
async def enter_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Odam yuborayapsizmi yoki pochta?", reply_markup=trip_type_kb)
    await state.set_state(Form.trip_type)

# Trip type
@dp.callback_query(Form.trip_type)
async def choose_type(callback: CallbackQuery, state: FSMContext):
    trip_type = "Odam" if callback.data == "person" else "Pochta"
    await state.update_data(trip_type=trip_type)
    await callback.message.edit_text(f"Tanlangan: {trip_type}")
    await callback.message.answer("Mashina turini tanlang:", reply_markup=car_kb)
    await state.set_state(Form.car)

@dp.message(Form.trip_type)
async def block_trip_type(message: Message):
    await message.answer("Iltimos, tugmalardan foydalaning.")

# Mashina
@dp.callback_query(Form.car)
async def choose_car(callback: CallbackQuery, state: FSMContext):
    await state.update_data(car=callback.data)
    await callback.message.edit_text(f"Tanlangan mashina: {callback.data}")
    await callback.message.answer("Qayerdan olib ketish kerak? Manzilni yozing:")
    await state.set_state(Form.address)

@dp.message(Form.car)
async def block_car_text(message: Message):
    await message.answer("Iltimos, tugmalardan foydalaning.")

# Manzil
@dp.message(Form.address)
async def enter_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer("Izoh qoldirmoqchimisiz? (ixtiyoriy):")
    await state.set_state(Form.comment)

# Izoh
@dp.message(Form.comment)
async def enter_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    data = await state.get_data()

    # Yuboriladigan matn
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
    await message.answer("Rahmat! Buyurtmangiz yuborildi ✅")
    await state.clear()

# Botni ishga tushirish
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
