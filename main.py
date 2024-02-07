from bs4 import BeautifulSoup
import requests
import re
import csv

main_url = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"

# Get the HTML from the main_url site
response = requests.get(main_url)

# Start the soup
soup = BeautifulSoup(response.text, "html.parser")

# Scraps all URLs that lead to products
product_url_list = []
for titre in soup.find_all("a", {"href": True, "title": True}, ):
    product_url_list.append((titre['href']).encode('latin1').decode('UTF-8'))

# Formats the relative URL into complete path
full_url_list = []
for item in product_url_list:
    full_url_list.append(item.replace('../../..', 'https://books.toscrape.com/catalogue'))

# ------------------------------------- PRE-LOOP VARIABLES -------------------------------------
# Creating dictionary to translate writen number ratings into numerical one in the loop
word_to_number = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
# All the required data to scrap
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
# Declaring loop iteration variable
i = 0
# ------------------------------------- SCRAPPING LOOP -------------------------------------
# Loops until all i equals the number of URLs contained in full_url_list
while i != len(full_url_list):
    # Get the HTML for the page to scrap in this iteration from the full_url_list
    page_response = requests.get(full_url_list[i])
    # Start the soup
    soup = BeautifulSoup(page_response.text, "html.parser")

    # ------------------------------------- Appending data to the different lists -------------------------------------
    product_page_url.append(full_url_list[i])

    # The UPC code is always in a <td> which has a sibling <th> containing UPC
    universal_product_code.append(soup.find("th", string="UPC").find_next("td").text)

    # Encoding and decoding is done to fix a problem with special characters
    title.append(soup.find("h1").text.encode('latin1').decode('UTF-8'))

    # Same as with UPC, but we only need the numerical value, so we filter out the first 2 characters
    price_including_tax.append(float(soup.find("th", string="Price (incl. tax)").find_next("td").text[2:]))

    # Same as with price including tax just above
    price_excluding_tax.append(float(soup.find("th", string="Price (excl. tax)").find_next("td").text[2:]))

    # Regular expression used to find a series of numbers to obtain the "currently in stock" value
    number_available.append(int(re.search(r'\d+', (soup.find("th", string="Availability")
                                                   .find_next("td").text)).group()))

    product_description.append(soup.find("div", id="product_description").find_next("p").text
                               .encode('latin1').decode('UTF-8'))

    category.append(soup.find("ul", class_="breadcrumb").find("li").find_next("li").find_next("li").text.strip())

    review_rating.append(word_to_number.get
                         ((soup.find("p", class_=re.compile(r'^star-rating ')).get('class'))[1]))

    # the alt content matches the book title, we get the title and extract the href
    image_url.append((soup.find("img", alt=soup.find("h1").text).get('src'))
                     .replace('../../', 'https://books.toscrape.com'))

    # Progress indicator
    print("Scrapped : ", i + 1, " / ", len(full_url_list), " pages")

    i += 1
    # ------------------------------------- LOOP END -------------------------------------

# Scanning done indicator
print("Done ", i, " pages scanned")

# ------------------------------------- CSV CREATION -------------------------------------
# Creating list of headers
header = ["product_page_url", "universal_product_code", "title", "price_including_tax", "price_excluding_tax",
          "number_available", "product_description", "category", "review_rating", "image_url"]

# Creating output.csv and populating it
with open("output.csv", mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(header)
    writer.writerows(zip(product_page_url, universal_product_code, title, price_including_tax, price_excluding_tax,
                         number_available, product_description, category, review_rating, image_url))
