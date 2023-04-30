from neo4j import GraphDatabase
import time
from game import Game
from neo4j_info import PASSWORD, USER_NAME, URL

password = PASSWORD
user_name = USER_NAME
url = URL

def game_recommendations(node_id_list, num_particles=10, c=0.15):
    """
    Particle Filtering based on https://github.com/DenisGallo/Neo4j-ParticleFiltering/blob/master/src/main/java/pfiltering/ParticleFiltering.java
    Finds nodes similar to input nodes by traversing the graph using particles
    Inputs:
        list of node ids to start the traversal
        number of particles which will be split between the starting nodes equally
        c: a decay rate so that nodes further from the starting node won't contribute as much to the similarity and less edges will be chosen to traverse
    Outputs:
        A list of game objects that are similar to the input nodes
    """
    start_time = time.time()
    driver = GraphDatabase.driver(url, auth=(user_name, password))
    p = {}
    v = {}
    tao = 1.0/num_particles
    with driver.session(database='neo4j') as session:

        ### Initialize Starting Nodes
        transaction = session.begin_transaction()
        query = (
        """
        MATCH (n)
        WHERE n.id IN $node_id_list
        RETURN n
        """
        )
        result = transaction.run(query, node_id_list=node_id_list)
        for node in result:
            p[node['n'].get("id")] = (1/tao)/len(node_id_list)
            v[node['n'].get("id")] = (1/tao)/len(node_id_list)

        ### Iterate through neighbors until the particles degrade to 0
        while(len(p.keys())):
            temp = {}
            for node in p.keys():
                particles = p[node] * (1-c)
                neighbors, total_weight = get_neighbors(transaction, node)
                for neighbor_id, neighbor_weight in neighbors:
                    if particles <= tao:
                        break
                    passing = particles * (neighbor_weight / total_weight)
                    if passing < tao:
                        passing = tao
                    particles -= passing
                    if neighbor_id in temp:
                        passing += temp[neighbor_id]
                    temp[neighbor_id] = passing
            p = temp
            for id, value in p.items():
                if id in v:
                    v[id] = v[id] + value
                else:
                    v[id] = value
        
        ### Filter the similar nodes for games only
        similar_games = []
        for node_id, similarity in v.items():
            if type(node_id) == int and node_id not in node_id_list:
                similar_games.append((node_id, similarity))

        ### Find the information for each game
        
        recommendations = get_game_info(transaction, similar_games)
        transaction.close()
    print(f"Recommendations took {time.time()-start_time} seconds to compute")
    return recommendations


@staticmethod
def get_neighbors(tx, node_id):
    """
    Finds all of the neighbors for a given node id
        Inputs:
            tx: Neo4j transaction
            node_id: the node's 'id' attribute
        Outputs:
            list of (neighbor ids, edge_weight) sorted by edge_weight descending
            the cumulative weights of all neighbors
        """
    query = (
        """
        MATCH (n)-[r]-(m)
        WHERE n.id = $node_id
        RETURN r.weight, m.id
        """
    )
    results = tx.run(query, node_id=node_id)
    neighbors = []
    total_weight = 0.0
    for result in results:
        neighbor_id = result.get("m.id")
        relation_weight = result.get("r.weight")
        total_weight += relation_weight
        neighbors.append( (neighbor_id, relation_weight) )
    neighbors.sort(key=lambda x: x[1])
    return neighbors[-1::-1], total_weight


@staticmethod
def get_game_info(tx, similar_games):
        """
        Creates a list of Game objects based on the game ids provided
            Input:
                Neo4j transaction
                List of (game id, similarity score)
            Output:
                List of Game Objects, sorted by similarity score descending"""
        query = (
        """
        MATCH (n:Game)
        WHERE n.id IN $game_ids
        RETURN 
                n.id, n.num_ratings, n.name, n.short_description, n.long_description, n.complexity_socre, n.year_published, 
                n.expected_play_time, n.avg_rating, n.thumbnail_url, n.image_url, n.min_play_time, n.max_play_time, n.rank
        """
        )
        ## Extract the game ids from the similar games list and store the similarities so we can access them later
        game_ids = list(map(lambda x: x[0], similar_games))
        similarity_map = {}
        for game_id, similarity in similar_games:
            similarity_map[game_id] = similarity
        result = tx.run(query, game_ids=game_ids)

        game_recs = []
        for record in result:
            attr = {}
            attr["id"] = record.get("n.id")
            attr["num_ratings"] = record.get("n.num_ratings")
            attr["name"] = record.get("n.name")
            attr["short_descrption"] = record.get("n.short_descrption")
            attr["long_description"] = record.get("n.long_description")
            attr["complexity_score"] = record.get("n.complexity_socre")
            attr["year_published"] = record.get("n.year_published")
            attr["expected_play_time"] = record.get("n.expected_play_time")
            attr["avg_rating"] = record.get("n.avg_rating")
            attr["thumbnail_url"] = record.get("n.thumbnail_url")
            attr["image_url"] = record.get("n.image_url")
            attr["min_play_time"] = record.get("n.min_play_time")
            attr["max_play_time"] = record.get("n.max_play_time")
            attr["rank"] = record.get("n.rank")
            attr['similarity'] = similarity_map[attr['id']]
            game_recs.append(Game(attr))
    
        return sorted(game_recs, key=lambda x: x.similarity, reverse=True)