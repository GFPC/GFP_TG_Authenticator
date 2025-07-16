# This project is developed by GFP.
import os
import asyncio
import json

from aiogram.filters import CommandStart
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
import uvicorn
from api import API, logger  # импортируем logger

load_dotenv()
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
API_SECRET = os.getenv("API_SECRET")
PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "localhost")

bot = Bot(token=TG_BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()
user_chats = {}
try:
    with open('configs.json', 'r') as f:
        configs = json.load(f)
except FileNotFoundError:
    logger.error("configs.json not found! Application will exit.")
    raise SystemExit(1)
api = API(configs=configs)
def parse_start_args(args: str):
    """
    Separates a string like 'phone_config' into phone and config.
    Returns (phone, config) or (None, None) if invalid.
    """
    if not args:
        return None, None
    if "_" in args:
        parts = args.split("_", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
    return None, None

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    args = ""
    if message.text:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            args = parts[1]
    phone, config = parse_start_args(args)
    if phone and config:
        user = await api.getUserByPhone(config, phone)
        if user.get("data",[]) == []:
            await message.answer("User not found. Please try again later.")
            return
        u_id = list(user.get("data", {"user":{}}).get("user",{}).keys())[0]
        u_tg = message.from_user.id
        logger.info(f"User {u_id} ({u_tg}) started with args: {args}")
        result = await api.editUser(config, u_id, u_tg)
        logger.info(f"Result: code={result.get('code')}, message={result.get('message')}")
        if result and result.get("success"):
            await message.answer("Your Telegram account has been successfully linked! No further action is required, codes will be sent automatically. Now return to the app/website and press the 'Send code' button.")
        elif result and result.get("message")=="busy user data: double tg":
            await message.answer("This account is already linked to another Telegram account. You will not be able to receive authorization codes in this account.")
        else:
            await message.answer("Error linking Telegram. Please try again later.")
    else:
        await message.answer("Hello!\nPlease access the bot only via the link provided in the app/website instructions.\nTo link your account, use the link with parameters or the command /start [phone]_[config].")

@app.post("/send-message")
async def send_code(request: Request):
    data = await request.json()
    code = data.get("code")
    user_id = data.get("user_id", None)  # Standard mode
    secret = request.headers.get("x-api-key", None)

    if secret != API_SECRET:
        logger.warning("Invalid API secret provided.")
        return JSONResponse(status_code=401, content={
            "code": 401,
            "status": "error",
            "message": "Invalid API secret.",
            "data": None
        })
    if not code or (not user_id):
        logger.warning("Code and user_id or (phone+config) required.")
        return JSONResponse(status_code=400, content={
            "code": 400,
            "status": "error",
            "message": "Code and user_id or (phone+config) required.",
            "data": None
        })

    # Standard mode: user_id is provided directly
    try:
        sent_message = await bot.send_message(user_id, f"Your authentication code: <b>{code}</b>", parse_mode="HTML")
        logger.info(f"Message sent to user_id {user_id}, message_id {sent_message.message_id}")
        return JSONResponse(status_code=200, content={
            "code": 200,
            "status": "success",
            "message": "Message sent successfully",
            "data": {
                "user_id": user_id,
                "message_id": sent_message.message_id,
                "date": sent_message.date.isoformat() if hasattr(sent_message, 'date') else None,
                "chat_id": sent_message.chat.id if hasattr(sent_message, 'chat') else None
            }
        })
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return JSONResponse(status_code=500, content={
            "code": 500,
            "status": "error",
            "message": f"Failed to send message: {e}",
            "data": None
        })

@app.middleware("http")
async def log_exceptions_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException as exc:
        logger.error(f"HTTPException: {exc.status_code} {exc.detail} | Path: {request.url.path} | Method: {request.method}")
        return JSONResponse(status_code=exc.status_code, content={
            "code": exc.status_code,
            "status": "error",
            "message": str(exc.detail),
            "data": None
        })
    except Exception as exc:
        logger.error(f"Unhandled Exception: {exc} | Path: {request.url.path} | Method: {request.method}")
        return JSONResponse(status_code=500, content={
            "code": 500,
            "status": "error",
            "message": "Internal server error",
            "data": None
        })

async def main():
    await api.auth()
    config = uvicorn.Config(app, host=HOST, port=PORT, loop="asyncio")
    server = uvicorn.Server(config)
    api_task = asyncio.create_task(server.serve())
    await dp.start_polling(bot)
    await api_task

if __name__ == "__main__":
    asyncio.run(main())
