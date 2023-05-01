from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from models.particle_filtering import game_recommendations
from pydantic import BaseModel

class StartingNodes(BaseModel):
    ids : list

app = FastAPI()

@app.post("/particle_filtering")
async def get_recommendations(nodes: StartingNodes):
    # Call your recommendation model with the input node ids to get similar game nodes
    recommended_games = game_recommendations(nodes.ids)
    recommended_games_json = jsonable_encoder(recommended_games)
    
    # Return the recommended nodes as a response
    return {"recommended_games": recommended_games_json}
