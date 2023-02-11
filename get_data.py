import numpy as np
import pandas as pd
import chess
import chess.pgn
import os
import requests
import io

# get a list of the archive urls for a given user
def get_archives(user):
    # response is a list of links containing the game archives for the user
    response = requests.get("https://api.chess.com/pub/player/"+user+"/games/archives")
    # get the urls and return the list of urls
    urls = response.json()
    return urls['archives']

# get a list of lists of all of a user's games from their archive
def get_game_pgn(urls):
    # games will hold the a list pgns of games from a given archive url
    # each item in the list will be a list of games (list of lists/dicts)
    nested_games = []
    for url in urls:
        nested_games.append(requests.get(url).json())
    return nested_games

# unnest the list of lists of a user's pgn's
def flatten_games(nested_games):
    flat_games = []
    for games_list in nested_games:
        for game in games_list['games']:
            flat_games.append(game['pgn'])
    return flat_games

# process the flattened games in to a more readable pgn format for the stockfish engine
def process_pgn(flat_games, user):
    rows = []
    for pgn in flat_games:
        row = {}
        # the pgn needs to be in a readline format. It assumes a pgn file and uses nextline in the function
        # io.StringIO turns a string into something like a read(rhymes with red) file with nextline capabilities
        pgn = io.StringIO(pgn)

        # use chess.pgn to parse the pgn of each game
        game = chess.pgn.read_game(pgn)
        # below line contains all the header info in a nested list. I have extracted it in the row['game_date']... lines below

        # Link is a unique id for each game
        row['game_link'] = game.headers['Link']

        # get the date
        row['game_date'] = game.headers["Date"]

        # get who was playing as black and white
        row['white'] = game.headers['White']
        row['black'] = game.headers['Black']
        # will use the termination statement to determine the winner. This will be easier than figuring out who won from the
        # result which would be difficult when playing friends
        row['result'] = game.headers['Termination']

        # get the opening used
        row['opening'] = game.headers['ECOUrl'].split("https://www.chess.com/openings/",1)[1]
        # get the user that won
        if row['white'] in row['result']:
            row['winner'] = row['white']
        elif row['black'] in row['result']:
            row['winner'] = row['black']
        else:
            row['winner'] = 'draw'

        # get the user color
        if row['white'] == user:
            row['user_color'] = 'white'
        else:
            row['user_color'] = 'black'

        # split into categories for counting winners
        if row['winner'] == user:
            row['winner_count'] = row['winner']
        elif row['winner'] == 'draw':
            row['winner_count'] = 'draw'
        else:
            row['winner_count'] = 'other'

        if 'EndTime' in game.headers:
            row['end_time'] = game.headers['EndTime']
        else:
            row['end_time'] = game.headers['EndDate']
        row['time_control'] = game.headers['TimeControl']
        row['white_elo'] = game.headers['WhiteElo']
        row['black_elo'] = game.headers['BlackElo']
        row['moves']=[x.uci() for x in game.mainline_moves()]
        rows.append(row)
    return rows

# take processed pgn list and turn into pandas df and add some helpful columns
def pgn_to_pandas(rows):
    #create a pd df of the extracted data
    loaded_games = pd.DataFrame(rows)

    #convert the date into a date object
    loaded_games['game_date'] = pd.to_datetime(loaded_games['game_date'])
    
    #convert the elos to int
    loaded_games['white_elo'] = loaded_games['white_elo'].astype(int)
    loaded_games['black_elo'] = loaded_games['black_elo'].astype(int)
    
    # explode the moves column. it is a column with each row containing a list
    loaded_games = loaded_games.explode('moves', ignore_index = True)

    #the line below adds all the moves into a single string of all the moves
    loaded_games['moves_list'] = loaded_games.groupby('end_time')['moves'].apply(lambda x: (x + ' ').cumsum().str.strip())
    loaded_games['moves_list'] = loaded_games['moves_list'].str.split()

    # group each row by the end time and then add a counter for each row in the group. Then
    # apply floor division to get the move
    # number. a "move" is each player making a turn.
    loaded_games['move_number'] = loaded_games.groupby('game_link').cumcount()//2
    loaded_games['move_number_actual'] = loaded_games.groupby('game_link').cumcount()
    
    return loaded_games

# get the pgn data from chess.com for a given user and flatten it into one game per list item
def get_chess_data(user):
    # get the game urls
    urls = get_archives(user)
    # get the games from chess.com
    raw_games = get_game_pgn(urls)
    # unnest the list of lists
    flat_games = flatten_games(raw_games)
    # clean games for stockfish processing
    processed_games = process_pgn(flat_games, user)
    # turn games into pandas df and add some valuable columns
    games = pgn_to_pandas(processed_games)
    return games


    


