import requests
from .models import Alimento
from django.conf import settings

def obtener_datos_alimentos(query):
    api_key = settings.USDA_API_KEY
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={query}&api_key={api_key}"
    response = requests.get(url)
    data = response.json()

    for item in data['foods']:
        nombre = item['description']
        calorias = item['foodNutrients'][3]['value']
        proteinas = item['foodNutrients'][0]['value']
        carbohidratos = item['foodNutrients'][1]['value']
        grasas = item['foodNutrients'][2]['value']

        Alimento.objects.create(nombre=nombre, calorias=calorias, proteinas=proteinas, carbohidratos=carbohidratos, grasas=grasas)
