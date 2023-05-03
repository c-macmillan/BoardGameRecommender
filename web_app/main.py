from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from models.particle_filtering import game_recommendations
from pydantic import BaseModel
from models.game import Game

class Input(BaseModel):
    ids : list
    expected_complexity : int | None = None
    expected_play_time : int | None = None

app = FastAPI()

@app.post("/particle_filtering")
async def get_recommendations(input: Input):
    # Call your recommendation model with the input node ids to get similar game nodes
    recommended_games = game_recommendations(input.ids)

    filtered_games = []
    for game in recommended_games:
        add_game = True
        if game.__getattribute__("complexity_score"):
            if game.complexity_score < input.expected_complexity - 1.25 and game.complexity_score > input.expected_complexity + 1.25:
                add_game = False

        if game.__getattribute__("expected_play_time"):
            if game.expected_play_time > input.expected_play_time - 45 and game.expected_play_time < input.expected_play_time + 15:
                add_game = False
        if add_game:
            filtered_games.append(game)

    if len(filtered_games) > 1:
        recommended_games_json = jsonable_encoder(filtered_games)
    else:
        print("Couldn't find games within complexity and length requirement")
        recommended_games_json = jsonable_encoder(recommended_games)
    print(f"Filtered out {len(recommended_games)-len(filtered_games)} games based on complexity/length")

    # Return the recommended nodes as a response
    return {"recommended_games": recommended_games_json}
