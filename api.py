# This project is developed by GFP.
import asyncio
import json

import aiohttp
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

URL_PATTERN = "https://ibronevik.ru/taxi/c/^CONFIG^/api/v1/"

# Load configs from JSON file
with open('configs.json', 'r') as f:
    configs = json.load(f)

# Setup logger
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def async_post(url: str, data: dict = None, headers: dict = None) -> dict:
    """
    Асинхронно отправляет POST-запрос по указанному url с data и headers.
    :param url: URL для запроса
    :param data: Данные (dict), которые будут отправлены как JSON
    :param headers: Заголовки (dict)
    :return: Ответ сервера (dict)
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()

class API:
    def __init__(self, configs: {}):
        self.configs = configs
        self.auth_data = {}

    async def auth(self):
        async def auth_one(i):
            data = {
                "login": self.configs[i]["login"],
                "password": self.configs[i]["password"],
                "type": self.configs[i]["type"]
            }
            logger.info(f"Authenticating config: {i}")
            response = await async_post(URL_PATTERN.replace("^CONFIG^", i) + "auth", data=data)
            if response.get("auth_hash"):
                auth_hash = response["auth_hash"]
                data = {"auth_hash": auth_hash}
                response2 = await async_post(URL_PATTERN.replace("^CONFIG^", i) + "token", data=data)
                if response2.get("data") and response2["data"].get("token") and response2["data"].get("u_hash"):
                    self.auth_data[i] = {
                        "token": response2["data"]["token"],
                        "u_hash": response2["data"]["u_hash"]
                    }
                    logger.info(f"[api] (✔) Auth success: {i}")
                else:
                    logger.error(f"[api] (✖) Auth failed: {i}, can't get token or u_hash from /token")
            else:
                logger.error(f"[api] (✖) Auth failed: {i}, can't get auth_hash from /auth")
        await asyncio.gather(*(auth_one(i) for i in self.configs))
        return "OK"
    async def getUserByPhone(self, config, phone):
        if not self.auth_data.get(config):
            logger.error(f"[api] (✖) Can't get auth data for config: {config}")
            return None
        data = {
            "token": self.auth_data[config]["token"],
            "u_hash": self.auth_data[config]["u_hash"],
            "u_a_phone": phone
        }
        logger.info(f"Getting user by phone for config: {config}, phone: {phone}")
        response = await async_post(URL_PATTERN.replace("^CONFIG^", config) + "user", data=data)
        logger.info(f"User by phone response: {response}")
        return response
    async def editUser(self, config, u_id, u_tg):
        if not self.auth_data.get(config):
            logger.error(f"[api] (✖) Can't get auth data for config: {config}")
            return None
        data = {
            "token": self.auth_data[config]["token"],
            "u_hash": self.auth_data[config]["u_hash"],
            "data": json.dumps({
                "u_tg": u_tg
            })
        }
        logger.info(f"Editing user {u_id} for config: {config}, set u_tg: {u_tg}")
        response = await async_post(URL_PATTERN.replace("^CONFIG^", config) + "user/" + str(u_id), data=data)
        logger.info(f"Edit user response: {response}")
        return response