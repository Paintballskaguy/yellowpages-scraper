import requests
from lxml import html
import unicodecsv as csv
import argparse

def parse_listing(keyword, place, max_pages=10):
    """
    Function to process Yellow Pages listing pages with pagination
    :param keyword: search query
    :param place: place name
    :param max_pages: maximum number of pages to scrape
    """
    base_url = "https://www.yellowpages.com/search?search_terms={0}&geo_location_terms={1}&page={2}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36'
    }

    scraped_results = []

    for page in range(1, max_pages + 1):
        url = base_url.format(keyword, place, page)
        print("Retrieving page:", page, url)

        try:
            response = requests.get(url, verify=False, headers=headers)
            if response.status_code == 200:
                parser = html.fromstring(response.text)
                # Absolute URL for relative links
                parser.make_links_absolute("https://www.yellowpages.com")

                XPATH_LISTINGS = "//div[@class='search-results organic']//div[@class='v-card']"
                listings = parser.xpath(XPATH_LISTINGS)

                if not listings:
                    print("No more listings found. Exiting.")
                    break

                for results in listings:
                    XPATH_BUSINESS_NAME = ".//a[@class='business-name']//text()"
                    XPATH_BUSSINESS_PAGE = ".//a[@class='business-name']//@href"
                    XPATH_TELEPHONE = ".//div[@class='phones phone primary']//text()"
                    XPATH_ADDRESS = ".//div[@class='info']//div//p[@itemprop='address']"
                    XPATH_STREET = ".//div[@class='street-address']//text()"
                    XPATH_LOCALITY = ".//div[@class='locality']//text()"
                    XPATH_REGION = ".//div[@class='info']//div//p[@itemprop='address']//span[@itemprop='addressRegion']//text()"
                    XPATH_ZIP_CODE = ".//div[@class='info']//div//p[@itemprop='address']//span[@itemprop='postalCode']//text()"
                    XPATH_RANK = ".//div[@class='info']//h2[@class='n']/text()"
                    XPATH_CATEGORIES = ".//div[@class='info']//div[contains(@class,'info-section')]//div[@class='categories']//text()"
                    XPATH_WEBSITE = ".//div[@class='info']//div[contains(@class,'info-section')]//div[@class='links']//a[contains(@class,'website')]/@href"
                    XPATH_RATING = ".//div[@class='info']//div[contains(@class,'info-section')]//div[contains(@class,'result-rating')]//span//text()"

                    raw_business_name = results.xpath(XPATH_BUSINESS_NAME)
                    raw_business_telephone = results.xpath(XPATH_TELEPHONE)
                    raw_business_page = results.xpath(XPATH_BUSSINESS_PAGE)
                    raw_categories = results.xpath(XPATH_CATEGORIES)
                    raw_website = results.xpath(XPATH_WEBSITE)
                    raw_rating = results.xpath(XPATH_RATING)
                    raw_street = results.xpath(XPATH_STREET)
                    raw_locality = results.xpath(XPATH_LOCALITY)
                    raw_region = results.xpath(XPATH_REGION)
                    raw_zip_code = results.xpath(XPATH_ZIP_CODE)
                    raw_rank = results.xpath(XPATH_RANK)

                    business_name = ''.join(raw_business_name).strip() if raw_business_name else None
                    telephone = ''.join(raw_business_telephone).strip() if raw_business_telephone else None
                    business_page = ''.join(raw_business_page).strip() if raw_business_page else None
                    rank = ''.join(raw_rank).replace('.\xa0', '') if raw_rank else None
                    category = ','.join(raw_categories).strip() if raw_categories else None
                    website = ''.join(raw_website).strip() if raw_website else None
                    rating = ''.join(raw_rating).replace("(", "").replace(")", "").strip() if raw_rating else None
                    street = ''.join(raw_street).strip() if raw_street else None
                    locality = ''.join(raw_locality).replace(',\xa0', '').strip() if raw_locality else None
                    locality, locality_parts = locality.split(',')
                    _, region, zipcode = locality_parts.split(' ')

                    business_details = {
                        'business_name': business_name,
                        'telephone': telephone,
                        'business_page': business_page,
                        'rank': rank,
                        'category': category,
                        'website': website,
                        'rating': rating,
                        'street': street,
                        'locality': locality,
                        'region': region,
                        'zipcode': zipcode,
                        'listing_url': response.url
                    }
                    scraped_results.append(business_details)

            else:
                print("Page retrieval failed with status:", response.status_code)
                break  # Exit if page retrieval fails

        except Exception as e:
            print("Error retrieving page:", e)
            break  # Exit loop on error

    return scraped_results

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument('keyword', help='Search Keyword')
    argparser.add_argument('place', help='Place Name')
    argparser.add_argument('--pages', type=int, default=10, help='Max number of pages to scrape')

    args = argparser.parse_args()
    keyword = args.keyword
    place = args.place
    max_pages = args.pages

    scraped_data = parse_listing(keyword, place, max_pages)

    if scraped_data:
        filename = f"{keyword}-{place}-yellowpages-scraped-data.csv"
        print(f"Writing scraped data to {filename}")
        with open(filename, 'wb') as csvfile:
            fieldnames = ['rank', 'business_name', 'telephone', 'business_page', 'category', 'website', 'rating',
                          'street', 'locality', 'region', 'zipcode', 'listing_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for data in scraped_data:
                writer.writerow(data)
