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


# Appending data to the different lists
def append_data():

    # Appending the full url of the product
    product_page_url.append(full_url_list[a])

    # Appending the UPC code which is always in a <td> which has a sibling <th> containing the UPC
    check = soup.find("th", string="UPC")
    if check is not None:
        check = soup.find("th", string="UPC").find_next("td").text
        if check is not None:
            universal_product_code.append(check)
        else:
            universal_product_code.append("UPC Not Found")
    else:
        universal_product_code.append("UPC Not Found")

    # Appending the title, encoding and decoding is done to fix a problem with special characters
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
                     .replace('../../', 'https://books.toscrape.com/'))


# Setting the main page of "books to scrape"
main_url = "https://books.toscrape.com/index.html"
# Creating the empty list for storing the full urls of products
full_url_list = []
# Creating the empty list for storing all full urls of the different categories of the site
full_category_url = []

# Creating a list for the headers used during the creation of csv files
header = ["product_page_url", "universal_product_code", "title", "price_including_tax", "price_excluding_tax",
          "number_available", "product_description", "category", "review_rating", "image_url"]

# Creating dictionary to translate writen number ratings into numerical one
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

# Creating the "output" folder and the "images" folder inside
os.makedirs("output", exist_ok=True)
os.makedirs("output/images", exist_ok=True)

# Get the HTML from the main_url site
response = requests.get(main_url)

# Start the soup
soup = BeautifulSoup(response.text, "html.parser")

# Find all the categories and appending the href content in a list
categories = soup.find("ul", class_="nav nav-list").find_next("ul").find_all("a")

href_list = [link['href'] for link in categories]

# Transforming all the relative urls obtained above into full paths
i = 0
while i < len(href_list):
    full_category_url.append("https://books.toscrape.com/" + href_list[i])
    i += 1

# Scrapping loop
i = 0
while i < len(full_category_url):
    # Taking the active category url to later import for scanning
    url = full_category_url[i]

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    # Note the current category to display it in the progress indicator and the csv name
    category_title = soup.find("div", class_="page-header action").find_next("h1").get_text()

    # Progress indicator
    print("Scanning category ", i + 1, " out of ", len(full_category_url), " - ", category_title)

    # Checks if a "next" button is present on the page if so scraps current page for product urls and
    # adds the next page and runs again,
    # if no "next" button is present scraps the current page and moves on.
    while (soup.find("a", string="next")) is not None:
        find_append_urls()

        next_page = soup.find("a", string="next").get('href')

        # Removes the text after the last "/" in the link to replace it with "page x.html"
        url_last_slash = full_category_url[i].rfind("/")
        next_page = (full_category_url[i][:url_last_slash + 1] + next_page)

        response = requests.get(next_page)

        soup = BeautifulSoup(response.text, "html.parser")
    else:
        find_append_urls()

    # Uses the previously obtained list of product's urls to scrap their information and append the information into
    # the different lists
    a = 0
    while a != len(full_url_list):
        # Get the HTML for the pages to scrap in this iteration from the full_url_list
        page_response = requests.get(full_url_list[a])

        # Start the soup
        soup = BeautifulSoup(page_response.text, "html.parser")

        # Call data finding and appending function
        append_data()

        # Progress indicator
        print("Scrapped : ", a + 1, " / ", len(full_url_list), " pages - ", title[a])

        a += 1

    # Loop for downloading all images in the "images" folder
    a = 0
    while a < len(full_url_list):
        response = requests.get(image_url[a])

        # Writing the .jpg file, replacing "/" by "-" to prevent conflicts with the writing path
        if os.path.exists("output/images/" + title[a].replace("/", "-") + ".jpg"):
            with open("output/images/" + title[a].replace("/", "-") + "1.jpg", "wb") as file:
                file.write(response.content)
        else:
            with open("output/images/" + title[a].replace("/", "-") + ".jpg", "wb") as file:
                file.write(response.content)

        # Progress indicator
        print("Downloading images: ", a+1, " out of ", len(full_url_list), " - ", title[a])

        a += 1

    # Creating the csv file named after the books' category
    with open("output/" + category_title + ".csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(zip(product_page_url, universal_product_code, title, price_including_tax, price_excluding_tax,
                             number_available, product_description, category, review_rating, image_url))

    # Resetting all the lists
    full_url_list = []

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

    i += 1

print("Done")
