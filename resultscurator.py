import csv
from utilities.csvhandling import save_to_csv

keywords = ["Technology", "technology", "Future Of Work", "AI", "ai", "Artificial Intelligence", "artificial intelligence", "Artificial intelligence", "artificial intelligence", "Artificial intelligence", "artificial intelligence", "Engineering", "engineering"]
curated_categories = []
curated_categories_csvpath = "/Users/goobinu/Documents/CSE573/curatedcategories.csv"
with open('results.csv', newline='') as f:
    reader = csv.reader(f)
    print("\nPRINTING CSV ROW BY ROW ...\n")
    for row in reader:
        category = row[0]
        link = row[1]
        print("category", category)
        print("row:", row)
        print(" ")
        if any(item in (category or link) for item in keywords):
            curated_categories.append((category, link))

print("PRINTING CURATED RESULTS ...\n")
for item in curated_categories:
    print(item)
    print(" ")

print("Initiating results save ...\n")
save_to_csv(curated_categories_csvpath, curated_categories)

        