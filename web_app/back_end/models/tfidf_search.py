from neo4j import GraphDatabase
import time
import os
from models.game import Game
from models.graph_utils import get_game_info


password = os.getenv('PASSWORD')
user_name = os.getenv('USER_NAME')
url = os.getenv('URL')

def get_top_n_games(game_id, num_recs=10):
    driver = GraphDatabase.driver(url, auth=(user_name, password))
    print("Connected to neo4j")
    with driver.session(database='neo4j') as session:
        tx = session.begin_transaction()
        query = (
        """
        MATCH (n:Game)-[r:similarTo]-(m:Game)
        WHERE n.id = $game_id
        RETURN r.weight, m.id
        """
        )
        results = tx.run(query, game_id=game_id)
        neighbors = []
        for result in results:
            neighbor_id = result.get("m.id")
            relation_weight = result.get("r.weight")
            neighbors.append( (neighbor_id, relation_weight) )

        similar_games = sorted(neighbors, key=lambda x: x[1], reverse=True)[:num_recs]
        recommendations = get_game_info(tx, similar_games)
        tx.close()

    return recommendations
