from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import os

# Skapa en FastAPI-applikation
app = FastAPI()

# Filnamn för JSON-filer som lagrar recept och recensioner
DATA_FILE = "data.json"
REVIEWS_FILE = "reviews.json"

# Modell för recept utan recensioner och betyg
class Recipe(BaseModel):
    title: str = Field(..., min_length=1)  # Receptets namn (minst 1 tecken)
    ingredients: List[str] = Field(..., min_items=1)  # Lista över ingredienser (minst 1 ingrediens)
    steps: List[str] = Field(..., min_items=1)  # Lista över steg (minst 1 steg)
    category: str  # Receptkategori, t.ex. "breakfast", "lunch", etc.

# Modell för recept som inkluderar ett unikt ID
class RecipewithID(Recipe):
    id: int  # Unikt ID för receptet

# Modell för recension och betyg
class ReviewRating(BaseModel):
    recipe_id: int  # ID för receptet som recensionen tillhör
    rating: float = Field(..., ge=0, le=5)  # Betyg mellan 0 och 5
    reviews: Optional[List[str]] = []  # Lista över recensioner (valfri)

# Funktion för att läsa data från en JSON-fil
def read_data(filename):
    # Om filen inte finns, returnera tom struktur beroende på filnamn
    if not os.path.exists(filename):
        return [] if filename == REVIEWS_FILE else {"recipes": [], "last_id": 0}
    with open(filename, "r") as file:
        return json.load(file)  # Läs in data från JSON-filen

# Funktion för att skriva data till en JSON-fil
def write_data(data, filename):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)  # Skriv data till JSON-fil med indragning

# Endpoint för att lägga till ett nytt recept
@app.post("/recipes/", response_model=RecipewithID, status_code=201)
def add_recipe(recipe: Recipe):
    data = read_data(DATA_FILE)  # Läs in receptdata
    reviews_data = read_data(REVIEWS_FILE)  # Läs in recensiondata

    # Öka senaste ID:t och tilldela ett nytt ID till det nya receptet
    last_id = data["last_id"]
    new_id = last_id + 1

    # Lägg till nytt recept
    new_recipe = recipe.model_dump()  # Konvertera receptet till ordbok
    new_recipe["id"] = new_id  # Tilldela nytt ID
    data["recipes"].append(new_recipe)  # Lägg till recept i listan
    data["last_id"] = new_id  # Uppdatera senaste ID
    write_data(data, DATA_FILE)  # Spara uppdaterad data

    # Initiera recensioner och betyg för det nya receptet
    reviews_data.append({"recipe_id": new_id, "rating": 0, "reviews": []})
    write_data(reviews_data, REVIEWS_FILE)  # Spara uppdaterad recensiondata

    return new_recipe  # Returnera det nya receptet med ID

# Endpoint för att hämta alla recept eller filtrera efter ingrediens/kategori
@app.get("/recipes/", response_model=List[RecipewithID])
def get_recipes(ingredient: Optional[str] = None, category: Optional[str] = None):
    data = read_data(DATA_FILE)  # Läs in receptdata
    recipes = data["recipes"]

    # Filtrera recept baserat på ingrediens och kategori
    filtered_recipes = [
        recipe for recipe in recipes
        if (any(ingredient.lower() in ing.lower() for ing in recipe["ingredients"]) if ingredient else True) and
           (recipe["category"].lower() == category.lower() if category else True)
    ]

    if not filtered_recipes:  # Om inga recept hittas, returnera ett fel
        raise HTTPException(status_code=404, detail="No recipes found matching the criteria.")
    return filtered_recipes  # Returnera filtrerade recept

# Endpoint för att hämta recensioner och betyg för ett specifikt recept
@app.get("/recipes/{recipe_id}/reviews", response_model=ReviewRating)
def get_reviews(recipe_id: int):
    reviews_data = read_data(REVIEWS_FILE)  # Läs in recensiondata
    for item in reviews_data:
        if item["recipe_id"] == recipe_id:  # Om rätt ID hittas, returnera recensioner och betyg
            return item
    raise HTTPException(status_code=404, detail="Reviews not found for this recipe")  # Returnera fel om recensionen inte hittas

# Endpoint för att uppdatera en recension och betyg
@app.put("/recipes/{recipe_id}/reviews", response_model=ReviewRating)
def update_reviews(recipe_id: int, review_rating: ReviewRating):
    reviews_data = read_data(REVIEWS_FILE)  # Läs in recensiondata
    for item in reviews_data:
        if item["recipe_id"] == recipe_id:  # Om rätt recept hittas
            item.update(review_rating.model_dump())  # Uppdatera recension och betyg
            write_data(reviews_data, REVIEWS_FILE)  # Spara uppdaterad data
            return item
    raise HTTPException(status_code=404, detail="Recipe not found for updating reviews")  # Fel om receptet inte hittas

# Endpoint för att ta bort ett recept baserat på ID
@app.delete("/recipes/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: int):
    data = read_data(DATA_FILE)  # Läs in receptdata
    reviews_data = read_data(REVIEWS_FILE)  # Läs in recensiondata

    # Kontrollera om receptet finns
    recipe_exists = any(recipe["id"] == recipe_id for recipe in data["recipes"])
    if not recipe_exists:
        raise HTTPException(status_code=404, detail="Recipe not found")  # Returnera fel om receptet inte hittas

    # Ta bort receptet från data
    data["recipes"] = [recipe for recipe in data["recipes"] if recipe["id"] != recipe_id]
    write_data(data, DATA_FILE)  # Spara uppdaterad data

    # Ta bort recensioner kopplade till receptet
    reviews_data = [review for review in reviews_data if review["recipe_id"] != recipe_id]
    write_data(reviews_data, REVIEWS_FILE)  # Spara uppdaterad recensiondata

    return {"message": "Recipe and associated reviews deleted successfully"}  # Bekräftelsemeddelande

# Global felhanterare för oväntade undantag
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."}  # Returnera ett standardfelmeddelande
    )
