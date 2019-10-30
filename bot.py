import vk_api, pytesseract, requests, io, re, time, json
from PIL import Image
from vk_api.bot_longpoll import VkBotMessageEvent

class Bot:
    def __init__(self, token):
        self.token = token
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()
        self.text_commands = {'/ocr': self.ocr, '/trans': self.trans,
                              '/ping': self.ping, '/json': self.json}
        self.commands = {'/echo': self.echo}
        self.commands.update(self.text_commands)

    def handle(self, data):
        event = VkBotMessageEvent(data)
        msg = event.object
        command = self.get_command(msg).lower()
        if command in self.text_commands:
            self.send(self.text_commands[command](msg), msg.from_id)
        elif command in self.commands:
            self.commands[command](msg)

    def send(self, text, to=None, attachments=None):
        if not text and not attachments:
            text = 'empty'
        text = str(text)
        if not to:
            to = self.admin_id
        if attachments:
            att = []
            for doc in attachments:
                d = doc[doc['type']]
                s = f"{doc['type']}{d['owner_id']}_{d['id']}"
                if 'access_key' in d:
                    s += '_' + d['access_key']
                att.append(s)
            attachments = ','.join(att)
        rd_id = vk_api.utils.get_random_id()
        self.vk.messages.send(user_id=to, random_id=rd_id, message=text[:4000],
                              attachment=attachments)
        if len(text) > 4000:
            time.sleep(0.4)
            self.send(text[4000:], to)

    def get_command(self, msg):
        text = msg.text
        if len(text) == 0:
            return None
        else:
            return text.split()[0]

    def get_args(self, msg):
        r = re.search('(?<= ).*$', msg.text)
        return r.group() if r else ''

    def ocr(self, msg):
        lang = self.get_args(msg)
        if not lang:
            lang = 'eng'
        for attachment in msg.attachments:
            if attachment['type'] == 'photo':
                for size in reversed(attachment['photo']['sizes']):
                    if size['type'] not in 'opqr':
                        url = size['url']
                        break
                r = requests.get(url)
                try:
                    txt = pytesseract.image_to_string(Image.open(io.BytesIO(r.content)), lang=lang)
                except pytesseract.pytesseract.TesseractError as e:
                    return 'Error: language not supported'
                else:
                    return txt

    def json(self, msg):
        return json.dumps(dict(msg), indent=2, ensure_ascii=False)

    def trans(self, msg):
        ru_layout = 'йцукенгшщзхъфывапролджэ\\ячсмитьбю.ЙЦУКЕНГШЩЗхъФЫВАПРОЛДжэ\\ЯЧСМИТЬбю.'
        en_layout = 'qwertyuiop[]asdfghjkl;\'\\zxcvbnm,./QWERTYUIOP[]ASDFGHJKL;\'\\ZXCVBNM,./'
        trtab = str.maketrans(ru_layout + en_layout, en_layout + ru_layout)
        return self.get_args(msg).translate(trtab)

    def ping(self, msg):
        return 'pong'
   
    def echo(self, msg):
        self.send(self.get_args(msg), msg.from_id, msg.attachments)
