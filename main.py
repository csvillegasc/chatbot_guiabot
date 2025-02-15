"""
Chatbot de asistencia para encuestas de servicio al cliente

Desarrollado por:
Equipo 19

"""

#importa la clase FastAPI de la librería fastapi
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize 
from nltk.corpus import wordnet 

# Indicamos donde nltk buscará los datos
nltk.data.path.append("C:/Users/admin_bizagi06/AppData/Local/Programs/Python/Python312/Scripts/nltk_data")

nltk.download('punkt')  # Paquete para dividir el texto en palabras
nltk.download('wordnet')  # Paquete para buscar sinónimos en inglés

# ✅ Cargar el archivo de datos normalizando la categoría
def load_data():
    df = pd.read_csv("Dataset/Customer_support_data.csv")

    # Convertir todas las categorías a minúsculas y eliminar espacios extra
    df['category'] = df['category'].astype(str).str.strip().str.lower()

    return df.fillna('').to_dict('records')

survey_list = load_data()

# ✅ Función para encontrar sinónimos de una palabra
def get_synonyms(word):
    synonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.append(lemma.name())
    return synonyms

# ✅ Creamos la aplicación
app = FastAPI(
    title="GuIAbot, tu asistente virtual",
    description="Este es un chatbot que te ayudará a resolver tus dudas sobre las encuestas de servicio al cliente",
    version="1.0.0"
)

# ✅ Ruta de inicio
@app.get("/", tags=["Home"])
def home():
    return HTMLResponse(content="<h1> Bienvenido a GuIAbot </h1>")

# ✅ Ruta para obtener todas las encuestas
@app.get("/survey/", tags=["Encuestas"])
def get_survey():
    if not survey_list:
        raise HTTPException(status_code=500, detail="No se encontraron encuestas")
    return survey_list

# ✅ Ruta para obtener una encuesta por su ID
@app.get("/survey/{survey_id}", tags=["Encuestas"])
def get_survey(survey_id: str):
    encuesta = next((m for m in survey_list if m["Unique id"] == survey_id), None)

    if encuesta is None:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    return encuesta

# ✅ Nueva ruta para depurar y ver todas las categorías en la API
@app.get("/survey/category/debug/", tags=["Debug"])
def debug_categories():
    categories = {m.get("category", "SIN CATEGORÍA") for m in survey_list}
    return {"categorias_encontradas": list(categories)}

# ✅ Ruta para buscar encuestas por categoría
@app.get("/survey/category/", tags=["Encuestas"])
def get_survey_by_category(category: str):
    category = category.strip().lower()  # Asegurar que la búsqueda sea correcta

    # Buscar encuestas que contengan la categoría exacta
    results = [m for m in survey_list if "category" in m and category in m["category"]]

    if not results:
        raise HTTPException(status_code=404, detail=f"No se encontraron encuestas en la categoría '{category}'")

    return results

# ✅ Ruta del chatbot
@app.get("/chatbot/", tags=["Chatbot"]) 
def chatbot(query: str):
    try:
        query_words = word_tokenize(query.lower())

        # Buscar sinónimos de cada palabra
        synonyms = {word for q in query_words for word in get_synonyms(q)} | set(query_words)

        # Filtramos las encuestas buscando coincidencias en la categoría
        results = [m for m in survey_list if "category" in m and any(s in m["category"] for s in synonyms)]

        return JSONResponse(content={
            "respuesta": "Aquí tienes algunas encuestas que podrían ayudarte" if results else "No se encontraron encuestas que coincidan con tu búsqueda",
            "encuestas": results
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el chatbot: {str(e)}")
