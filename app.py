import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

CHANNELS = [
    {
        "name": "📺 قناة المسلسلات",
        "chat_id": "-1003311498383",
        "invite": "https://t.me/+Ufb3FJpNAj4wYzNk"
    },
    {
        "name": "🎬 قناة الأفلام",
        "chat_id": "-1003332907628",
        "invite": "https://t.me/+cILnHs01BzRiNzVk"
    }
]


def tg(method, payload=None):
    response = requests.post(
        f"{API}/{method}",
        json=payload or {},
        timeout=20
    )
    return response.json()


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return tg("sendMessage", data)


def answer_callback(callback_id):
    return tg(
        "answerCallbackQuery",
        {"callback_query_id": callback_id}
    )


def get_chat_member(chat_id, user_id):
    try:
        data = tg(
            "getChatMember",
            {
                "chat_id": chat_id,
                "user_id": user_id
            }
        )

        if data.get("ok"):
            return data.get("result")

    except Exception:
        pass

    return None


def is_subscribed(user_id):
    for channel in CHANNELS:
        member = get_chat_member(
            channel["chat_id"],
            user_id
        )

        if not member:
            return False

        if member.get("status") not in (
            "member",
            "administrator",
            "creator"
        ):
            return False

    return True


def send_welcome(chat_id):
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "📺 اشترك في قناة المسلسلات",
                    "url": CHANNELS[0]["invite"]
                }
            ],
            [
                {
                    "text": "🎬 اشترك في قناة الأفلام",
                    "url": CHANNELS[1]["invite"]
                }
            ],
            [
                {
                    "text": "✅ تحقق من الاشتراك",
                    "callback_data": "check"
                }
            ]
        ]
    }

    send_message(
        chat_id,
        "👋 أهلاً بيك في MoovieTalk\n\n"
        "علشان تدخل المحتوى، اشترك في القناتين ثم اضغط على:\n\n"
        "✅ تحقق من الاشتراك",
        keyboard
    )


def show_menu(chat_id):
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "🎬 الأفلام",
                    "callback_data": "movies"
                },
                {
                    "text": "📺 المسلسلات",
                    "callback_data": "series"
                }
            ]
        ]
    }

    send_message(
        chat_id,
        "✅ تم التحقق من اشتراكك بنجاح!\n\n"
        "🎬 أهلاً بيك في MoovieTalk\n\n"
        "اختار القسم اللي عايز تدخل عليه:",
        keyboard
    )


def handle_update(update):

    if "message" in update:
        message = update["message"]

        if message.get("text", "").strip() == "/start":
            send_welcome(message["chat"]["id"])

    if "callback_query" in update:

        callback = update["callback_query"]

        chat_id = callback["message"]["chat"]["id"]
        data = callback.get("data")

        if data == "check":

            answer_callback(callback["id"])

            if is_subscribed(chat_id):
                show_menu(chat_id)
            else:
                send_welcome(chat_id)

                send_message(
                    chat_id,
                    "❌ لسه مش مشترك في القناتين.\n\n"
                    "اشترك في القناتين ثم اضغط "
                    "«تحقق من الاشتراك» مرة تانية."
                )

        elif data == "movies":

            answer_callback(callback["id"])

            send_message(
                chat_id,
                "🎬 قسم الأفلام\n\n"
                "القسم جاهز لإضافة محتوى الأفلام."
            )

        elif data == "series":

            answer_callback(callback["id"])

            send_message(
                chat_id,
                "📺 قسم المسلسلات\n\n"
                "القسم جاهز لإضافة محتوى المسلسلات."
            )


def set_webhook():

    webhook_url = os.environ.get("WEBHOOK_URL")

    if not TOKEN or not webhook_url:
        return

    try:
        tg(
            "setWebhook",
            {
                "url": webhook_url
            }
        )

    except Exception as e:
        app.logger.exception(e)


@app.get("/")
def home():
    return "MoovieTalk Bot is running ✅", 200


@app.post("/webhook")
def webhook():

    try:
        update = request.get_json(silent=True) or {}
        handle_update(update)

    except Exception as e:
        app.logger.exception(e)

    return "OK", 200

