import requests
from bs4 import BeautifulSoup
import json

url = 'https://www.fiverr.com/categories'
headers = {
    "User-Agent": "Mozilla/5.0"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

result = {}

sections = soup.select('section.mp-categories-columns')

for section in sections:
    ul = section.find('ul')
    if not ul:
        continue

    lis = ul.find_all('li')
    current_category = None
    current_subcategory = None

    for li in lis:
        a_tag = li.find('a')
        if not a_tag:
            continue

        text = a_tag.get_text(strip=True)

        # Main category (h5 inside li)
        if li.find('h5'):
            current_category = text
            result[current_category] = {}
            current_subcategory = None

        # Nested subcategory
        elif 'nested-subcategory' in li.get('class', []):
            if current_category and current_subcategory:
                clean_nested = text.lstrip('-').strip()
                result[current_category][current_subcategory].append(clean_nested)

        # Subcategory
        else:
            current_subcategory = text
            if current_category:
                result[current_category][current_subcategory] = []

# Save output
with open('fiverr_categories.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("✅ Fiverr categories and subcategories saved to fiverr_categories.json")
