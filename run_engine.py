from stockfish import Stockfish
import numpy as np
import pandas as pd
import chess
import chess.pgn

# this is the path to the .exe of stockfish, not the stockfish python module
stockfish = Stockfish(path="/home/sam/Desktop/stockfish_14_linux_x64/stockfish_14_x64")

def get_score(move, move_num):
    if(move_num == 0):
        stockfish.set_position([move])
        score_dict = stockfish.get_evaluation()
    else:
        stockfish.make_moves_from_current_position([move])
        score_dict = stockfish.get_evaluation()
    return score_dict

def run_engine(games):
    games['score_dict'] = games.apply(lambda x: get_score(x.moves, x.move_number_actual), axis=1)
    games = games.join(pd.json_normalize(games.score_dict))
    games.rename({'type':'score_type', 'value':'score'}, axis = 'columns', inplace = True)
    games['score'] = games['score'] / 100
    games = games.drop('score_dict', axis = 1)
    return games