# BoardGameRecommender

Get Board Game recommendations based on a game you enjoy playing, or select game mechanisms, categories, or designers to get games that share characteristics.

The data that backs these recommendations was scraped from BoardGameGeek.com and is hosted on a Neo4j knowledge-graph. The deployed web app can be found at https://web-app-streamlit-wka7c67hba-uc.a.run.app/ which is hosted by Google Cloud Run with two Docker containers. One is the FastAPI backend that provides TF-IDF similarity recommendations or a Particle Filtering recommendation algorithm, which is based on this paper: https://openproceedings.org/2020/conf/edbt/paper_357.pdf
