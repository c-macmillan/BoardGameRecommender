import requests
import pandas as pd
import xmltodict
from ENV_CONSTANTS import GAME_INFO_PATH, REVIEW_DATA_PATH
import os
from tqdm import tqdm
import time




## Find the reviews on the main page for each board game
def get_reviews_from_game():
    game_df = pd.read_csv(GAME_INFO_PATH)
    game_ids = game_df['id'].values
    for game_id in tqdm(game_ids):
        usernames = []
        ratings = []
        comments = []
        response = requests.get(f"https://www.boardgamegeek.com/xmlapi2/thing?id={game_id}&comments=1")
        # Convert the XML response to a dictionary
        data_dict = xmltodict.parse(response.content)
        if 'items' not in data_dict or 'item' not in data_dict['items']:
            continue
        for comment in data_dict['items']['item']['comments']['comment']:
            if comment['@rating'] == 'N/A':
                continue
            usernames.append(comment["@username"])
            ratings.append(comment['@rating'])
            comments.append(comment['@value'])

        include_header = not (os.path.isfile(REVIEW_DATA_PATH))
        pd.DataFrame({
            "source_type": "Person",
            "source_id": usernames,
            "edge_type": "hasReviewed",
            "target_type": "Game",
            "target_id": game_id,
            "rating": ratings,
            "comment": comments
        }).to_csv(REVIEW_DATA_PATH, index=False, header=include_header, mode='a')


def get_reviews_by_users():
    ## Get the other reviews by each user in our dataset
    with open("data/users_to_check.txt", 'r') as f:
        user_ids = f.read().split(",")
    games = []
    ratings = []
    usernames = []
    comments = []
    users_to_retry = []
    users_completed = []
    for user_id in tqdm(user_ids):
        response = requests.get(f"https://boardgamegeek.com/xmlapi/collection/{user_id}?rated=1")
        try:
            data_dict = xmltodict.parse( response.content)
        except:
            continue

        # The server might have sent a "we are processing your request message"
        if 'items' not in data_dict:
            # Didn't get the data for these users, check again at the end
            users_to_retry.append(user_id)
            continue

        rated_games = data_dict['items']['item']
        
        ## This user only rated one game, so just skip them
        if type(rated_games) != list or len(rated_games) < 10:
            users_completed.append(user_id)
            continue

        for rated_game in rated_games:
            rating = rated_game['stats']['rating'].get('@value', rated_game['stats']['rating'])
            game_id = rated_game['@objectid']
            comment = rated_game.get('comment', "")
            games.append(game_id)
            ratings.append(rating)
            usernames.append(user_id)
            comments.append(comment)
        users_completed.append(user_id)

    for user_id in tqdm(users_to_retry):
        response = requests.get(f"https://boardgamegeek.com/xmlapi/collection/{user_id}?rated=1")
        try:
            data_dict = xmltodict.parse( response.content)
        except:
            continue

        # The server might have sent a "we are processing your request message"
        delay = 0
        while delay < 2:
            if 'items' in data_dict:
                break
            time.sleep(5)
            response = requests.get(f"https://boardgamegeek.com/xmlapi/collection/{user_id}?rated=1")
            try:
                data_dict = xmltodict.parse( response.content)
            except:
                delay += 1
                continue
                
            delay += 1

        else:
            # Didn't get the data for this user
            continue

        rated_games = data_dict['items']['item']
        print("Found Rated Games For:", user_id, "After", delay, "seconds")
        if type(rated_games) != list or len(rated_games) < 10:
            users_completed.append(user_id)
            continue
        for rated_game in rated_games:
            rating = rated_game['stats']['rating'].get('@value', rated_game['stats']['rating'])
            game_id = rated_game['@objectid']
            comment = rated_game.get('comment', "")
            games.append(game_id)
            ratings.append(rating)
            usernames.append(user_id)
            comments.append(comment)
        users_completed.append(user_id)

    review_df = pd.read_csv(REVIEW_DATA_PATH)
    print("Previous number of reviews:", len(review_df))
    review_df = pd.concat([review_df, pd.DataFrame({
                "source_type": "Person",
                "source_id": usernames,
                "edge_type": "hasReviewed",
                "target_type": "Game",
                "target_id": games,
                "rating": ratings,
                "comment": comments
            })])


    review_df.drop_duplicates(subset=['source_id', 'target_id'], inplace=True, keep='last')
    print("New number of reviews:", len(review_df))
    review_df.to_csv(REVIEW_DATA_PATH, index=False)

    for user in users_completed:
        try:
            user_ids.remove(user)
        except:
            print("Couldn't remove", user)
            continue

    with open("data/users_to_check.txt", 'w') as f:
        f.write(",".join(user_ids))

    print(len(user_ids), "users remaining to be checked")
