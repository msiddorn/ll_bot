'''
    In game workings of lover letter
'''
import requests
from random import shuffle, choice
from itertools import cycle
import re


class LoveLetter:

    STARTING_DECK = [1, 1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8]

    # play and nominate at the same time

    def __init__(self, spark_headers, room, players, rounds, aliases):
        self.spark_headers = spark_headers
        self.room = room
        self.aliases = aliases

        self.players = players
        shuffle(self.players)
        self.turn_order = cycle(self.players)

        self.win_score = rounds
        self.start_round()

    def start_round(self):
        self.expecting_card = True
        self.hands = {}

    def parse_message(self, text, player):
        if self.expecting_card:
            match = re.match('[1-8]', text)
            if not match:
                self.send_message('Expecting a card from 1-8')
                return
            card = int(text)
            if card not in self.hands(player):
                self.send_message('You don\'t have a {}'.format(card))
                return

    def send_message(self, text, person=None):
        data = {'text': text}
        if person is None:
            data['roomId'] = self.room
        else:
            data['toPersonId'] = person
        self.API_CALLS['new_message'](data=data, headers=self.spark_headers)

    def __repr__(self):
        info = {
            'players': self.players,
            'aliases': self.aliases,
            'win_score': self.win_score,
        }
        return repr(info)

