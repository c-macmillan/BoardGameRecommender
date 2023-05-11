import streamlit as st
import requests
import pickle
import os


fastapi = os.getenv('FASTAPI_URL') ## Used if deployed to Google Run
if fastapi is None:
    fastapi = "http://fastapi:8000" ## Used if running through the docker-compose


with open("static_data/name2nodeID.pickle", 'rb') as f:
    name2nodeID = pickle.load(f)


available_games = [name for name in name2nodeID.keys() if name.startswith("Game")]

initial_game_name = st.selectbox(
    'Choose a game that you want to get recommendations for',
    available_games)

game_id = name2nodeID[initial_game_name]

if st.button("Get Recommendations"):
        with st.spinner("Collecting recommendations"):

            url = f"{fastapi}/tfidf_similarity"
            params = {"id": game_id
                      }

            # Make a GET request to the URL endpoint, passing the query parameters
            response = requests.post(url, json=params)
            recommended_games = response.json()['recommended_games']
        if recommended_games:
            made_recommendations = True
        else:
            made_recommendations = False
            st.warning("Couldn't find any games to recommend with those inputs")
else:
    made_recommendations = False



if made_recommendations:
    for j in range(0,len(recommended_games), 5):
        rec_columns = st.columns(5)
        for i, recommendation in enumerate(recommended_games[j : j+5]):
            with rec_columns[i % 5]:
                try:
                    st.image(recommendation.get('image_url', recommendation['thumbnail_url']), caption=recommendation['name'], use_column_width=True)
                except:
                    st.image(recommendation.get('thumbnail_url'), caption=recommendation['name'])
                st.write(f"Average rating: {round(recommendation['avg_rating'],1)} by {recommendation['num_ratings']} users")
                st.write(f"Cosine similarity of descriptions: {round(recommendation['similarity'],2)}")
                try:
                    st.write(f"Description: {recommendation['short_description']}")
                except:
                    desc = recommendation.get('long_description')
                    if not desc:
                        desc = ""

                    st.write(desc[:100] + "...")
                link = f"https://boardgamegeek.com/boardgame/{recommendation['id']}/"
                st.markdown(f"[Learn more here]({link})")
        
        st.divider()