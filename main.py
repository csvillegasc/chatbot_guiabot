from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import nltk
nltk.data.find('tokenizers/punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet


# Cargar NLTK y descargar datos necesarios
nltk.data.path.append("C:/Users/admin_bizagi06/AppData/Local/Programs/Python/Python312/Scripts/nltk_data")
nltk.download("punkt")
nltk.download("wordnet")
nltk.download("punkt_tab")
# Cargar dataset
def load_data():
    df = pd.read_csv("Dataset/Customer_support_data.csv")
    df["category"] = df["category"].astype(str).str.strip().str.lower()
    return df.fillna("").to_dict("records")

survey_list = load_data()

# Función para obtener sinónimos
def get_synonyms(word):
    synonyms = []
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.append(lemma.name())
    return list(set(synonyms))

# Crear la aplicación FastAPI
app = FastAPI()

# Montar la carpeta static para servir imágenes locales
app.mount("/static", StaticFiles(directory="static"), name="static")

# Interfaz HTML del chatbot

html_content = """
 <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GuIAbot - Chatbot de Encuestas</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 20px; display: flex; flex-direction: column; align-items: center; background-color: black; color: white; }
            #header-container { display: flex; justify-content: center; width: 80%; max-width: 1000px; }
            h1 { text-align: center; color: white; }
            #container { display: flex; justify-content: space-between; align-items: center; width: 80%; max-width: 1000px; }
            #chatbox-container { width: 65%; }
            #chatbox { width: 100%; height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; text-align: left; background-color: white; color: black; }
            #userInput { width: 70%; padding: 8px; }
            button { padding: 8px; }
            .user { color: cyan; font-weight: bold; }
            .bot { color: lime; font-weight: bold; }
            .error { color: red; font-weight: bold; }
            #chat-image { width: 200px; height: auto; }
        </style>
    </head>
    <body>
        <div id="header-container">
            <h1>Bienvenido a GuIAbot</h1>
        </div>
        <div id="container">
            <div id="chatbox-container">
                <div id="chatbox"></div>
                <input type="text" id="userInput" placeholder="Escribe tu pregunta aquí...">
                <button onclick="sendMessage()">Enviar</button>
            </div>
            <img id="chat-image" src="/static/chatbot_image.jpg" alt="Chatbot Image">
        </div>
        <script>
            function sendMessage() {
                let input = document.getElementById("userInput").value;
                if (input.trim() === "") return;

                let chatbox = document.getElementById("chatbox");
                chatbox.innerHTML += "<p class='user'>Tú: " + input + "</p>";

                fetch("/chatbot/?query=" + encodeURIComponent(input))
                    .then(response => response.json())
                    .then(data => {
                        if (!data || !data.respuesta) {
                            chatbox.innerHTML += "<p class='error'>Error: Respuesta vacía de la API</p>";
                            return;
                        }

                        chatbox.innerHTML += "<p class='bot'>GuIAbot: " + data.respuesta + "</p>";

                        if (data.encuestas && data.encuestas.length > 0) {
                            data.encuestas.forEach(encuesta => {
                                chatbox.innerHTML += "<p class='bot'>Encuesta ID: " + encuesta["Unique id"] + " (Categoría: " + encuesta.category + ")</p>";
                            });
                        }
                        chatbox.scrollTop = chatbox.scrollHeight;
                    })
                    .catch(error => {
                        chatbox.innerHTML += "<p class='error'>Error al obtener respuesta: " + error.message + "</p>";
                    });
                document.getElementById("userInput").value = "";
            }
        </script>
    </body>
    </html>
    """

# Ruta de inicio con la interfaz del chatbot
@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content=html_content)

# ✅ Ruta para obtener todas las encuestas
@app.get("/survey/", tags=["Encuestas"])
def get_survey():
    if not survey_list:
        raise HTTPException(status_code=500, detail="No se encontraron encuestas")
    return survey_list

# ✅ Ruta para obtener una encuesta por ID
@app.get("/survey/{survey_id}", tags=["Encuestas"])
def get_survey_by_id(survey_id: str):
    encuesta = next((m for m in survey_list if m["Unique id"] == survey_id), None)
    
    if encuesta is None:
        raise HTTPException(status_code=404, detail="Encuesta no encontrada")

    return encuesta

# ✅ Ruta para obtener encuestas por categoría
@app.get("/survey/category/", tags=["Encuestas"])
def get_survey_by_category(category: str):
    category = category.strip().lower()  # Normalizar la búsqueda
    results = [m for m in survey_list if "category" in m and category in m["category"]]

    if not results:
        raise HTTPException(status_code=404, detail=f"No se encontraron encuestas en la categoría '{category}'")

    return results

# ✅ Ruta para el chatbot
@app.get("/chatbot/", tags=["Chatbot"])
def chatbot(query: str = Query(..., title="Consulta del usuario")):
    try:
        print(f"📌 Pregunta recibida: {query}")  # Depuración en la terminal
         # Verifica si la consulta es un ID de encuesta directamente
        encuesta_por_id = next((m for m in survey_list if m["Unique id"] == query.strip()), None)
        if encuesta_por_id:
            return JSONResponse(content={"respuesta": "Aquí está la información de la encuesta:", "encuestas": [encuesta_por_id]})
        
         # Si no es un ID, sigue con la búsqueda normal
        query_words = word_tokenize(query.lower())
       
        synonyms = set(query_words)
        for word in query_words:
            synonyms.update(get_synonyms(word))

        # Filtrar encuestas que coincidan con la consulta
        results = [m for m in survey_list if "category" in m and any(s in m["category"] for s in synonyms)]

        if not results:
            return JSONResponse(content={"respuesta": "No se encontraron encuestas que coincidan con tu búsqueda", "encuestas": []})

        return JSONResponse(content={"respuesta": "Aquí tienes algunas encuestas que podrían ayudarte", "encuestas": results})

    except Exception as e:
        print(f"⚠️ Error en chatbot: {str(e)}")  # Mostrar error en la terminal
        return JSONResponse(content={"error": str(e)}, status_code=500)
