from stockfish import Stockfish
import numpy as np
import pandas as pd
import chess
import chess.pgn
import tqdm
import os

# this is the path to the .exe of stockfish, not the stockfish python module
stockfish = Stockfish(path="/home/sam/Desktop/stockfish_14_linux_x64/stockfish_14_x64", depth = 15,
                      parameters={"Threads": 2})

# get the score for a given move
def get_scores(move, move_num):
    # if the move number is 0, i.e., the first move of a game, set the board position and evaluate
    if(move_num == 0):
        stockfish.set_position([move])
        score_dict = stockfish.get_evaluation()
    # otherwise, move the piece given the move and evaluate
    else:
        stockfish.make_moves_from_current_position([move])
        score_dict = stockfish.get_evaluation()
    return score_dict

# run the chess engine given a df of games where each row represents a single move
def run_engine(games):
    # initialize empty lists for score values and score types
    scores = []
    score_types = []
    
    # use tqdm for progess bar. runs from 0 to length of games df
    for i in tqdm.tqdm(range(games.shape[0])):
        # get the score for the current row
        score_dict = get_scores(games.iloc[i]['moves'], games.iloc[i]['move_number_actual'])
        # add the score value divided by 100 (centipawns to pawns) to the scores list
        scores.append(score_dict['value'] / 100)
        # add the score type to the score_types list
        score_types.append(score_dict['type'])

    # add columns to the games df for the score and score type
    games['score'] = scores
    games['score_type'] = score_types
    
    return games

# check if any scores are stored and get new scores for games that haven't been run
def load_scores(fp, games):
    # check if scored game file exists and load
    if os.path.exists(fp):
        scored_games = pd.read_csv(fp)
    # if no scores saved, run the engine on full game df
    else:
        return run_engine(games)
    
    # with loaded scored games, get the max date
    max_date = scored_games['game_date'].max()
    # filter the games from the api call with the max date from the loaded scored games
    unscored_games = games[games['game_date'] >= max_date]
    # run the engine on just the games that haven't been scored yet and append to the end of df
    scored_games = pd.concat([scored_games, run_engine(unscored_games)])
    
    return scored_games