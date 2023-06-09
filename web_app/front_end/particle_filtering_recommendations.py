import streamlit as st
import requests
import pickle
import os

st.set_page_config(
    page_title="Board Game Recommender",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)


fastapi = os.getenv('FASTAPI_URL') ## Used if deployed to Google Run
if fastapi is None:
    fastapi = "http://fastapi:8000" ## Used if running through the docker-compose

st.title("Board Game Recommendations")
st.subheader("Find new games to try based on your preferences!")
with open("static_data/name2nodeID.pickle", 'rb') as f:
    name2nodeID = pickle.load(f)

col1, col2 = st.columns([3,1])

with col1:
    initial_node_names = st.multiselect(
        'Choose which games, categories, mechanics, etc that you are interested in by typing in the search below',
        list(name2nodeID.keys()))

    initial_node_ids = []
    for node_name in initial_node_names:
        initial_node_ids.append(name2nodeID[node_name])

#     expected_playtime = st.slider("How long do you want the game to last?", 15,180,step=15)
#     expected_complexity = st.select_slider("How much brain power do you want to use?", ["None", "Casual", "Smarty Pants", "Einstein"])
#     complexityMap = {
#         "None":1,
#         "Casual":2,
#         "Smarty Pants": 3,
#         "Einstein": 4
#     }
# expected_complexity = complexityMap[expected_complexity]
st.write("These recommendations are based on the Particle Filtering algorithm proposed in this paper: https://openproceedings.org/2020/conf/edbt/paper_357.pdf")
with col2:
    st.write("")
    st.write("")
    if st.button("Get Recommendations"):
        with st.spinner("Collecting recommendations"):
            # Define the URL endpoint of the FastAPI application
            url = f"{fastapi}/particle_filtering"

            # Define the query parameters
            params = {"ids": initial_node_ids,
                    #   "expected_play_time": expected_playtime,
                    #   "expected_complexity": expected_complexity
                    }

            # Make a GET request to the URL endpoint, passing the query parameters
            try:
                response = requests.post(url, json=params)

                recommended_games = response.json()['recommended_games']
            except ValueError:
                st.error("It looks like our Neo4j Database is down (a byproduct of using the free version) contact macmillan.connor@gmail.com to get it back up and running")
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
                st.write(f"Particle Filtering similarity to inputs: {round(recommendation['similarity'],2)}")
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