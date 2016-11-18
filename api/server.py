#!/usr/bin/python3
'''
    Backend webapi for the ll bot
'''
import requests
import json
from bottle import Bottle, abort
from backend import LoveLetterFactory
from .bottle_helpers import webapi, picture


class Server:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.last_message = None
        self.spark_headers = {}
        self.game_maker = LoveLetterFactory()
        self._app = Bottle()

    def start(self):
        ''' start the server '''
        self._app.run(host=self.host, port=self.port)

    @webapi('POST', '/messages')
    def get_messages(self, data):
        try:
            message_id = data['data']['id']
        except KeyError:
            abort(400, 'expected message id')
        api_call = 'https://api.ciscospark.com/v1/messages/{}'.format(message_id)
        r = requests.get(api_call, headers=self.spark_headers)
        message_info = json.loads(r.text)
        self.game_maker.parse_message(message_info)

    @webapi('POST', '/token')
    def set_token(self, data):
        access_token = data.get('token', '')
        self.spark_headers = {"Authorization": "Bearer {}".format(access_token)}
        self.game_maker.spark_headers = self.spark_headers

    @picture('/images/letter')
    def letter_pic(self):
        return 'letter_big.jpg'

    @webapi('GET', '/debug/<room>')
    def debug_room(self, room):
        result = (
            'Games in progress\n'
            '  {}\n\n'
            'Games in setup\n'
            '  {}'.format(
                self.game_maker.games_in_progress.get(room),
                self.game_maker.games_in_setup.get(room),
            )
        )
        return result
