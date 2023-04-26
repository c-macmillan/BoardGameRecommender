import requests
import re
import os
import xmltodict
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from ENV_CONSTANTS import GRAPH_PATH, GAME_INFO_PATH, edgeType_NodeMap

def get_suggested_player_counts(data_dict):
    # Extract the best player counts for this game based on the BGG user poll
    num_players_poll = [poll for poll in data_dict['items']['item']
                        ['poll'] if poll['@name'] == 'suggested_numplayers'][0]
    num_votes = int(num_players_poll['@totalvotes'])
    num_players_dict = {}
    for poll_result in num_players_poll['results']:
        recommended = 0
        not_recommended = 0
        player_count = poll_result['@numplayers']
        for vote in poll_result['result']:
            match vote['@value']:
                case 'Best':
                    recommended += int(vote['@numvotes'])
                    not_recommended -= int(vote['@numvotes'])
                case 'Recommended':
                    recommended += int(vote['@numvotes'])
                case 'Not Recommended':
                    not_recommended += int(vote['@numvotes'])
        rec = recommended - not_recommended

        if '+' in player_count:
            max_players = int(data_dict['items']
                              ['item']['maxplayers']['@value'])
            for i in range(int(player_count.strip("+")), max_players + 1):
                if i in num_players_dict:
                    num_players_dict[i] = num_players_dict[i] + rec
                else:
                    num_players_dict[i] = rec
        else:
            num_players_dict[int(player_count)] = rec
    return {
        "suggestedPlayerCount": {
            "weight": [w / num_votes for w in num_players_dict.values()],
            "value": list(num_players_dict.keys())
        }
    }


def get_categorizations(data_dict):
    hasCategory = []
    hasMechanic = []
    hasPublisher = []
    hasDesigner = []
    hasArtist = []
    hasImplementation = []
    hasFamily = []
    for data in data_dict['items']['item']['link']:
        match data['@type']:
            case "boardgamecategory":
                hasCategory.append(data['@value'])
            case "boardgamemechanic":
                hasMechanic.append(data['@value'])
            case 'boardgamepublisher':
                hasPublisher.append(data['@value'])
            case 'boardgamedesigner':
                hasDesigner.append(data['@value'])
            case 'boardgameartist':
                hasArtist.append(data['@value'])
            case 'boardgameimplementation':
                hasImplementation.append(data['@id'])
            case 'boardgamefamily':
                hasFamily.append(data['@value'])

    return {
        "hasCategory": hasCategory,
        "hasMechanic": hasMechanic,
        "hasPublisher": hasPublisher,
        "hasDesigner": hasDesigner,
        "hasArtist": hasArtist,
        "hasImplementation": hasImplementation,
        "hasFamily": hasFamily
    }


def visit_game_page(game_id):
    """Extract properties from the BGG API based on the game id, 
        returns the long description, year published, min playing time, max playing time, complexity score and
        dictionary of player counts with how much the BGG community suggests playing at that count,
        all of the mechanics, categories, 'families', designers, artists, publishers,
    """
    response = requests.get(
        "https://www.boardgamegeek.com/xmlapi2/thing?id=" + str(game_id) + "&stats=1&comments=1")
    # Convert the XML response to a dictionary
    data_dict = xmltodict.parse(response.content)
    if 'items' not in data_dict:
        return None, None

    # Get data that will be attributes to the game node
    long_description = data_dict['items']['item']['description']
    complexity_score = data_dict['items']['item']['statistics']['ratings']['averageweight']['@value']
    year_published = data_dict['items']['item']['yearpublished']['@value']
    image_url = data_dict['items']['item']['image']
    playing_time = {"min": data_dict['items']['item']['minplaytime']['@value'],
                    "expected": data_dict['items']['item']['playingtime']['@value'],
                    "max": data_dict['items']['item']['maxplaytime']['@value']}

    # Get data that will have an edge to another node
    edges = get_categorizations(data_dict=data_dict)
    num_players_dict = get_suggested_player_counts(data_dict=data_dict)

    attributes = {"long_description": long_description, "complexity_socre": complexity_score, "year_published": year_published,
                  "image_url": image_url, "min_play_time": playing_time['min'], "max_play_time": playing_time['max'], 'expected_play_time': playing_time['expected']}

    edges.update(num_players_dict)

    return attributes, edges


def process_page(page_number):
    """Extracts the rank, game_id, name, short description, average rating and thumbnail for every game listed in the results table"""

    response = requests.get(
        "https://boardgamegeek.com/browse/boardgame/page/" + str(page_number))
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'class': 'collection_table'})
    rows = table.find_all('tr')[1:]

    board_game_info = []
    for row in rows:
        columns = row.find_all('td')
        if len(columns) < 6:
            continue

        rank = int(columns[0].text.strip())

        image_html_tag = str(columns[1].find("a").find("img"))
        id_html_tag = str(columns[1].find("a"))
        game_id = re.search('/(\d+)/', id_html_tag).group(1)
        thumbnail_url = re.search('src="(.*?)"', image_html_tag).group(1)

        name = columns[2].find_all('a')[0].text.strip()
        try:
            short_description = columns[2].find(
                'p', class_='smallefont dull').text.strip()
        except:
            short_description = None

        geek_rating = columns[3].text.strip()
        avg_rating = columns[4].text.strip()

        num_ratings = columns[5].text.strip()

        attributes, edges = visit_game_page(game_id)

        board_game = {'id': game_id, 'rank': rank, 'name': name, 'short_description': short_description,
                      'avg_rating': avg_rating, 'num_ratings': num_ratings, 'thumbnail_url': thumbnail_url}
        if attributes:
            board_game.update(attributes)
        board_game_info.append(board_game)
        if edges:
            for edge, value in edges.items():
                file_path = GRAPH_PATH + ".csv"
                include_header = not (os.path.isfile(file_path))
                if edge == 'suggestedPlayerCount':
                    df = pd.DataFrame({
                        "game_id": [game_id] * len(value['value']),
                        "target": value['value'],
                        "target_type": ["playerCount"] * len(value['value']),
                        "edge_type": ["suggestedPlayerCount"] * len(value['value']),
                        "weight": value['weight']
                    })
                else:
                    df = pd.DataFrame({
                        "game_id": [game_id] * len(value),
                        "target": value,
                        "target_type": edgeType_NodeMap[edge],
                        "edge_type": [edge] * len(value),
                        "weight": [1] * len(value)
                    })
                df.to_csv(file_path, index=False,
                          header=include_header, mode='a')
    return board_game_info


response = requests.get("https://boardgamegeek.com/browse/boardgame/")
soup = BeautifulSoup(response.content, 'html.parser')
num_pages = int(soup.find('a', title='last page').text.strip("[] "))
boardgames = []
for page_number in tqdm(range(1, min(num_pages, 21))):
    boardgames.extend(process_page(page_number))
include_header = not (os.path.isfile(GAME_INFO_PATH))
pd.DataFrame(boardgames).to_csv(GAME_INFO_PATH,
                                index=False, header=include_header, mode='a')
