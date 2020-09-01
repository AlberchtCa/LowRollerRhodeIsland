import itertools
from typing import List

# Straight flush : 1
# Three of a kind : 2
# Straight : 3
# Flush : 4
# Pair : 5
# High card: 6


def get_winning_hand(hand1: List[str], hand2: List[str]) -> int:
    rank1 = get_rank(hand1)
    rank2 = get_rank(hand2)
    if rank1 > rank2:
        return 0
    if rank2 > rank1:
        return 2
    if rank2 == rank1:
        count1 = count_cards(hand1)
        count2 = count_cards(hand2)
        for i in range(13, -1, -1):
            if count1[i] > count2[i]:
                return 0
            if count1[i] < count2[i]:
                return 2
        return 1


def get_deck() -> List[str]:
    cards = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suits = ['h', 'c', 'd', 's']
    deck = []
    for card, suit in itertools.product(cards, suits):
        deck.append(card + suit)
    return deck


def get_rank(hand: List[str]) -> int:
    count = count_cards(hand)
    if is_straight_flush(hand, count):
        return 1
    if is_triplet(count):
        return 2
    if is_straight(count):
        return 3
    if is_flush(hand):
        return 4
    if is_pair(count):
        return 5

    return 6


def count_cards(hand: List[str]) -> List[int]:
    cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    count = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for i in range(3):
        for j in range(14):
            if hand[i][0] == cards[j]:
                count[j] += 1
    return count


def is_pair(count: List[int]) -> bool:
    if 2 in count:
        return True
    return False


def is_flush(hand: List[str]) -> bool:
    for i in range(2):
        if hand[i][1] != hand[i+1][1]:
            return False
    return True


def is_straight(count: List[int]) -> bool:
    for i in range(12):
        if count[i] == count[i + 1] == count[i + 2] == 1:
            return True
    return False


def is_triplet(count: List[int]) -> bool:
    if 3 in count:
        return True
    return False


def is_straight_flush(hand: List[str], count: List[int]) -> bool:
    if is_flush(hand) and is_straight(count):
        return True
    return False
