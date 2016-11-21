'''
    In game workings of lover letter
'''
from random import shuffle
from itertools import cycle
from functools import partial
from copy import copy
import json
import re
from bot_helpers import API_CALLS


class LoveLetter:

    STARTING_DECK = [1, 1, 1, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 7, 8]

    # play and nominate at the same time

    def __init__(self, spark_headers, room, players, owner, aliases, rounds):
        self.spark_headers = spark_headers
        self.room = room
        self.finished = False

        self.players = [Player(p_id, self.spark_headers, aliases.get(p_id)) for p_id in players]
        shuffle(self.players)
        self.turn_order = cycle(self.players)

        self.win_score = rounds
        self.start_round()

    def start_round(self):
        self.deck = copy(self.STARTING_DECK)
        shuffle(self.deck)
        self.round_players = []
        for player in self.players:
            card = self.deck.pop()
            player.hand = [card]
            self.round_players.append(player)
            self.send_message('You have been dealt a {}'.format(card), person=player.id)
        self.turn = next(self.turn_order)
        self.next_turn()

    def receive_message(self, text, player):
        if player != self.turn.id:
            self.send_message('It\'s not your turn')
            return False
        self.current_play_function(text)
        if self.finished:
            return True
        return False

    def send_message(self, text, person=None):
        data = {'text': text}
        if person is None:
            data['roomId'] = self.room
        else:
            data['toPersonId'] = person
        API_CALLS['create_message'](data=data, headers=self.spark_headers)

    def end_round(self, winner=None):
        if winner is None:
            winners = []
            for player in self.round_players:
                self.send_message('{} has a {}'.format(player.name, player.card))
                if winners == [] or player.card > winners[0].card:
                    winners = [player]
                elif player.card == winners[0].card:
                    winners.append(player)
            if len(winners) == 1:
                winner = winners[0]
            else:
                discards = []
                for player in winners:
                    self.send_message('{} discarded a total of {}'.format(
                        player.name,
                        player.total - player.card,
                    ))
                    if discards == [] or player.total > discards[0].total:
                        discards = [player]
                    elif player.total == discards[0].total:
                        discards.append(player)
                if len(discards) == 1:
                    winner = discards[0]
                else:
                    self.send_message('Fine, nobody wins')
                    self.start_round()
                    return
        self.send_message('{} wins the round'.format(winner.name))
        winner.score += 1
        if winner.score == self.win_score:
            self.send_message('{} is the winner! Final scores are:'.format(winner.name))
            self.show_scores()
            self.finished = True
        else:
            self.start_round()

    def next_turn(self):
        '''progress the turns '''
        if len(self.round_players) < 2:
            self.end_round(winner=self.round_players[0])
            return
        if len(self.deck) < 2:
            self.end_round()
            return
        previous = self.turn
        for turn in self.turn_order:
            print('{}\'s turn'.format(turn.name))
            if turn in self.round_players:
                self.turn = turn
                break
            else:
                print('not in round')
            if turn == previous:
                self.send_message('oops, same person\'s turn again. Something went wrong')
                return
        card = self.deck.pop()
        self.turn.hand.append(card)
        self.send_message(
            'You have been dealt a {}, your hand is {}'.format(card, self.turn.hand),
            self.turn.id
        )
        self.turn.protected = False
        self.current_play_function = self.get_card
        if len(self.deck) == 1:
            self.send_message('{} just picked up the last card'.format(self.turn.name))
        else:
            self.send_message('It\'s {}\'s turn.'.format(self.turn.name))

    def get_card(self, text, guessing_player=None):
        match = re.match('[1-8]', text)
        if not match:
            self.send_message('Expecting a card from {}-8'.format(
                1 if guessing_player is None else 2)
            )
            return
        card = int(text)
        if guessing_player is not None:
            if card == 1:
                self.send_message('Sorry you can only guess cards 2-8')
            if card == guessing_player.card:
                self.send_message('Correctly guessed {} had a {}. They are out!'.format(
                    guessing_player.name,
                    card
                ))
                self.round_players.remove(guessing_player)
            else:
                self.send_message('Guessed incorrectly. {}\ does not have {}'.format(
                    guessing_player.name,
                    card
                ))
            self.next_turn()
            return

        if card not in self.turn.hand:
            self.send_message('Shame you don\'t have a {}'.format(card))
            return

        if card in [5, 6] and 7 in self.turn.hand:
            self.send_message('I\'m sorry but you have to play your 7')
            return

        # card is played and gone at this point
        self.turn.hand.remove(card)

        if card in [1, 2, 3, 6]:  # can be nulled by handmaidens
            if len([p for p in self.round_players if not p.protected if p != self.turn]) < 1:
                self.send_message('Everyone else is either hiding or out')
                self.next_turn()
                return
            action = {
                1: 'guess',
                2: 'see',
                3: 'challenge',
                6: 'swap with yours',
            }[card]
            self.send_message('Who\'s card do you want to {}?'.format(action))
            self.current_play_function = partial(self.get_target, card)
        elif card == 4:
            self.send_message('Coward')
            self.turn.protected = True
            self.next_turn()
        elif card == 5:
            self.send_message('Who do you want to discard?')
            self.current_play_function = partial(self.get_target, 5, allow_self=True)
        elif card == 7:
            self.next_turn()
        elif card == 8:
            self.send_message('{} played an 8 and is out'.format(self.turn.name))
            self.round_players.remove(self.turn)
            self.next_turn()

    def get_target(self, card, text, allow_self=False):
        ''' Get the target player '''
        possible_targets = [p for p in self.round_players if (p != self.turn or allow_self)]
        for target in possible_targets:
            if text == target.id or text == target.alias:
                break
        else:
            self.send_message('I don\'t know who that is. You can tag them or use their nickname')
            return
        if target.protected:
            self.send_message('{} is protected by a handmaiden. Try someone else'.format(
                target.name
            ))
            return
        if card == 1:
            self.send_message('What card do you think they have?')
            self.current_play_function = partial(self.get_card, guessing_player=target)
            return
        elif card == 2:
            self.send_message(
                '{} has a {}'.format(target.name, target.card),
                player=self.turn.id,
            )
        elif card == 3:
            if self.turn.card < target.card:
                self.round_players.remove(self.turn)
                self.send_message('{} has the lower card, they discard their {} and are out'.format(
                    self.turn.name,
                    self.turn.card,
                ))
                self.send_message(
                    '{} beat you with a {}'.format(target.name, target.card),
                    person=self.turn.id,
                )
            elif self.turn.card > target.card:
                self.round_players.remove(target)
                self.send_message('{} has the lower card, they discard their {} and are out'.format(
                    target.name,
                    target.card,
                ))
                self.send_message(
                    '{} beat you with a {}'.format(self.turn.name, self.turn.card),
                    person=target.id,
                )
            else:
                self.send_message('{} and {} have the same card'.format(
                    self.turn.name,
                    target.name,
                ))
        elif card == 5:
            self.send_message('{} had to discard {}'.format(
                target.name,
                target.card[0],
            ))
            if target.card == 8:
                self.send_message('{} is out!'.format(target.name))
                self.round_players.remove(target)
            else:
                new_card = self.deck.pop()
                target.hand = [new_card]
                self.send_message('You have been dealt a {}'.format(new_card), person=target.id)
        elif card == 6:
            target.hand, self.turn.hand = self.turn.hand, target.hand
            self.send_message('{} and {} have swapped cards'.format(self.turn.name, target.name))
        self.next_turn()

    def show_scores(self):
        scores = ', '.join([
            '{}: {}'.format(player.name, player.score)
            for player in self.players
        ])
        self.send_message(scores)


class Player:

    def __init__(self, p_id, spark_headers, alias):
        self.id = p_id
        self.spark_headers = spark_headers
        self.alias = alias
        self.hand = []
        self.score = 0
        self.protected = False

    @property
    def name(self):
        if self.alias is None:
            r = API_CALLS['get_person_details'](headers=self.spark_headers, person_id=self.id)
            if r.status_code == 200:
                person_info = json.loads(r.text)
                if 'firstName' in person_info:
                    self.alias = person_info['firstName']
                else:
                    self.alias = person_info['displayName']
            else:
                self.alias = 'Unknown (bad response from spark)'
        return self.alias

    @property
    def card(self):
        ''' hand is only 1 card most of the time '''
        return self.hand[0]
