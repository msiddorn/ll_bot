#!/usr/bin/python3
'''
    Backend webapi for the ll bot
'''
import requests
from bottle import Bottle, abort
from .bottle_helpers import webapi, picture


class Server:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.last_message = None
        self.spark_headers = {}
        self._app = Bottle()

    def start(self):
        ''' start the server '''
        self._app.run(host=self.host, port=self.port)

    @webapi('GET', '/')
    def home_world(self):
        return repr(self.spark_headers)

    @webapi('GET', '/seen')
    def show_message(self):
        return repr(self.last_message)

    @webapi('POST', '/messages')
    def get_messages(self, data):
        try:
            message_id = data['data']['id']
        except KeyError:
            abort(400, 'expected message id')
        api_call = 'https://api.ciscospark.com/vi/messages/{}'.format(message_id)
        print(api_call)
        r = requests.get(api_call, headers=self.spark_headers)
        print(r)
        print(r.text)
        self.last_message = r.text

    @webapi('POST', '/token')
    def set_token(self, data):
        access_token = data.get('token', '')
        self.spark_headers = {"Authorization": "Bearer {}".format(access_token)}

    @picture('/images/letter')
    def letter_pic(self):
        return 'letter_big.jpg'
