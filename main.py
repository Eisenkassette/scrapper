from bs4 import BeautifulSoup
import requests
import re
import os
import csv


# Finds all product URLs and formats them
def find_append_urls():
    # To prevent duplication a temp variable is created
    temp_url_list = []
    # Scraps all URLs that lead to products
    for titre in soup.find_all("a", {"href": True, "title": True}):
        temp_url_list.append((titre['href']).encode('latin1').decode('UTF-8'))

    # Formats the relative URL into a complete path
    for item in temp_url_list:
        full_url_list.append(item.replace('../../..', 'https://books.toscrape.com/catalogue'))


def append_data():
    # ------------------------------------- Appending data to the different lists -------------------------------------
    product_page_url.append(full_url_list[a])

    # The UPC code is always in a <td> which has a sibling <th> containing UPC
    check = soup.find("th", string="UPC").find_next("td").text
    if check is not None:
        universal_product_code.append(check)
    else:
        universal_product_code.append("UPC Not Found")

    # Encoding and decoding is done to fix a problem with special characters
    check = soup.find("h1").text.encode('latin1').decode('UTF-8')
    if check is not None:
        title.append(check)
    else:
        title.append("Title Not Found")

    # Same as with UPC, but we only need the numerical value, so we filter out the first 2 characters
    price_including_tax.append(float(soup.find("th", string="Price (incl. tax)").find_next("td").text[2:]))

    # Same as with price including tax just above
    price_excluding_tax.append(float(soup.find("th", string="Price (excl. tax)").find_next("td").text[2:]))

    # Regular expression used to find a series of numbers to obtain the "currently in stock" value
    number_available.append(int(re.search(r'\d+', (soup.find("th", string="Availability")
                                                   .find_next("td").text)).group()))

    # Checking for the presence of a description, if no description present, print "No Description"
    check = soup.find("div", id="product_description")
    if check is not None:
        check = soup.find("div", id="product_description").find_next("p").text.encode('latin1').decode('UTF-8')
        product_description.append(check)
    else:
        product_description.append("No Description Found")

    category.append(soup.find("ul", class_="breadcrumb").find("li").find_next("li").find_next("li").text.strip())

    review_rating.append(word_to_number.get
                         ((soup.find("p", class_=re.compile(r'^star-rating ')).get('class'))[1]))

    # the alt content matches the book title, we get the title and extract the href
    image_url.append((soup.find("img", alt=soup.find("h1").text).get('src'))
                     .replace('../../', 'https://books.toscrape.com'))


main_url = "https://books.toscrape.com/index.html"
product_url_list = []
full_url_list = []
full_category_url = []

category_name = []

header = ["product_page_url", "universal_product_code", "title", "price_including_tax", "price_excluding_tax",
          "number_available", "product_description", "category", "review_rating", "image_url"]

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

os.makedirs("output", exist_ok=True)

# Get the HTML from the main_url site
response = requests.get(main_url)

# Start the soup
soup = BeautifulSoup(response.text, "html.parser")

# Find all the categories and appending the href content in a list
categories = soup.find("ul", class_="nav nav-list").find_next("ul").find_all("a")
href_list = [link['href'] for link in categories]

# Transforming the relative URL into full paths
i = 0
while i < len(href_list):
    full_category_url.append("https://books.toscrape.com/" + href_list[i])
    i += 1

i = 0
while i < len(full_category_url):
    print("Scanning category ", i + 1, " out of ", len(full_category_url))
    url = full_category_url[i]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    # Checks if a "next" button is present on the page if so scraps the page and adds the next page and runs again,
    # if no "next" button is present scraps the page and moves on.
    while (soup.find("a", string="next")) is not None:
        find_append_urls()
        next_page = soup.find("a", string="next").get('href')
        url_last_slash = full_category_url[i].rfind("/")
        next_page = (full_category_url[i][:url_last_slash + 1] + next_page)
        response = requests.get(next_page)
        soup = BeautifulSoup(response.text, "html.parser")
    else:
        find_append_urls()

    a = 0
    while a != len(full_url_list):
        # Get the HTML for the page to scrap in this iteration from the full_url_list
        page_response = requests.get(full_url_list[a])

        # Start the soup
        soup = BeautifulSoup(page_response.text, "html.parser")

        # Call data finding and appending function
        append_data()

        # Progress indicator
        print("Scrapped : ", a + 1, " / ", len(full_url_list), " pages")

        a += 1

    response = requests.get(full_category_url[i])
    soup = BeautifulSoup(response.text, "html.parser")
    category_title = soup.find("div", class_="page-header action").find_next("h1").get_text()

    with open("output/" + category_title + ".csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(zip(product_page_url, universal_product_code, title, price_including_tax, price_excluding_tax,
                             number_available, product_description, category, review_rating, image_url))

    full_url_list = []

    i += 1

print("Done")
