# poker_logic.py - 核心扑克逻辑
from enum import Enum
from collections import Counter
from typing import List, Tuple, Dict, Set
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
    
    def to_code(self) -> str:
        """转换为代码格式，如 'As', 'Kh'"""
        suit_map = {Suit.HEARTS: 'h', Suit.DIAMONDS: 'd', Suit.CLUBS: 'c', Suit.SPADES: 's'}
        return f"{self.rank.value}{suit_map[self.suit]}"

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
    
    def calculate_outs(self, player_hand_str: str, board_str: str, 
                       opponent_hands_str: List[str], sims: int = 5000) -> Dict:
        """
        计算转牌阶段的Outs
        返回能让当前玩家获胜的所有河牌
        """
        if not player_hand_str or len(player_hand_str) != 4:
            return {"error": "无效的手牌"}
        
        if not board_str or len(board_str) != 8:  # 转牌阶段应该有4张公共牌
            return {"error": "转牌阶段需要4张公共牌"}
        
        # 解析手牌
        player_hand = [self._parse_card(player_hand_str[0:2]), 
                       self._parse_card(player_hand_str[2:4])]
        
        # 解析公共牌（4张）
        board_cards = []
        for i in range(0, 8, 2):
            card = self._parse_card(board_str[i:i+2])
            board_cards.append(card)
        
        # 解析已知对手手牌
        opponent_hands = []
        for hand_str in opponent_hands_str:
            if hand_str and len(hand_str) == 4:
                opp_hand = [self._parse_card(hand_str[0:2]),
                           self._parse_card(hand_str[2:4])]
                opponent_hands.append(opp_hand)
        
        # 创建可用牌堆
        deck = self._create_deck()
        used_cards = set()
        
        # 移除已知牌
        for card in player_hand:
            used_cards.add(card)
        for card in board_cards:
            used_cards.add(card)
        for opp_hand in opponent_hands:
            for card in opp_hand:
                used_cards.add(card)
        
        for card in used_cards:
            if card in deck:
                deck.remove(card)
        
        # 计算当前胜率（不带河牌）
        current_equity = self._simulate_equity(
            player_hand, opponent_hands, board_cards, deck.copy(), sims
        )
        
        # 遍历所有可能的河牌，计算Outs
        outs_cards = []
        outs_details = []
        
        for river_card in deck:
            # 模拟带这张河牌的情况
            new_equity = self._simulate_equity_with_river(
                player_hand, opponent_hands, board_cards, river_card, sims // 10
            )
            
            # 如果这张河牌能显著提升胜率（从落后到领先），则视为Out
            if new_equity > current_equity + 20:  # 胜率提升超过20%
                outs_cards.append(river_card.to_code())
                outs_details.append({
                    "card": river_card.to_code(),
                    "card_display": f"{river_card.rank.value}{river_card.suit.value}",
                    "current_equity": round(current_equity, 2),
                    "new_equity": round(new_equity, 2),
                    "equity_gain": round(new_equity - current_equity, 2)
                })
        
        # 按胜率提升排序
        outs_details.sort(key=lambda x: x["equity_gain"], reverse=True)
        
        return {
            "outs_count": len(outs_cards),
            "outs_cards": outs_cards,
            "outs_details": outs_details,
            "current_equity": round(current_equity, 2),
            "deck_remaining": len(deck),
            "outs_percentage": round(len(outs_cards) / len(deck) * 100, 2) if deck else 0
        }
    
    def _simulate_equity(self, player_hand: List[Card], opponent_hands: List[List[Card]], 
                         board_cards: List[Card], deck: List[Card], sims: int) -> float:
        """模拟计算当前胜率"""
        wins = 0
        ties = 0
        
        num_opponents = len(opponent_hands) if opponent_hands else 1
        
        for _ in range(sims):
            temp_deck = deck.copy()
            
            # 补齐未知对手手牌
            all_hands = [player_hand.copy()]
            for opp_hand in opponent_hands:
                all_hands.append(opp_hand.copy())
            
            # 如果有未知对手，随机发牌
            while len(all_hands) <= num_opponents:
                if len(temp_deck) >= 2:
                    new_hand = random.sample(temp_deck, 2)
                    all_hands.append(new_hand)
                    for card in new_hand:
                        temp_deck.remove(card)
            
            # 发河牌
            if temp_deck:
                river = random.choice(temp_deck)
                final_board = board_cards + [river]
            else:
                final_board = board_cards
            
            # 比较手牌
            best_scores = []
            for hand in all_hands:
                best_score = None
                for combo in itertools.combinations(hand + final_board, 5):
                    hand_type, score = self.evaluate_hand(list(combo))
                    if best_score is None or score > best_score:
                        best_score = score
                best_scores.append(best_score)
            
            player_score = best_scores[0]
            opponent_best = max(best_scores[1:]) if len(best_scores) > 1 else [0]
            
            if player_score > opponent_best:
                wins += 1
            elif player_score == opponent_best:
                ties += 1
        
        return (wins + ties / 2) / sims * 100
    
    def _simulate_equity_with_river(self, player_hand: List[Card], 
                                     opponent_hands: List[List[Card]], 
                                     board_cards: List[Card], 
                                     river_card: Card, sims: int) -> float:
        """模拟计算特定河牌下的胜率"""
        wins = 0
        ties = 0
        
        num_opponents = len(opponent_hands) if opponent_hands else 1
        final_board = board_cards + [river_card]
        
        for _ in range(sims):
            # 补齐未知对手手牌（从剩余牌堆中随机发）
            temp_deck = self._create_deck()
            used = set(player_hand + list(final_board))
            for opp_hand in opponent_hands:
                used.update(opp_hand)
            
            for card in used:
                if card in temp_deck:
                    temp_deck.remove(card)
            
            all_hands = [player_hand.copy()]
            for opp_hand in opponent_hands:
                all_hands.append(opp_hand.copy())
            
            # 补齐未知对手
            while len(all_hands) <= num_opponents:
                if len(temp_deck) >= 2:
                    new_hand = random.sample(temp_deck, 2)
                    all_hands.append(new_hand)
                    for card in new_hand:
                        temp_deck.remove(card)
            
            # 比较手牌
            best_scores = []
            for hand in all_hands:
                best_score = None
                for combo in itertools.combinations(hand + final_board, 5):
                    hand_type, score = self.evaluate_hand(list(combo))
                    if best_score is None or score > best_score:
                        best_score = score
                best_scores.append(best_score)
            
            player_score = best_scores[0]
            opponent_best = max(best_scores[1:]) if len(best_scores) > 1 else [0]
            
            if player_score > opponent_best:
                wins += 1
            elif player_score == opponent_best:
                ties += 1
        
        return (wins + ties / 2) / sims * 100
