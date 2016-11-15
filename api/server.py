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

    @picture('/images/letter')
    def letter_pic(self):
        return 'letter.jpg'
