from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from models.particle_filtering import game_recommendations
from models.tfidf_search import get_top_n_games
from pydantic import BaseModel
import uvicorn

class Particle_Filtering_Input(BaseModel):
    ids : list
    num_recs : int | None = 10

class TFIDF_Input(BaseModel):
    id : int
    num_recs : int | None = 10

app = FastAPI()

@app.post("/test")
async def get_test():
    return {"message": "You received a response"}

@app.post("/tfidf_similarity")
async def get_tfidf_recommendations(input: TFIDF_Input):
    recommended_games = get_top_n_games(input.id, n=input.num_recs)
    recommended_games_json = jsonable_encoder(recommended_games)
    return {"recommended_games": recommended_games_json}


@app.post("/particle_filtering")
async def get_particle_filtering_recommendations(input: Particle_Filtering_Input):
    # Call your recommendation model with the input node ids to get similar game nodes
    recommended_games = game_recommendations(input.ids, num_recs=input.num_recs)
    recommended_games_json = jsonable_encoder(recommended_games)

    # Return the recommended nodes as a response
    return {"recommended_games": recommended_games_json}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)