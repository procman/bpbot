from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator, validate_token
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatCommand, ChatUser

import asyncio
import csv
import os.path
from operator import attrgetter
import configparser

AUTH_SCOPE = [
    AuthScope.CHAT_READ,
    AuthScope.CHAT_EDIT,
]

CONFIG_FILE = 'config.ini'
TOKEN_FILE = 'token.ini'

TOP_N = 3

async def is_token_valid(token):
    msg = await validate_token(token)
    return 'client_id' in msg

def is_broadcaster(user: ChatUser):
    return 'broadcaster' in user.badges

class BPBot:
    def __init__(self, chat: Chat, config):
        self.bp = BPTable(config['DEFAULT']['BP_FILE'], int(config['DEFAULT']['INITIAL_BP']))
        self.config = config
        self.chat = chat
        self.chat.register_event(ChatEvent.READY, self.on_ready)
        self.chat.register_command('bp-add', self.bp_add)
        self.chat.register_command('bp-remove', self.bp_remove)
        self.chat.register_command('bp-give', self.bp_give)
        self.chat.register_command('bp-take', self.bp_give)
        self.chat.register_command('bp-set', self.bp_set)
        self.chat.register_command('bp-reset', self.bp_reset)
        self.chat.register_command('bp-save', self.bp_save)
        self.chat.register_command('bp-load', self.bp_load)
        self.chat.register_command('bp-show', self.bp_show)
        self.chat.register_command('bp-top', self.bp_top)
    
    def start(self):
        self.chat.start()
    
    def stop(self):
        self.chat.stop()
    
    async def on_ready(self, event: EventData):
        await event.chat.join_room(self.config['DEFAULT']['CHANNEL'])

    async def bp_add(self, cmd: ChatCommand):
        if not is_broadcaster(cmd.user):
            return
        try:
            [user] = cmd.parameter.split()
        except ValueError:
            await cmd.send(f'usage: !{cmd.name} name')
            return
        try:
            self.bp.addUser(user)
        except BPTable.DuplicateUser:
            await cmd.send(f'{user} is already in the BP game.')
            return
        self.bp.saveTable()
        await cmd.send(f'{user} added to the BP game.')
    
    async def bp_remove(self, cmd: ChatCommand):
        if not is_broadcaster(cmd.user):
            return
        try:
            [user] = cmd.parameter.split()
        except ValueError:
            await cmd.send(f'usage: !{cmd.name} name')
            return
        try:
            self.bp.removeUser(user)
        except BPTable.NoUser:
            await cmd.send(f'{user} is not in the BP game.')
            return
        self.bp.saveTable()
        await cmd.send(f'{user} removed from the BP game.')

    async def bp_give(self, cmd: ChatCommand):
        if not is_broadcaster(cmd.user):
            return
        try:
            [user, amount] = cmd.parameter.split()
            amount = int(amount)
        except ValueError:
            await cmd.send(f'usage: !{cmd.name} name amount')
            return
        if cmd.name == 'bp-take':
            amount = -amount
        try:
            entry = self.bp.add(user, amount)
        except BPTable.NoUser:
            await cmd.send(f'{user} is not in the BP game.')
            return
        self.bp.saveTable()
        await cmd.send(f'{entry.user} now has {entry.amount} BP')
    
    async def bp_set(self, cmd: ChatCommand):
        if not is_broadcaster(cmd.user):
            return
        try:
            [user, amount] = cmd.parameter.split()
            amount = int(amount)
        except ValueError:
            await cmd.send(f'usage: !{cmd.name} name amount')
            return
        try:
            entry = self.bp.set(user, amount)
        except BPTable.NoUser:
            await cmd.send(f'{user} is not in the BP game.')
            return
        self.bp.saveTable()
        await cmd.send(f'{entry.user} now has {entry.amount} BP.')

    async def bp_reset(self, cmd: ChatCommand):
        if not is_broadcaster(cmd.user):
            return
        try:
            [yes] = cmd.parameter.split()
            if yes != 'yes':
                raise ValueError()
        except ValueError:
            await cmd.send(f'usage: !{cmd.name} yes')
            return
        self.bp.reset()
        self.bp.saveTable()
        await cmd.send('BP has been reset.')
    
    async def bp_save(self, cmd: ChatCommand):
        if not is_broadcaster(cmd.user):
            return
        if len(cmd.parameter.split()) != 0:
            await cmd.set(f'usage: !{cmd.name}')
            return
        n = self.bp.saveTable()
        await cmd.send(f'{n} players saved')

    async def bp_load(self, cmd: ChatCommand):
        if not is_broadcaster(cmd.user):
            return
        if len(cmd.parameter.split()) != 0:
            await cmd.set(f'usage: !{cmd.name}')
            return
        n = self.bp.loadTable()
        await cmd.send(f'{n} players loaded')
    
    async def bp_show(self, cmd: ChatCommand):
        param = cmd.parameter.split()
        match len(param):
            case 0:
                user = cmd.user.name
            case 1:
                user = param[0]
            case _:
                await cmd.send(F'usage: {cmd.name} [name]')
                return
        try:
            entry = self.bp.get(user)
            await cmd.send(f'{entry.user} has {entry.amount} BP')
        except BPTable.NoUser:
            await cmd.send(f'{user} is not in the BP game.')
            return

    async def bp_top(self, cmd: ChatCommand):
        param = cmd.parameter.split()
        if len(param) != 0:
            await cmd.send(f'usage: !{cmd.name}')
            return
        i = 0
        res = ''
        for entry in self.bp.sorted():
            res += f'{entry.user} has {entry.amount} BP. '
            i += 1
            if i >= TOP_N:
                break
        await cmd.send(res)


async def run():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    token = configparser.ConfigParser()
    token.read(TOKEN_FILE)
    def write_tokens(access, refresh):
        token['DEFAULT']['ACCESS_TOKEN'] = access
        token['DEFAULT']['REFRESH_TOKEN'] = refresh
        with open(TOKEN_FILE, 'w') as f:
            token.write(f)
    async def token_refresh(access: str, refresh: str):
        write_tokens(access, refresh)
    twitch = await Twitch(config['DEFAULT']['CLIENT_ID'], config['DEFAULT']['CLIENT_SECRET'])
    twitch.user_auth_refresh_callback = token_refresh
    if 'ACCESS_TOKEN' in token['DEFAULT']:
        access = token['DEFAULT']['ACCESS_TOKEN']
        refresh = token['DEFAULT']['REFRESH_TOKEN']
    else:
        auth = UserAuthenticator(twitch, AUTH_SCOPE)
        access, refresh = await auth.authenticate()
        write_tokens(access, refresh)
    # WORKAROUND: set_user_authentication validates, but doesn't try to refresh invlid tokens
    if await is_token_valid(access):
        await twitch.set_user_authentication(access, AUTH_SCOPE, refresh)
    else:
        await twitch.set_user_authentication(access, AUTH_SCOPE, refresh, validate=False)
        await twitch.refresh_used_token()

    chat = await Chat(twitch)
    bot = BPBot(chat, config)
    bot.start()

    try:
        input('press ENTER to stop\n')
    finally:
        bot.stop()
        await twitch.close()

class BPTable:
    class Entry:
        def __init__(self, user: str, amount):
            self.user = user
            self.amount = amount

    class DuplicateUser(Exception):
        pass
    class NoUser(Exception):
        pass

    def __init__(self, filename, initial_bp):
        self.filename = filename
        self.initial_bp = initial_bp
        self.loadTable()

    def loadTable(self):
        self.bp = dict()
        if not os.path.isfile(self.filename):
            return 0
        with open(self.filename, encoding='utf-8', newline='') as f:
            for row in csv.reader(f):
                casefold_user = row[0]
                display_user = row[1]
                amount = int(row[2])
                self.bp[casefold_user] = BPTable.Entry(display_user, amount)
        return len(self.bp)

    def saveTable(self):
        if os.path.isfile(self.filename):
            os.replace(self.filename, self.filename+'.old')
        with open(self.filename, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            for casefold_user, entry in self.bp.items():
                w.writerow([casefold_user, entry.user, entry.amount])
        return len(self.bp)
    
    def addUser(self, user: str):
        luser = user.casefold()
        if luser in self.bp:
            raise BPTable.DuplicateUser()
        self.bp[luser] = BPTable.Entry(user, self.initial_bp)

    def removeUser(self, user: str):
        luser = user.casefold()
        if luser not in self.bp:
            raise BPTable.NoUser()
        del self.bp[luser]

    def add(self, user: str, v):
        luser = user.casefold()
        if luser not in self.bp:
            raise BPTable.NoUser()
        self.bp[luser].amount += v
        return self.bp[luser]
    
    def get(self, user: str):
        luser = user.casefold()
        if luser not in self.bp:
            raise BPTable.NoUser()
        return self.bp[luser]
    
    def set(self, user: str, v):
        luser = user.casefold()
        if luser not in self.bp:
            raise BPTable.NoUser()
        self.bp[luser].amount = v
        return self.bp[luser]
    
    def sorted(self):
        return sorted(self.bp.values(), key=attrgetter('amount'))

    def reset(self):
        for user in self.bp:
            self.bp[user].amount = self.initial_bp

asyncio.run(run())
