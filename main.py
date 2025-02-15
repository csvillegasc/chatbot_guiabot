"""

"""

#importa la clase FastAPI de la librería fastapi
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import pandas as pd
import nltk 
from nltk.tokenize import word_tokenize 
from nltk.corpus import wordnet 


#indicamos donde nltk buscará los datos
nltk.data.path.append("C:/Users/admin_bizagi06/AppData/Local/Programs/Python/Python312/Scripts/nltk_data")

nltk.download('punkt') #paqueta para dividir el texto en palabras
nltk.download('wordnet') #paqueta para buscar sinónimos en ingles

#Cargar el archivo de datos
def load_data():
    df= pd.read_csv("Dataset/Customer_support_data.csv") #df = pd.read_csv("Dataset/Customer_support_data.csv")

    return df.fillna('').to_dict('records')

survey_list = load_data()

#funcion para encontrar sinonimos de una palabra
def get_synonyms(word):
    synonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.append(lemma.name())
    return synonyms
    
    
#creamos la aplicacion

app = FastAPI(title="GuIAbot, tú asistente virtual", description = "Este es un chatbot que te ayudará a resolver tus dudas sobre las encuestas de servicio al cliente", version = "1.0.0")
              
#Ruta de inicio
@app.get('/', tags=["Home"])
def home():
    #Cuando entremos en el navegador a http://127.0.0.1:8000/ veremos el mensaje de bienvenida
    return HTMLResponse(content="<h1> Bienvenido a GuIAbot </h1>")

@app.get('/survey/', tags=["Encuestas"])
def get_survey():
    return survey_list or HTTPException(status_code=500, detail="No se encontraron encuestas")
#ruta para obtener una encuesta por su id
@app.get('/survey/{survey_id}', tags=["Encuestas"])
def get_survey(id: str):
    return next(m for m in survey_list if m['Unique id'] == id) or HTTPException(status_code=404, detail="Encuesta no encontrada")

#ruta del chatbot
@app.get('/chatbot/', tags=["Chatbot"]) 
def chatbot(query: str):
    #Dividir la consulta en palabras
    query_words = word_tokenize(query.lower())
    
    #Buscar sinónimos de cada palabra
    synonyms = {word for q in query_words for word in get_synonyms(q)}|set (query_words)
    
    #filtramos las encuestas buscando coincidencias en la categoría
    results = [m for m in survey_list if any (s in m['category'].lower() for s in synonyms)] 
    
    return JSONResponse (content={
        "respuesta": "Aquí tienes algunas encuestas que podrían ayudarte" if results else "No se encontraron encuestas que coincidan con tu búsqueda",
        "encuestas": results
    })
    
    #ruta para buscar encuestas por categoría específica
    @app.get('/survey/', tags=["Encuestas"])
    def get_survey_by_category(category: str):
        #filtramos las encuestas segun la categoría
        return [m for m in survey_list if category.lower() in m['category'].lower()] or HTTPException(status_code=404, detail="No se encontraron encuestas en esa categoría")



""""""""""
app = FastAPI() #Crea un objeto de la clase FastAPI
app.title = "Soporte DS4B" #Define el título de la aplicación
@app.get('/', tags=["Bienvenido"]) #Define la ruta 

def message(): #Define una función de la ruta
    return {"message": "Bienvenido al chatbot de DS4B"} #Retorna un mensaje en formato JSON
"""
