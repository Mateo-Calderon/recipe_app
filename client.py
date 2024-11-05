import pyinputplus as pyip
import requests

# Bas-URL för API:et som hanterar recept och recensioner
BASE_URL = "http://127.0.0.1:8000/recipes/"

# Funktion för att lägga till ett nytt recept
def add_recipe():
    '''
    Denna funktion samlar in information om ett nytt recept från användaren, 
    så som titel, ingredienser, tillagningssteg och kategori. 
    Den skickar sedan en POST-förfrågan till API för att lägga till 
    det nya receptet och skriver ut ett bekräftelsemeddelande om 
    receptet har lagts till.
    '''
    print("\n--- Add a New Recipe ---")
    # Skapa ett recept genom att samla in data från användaren
    recipe = {
        "title": pyip.inputStr("Enter Recipe Title: "),  # Receptets titel
        "ingredients": pyip.inputStr("Enter Ingredients (comma-separated): ").split(","),  # Ingredienser, separerade med kommatecken
        "steps": pyip.inputStr("Enter Steps (comma-separated): ").split(","),  # Tillagningssteg, separerade med kommatecken
        "category": pyip.inputMenu(["breakfast", "lunch", "dinner", "dessert"], prompt="Choose a Category:\n", numbered=True)  # Välj kategori från en lista
    }
    try:
        # Skicka POST-förfrågan för att lägga till receptet
        response = requests.post(BASE_URL, json=recipe)
        response.raise_for_status()
        print("Recipe added successfully!", response.json())  # Bekräfta att receptet har lagts till
    except requests.exceptions.HTTPError as e:
        print("Error adding recipe:", e)  # Hantera eventuella fel

# Funktion för att lägga till en recension och betyg för ett recept
def add_review(recipe_id):
    '''
    Denna funktion tar in ett recept-ID och samlar in ett betyg och en recension 
    från användaren. Den hämtar befintliga recensioner för receptet och uppdaterar 
    sedan recensionerna och betyget med den nya informationen. Funktionen skickar en 
    PUT-förfrågan för att spara ändringarna och bekräftar om recensionen har lagts till 
    framgångsrikt.
    '''
    print("\n--- Add a Review ---")
    # Samla in betyg och recension från användaren
    rating = pyip.inputFloat("Enter Rating (0-5): ", min=0, max=5)  # Betyg mellan 0 och 5
    review = pyip.inputStr("Enter Review: ")  # Användarens recensionstext

    try:
        # Hämta befintliga recensioner för receptet
        response = requests.get(f"{BASE_URL}{recipe_id}/reviews")
        response.raise_for_status()
        reviews_data = response.json()
        # Uppdatera betyget och lägg till ny recension
        reviews_data["rating"] = rating
        reviews_data["reviews"].append(review)

        # Skicka PUT-förfrågan för att uppdatera recensionerna
        response = requests.put(f"{BASE_URL}{recipe_id}/reviews", json=reviews_data)
        response.raise_for_status()
        print("Review added successfully!", response.json())  # Bekräftelsemeddelande
    except requests.exceptions.HTTPError as e:
        print("Error adding review:", e)  # Hantera eventuella fel

# Funktion för att söka efter recept baserat på ingrediens och kategori
def search_recipes():
    '''
    Denna funktion låter användaren söka efter recept baserat på en specifik 
    ingrediens och/eller kategori. Den skickar en GET-förfrågan med sökparametrarna 
    till API och returnerar en lista över matchande recept. Funktionen hämtar även 
    recensioner och betyg för varje recept i resultatet och skriver ut detaljerna för 
    användaren.
    '''
    print("\n--- Search for Recipes ---")
    # Samla in sökparameter för ingrediens
    ingredient = pyip.inputStr("Enter Ingredient to Search for (press Enter to skip): ", blank=True)
    # Välj kategori från en meny, med möjlighet att hoppa över
    category = pyip.inputMenu(["breakfast", "lunch", "dinner", "dessert", ""], prompt="Choose a Category (or press Enter to skip):\n", numbered=True)

    # Skapa sökparametrar
    params = {}
    if ingredient:
        params["ingredient"] = ingredient
    if category:
        params["category"] = category

    try:
        # Skicka GET-förfrågan med sökparametrar
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        recipes = response.json()  # Få sökresultaten

        if recipes:
            print("\nFound Recipes:")
            # Gå igenom och skriv ut detaljer för varje recept
            for recipe in recipes:
                print(f"\n- {recipe['title']} (ID: {recipe['id']})")
                print(f"  Category: {recipe['category']}")
                print(f"  Ingredients: {', '.join(recipe['ingredients'])}")
                print(f"  Steps: {', '.join(recipe['steps'])}")
                
                # Hämta och skriv ut recensioner och betyg för varje recept
                try:
                    review_response = requests.get(f"{BASE_URL}{recipe['id']}/reviews")
                    review_response.raise_for_status()
                    review_data = review_response.json()
                    
                    # Skriv ut betyg och recensioner
                    print(f"  Rating: {review_data['rating']}")
                    if review_data["reviews"]:
                        print("  Reviews:")
                        for review in review_data["reviews"]:
                            print(f"    - {review}")
                    else:
                        print("  No reviews yet.")
                except requests.exceptions.HTTPError:
                    print("  Error retrieving reviews and rating.")
                    
    except requests.exceptions.HTTPError as e:
        print("Error retrieving recipes:", e)  # Hantera eventuella fel

# Funktion för att ta bort ett recept baserat på ID
def delete_recipe():
    '''
    Denna funktion låter användaren ange ett recept-ID för att radera receptet 
    från systemet. Funktionen skickar en DELETE-förfrågan till API för att ta bort 
    det angivna receptet och bekräftar borttagningen genom att skriva ut ett meddelande.
    '''
    print("\n--- Delete a Recipe ---")
    recipe_id = pyip.inputInt("Enter Recipe ID to delete: ")  # Samla in recept-ID

    try:
        # Skicka DELETE-förfrågan för att radera receptet
        response = requests.delete(f"{BASE_URL}{recipe_id}")
        response.raise_for_status()
        print("Recipe deleted successfully!")  # Bekräftelse om receptet har raderats
    except requests.exceptions.HTTPError as e:
        print("Error deleting recipe:", e)  # Hantera eventuella fel

# Menyfunktion för att navigera mellan olika alternativ
def menu():
    '''
    Menyfunktionen presenterar en lista med alternativ för användaren, som att 
    lägga till ett recept, lägga till en recension, söka efter recept, radera ett recept, 
    eller avsluta programmet. Baserat på användarens val anropar funktionen motsvarande 
    funktion och hanterar interaktionen med API.
    '''
    while True:
        # Visa meny och låt användaren välja ett alternativ
        choice = pyip.inputMenu(
            ["Add Recipe", "Add Review", "Search Recipes", "Delete Recipe", "Exit"],
            prompt="\n--- Recipe Menu ---\nChoose an option:\n",
            numbered=True
        )

        # Kör respektive funktion baserat på användarens val
        if choice == "Add Recipe":
            add_recipe()
        elif choice == "Add Review":
            recipe_id = pyip.inputInt("Enter Recipe ID to add a review for: ")
            add_review(recipe_id)
        elif choice == "Search Recipes":
            search_recipes()
        elif choice == "Delete Recipe":
            delete_recipe()
        elif choice == "Exit":
            print("Exiting the application.")
            break  # Avsluta programmet om användaren väljer "Exit"

# Startar menyn om skriptet körs direkt
if __name__ == "__main__":
    menu()
