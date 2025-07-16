# TGAuthenticator

**This project is developed by GFP.**

## Overview
TGAuthenticator is a Telegram bot and API service for securely linking user accounts and delivering authentication codes via Telegram. It is designed for integration with external applications or websites that require two-factor authentication or code delivery to users through Telegram.

### How it works
- The bot links a user's Telegram account to their application account using a special `/start` command with parameters (phone and config).
- The backend API can send authentication codes to users by making a POST request to the bot's API endpoint.
- All configuration for external services is stored in `configs.json`.
- Logging is performed per day in the `logs` directory.

## API Developer Guide

### 1. Linking a Telegram account
To link a user's Telegram account:
- Generate a link for the user in the format: `https://t.me/<your_bot_username>?start=<phone>_<config>`
- When the user starts the bot with this link, their Telegram ID will be linked to their account in your system.

### 2. Sending an authentication code
To send an authentication code to a user, make a POST request to the following endpoint:

**Endpoint:**
```
POST /send-message
```

**Full Example Request:**
```
POST http://<your_server>:<port>/send-message
Headers:
  Content-Type: application/json
  x-api-key: <API_SECRET>
Body:
{
  "user_id": <telegram_user_id>,
  "code": "123456"
}
```

- **URL:** Replace `<your_server>` and `<port>` with your actual host and port (see .env `HOST` and `PORT`).
- **Headers:**
  - `Content-Type: application/json` — required
  - `x-api-key: <API_SECRET>` — required, must match your .env
- **Body:**
  - `user_id` (integer, required): Telegram user ID to send the code to (must be previously linked)
  - `code` (string, required): The authentication code to deliver

**Example using curl:**
```
curl -X POST http://localhost:8000/send-message \
  -H "Content-Type: application/json" \
  -H "x-api-key: <API_SECRET>" \
  -d '{"user_id":123456789, "code":"123456"}'
```

**Response:**
- All responses use the unified format described below (see API Response Format).
- On success, you will receive:
```
{
  "code": 200,
  "status": "success",
  "message": "Message sent successfully",
  "data": {
    "user_id": 123456789,
    "message_id": 1234,
    "date": "2024-07-16T12:34:56+00:00",
    "chat_id": 123456789
  }
}
```
- On error, see error examples in the API Response Format section below.

### 3. API Response Format
All API responses are returned in a unified JSON format:

```
{
  "code": <int>,
  "status": "success" | "error",
  "message": <string>,
  "data": <object|null>
}
```

#### Example: Success
```
{
  "code": 200,
  "status": "success",
  "message": "Message sent successfully",
  "data": {
    "user_id": 123456789,
    "message_id": 1234,
    "date": "2024-07-16T12:34:56+00:00",
    "chat_id": 123456789
  }
}
```

- `user_id`: Telegram user ID
- `message_id`: ID of the sent Telegram message
- `date`: ISO8601 date/time when the message was sent
- `chat_id`: Telegram chat ID (usually same as user_id for private chats)

#### Example: Error (Invalid API secret)
```
{
  "code": 401,
  "status": "error",
  "message": "Invalid API secret.",
  "data": null
}
```

#### Example: Error (Missing fields)
```
{
  "code": 400,
  "status": "error",
  "message": "Code and user_id or (phone+config) required.",
  "data": null
}
```

#### Example: Error (Internal server error)
```
{
  "code": 500,
  "status": "error",
  "message": "Internal server error",
  "data": null
}
```

### 4. Configuration
- All external service configs are stored in `configs.json`.
- Update this file to add or modify service credentials.

### 5. Logging
- All logs are written to `logs/YYYY-MM-DD.log`.
- Logs include authentication attempts, user linking, message delivery events, and all HTTP errors.

## Running the Project
1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Set environment variables in a `.env` file:
   - `TG_BOT_TOKEN` — Telegram bot token
   - `API_SECRET` — Secret key for API authentication
   - `PORT` — (optional) Port for the FastAPI server (default: 8000)
   - `HOST` — (optional) Host for the FastAPI server (default: localhost)
   - `API_URL` — (optional) URL for external API (default: http://localhost:8000/send-message)
3. Start the bot and API server:
   ```
   python main.py
   ```

## Example
To link a user:
- Send them a link: `https://t.me/YourBotUsername?start=79991234567_gruzvill`

To send a code:
- Make a POST request:
```
curl -X POST http://localhost:8000/send-message \
  -H "Content-Type: application/json" \
  -H "x-api-key: <API_SECRET>" \
  -d '{"user_id":123456789, "code":"123456"}'
``` 

## DevOps: Running as a systemd Service

1. Edit `tg_authenticator.service`:
   - Set `WorkingDirectory` and `EnvironmentFile` to your project path
   - Set `User` to the user that should run the service
2. Install the service:
   ```
   sh install_tg_authenticator.sh
   ```
   - The script copies the service file, reloads systemd, enables and starts the service.
   - No need to run `chmod +x` on the script; it does not change its own permissions, so git will not see it as modified.
3. Check status:
   ```
   sudo systemctl status tg_authenticator.service
   ```
4. Logs:
   ```
   sudo journalctl -u tg_authenticator.service
   ``` 