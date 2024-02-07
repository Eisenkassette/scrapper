from bs4 import BeautifulSoup
import requests
import re

main_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"

# Get the HTML from the main_url site
response = requests.get(main_url)

# Start the soup
soup = BeautifulSoup(response.text, "html.parser")

# Scraps all URLs that lead to products
product_url_list = []
for titre in soup.find_all("a", {"href": True, "title": True}, ):
    product_url_list.append((titre['href']).encode('latin1').decode('UTF-8'))

# Formats the abstract URLs into usable ones
modified_list = []
for item in product_url_list:
    modified_list.append(item.replace('../../..', 'https://books.toscrape.com/catalogue'))

# ---------------------------- SCRAPPING LOOP ----------------------------
# Creating dictionary to translate writen number ratings into numerical later on
word_to_number = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}

product_page_url = []
universal_product_code = []
title = []
price_including_tax = []
price_excluding_tax = []
number_available = []
product_description = []
category = []
review_rating = []
image_url = []

i = 0

while i < len(modified_list):

    page_response = requests.get(modified_list[i])

    soup = BeautifulSoup(page_response.text, "html.parser")

    product_page_url.append(modified_list[i])
    universal_product_code.append(soup.find("th", string="UPC").find_next("td").text)
    title.append(soup.find("h1").text)
    price_including_tax.append(float(soup.find("th", string="Price (incl. tax)").find_next("td").text[2:]))
    price_excluding_tax.append(float(soup.find("th", string="Price (excl. tax)").find_next("td").text[2:]))
    number_available.append(int(re.search(r'\d+', (soup.find("th", string="Availability")
                                                   .find_next("td").text)).group()))
    product_description.append(soup.find("div", id="product_description").find_next("p").text
                               .encode('latin1').decode('UTF-8'))
    category.append(soup.find("ul", class_="breadcrumb").find("li").find_next("li").find_next("li").text.strip())
    review_rating.append(word_to_number.get
                         ((soup.find("p", class_=re.compile(r'^star-rating ')).get('class'))[1]))
    image_url.append(soup.find("img", alt=(title[i])).get('src'))

    i += 1

print(universal_product_code)
print(title)
print(price_including_tax)
print(price_excluding_tax)
print(number_available)
print(product_description)
print(category)
print(review_rating)
print(image_url)
