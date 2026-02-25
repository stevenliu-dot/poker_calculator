# poker_logic.py - 核心扑克逻辑
from enum import Enum
from collections import Counter
from typing import List, Tuple, Dict
import random
import itertools

class Suit(Enum):
    HEARTS = '♥'
    DIAMONDS = '♦'
    CLUBS = '♣'
    SPADES = '♠'

class Rank(Enum):
    TWO = '2'; THREE = '3'; FOUR = '4'; FIVE = '5'; SIX = '6'
    SEVEN = '7'; EIGHT = '8'; NINE = '9'; TEN = 'T'
    JACK = 'J'; QUEEN = 'Q'; KING = 'K'; ACE = 'A'

class Card:
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit
        self.value = list(Rank).index(rank)
    
    def __repr__(self):
        return f"{self.rank.value}{self.suit.value}"
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit
    
    def __hash__(self):
        return hash((self.rank, self.suit))

class PokerCalculator:
    def __init__(self):
        self.deck = self._create_deck()
    
    def _create_deck(self):
        return [Card(rank, suit) for suit in Suit for rank in Rank]
    
    def _parse_card(self, card_str: str) -> Card:
        rank_map = {'2':Rank.TWO,'3':Rank.THREE,'4':Rank.FOUR,'5':Rank.FIVE,
                   '6':Rank.SIX,'7':Rank.SEVEN,'8':Rank.EIGHT,'9':Rank.NINE,
                   'T':Rank.TEN,'J':Rank.JACK,'Q':Rank.QUEEN,'K':Rank.KING,'A':Rank.ACE}
        suit_map = {'h':Suit.HEARTS,'d':Suit.DIAMONDS,'c':Suit.CLUBS,'s':Suit.SPADES}
        return Card(rank_map[card_str[0].upper()], suit_map[card_str[1].lower()])
    
    def evaluate_hand(self, cards: List[Card]) -> Tuple[str, List[int]]:
        if len(cards) != 5:
            return ("Invalid", [0])
        
        ranks = [c.rank for c in cards]
        rank_values = sorted([c.value for c in cards], reverse=True)
        
        rank_counter = Counter(ranks)
        suit_counter = Counter([c.suit for c in cards])
        
        is_flush = len(suit_counter) == 1
        
        sorted_vals = sorted(rank_values)
        is_straight = all(sorted_vals[i]+1 == sorted_vals[i+1] for i in range(4))
        
        # 特殊顺子 A-2-3-4-5
        if set(rank_values) == {14,2,3,4,5}:
            is_straight = True
            rank_values = [5,4,3,2,14]
        
        # 手牌等级判断
        if is_flush and is_straight:
            if max(rank_values) == 14 and min(rank_values) == 10:
                return ("Royal Flush", [10, max(rank_values)])
            return ("Straight Flush", [9, max(rank_values)])
        
        if 4 in rank_counter.values():
            quad_rank = [r for r,cnt in rank_counter.items() if cnt==4][0]
            kicker = [r for r in rank_counter if r!=quad_rank][0]
            return ("Four of a Kind", [8, list(Rank).index(quad_rank), list(Rank).index(kicker)])
        
        if 3 in rank_counter.values() and 2 in rank_counter.values():
            trips = [r for r,cnt in rank_counter.items() if cnt==3][0]
            pair = [r for r,cnt in rank_counter.items() if cnt==2][0]
            return ("Full House", [7, list(Rank).index(trips), list(Rank).index(pair)])
        
        if is_flush:
            return ("Flush", [6] + rank_values)
        
        if is_straight:
            return ("Straight", [5] + [max(rank_values)])
        
        if 3 in rank_counter.values():
            trips = [r for r,cnt in rank_counter.items() if cnt==3][0]
            kickers = sorted([r for r in rank_counter if r!=trips], 
                           key=lambda x: list(Rank).index(x), reverse=True)
            return ("Three of a Kind", [4, list(Rank).index(trips)] + 
                   [list(Rank).index(k) for k in kickers])
        
        pairs = [r for r,cnt in rank_counter.items() if cnt==2]
        if len(pairs) == 2:
            pair_vals = sorted([list(Rank).index(p) for p in pairs], reverse=True)
            kicker = [r for r,cnt in rank_counter.items() if cnt==1][0]
            return ("Two Pair", [3] + pair_vals + [list(Rank).index(kicker)])
        
        if len(pairs) == 1:
            pair_val = list(Rank).index(pairs[0])
            kickers = sorted([r for r,cnt in rank_counter.items() if cnt==1],
                           key=lambda x: list(Rank).index(x), reverse=True)
            return ("One Pair", [2, pair_val] + [list(Rank).index(k) for k in kickers])
        
        return ("High Card", [1] + rank_values)
    
    def calculate_odds(self, hands_str: List[str], board_str: str, 
                      num_players: int, sims: int = 10000) -> Dict:
        # 解析手牌
        player_hands = []
        for hand_str in hands_str:
            if hand_str and len(hand_str) == 4:
                card1 = self._parse_card(hand_str[0:2])
                card2 = self._parse_card(hand_str[2:4])
                player_hands.append([card1, card2])
            else:
                player_hands.append([])
        
        # 解析公共牌
        board_cards = []
        if board_str:
            for i in range(0, len(board_str), 2):
                if i+2 <= len(board_str):
                    card = self._parse_card(board_str[i:i+2])
                    board_cards.append(card)
        
        # 蒙特卡洛模拟
        results = {i: {'wins': 0, 'ties': 0} for i in range(num_players)}
        
        for _ in range(sims):
            # 创建可用牌堆
            deck = self._create_deck()
            used_cards = []
            
            # 移除已知牌
            for hand in player_hands:
                if hand:
                    for card in hand:
                        if card in deck:
                            deck.remove(card)
                            used_cards.append(card)
            
            for card in board_cards:
                if card in deck:
                    deck.remove(card)
                    used_cards.append(card)
            
            # 补齐未知手牌
            all_hands = []
            for i in range(num_players):
                if i < len(player_hands) and player_hands[i]:
                    all_hands.append(player_hands[i].copy())
                else:
                    hand = random.sample(deck, 2)
                    all_hands.append(hand)
                    for card in hand:
                        deck.remove(card)
            
            # 补齐公共牌
            final_board = board_cards.copy()
            cards_needed = 5 - len(board_cards)
            if cards_needed > 0:
                additional = random.sample(deck, cards_needed)
                final_board.extend(additional)
            
            # 比较手牌
            best_scores = []
            for hand in all_hands:
                best_score = None
                for combo in itertools.combinations(hand + final_board, 5):
                    hand_type, score = self.evaluate_hand(list(combo))
                    if best_score is None or score > best_score:
                        best_score = score
                best_scores.append(best_score)
            
            # 确定赢家
            max_score = max(best_scores)
            winners = [i for i,s in enumerate(best_scores) if s == max_score]
            
            if len(winners) == 1:
                results[winners[0]]['wins'] += 1
            else:
                for w in winners:
                    results[w]['ties'] += 1
        
        # 计算百分比
        output = {}
        for i in range(num_players):
            win_pct = results[i]['wins'] / sims * 100
            tie_pct = results[i]['ties'] / sims * 100
            equity = win_pct + tie_pct / len(winners) if winners else win_pct
            
            output[f"player{i+1}"] = {
                "win": round(win_pct, 2),
                "tie": round(tie_pct, 2),
                "equity": round(equity, 2)
            }
        
        return output