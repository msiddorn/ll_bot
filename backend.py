#!/usr/bin/python3
'''
    Implementation of the love letter game
'''
import re
import requests
from functools import partial
# import json


class LoveLetterFactory:
    ''' main game object '''

    help_text = "I'm afraid i cannot help you yet."

    new_game_pattern = '(?i)@ll ?first to (\d)+'
    help_pattern = '(?i)@ll ?help'

    API_CALLS = {
        'new_message': partial(requests.post, 'https://api.ciscospark.com/v1/messages')
    }

    def __init__(self):
        self.spark_headers = ''
        self.games_in_progress = []

    def get_players(self):
        return 'Mark'

    def parse_message(self, message):
        room = message['roomId']
        if room in self.games_in_progress:
            pass
        else:
            if re.match(self.help_pattern, message['text']):
                self.send_help(room)
                return
            match = re.match(self.new_game_pattern)
            if match:
                self.start_game(room, int(match.group(1)))

    def start_game(self, room_id, rounds):
        data = {
            'roomId': room_id,
            'text': 'you want to play {} rounds?'.format(rounds),
        }
        self.API_CALLS['new_message'](data=data, headers=self.spark_headers)

    def send_help(self, room_id):
        data = {
            'roomId': room_id,
            'text': self.help_text,
        }
        self.API_CALLS['new_message'](data=data, headers=self.spark_headers)


class LoveLetter:

    def __init__(self, rounds, players, room_id, auth_headers):
        pass
