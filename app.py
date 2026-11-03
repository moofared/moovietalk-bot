import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("9061459483:AAHJLbslFzBvy9tr9aCqPKRqSNWGnLd0WYM")
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


def telegram(method, payload=None):
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

    return telegram("sendMessage", data)


def answer_callback(callback_id):
    return telegram(
        "answerCallbackQuery",
        {"callback_query_id": callback_id}
    )


def get_chat_member(chat_id, user_id):
    try:
        result = telegram(
            "getChatMember",
            {
                "chat_id": chat_id,
                "user_id": user_id
            }
        )

        if result.get("ok"):
            return result.get("result")

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
        "علشان تدخل المحتوى، اشترك في القناتين ثم اضغط:\n\n"
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
        text = message.get("text", "").strip()
        chat_id = message["chat"]["id"]

        if text == "/start":
            send_welcome(chat_id)

    if "callback_query" in update:

        callback = update["callback_query"]
        callback_id = callback["id"]
        data = callback.get("data")
        chat_id = callback["message"]["chat"]["id"]

        if data == "check":

            answer_callback(callback_id)

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

            answer_callback(callback_id)

            send_message(
                chat_id,
                "🎬 قسم الأفلام\n\n"
                "القسم جاهز لإضافة محتوى الأفلام."
            )

        elif data == "series":

            answer_callback(callback_id)

            send_message(
                chat_id,
                "📺 قسم المسلسلات\n\n"
                "القسم جاهز لإضافة محتوى المسلسلات."
            )


@app.get("/")
def home():
    return "MoovieTalk Bot is running ✅", 200


@app.post("/webhook")
def webhook():

    try:
        update = request.get_json(silent=True) or {}
        handle_update(update)

    except Exception as error:
        app.logger.exception(error)

    return "OK", 200


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
