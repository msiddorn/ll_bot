#!/usr/bin/python3
'''
    Backend webapi for the ll bot
'''
import requests
import json
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

    @webapi('GET', '/messages')
    def show_message(self):
        return repr(self.last_message)

    @webapi('POST', '/messages')
    def get_messages(self, data):
        try:
            message_id = data['data']['id']
        except KeyError:
            abort(400, 'expected message id')
        api_call = 'https://api.ciscospark.com/v1/messages/{}'.format(message_id)
        r = requests.get(api_call, headers=self.spark_headers)
        message_info = json.loads(r.text)
        self.last_message = message_info['text']

    @webapi('POST', '/token')
    def set_token(self, data):
        access_token = data.get('token', '')
        self.spark_headers = {"Authorization": "Bearer {}".format(access_token)}

    @picture('/images/letter')
    def letter_pic(self):
        return 'letter_big.jpg'
