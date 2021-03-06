#!/usr/bin/python3
'''
    Implementation of the love letter game
'''
import re
from love_letter import LoveLetter
from bot_helpers import MENTION_REGEX, PERSON_ID, API_CALLS


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
    scores_pattern = '(?i)scores'

    def __init__(self):
        self.spark_headers = ''
        self.games_in_setup = {}
        self.games_in_progress = {}

    def parse_message(self, message):
        try:
            room = message['roomId']
            sender = message['personId']
            html = message['html']
        except KeyError:
            # I need all of those so do nothing otherwise
            return

        # swap all mentions for the person_id
        text = re.sub(MENTION_REGEX, '\g<1>', html)

        # remove mentions of the bot and strip whitespace
        text = re.sub(PERSON_ID, '', text).strip()

        print('Saw message - {}'.format(text))

        # deal with cancel
        if re.match(self.cancel_pattern, text):
            self.cancel_game(room, sender)
            return

        # Games which are in progress
        if room in self.games_in_progress:
            for regex in [self.new_game_pattern, self.join_pattern, self.start_pattern]:
                if re.match(regex, text):
                    self.send_message(
                        room,
                        'Operation not allowed whilst there is a game in progress in this room'
                    )
            if re.match(self.scores_pattern, text):
                self.games_in_progress[room].show_scores()
                return
            finished = self.games_in_progress[room].receive_message(text, sender)
            if finished:
                self.games_in_progress = {
                    k: v for k, v in self.games_in_progress.items()
                    if k != room
                }
            return

        # Out of game help
        if re.match(self.help_pattern, text):
            self.send_message(room, self.help_text, markdown=True)

        # Games being set up
        if room in self.games_in_setup:
            # Start a game
            if re.match(self.start_pattern, text):
                self.start_game(room, sender)
            # Join a game
            match = re.match(self.join_pattern, text)
            if match:
                self.join_game(room, sender, match.group(1))
            # Change nickname
            match = re.match(self.nickname_pattern, text)
            if match:
                self.change_nickname(room, sender, match.group(1))
        # New Games
        else:
            # Create a game
            match = re.match(self.new_game_pattern, text)
            print(match.groups())
            if match:
                self.new_game(room, sender, int(match.group(1)), match.group(2))

    def send_message(self, room, text, markdown=False):
        data = {'roomId': room}
        if markdown:
            data['markdown'] = text
        else:
            data['text'] = text
        API_CALLS['create_message'](data=data, headers=self.spark_headers)

    def new_game(self, room, sender, rounds, nickname):
        print('saw new game')
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
        print('saw join game')
        game = self.games_in_setup[room]
        if sender in game['players']:
            self.send_message(room, 'You can\'t join the same game twice')
            return
        aliases = game['aliases']
        if nickname is not None:
            aliases[sender] = nickname
        game['players'].append(sender)
        self.send_message(
            room,
            'successfully joined. There are currently {} players'.format(len(game['players']))
        )
        if len(game['players']) == 4:
            self.start_game(room, game['owner'])

    def change_nickname(self, room, sender, nickname):
        game = self.games_in_progress.get(room)
        if game is not None:
            players = [player for player in game.players if player.id == sender]
            if not players:
                self.send_message(room, 'Why would I need to know your name?')
                return
            else:
                player = players[0]
                player.alias = nickname
                self.send_message(room, 'Nickname set')
            game.players[sender].alias = nickname

        game = self.games_in_setup.get(room)
        if game is not None:
            if sender not in game['players']:
                self.send_message(room, 'If you\'re not in the game I don\'t care what you\'re called')
                return
            else:
                game['aliases'][sender] = nickname
                self.send_message(room, 'Nickname set')

    def start_game(self, room, sender):
        game = self.games_in_setup[room]
        if sender == game['owner']:
            if len(game['players']) <= 1:
                self.send_message(room, 'There must be at least 2 players in order to begin')
            else:
                self.send_message(room, 'Game started with {} players. First to {} wins'.format(
                    len(game['players']),
                    game['rounds'],
                ))
                self.games_in_progress[room] = LoveLetter(self.spark_headers, room, **game)
        else:
            self.send_message(room, 'Only the creator of the game can start it')

    def cancel_game(self, room, sender):
        for game_type in ('games_in_setup', 'games_in_progress'):
            game_dict = getattr(self, game_type)
            game = game_dict.get(room)
            if game:
                if sender == game['owner']:
                    self.send_message(room, 'Game cancelled')
                    setattr(self, game_type, {
                        k: v for k, v in game_dict.items()
                        if k != room
                    })
                else:
                    self.send_message(room, 'Only the creater of the game can end it prematurely')
