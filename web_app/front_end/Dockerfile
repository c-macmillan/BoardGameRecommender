FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD streamlit run --server.port 8501 --server.enableCORS false particle_filtering_recommendations.py