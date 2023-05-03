import streamlit as st
import json
import requests


st.title("Board Game Recommendations")
with open("static_data/name2nodeID.json", 'r') as f:
    name2nodeID = json.load(f)

col1, col2 = st.columns([3,1])

with col1:
    initial_node_names = st.multiselect(
        'Choose which games, categories, mechanics, etc that you are interested in',
        list(name2nodeID.keys()))

    initial_node_ids = []
    for node_name in initial_node_names:
        initial_node_ids.append(name2nodeID[node_name])

expected_playtime = st.slider("How long do you want the game to last?", 15,180,step=15)
expected_complexity = st.select_slider("How much brain power do you want to use?", ["None", "Casual", "Smarty Pants", "Einstien"])
complexityMap = {
    "None":1,
    "Casual":2,
    "Smarty Pants": 3,
    "Einstien": 4
}
expected_complexity = complexityMap[expected_complexity]

with col2:
    st.write("")
    st.write("")
    if st.button("Get Recommendations"):
        with st.spinner("Collecting recommendations"):
            # Define the URL endpoint of the FastAPI application
            url = "http://127.0.0.1:8000/particle_filtering"

            # Define the query parameters
            params = {"ids": initial_node_ids,
                      "expected_play_time": expected_playtime,
                      "expected_complexity": expected_complexity}

            # Make a GET request to the URL endpoint, passing the query parameters
            response = requests.post(url, json=params)
            recommended_games = response.json()['recommended_games']
        if recommended_games:
            made_recommendations = True
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
        
        st.divider()