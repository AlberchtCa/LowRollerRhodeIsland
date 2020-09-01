import csv
import random
import GameFunctionsShort
import matplotlib.pyplot as plt
from typing import List, Dict
from copy import deepcopy



def pick_action_randomly(game_state):
    choice = [0, 1, 2, 3, 4]
    random.shuffle(choice)
    possible_actions = game_state.get_actions()
    for i in range(5):
        if game_state.actions[choice[i]] in possible_actions:
            game_state = game_state.handle_action(game_state.actions[choice[i]])
            break
    return game_state


def pick_from_strategy(game_state, strategy):
    possibilities = strategy[game_state.get_representation()]
    possibilities = [i * 100 for i in possibilities]

    possible_actions = game_state.get_actions()
    possible_action_indexes = [0, 0, 0, 0, 0]

    for action in possible_actions:
        possible_action_indexes[game_state.actions.index(action)] = 1

    possibilities_sum = 0

    for i in range(5):
        if possible_action_indexes[i] == 1:
            possibilities_sum += possibilities[i]

    choice = random.randint(0, int(possibilities_sum))


    choice_sum = 0
    for i in range(5):
        if possible_action_indexes[i] == 1:
            choice_sum += possibilities[i]
            if choice <= choice_sum:
                game_state = game_state.handle_action(game_state.actions[i])
                break
    return game_state


class Player:
    def __init__(self, index: int, invested: int):
        self.index = index
        self.invested = invested


class GameState:
    def __init__(self, deck):
        self.deck = deck
        self.history = []
        self.players = [Player(0, 1), Player(1, 1)]
        self.acting_player = 0
        self.street = 0
        self.street_history = ''
        self.re_raise_param = 0
        self.last_action = 'none'
        self.actions = ['C', 'B', 'c', 'R', 'F']

    def is_terminal(self) -> bool:
        if self.last_action == 'none':
            return False
        if self.history[-1] == 'F':
            return True
        if self.last_action != 'none' and self.street == 2 and (self.history[-1] == 'C'
                                                                or self.street_history == 'cc'):
            return True
        return False

    def get_payoff(self) -> int:
        h_index = self.acting_player
        o_index = (self.acting_player + 1) % 2
        if self.history[-1] == 'F':
            return self.players[o_index].invested
        else:
            showdown = GameFunctionsShort.get_winning_hand([self.deck[h_index]] + self.deck[2:4],
                                                      [self.deck[o_index]] + self.deck[2:4])

            if showdown == 0:
                return self.players[o_index].invested
            if showdown == 1:
                return 0
            else:
                return -self.players[h_index].invested

    def get_actions(self) -> List[str]:
        if self.last_action == 'none':
            return ['c', 'B']
        if self.last_action == 'c':
            return ['c', 'B']
        if self.last_action == 'B':
            return ['C', 'F', 'R']
        if self.last_action == 'R' and self.re_raise_param < 2:
            return ['C', 'F', 'R']
        if self.last_action == 'R' and self.re_raise_param == 2:
            return ['C', 'F']

    def handle_action(self, action: str):
        new_game_state = deepcopy(self)
        new_game_state.history.append(action)
        new_game_state.last_action = action
        new_game_state.street_history += action
        new_game_state.acting_player = (self.acting_player + 1) % 2

        if self.last_action != 'none':
            if action in ['C', 'c'] and self.history[-1] in ['R', 'B', 'c']:
                if self.street in [0, 1]:
                    new_game_state.street += 1
                    new_game_state.last_action = 'none'
                    new_game_state.re_raise_param = 0
                    new_game_state.street_history = ''

            if action in ['B', 'C', 'R']:
                new_game_state.players[self.acting_player].invested += 2 + 2 * min([self.street, 1])

            if action == 'R':
                new_game_state.re_raise_param += 1
        else:
            if action == 'B':
                new_game_state.players[self.acting_player].invested += 2 + 2 * min([self.street, 1])

        return new_game_state

    def get_representation(self) -> str:
        player_card = self.deck[self.acting_player][0]
        actions_as_string = "/".join([str(x) for x in self.history])
        if self.street == 0:
            community_cards = ''
        else:
            if self.street == 1:
                community_cards = self.deck[2][0]
            else:
                community_cards = self.deck[2][0] + self.deck[3][0]
        drawing = 'n'
        if self.street == 1:
            if self.deck[self.acting_player][1] == self.deck[2][1]:
                drawing = 'd'
        if self.street == 2:
            if self.deck[self.acting_player][1] == self.deck[2][1] == self.deck[3][1]:
                drawing = 'y'
            else:
                drawing = 'n'
        return f'{player_card}/{community_cards}/{drawing}-{actions_as_string}'



hero_strategy = {}
opponent_strategy = {}
#Testing against opponent strategy

with open('Strategies/500k_iterations.csv', 'r', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=' ',
                        quoting=csv.QUOTE_NONE,
                        escapechar=',')
    for row in reader:
        history, odds = row
        odds_f = [float(odds[1:5]), float(odds[6:10]), float(odds[11:15]), float(odds[16:20]), float(odds[21:25])]
        hero_strategy[history] = odds_f

with open('Strategies/100k_iterations.csv', 'r', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=' ',
                        quoting=csv.QUOTE_NONE,
                        escapechar=',')
    for row in reader:
        history, odds = row
        odds_f = [float(odds[1:5]), float(odds[6:10]), float(odds[11:15]), float(odds[16:20]), float(odds[21:25])]
        opponent_strategy[history] = odds_f


result = [0]
hero_acting = 1
for i in range(33240):
    pot = 0
    deck = GameFunctionsShort.get_deck()
    random.shuffle(deck)
    increment = 0
    increment_sum = 0
    game_state = GameState(deck)
    while not game_state.is_terminal():
        if game_state.acting_player == hero_acting:
             game_state = pick_from_strategy(game_state, hero_strategy)
            # game_state = pick_from_strategy(game_state, opponent_strategy)
            # game_state = pick_action_randomly(game_state)
        else:
            # game_state = pick_action_randomly(game_state)
             game_state = pick_from_strategy(game_state, opponent_strategy)
            # game_state = pick_from_strategy(game_state, hero_strategy)
    if game_state.acting_player == hero_acting:
        pot = game_state.get_payoff()
    else:
        pot = -game_state.get_payoff()
    increment_sum += pot
    if i > increment:
        result.append(increment_sum + result[-1])
        increment += 1000
        increment_sum = 0
    hero_acting = (hero_acting + 1) % 2

print(result[-1])

plt.plot(range(len(result)), result)
plt.ylabel('Gain')
plt.xlabel('No. of hands')
plt.title('500k vs 15k - 1m')
plt.show()
