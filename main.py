from bs4 import BeautifulSoup
import requests
import re
import os
import csv

def get_all_category_url(main_page_url):
    full_category_url = []
    # Get the HTML from the main_url site
    response = requests.get(main_page_url)
    # Start the soup
    main_page_soup = BeautifulSoup(response.text, "html.parser")
    # Find all the categories and appending the href content in a list
    categories = main_page_soup.find("ul", class_="nav nav-list").find_next("ul").find_all("a")
    href_list = [link['href'] for link in categories]
    # Transforming all the relative urls obtained above into full paths
    i = 0
    while i < len(href_list):
        full_category_url.append("https://books.toscrape.com/" + href_list[i])
        i += 1
    return full_category_url


# Function that looks for products in a given page and appends the urls into a list.
# The function can be called over to scan several pages without as it does not reset
def find_product_urls(page_with_products):
    temp_url_list = []
    products_url_list = []

    # Scraps all URLs that lead to products
    for titre in page_with_products.find_all("a", {"href": True, "title": True}):
        temp_url_list.append((titre['href']).encode('latin1').decode('UTF-8'))

    # Formats the relative URL into a complete path
    for item in temp_url_list:
        products_url_list.append(item.replace('../../..', 'https://books.toscrape.com/catalogue'))

    return products_url_list


# Appending data to the different lists
# noinspection PyShadowingNames
def scrap_data_from_page(product_page_soup):
    # Creating dictionary to translate writen number ratings into numerical one
    word_to_number = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}

    universal_product_code = "none"
    title = "none"
    price_including_tax = "none"
    price_excluding_tax = "none"
    number_available = "none"
    product_description = "none"
    review_rating = "none"
    image_url = "none"

    # Finding the UPC code which is always in a <td> which has a sibling <th> containing the UPC
    check = product_page_soup.find("th", string="UPC")
    if check is not None:
        check = product_page_soup.find("th", string="UPC").find_next("td").text
        if check is not None:
            universal_product_code = check

    # Finding the title, encoding and decoding is done to fix a problem with special characters
    check = product_page_soup.find("h1").text.encode('latin1').decode('UTF-8')
    if check is not None:
        title = check

    # Same as with UPC, but we only need the numerical value, so we filter out the first 2 characters
    check = product_page_soup.find("th", string="Price (incl. tax)")
    if check is not None:
        check = product_page_soup.find("th", string="Price (incl. tax)").find_next("td")
        if check is not None:
            check = (product_page_soup.find("th", string="Price (incl. tax)").find_next("td").text[2:])
            if check is float or int:
                price_including_tax = check

    # Same as with price including tax just above
    check = product_page_soup.find("th", string="Price (excl. tax)")
    if check is not None:
        check = product_page_soup.find("th", string="Price (excl. tax)").find_next("td")
        if check is not None:
            check = (product_page_soup.find("th", string="Price (excl. tax)").find_next("td").text[2:])
            if check is float or int:
                price_excluding_tax = check

    # Regular expression used to find a series of numbers to obtain the "currently in stock" value
    check = product_page_soup.find("th", string="Availability")
    if check is not None:
        check = product_page_soup.find("th", string="Availability").find_next("td").text
        if check is not None:
            check = re.search(r'\d+', (product_page_soup.find("th", string="Availability")
                                       .find_next("td").text)).group()
            if check is int:
                number_available = (int(re.search(r'\d+', (product_page_soup.find("th", string="Availability")
                                                           .find_next("td").text)).group()))

    # Checking for the presence of a description, if no description present, print "No Description"
    check = product_page_soup.find("div", id="product_description")
    if check is not None:
        check = product_page_soup.find("div", id="product_description").find_next("p").text.encode('latin1').decode('UTF-8')
        if check is not None:
            product_description = check

    # Find the rating and translating it into numerical value
    check = product_page_soup.find("p", class_=re.compile(r'^star-rating '))
    if check is not None:
        review_rating = word_to_number.get((product_page_soup.find("p", class_=re.compile(r'^star-rating '))
                                            .get('class'))[1])

    # the alt content matches the book title, we get the title and extract the href
    check = product_page_soup.find("img", alt=product_page_soup.find("h1").text)
    if check is not None:
        image_url = ((product_page_soup.find("img", alt=product_page_soup.find("h1").text).get('src'))
                     .replace('../../', 'https://books.toscrape.com/'))


    return (universal_product_code, title, price_including_tax, price_excluding_tax, number_available,
            product_description, review_rating, image_url)


# Input a soup parsed category URL
# Checks if a "next" button is present on the page if so scraps current page for product urls and
# adds the next page and runs again,
# if no "next" button is present scraps the current page and moves on.
# Output all product urls of the category in a list
# noinspection PyShadowingNames
def get_all_product_url_in_category(category_page_soup, complete_category_url):
    # Creating the empty list for storing the full urls of products
    all_products_url_list = []
    while (category_page_soup.find("a", string="next")) is not None:
        # Adding the newly found urls into the all products url list
        all_products_url_list.extend(find_product_urls(category_page_soup))

        # Obtaining the href for the next page in the category
        next_page = category_page_soup.find("a", string="next").get('href')

        # Removes the text after the last "/" in the url to replace it with the href of the next page of the category
        url_last_slash = complete_category_url.rfind("/")
        next_page = (complete_category_url[:url_last_slash + 1] + next_page)

        response = requests.get(next_page)

        category_page_soup = BeautifulSoup(response.text, "html.parser")
    else:
        # Adding the newly found urls into the all products url list
        all_products_url_list.extend(find_product_urls(category_page_soup))

    return all_products_url_list


# ------------------------------------------------------- Start -------------------------------------------------------

# Creating a list for the headers used during the creation of csv files
header = ["product_page_url", "universal_product_code", "title", "price_including_tax", "price_excluding_tax",
          "number_available", "product_description", "category", "review_rating", "image_url"]

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

# Obtaining the list of categories' urls from the main page
all_category_url = get_all_category_url("https://books.toscrape.com/index.html")

# Main loop
i = 0
while i < len(all_category_url):
    # Taking the active category url to later import for scanning
    url = all_category_url[i]
    # Getting the html of the current category page
    response = requests.get(url)
    # Parsing the html with BeautifulSoup
    category_page_soup = BeautifulSoup(response.text, "html.parser")

    # Saving the current category to display it in the progress indicator and the csv name
    category_title = category_page_soup.find("div", class_="page-header action").find_next("h1").get_text()

    # Progress indicator
    print("Scanning category ", i + 1, " out of ", len(all_category_url), " - ", category_title)

    # Calling the recursive scan function to find all products contained in the current category
    all_products_url = get_all_product_url_in_category(category_page_soup, all_category_url[i])

    # Uses the previously obtained list of product's urls to scrap their information and append the information into
    # the different lists
    a = 0
    while a != len(all_products_url):
        # Get the HTML for the pages to scrap in this iteration from the all_products_url
        response = requests.get(all_products_url[a])
        # Start the soup
        product_page_soup = BeautifulSoup(response.text, "html.parser")

        # Unpacking values from the scrap_data_from_page function
        (universal_product_code_data, title_data, price_including_tax_data, price_excluding_tax_data,
         number_available_data, product_description_data, review_rating_data,
         image_url_data) = scrap_data_from_page(product_page_soup)

        # Appending all data to the lists
        product_page_url.append(all_products_url[a])
        universal_product_code.append(universal_product_code_data)
        title.append(title_data)
        price_including_tax.append(price_including_tax_data)
        price_excluding_tax.append(price_excluding_tax_data)
        number_available.append(number_available_data)
        product_description.append(product_description_data)
        category.append(category_title)
        review_rating.append(review_rating_data)
        image_url.append(image_url_data)

        # Progress indicator
        print("Scrapped : ", a + 1, " / ", len(all_products_url), " pages - ", title[a])

        a += 1

    # Loop for downloading all images in the "images" folder
    a = 0
    while a < len(all_products_url):
        response = requests.get(image_url[a])

        # Writing the .jpg file, replacing "/" by "-" to prevent conflicts with the writing path
        if os.path.exists("output/images/" + title[a].replace("/", "-") + ".jpg"):
            with open("output/images/" + title[a].replace("/", "-") + "(1).jpg", "wb") as file:
                file.write(response.content)
        else:
            with open("output/images/" + title[a].replace("/", "-") + ".jpg", "wb") as file:
                file.write(response.content)

        # Progress indicator
        print("Downloading images: ", a + 1, " out of ", len(all_products_url), " - ", title[a])

        a += 1

    # Creating the csv file named after the books' category
    with open("output/" + category_title + ".csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(zip(product_page_url, universal_product_code, title, price_including_tax, price_excluding_tax,
                             number_available, product_description, category, review_rating, image_url))

    # Resetting all the lists
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
