import csv
from typing import List, Dict
import random
from copy import deepcopy
import numpy as np
import GameFunctionsShort

NUM_ACTIONS = 5


class Player:
    def __init__(self, index: int, invested: int):
        self.index = index
        self.invested = invested


class InformationSet:
    def __init__(self):
        self.cumulative_regrets = np.zeros(shape=NUM_ACTIONS)
        self.strategy_sum = np.zeros(shape=NUM_ACTIONS)

    @staticmethod
    def normalize(strategy: np.array) -> np.array:
        if sum(strategy) > 0:
            strategy /= sum(strategy)
        else:
            strategy = np.array([1.0 / NUM_ACTIONS] * NUM_ACTIONS)
        return strategy

    def get_strategy(self, reach_probability: float) -> np.array:
        strategy = np.maximum(0, self.cumulative_regrets)
        strategy = self.normalize(strategy)

        self.strategy_sum += reach_probability * strategy
        return strategy

    def get_average_strategy(self) -> np.array:
        return self.normalize(self.strategy_sum.copy())


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

class RhodeIslandCFR:
    def __init__(self):
        self.infoset_map: Dict[str, InformationSet] = {}

    def get_information_set(self, game_state: GameState) -> InformationSet:
        representation = game_state.get_representation()
        if representation not in self.infoset_map:
            self.infoset_map[representation] = InformationSet()
        return self.infoset_map[representation]

    def cfr(self, game_state: GameState, reach_probabilities: np.array) -> int:
        if game_state.is_terminal():
            return game_state.get_payoff()

        info_set = self.get_information_set(game_state)

        strategy = info_set.get_strategy(reach_probabilities[game_state.acting_player])
        counterfactual_values = np.zeros(NUM_ACTIONS)

        for index, action in enumerate(game_state.actions):
            if action in game_state.get_actions():
                action_probability = strategy[index]

                new_reach_probabilities = reach_probabilities.copy()
                new_reach_probabilities[game_state.acting_player] *= action_probability

                counterfactual_values[index] = -self.cfr(game_state.handle_action(action), new_reach_probabilities)

        node_value = counterfactual_values.dot(strategy)

        for index, action in enumerate(game_state.actions):
            if action in game_state.get_actions():
                info_set.cumulative_regrets[index] += \
                    reach_probabilities[(game_state.acting_player + 1) % 2] *\
                    (counterfactual_values[index] - node_value)

        return node_value

    def train(self, iterations, increment):
        util = 0
        counter = 0
        deck = GameFunctionsShort.get_deck()
        for i in range(iterations):
            if i >= counter:
                print(str(i/5000) + "% done")
                counter += increment
            random.shuffle(deck)
            game_state = GameState(deck)
            reach_probabilities = np.ones(NUM_ACTIONS)
            util += self.cfr(game_state, reach_probabilities)
        return util


num_iterations = 500000
np.set_printoptions(precision=2, floatmode='fixed', suppress=True)

cfr_trainer = RhodeIslandCFR()
util = cfr_trainer.train(num_iterations, 500)

with open('Strategies/500k_iterations.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=' ',
                        quoting=csv.QUOTE_NONE,
                        escapechar=',')
    for name, info_set in sorted(cfr_trainer.infoset_map.items(), key=lambda s: len(s[0])):
        strategy = info_set.get_average_strategy()
        writer.writerow([name] + [strategy])
