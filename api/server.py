#!/usr/bin/python3
'''
    Backend webapi for the ll bot
'''
from bottle import Bottle  # , abort
from .bottle_helpers import webapi, picture


class Server:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.last_message = None
        self._app = Bottle()

    def start(self):
        ''' start the server '''
        self._app.run(host=self.host, port=self.port)

    @webapi('GET', '/')
    def home_world(self):
        return 'hello world'

    @webapi('POST', '/')
    def hello_name(self, data):
        name = data.get('name')
        return 'hello {}'.format(name)

    @webapi('GET', '/seen')
    def show_message(self):
        return repr(self.last_message)

    @webapi('POST', '/messages')
    def get_messages(self, data):
        self.last_message = data

    @picture('/images/letter')
    def letter_pic(self):
        return 'letter_big.jpg'
