from flask import Flask, request
from bot import Bot
import os

TOKEN = os.environ.get('VK_TOKEN')
confirmation_code = os.environ.get('VK_CONF')
SECRET = os.environ.get('VK_SECRET')

server = Flask(__name__)
bot = Bot(token=TOKEN)

last_msg = None

@server.route('/'+SECRET, methods=['POST'])
def handle():
    data = request.get_json(force=True, silent=True)
    if not data or 'type' not in data:
        return 'not ok'
    if data['type'] == 'confirmation':
        return confirmation_code
    elif data['type'] == 'message_new':
        global last_msg
        if data != last_msg:
            last_msg = data
            bot.handle(data)
        return 'ok'
    return 'ok'

@server.route('/', methods=["GET"])
def index():
    return "alive", 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
