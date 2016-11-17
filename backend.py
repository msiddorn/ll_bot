#!/usr/bin/python3
'''
    Implementation of the love letter game
'''
import re
import requests
from functools import partial
from love_letter import LoveLetter


class LoveLetterFactory:
    ''' creates and handles love letter games '''

    help_text = (
        '#  Love Letter\n'
        '* first to **3**: Start a game of LL, first to X wins\n'
        '* join / join as **bob**: Join the game, optionally setting a nickname\n'
        '* call me **Ishmael**: Set or change your nickname\n'
        '* start: Begin the game\n'
        '* cancel: Cancel a game in progress\n'
        '* help: Show this message\n'
        'N.B. you must mention me in every message, nicknames can only be alphabetical'
    )

    # regex for commands
    new_game_pattern = '(?i)first to (\d+)(?: as )?(\w+)?'
    help_pattern = '(?i)\help'
    nickname_pattern = '(?i)call me ([a-z]+)'
    join_pattern = '(?i)join(?: as )?(\w+)?'
    start_pattern = '(?i)start'
    cancel_pattern = '(?i)cancel'

    # spark stuff
    MENTION_REGEX = r'<spark-mention.*?data-object-id="(\w+)".*?spark-mention>'
    PERSON_ID = 'Y2lzY29zcGFyazovL3VzL1BFT1BMRS9jZjE5OTU0OC05MzE1LTQ2NjktOGJmYy03MmNjMGNiYjc0NWQ'
    API_CALLS = {
        'new_message': partial(requests.post, 'https://api.ciscospark.com/v1/messages')
    }

    def __init__(self):
        self.spark_headers = ''
        self.games_in_setup = {}
        self.games_in_progress = {}

    def parse_message(self, message):
        room = message['roomId']
        sender = message['personId']
        # all messages must mention the bot so will always have a html field
        html = message['html']
        print(html)

        # swap all mentions for the person_id
        text = re.sub(self.MENTION_REGEX, '\g<1>', html)
        print(text)

        # remove mentions of the bot and strip whitespace
        text = re.sub(self.PERSON_ID, '', text).strip()
        print(text)

        # deal with cancel
        if re.match(self.cancel_pattern, text):
            self.cancel(room, sender)
            return

        # Games which are in progress
        if room in self.games_in_progress:
            for regex in [self.new_game_pattern, self.join_pattern, self.start_pattern]:
                if re.match(regex, text):
                    self.send_message(
                        room,
                        'Operation not allowed whilst there is a game in progress in this room'
                    )
            self.games_in_progress[room].parse_message(text, sender)

        # Out of game help
        if re.match(self.help_pattern, text):
            self.send_message(room, self.help_text)

        # Games being set up
        if room in self.games_in_setup:
            # Start a game
            if re.match(self.start_pattern, text):
                self.start_game(room, sender)
            # Join a game
            match = re.match(self.join_pattern, text)
            if match:
                self.join(room, sender, match.group(1))
            # Change nickname
            match = re.match(self.nickname_pattern, text)
            if match:
                self.change_nickname(room, sender, match.group(1))
        # New Games
        else:
            # Create a game
            match = re.match(self.new_game_pattern, text)
            if match:
                self.new_game(room, sender, int(match.group(1)), match.group(2))

    def send_message(self, room, text):
        data = {
            'roomId': room,
            'text': text,
        }
        self.API_CALLS['new_message'](data=data, headers=self.spark_headers)

    def new_game(self, sender, room, rounds, nickname):
        aliases = {}
        if nickname is not None:
            aliases[sender] = nickname
        self.games_in_setup[room] = {
            'owner': sender,
            'players': [sender],
            'rounds': rounds,
            'aliases': aliases,
        }
        self.send_message(room, 'New game created with {} rounds'.format(rounds))

    def join_game(self, room, sender, nickname):
        game = self.games_in_setup[room]
        if sender in game['players']:
            self.send_message(room, 'You can\'t join the same game twice')
            return
        aliases = game['aliases']
        if nickname is not None:
            aliases[sender] = nickname
        game['players'].append(sender)

    def change_nickname(self, room, sender, nickname):
        game = self.games_in_setup[room]
        if sender not in game['players']:
            self.send_message(room, 'If you\'re not in the game I don\'t care what you\'re called')
            return
        game['aliases'][sender] = nickname

    def start_game(self, room, sender):
        game = self.games_in_setup[room]
        if sender == game['owner']:
            if len(game['players']) <= 1:
                self.send_message(room, 'There must be at least 2 players in order to begin')
            else:
                self.games_in_progress[room] = LoveLetter(self.spark_headers, **game)
                self.send_message(room, 'Game started with {} players. First to {} wins'.format(
                    len(game['players']),
                    game['rounds'],
                ))
        else:
            self.send_message(room, 'Only the creator of the game can start it')

    def cancel_game(self, room, sender):
        game = self.games_in_progress.get(room)
        if game:
            if sender == game['owner']:
                self.games_in_progress = {k: v for k, v in self.games_in_progress if k != room}
            else:
                self.send_message(room, 'Only the creater of the game can end it prematurely')
        game = self.games_in_setup.get(room)
        if game:
            if sender == game['owner']:
                self.games_in_setup = {k: v for k, v in self.games_in_setup if k != room}
            else:
                self.send_message(room, 'Only the creater of the game can end it prematurely')
