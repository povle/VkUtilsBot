import vk_api, pytesseract, requests, io, re, time, json, inspect
from PIL import Image
from vk_api.bot_longpoll import VkBotMessageEvent

class Bot:
    def __init__(self, token):
        self.token = token
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()
        self.text_commands = {'/ocr': self.ocr, '/trans': self.trans,
                              '/ping': self.ping, '/json': self.json,
                              '/help': self.help}
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

    def send(self, text, to=None, attachments=[], photos=[]):
        if not text and not attachments:
            text = 'empty'
        text = str(text)
        if not to:
            to = self.admin_id

        _attachments = []
        for doc in attachments:
            d = doc[doc['type']]
            s = f"{doc['type']}{d['owner_id']}_{d['id']}"
            if 'access_key' in d:
                s += '_' + d['access_key']
            _attachments.append(s)
        if photos:
            upload = vk_api.VkUpload(self.vk_session)
            for photo in upload.photo_messages(photos=photos):
                _attachments.append(f"photo{photo['owner_id']}_{photo['id']}")

        rd_id = vk_api.utils.get_random_id()
        self.vk.messages.send(user_id=to, random_id=rd_id, message=text[:4000],
                              attachment=','.join(_attachments))
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
        """распознает текст в полученных фото (по умолчанию английский, /ocr rus для русского)"""
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
                except pytesseract.pytesseract.TesseractError:
                    return 'Error: language not supported'
                else:
                    return txt

    def json(self, msg):
        """присылает json полученного сообщения"""
        return json.dumps(dict(msg), indent=2, ensure_ascii=False)

    def trans(self, msg):
        """перевод раскладки, например: /trans ghbdtn"""
        ru_layout = 'йцукенгшщзхъфывапролджэ\\ячсмитьбю.ЙЦУКЕНГШЩЗхъФЫВАПРОЛДжэ\\ЯЧСМИТЬбю.'
        en_layout = 'qwertyuiop[]asdfghjkl;\'\\zxcvbnm,./QWERTYUIOP[]ASDFGHJKL;\'\\ZXCVBNM,./'
        trtab = str.maketrans(ru_layout + en_layout, en_layout + ru_layout)
        return self.get_args(msg).translate(trtab)

    def ping(self, msg):
        """пинг"""
        return 'pong'

    def echo(self, msg):
        """присылает полученное фото ответным сообщением"""
        photos = []
        for att in msg.attachments:
            if att['type'] == 'photo':
                photo = att['photo']
                url = max(photo['sizes'], key=lambda x: x['width']*x['height'])['url']
                photos.append(io.BytesIO(requests.get(url).content))
        self.send(self.get_args(msg), msg.from_id, photos=photos)

    def help(self, msg):
        """список команд"""
        message = ''
        for command in self.commands:
            message += f'{command} - {inspect.getdocs(self.commands[command])}\n'
        return message
