from aiohttp import web
import ssl
import json
import time
import uuid
import re
import random
import copy
import threading
import html
import sys

from pprint import pprint

from richlinks import Richlinks

# third party modules
import socketio
from lxml.html.clean import autolink_html


sio = socketio.AsyncServer(async_mode='aiohttp', async_handlers=True)
app = web.Application()
sio.attach(app)

# TODO
# username selection (and related functions)
# pretty front end stuff
# max chatlog test
# database?

# keep the last 100 messages in memory
chatlog = [
    {
        'msg': '<code>*BEEP BOOP* Try posting a url *BEEP BOOP*</code>',
        'time': time.time()*1000,
        'msg_id': str(uuid.uuid4()),
        'public_token': '1234',
        'private_token': '4321'
    }
]
last_msg = None

# TODO def function to repopulate chatlog from database

# which sid is associated with which private_token
session_dict = {}  # {sid: private_token}

# private token assigned name
user_dict = {
    '4321': 'Robot #1'
}  # {private token: 'Choosen Name'}

# private token : public_token
token_dict = {
    '4321': '1234'
}  # {private token: public_token}

rl = Richlinks()
rl.settings["images"]["thumb"]["save_location"] = (
    "/var/www/html/temp/media/thumbs")

rl.settings["images"]["full"]["save_location"] = (
    "/var/www/html/temp/media/images")

rl.settings["general"]["webroot"] = "/var/www/html/"
rl.settings["general"]["domain"] = "https://comp2772.nm.tc/"


def save_msg(new_msg):
    # actually don't do this
    # this works fine but isn't really needed for the example
    return

    chatlog.append(new_msg)
    if len(chatlog) > 50:
        chatlog.pop(0)

    global last_msg
    last_msg = new_msg

    # database it


async def make_richlink(msg, urls):
    outgoing_data = {
        'time': time.time()*1000,
        'msg_id': msg['msg_id']
    }
    try:
        w = rl.fetch(urls[0])
    except:
        e = sys.exc_info()[0]
        w = None
        print('exception in fetch:', e)

    if not w:
        print("no website?")
        await sio.emit('delete_message', namespace='/chat', data=outgoing_data)
        return

    try:
        html = rl.get_html(w, "compact")
    except:
        e = sys.exc_info()[0]
        html = None
        print('exception in get_html:', e)

    if not html:
        print("no html?")
        await sio.emit('delete_message', namespace='/chat', data=outgoing_data)
        return

    outgoing_data['msg'] = html

    await sio.emit('update_message', namespace='/chat', data=outgoing_data)

    print("RICHLINK :: ", outgoing_data)

    # for saving
    msg['msg'] = outgoing_data['msg']
    msg['time'] = outgoing_data['time']
    save_msg(msg)


async def send_blank_richlink(msg, urls):
    html = """
        <div class='rl_compact rl_blank rl_preview fadeIn'>
            <div class="sk-folding-cube">
                <div class="sk-cube1 sk-cube"></div>
                <div class="sk-cube2 sk-cube"></div>
                <div class="sk-cube4 sk-cube"></div>
                <div class="sk-cube3 sk-cube"></div>
            </div>
        </div>"""

    outgoing_data = {
        'msg': html,
        'user': user_dict[msg['private_token']],
        'time': time.time()*1000,
        'msg_id': str(uuid.uuid4()),
        'public_token': msg["public_token"],
        'connect_to_id': msg['msg_id']
    }
    await sio.emit('chat_message', namespace='/chat', data=outgoing_data)

    outgoing_data['private_token'] = msg['private_token']
    del(outgoing_data['user'])

    tsk = sio.start_background_task(make_richlink, outgoing_data, urls)

async def send_chatlog(sid):
    clean_chatlog = copy.deepcopy(chatlog)

    for message in clean_chatlog:
        if message['private_token'] in user_dict:
            message['user'] = user_dict[message['private_token']]
        else:
            message['user'] = 'No name'

        del(message['private_token'])

    await sio.emit('chatlog', data=clean_chatlog, namespace='/chat', room=sid)


@sio.on('connect', namespace='/chat')
async def connect(sid, environ):
    print("connect ", sid)

    await send_chatlog(sid)


def is_authed(sid):
    return (sid in session_dict)


# yeah yeah i know
# don't reinvent the wheel -- i just wanted to try it
def new_tokens(sid):
    public_token = str(uuid.uuid4())
    private_token = str(uuid.uuid4())

    session_dict[sid] = private_token
    token_dict[private_token] = public_token

    return {'private_token': private_token, 'public_token': public_token}


def get_private_token(sid):
    return session_dict[sid]


def get_public_token(sid):
    private_token = get_private_token(sid)
    return token_dict[private_token]


# sid (session id) is essentially a single connection id
# private_token is essentially a multi connection id
@sio.on('auth', namespace='/chat')
async def auth(sid, data):
    try:
        # if tokens sent validate
        if ('private_token' in data and
                data['private_token'] in session_dict.values()):
            # just double check both tokens are correct
            private_token = str(data['private_token'])
            public_token = str(data['public_token'])

            if (token_dict[private_token] == public_token):
                session_dict[sid] = private_token

                return {'OK': True}
            else:
                # something is wrong send new tokens
                return new_tokens(sid)
        else:
            return new_tokens(sid)
    except:
        raise
        return {'OK': False}


def make_name():
    adjectives = ['Angry', 'Bewildered', 'Clumsy', 'Defeated', 'Embarrassed',
                  'Fierce', 'Grumpy', 'Helpless', 'Itchy', 'Jealous', 'Lazy',
                  'Mysterious', 'Nervous', 'Obnoxious', 'Panicky', 'Repulsive',
                  'Scary', 'Thoughtless', 'Uptight', 'Worried']

    nouns = ['bird', 'cat', 'dog', 'wolf', 'tiger', 'deer', 'snake', 'bear',
             'lion', 'giraffe', 'horse', 'pig', 'cow', 'turtle', 'goat',
             'hippo', 'rhino', 'goose', 'donkey', 'otter', 'camel', 'gorrila',
             'frog', 'weasel', 'mouse', 'crow', 'man']

    usr_name = (adjectives[random.randint(0, len(adjectives)-1)] + ' ' +
                nouns[random.randint(0, len(nouns)-1)])

    if (usr_name in user_dict.values()):
        # hope all 400 names aren't exhausted
        return make_name()
    else:
        return usr_name


@sio.on('name_request', namespace='/chat')
async def name_request(sid, data):

    if ('name_request' not in data):
        return {'OK': False, 'DESC': 'Bad Request'}

    if not is_authed(sid):
        return {'OK': False, 'DESC': 'Not Authenticated'}

    if (data['name_request'] is True):
        usr_name = make_name()

        user_dict[get_private_token(sid)] = usr_name
        return {'OK': True, 'name': usr_name}

    try:
        if (len(data['name_request']) > 64):
            return {'OK': False, 'DESC': 'Name can\'t exceed 64 characters'}

        if not re.match("^[A-Za-z0-9\040-]+$", data['name_request']):
            return {'OK': False,
                    'DESC': 'Invalid Chars: Accepts [A-Z], [1-9], -, Spaces'}

        if not re.match("^[A-Za-z].*$", data['name_request']):
            # stops all spaces or all dashes as a name
            return {'OK': False, 'DESC': 'Must have at least one letter'}

        # check if username in user_dict
        if (data['name_request'] in user_dict.values()):
            # check the requester owns the username
            if (user_dict[get_private_token(sid)] == data['name_request']):
                return {'OK': True, 'name': data['name_request']}
            else:
                return {'OK': False, 'DESC': 'Name already taken'}

        is_changed_name = (get_private_token(sid) in user_dict)

        if (is_changed_name):
            msg = ('<b>' + user_dict[get_private_token(sid)] +
                   '</b> is now know as <b>' + data['name_request'] + '</b>')

            outgoing_data = {'time': time.time()*1000,
                             'public_token': get_public_token(sid),
                             'msg': msg}

            await sio.emit('name_changed', namespace='/chat',
                           data=outgoing_data)

            global last_msg
            last_msg = None

        user_dict[get_private_token(sid)] = data['name_request']

        return {'OK': True, 'name': data['name_request']}

    except:
        raise
        return {'OK': False, 'DESC': 'Unknown Error. Please try again'}


@sio.on('chat_message', namespace='/chat')
async def message(sid, data):
    if ('temp_id' not in data):
        return {'OK': False, 'DESC': 'Bad Request'}

    if not is_authed(sid):
        return {'OK': False, 'temp_id': data['temp_id'],
                'DESC': 'Not Authenticated'}

    try:
        data['msg'] = html.escape(data['msg'])

        replacements = rl.replace_urls(data['msg'])
        data['msg'] = replacements[0]
        urls = replacements[1]

        print("message ", data['msg'], "sid ", sid)
        print(user_dict)

        if get_private_token(sid) in user_dict:
            msg_owner_name = user_dict[get_private_token(sid)]
        else:
            msg_owner_name = 'No name'

        outgoing_data = {'user': msg_owner_name, 'msg': data['msg'],
                         'time': time.time()*1000, 'msg_id': str(uuid.uuid4()),
                         'public_token': get_public_token(sid)}
        # Check if this should connect to the last message
        if last_msg is not None:

            # if same person sent the last message in the last 5 minutes
            if (last_msg['public_token'] == outgoing_data['public_token'] and
                    last_msg['time']+300 > time.time()):

                # assign it a connect_to_id so it will follow in the same block
                outgoing_data['connect_to_id'] = last_msg['msg_id']

        await sio.emit('chat_message', namespace='/chat', data=outgoing_data,
                       skip_sid=sid)

        print(outgoing_data)

        outgoing_data['private_token'] = get_private_token(sid)
        del(outgoing_data['user'])

        save_msg(outgoing_data)

        # Everything is fine, you gave us this id, this is the offical id
        resp = {'OK': True, 'temp_id': data['temp_id'],
                'msg_id': outgoing_data['msg_id']}
        await sio.emit('chat_message_resp', namespace='/chat',
                       room=sid, data=resp)

        if urls:
            await send_blank_richlink(outgoing_data, urls)

    except:
        raise
        return {'OK': False, 'temp_id': data['temp_id']}


@sio.on('disconnect', namespace='/chat')
def disconnect(sid):
    print('disconnect ', sid)

if __name__ == '__main__':
    web.run_app(app, port=8080)
