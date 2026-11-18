# Bonus, cycle 5: the API in a container.
#
#   docker build -t wine-api .
#   docker run --rm -p 8000:8000 wine-api
#
# The image carries the code and the trained model, nothing else: no DVC, no
# MLflow, no dataset. Run the pipeline before building, so that
# models/model.pkl exists.

FROM python:3.12-slim
WORKDIR /app

# Only what serving needs: the full requirements.txt would put DVC, MLflow
# and Evidently in an image that never trains anything.
COPY requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt

##### cycle 5, bonus : copiez dans l'image le code (src/) et le modele
##### (models/model.pkl), chacun a la meme place que dans le depot
COPY ...

EXPOSE 8000

##### cycle 5, bonus : la commande qui lance l'API, en liste, comme dans un
##### terminal. Sans --reload, et a l'ecoute de toutes les interfaces
##### (--host 0.0.0.0) : 127.0.0.1, dans un conteneur, c'est le conteneur seul.
CMD [ ... ]
