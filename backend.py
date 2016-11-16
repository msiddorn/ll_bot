#!/usr/bin/python3
'''
    Implementation of the love letter game
'''
import re
import requests
import json


class LoveLetter:
    ''' main game object '''

    def __init__(self):
        self.spark_headers = ''
        self.new_game_pattern = '(?i)@ll ?first to (\d)+'
        self.help_pattern = '(?i)@ll ?help'

    def get_players(self):
        return 'Mark'

    def parse_message(self, message):
        if re.match(self.help_pattern, message['text']):
            self.send_help(message['roomId'])

    def send_help(self, room_id):
        api_call = 'https://api.ciscospark.com/v1/messages'
        data = {
            'roomId': room_id,
            'text': 'There is no helping you yet',
        }
        print(data)
        r = requests.get(api_call, data=json.dumps(data), headers=self.spark_headers)
        print(r)
