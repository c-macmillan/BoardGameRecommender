
from models.game import Game

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
            attr["short_descrption"] = record.get("n.short_description")
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