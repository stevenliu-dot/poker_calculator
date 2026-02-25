# app.py - Flask网站主程序
from flask import Flask, render_template, request, jsonify
from poker_logic import PokerCalculator
import json
import random
import itertools

app = Flask(__name__)
calculator = PokerCalculator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        
        num_players = int(data.get('num_players', 2))
        stage = data.get('stage', 'preflop')
        sims = int(data.get('simulations', 10000))
        
        # 获取手牌
        hands = []
        for i in range(num_players):
            hand_key = f'hand{i+1}'
            hand_value = data.get(hand_key, '')
            if hand_value and len(hand_value) == 4:
                hands.append(hand_value.upper())
            else:
                hands.append('')
        
        # 获取公共牌
        board = data.get('board', '').upper()
        
        # 根据阶段验证公共牌数量
        stage_requirements = {
            'preflop': 0,
            'flop': 6,      # 3张牌 * 2字符
            'turn': 8,      # 4张牌 * 2字符
            'river': 10     # 5张牌 * 2字符
        }
        
        if stage in stage_requirements:
            required_len = stage_requirements[stage]
            if len(board) != required_len and board != '':
                return jsonify({
                    'error': f'{stage}阶段需要{required_len//2}张公共牌'
                })
        
        # 计算概率
        result = calculator.calculate_odds(hands, board, num_players, sims)
        
        # 格式化手牌显示
        hand_display = []
        for hand in hands:
            if hand:
                hand_display.append(f"{hand[0:2]} {hand[2:4]}")
            else:
                hand_display.append("随机")
        
        return jsonify({
            'success': True,
            'result': result,
            'hands': hand_display,
            'board': ' '.join([board[i:i+2] for i in range(0, len(board), 2)]),
            'stage': stage,
            'simulations': sims
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/calculate_outs', methods=['POST'])
def calculate_outs():
    """
    计算转牌阶段的Outs
    请求参数：
    - player_hand: 当前玩家手牌（如 "AsKs"）
    - board: 公共牌（转牌阶段4张，如 "AhKdQcJh"）
    - opponent_hands: 已知对手手牌列表（可选）
    - simulations: 模拟次数（默认5000）
    """
    try:
        data = request.get_json()
        
        player_hand = data.get('player_hand', '').upper()
        board = data.get('board', '').upper()
        opponent_hands = data.get('opponent_hands', [])
        sims = int(data.get('simulations', 5000))
        
        # 验证输入
        if not player_hand or len(player_hand) != 4:
            return jsonify({'error': '无效的手牌格式，需要4个字符（如AsKs）'})
        
        if not board or len(board) != 8:
            return jsonify({'error': '转牌阶段需要4张公共牌（8个字符）'})
        
        # 标准化对手手牌
        opp_hands = []
        for hand in opponent_hands:
            if hand and len(hand) == 4:
                opp_hands.append(hand.upper())
        
        # 计算Outs
        outs_result = calculator.calculate_outs(player_hand, board, opp_hands, sims)
        
        if 'error' in outs_result:
            return jsonify({'error': outs_result['error']})
        
        return jsonify({
            'success': True,
            'outs': outs_result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/random_hand')
def random_hand():
    """生成随机手牌"""
    ranks = ['A','K','Q','J','T','9','8','7','6','5','4','3','2']
    suits = ['s','h','d','c']
    
    rank1 = random.choice(ranks)
    suit1 = random.choice(suits)
    rank2 = random.choice(ranks)
    suit2 = random.choice(suits)
    
    # 确保不是同一张牌
    while rank1+suit1 == rank2+suit2:
        rank2 = random.choice(ranks)
        suit2 = random.choice(suits)
    
    return jsonify({
        'hand': f"{rank1}{suit1}{rank2}{suit2}"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
