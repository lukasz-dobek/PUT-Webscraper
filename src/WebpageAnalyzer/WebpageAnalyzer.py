import requests
import bs4
import urllib.request
from pprint import pprint
import time
from urllib.parse import urlparse
import os
import re

class WebpageAnalyzer:
    def __init__(self):
        pass

    def get_webpage_source(self, webpage_url):
        """
        Returns source of given webpage or raises exception if page not accessible
        :param webpage_url: URL to obtain source code from
        :return: string of raw source code, webpage url from response
        """
        response = requests.get(webpage_url)
        if response.status_code == 200:
            u = urlparse(response.url)
            link = u.scheme + "://" + u.netloc
            return response.content, link
        else:
            raise Exception(f"Source not obtained, response status code: [{response.status_code}]")

    def get_images(self, webpage_url, location, min_threshold=0, max_threshold=10000000):
        """
        Analyzes given webpage and downloads all images meeting given requirements
        :param webpage_url: URL to the site to download images from
        :param location: location to which images will be saved
        :param min_threshold: minumum image size in bytes
        :param max_threshold: maximum image size in bytes
        :return: number of images downloaded
        """
        webpage_source, webpage_url_from_request = self.get_webpage_source(webpage_url)

        soup = bs4.BeautifulSoup(webpage_source, features="html.parser")

        images = []
        for img in soup.findAll('img'):
            image = img.get('src')
            if image is None:
                image = img.get('data-original')
            if image is not None:
                images.append(image)

        images_for_download = []
        for i in images:
            if i[:4] != "http":
                file_name = webpage_url + i
                file = urllib.request.urlopen(file_name)
                file_size = len(file.read())
                if file_size > min_threshold and file_size<max_threshold:
                    images_for_download.append(file_name)
            else:
                file_name = i
                file = urllib.request.urlopen(file_name)
                file_size = len(file.read())
                if file_size > min_threshold and file_size < max_threshold:
                    images_for_download.append(file_name)

        if not os.path.exists(location):
            os.makedirs(location)

        downloaded = 0
        for i in images_for_download:
            flag = True
            name = i.split('/')[-1]
            if name.__contains__('?'):
                name = name.replace('?', '')
            regexa = name
            regexa = regexa.replace('.', '\.')
            regexa = re.compile(".*" + regexa)
            for pom in os.listdir(location):
                if (regexa.match(pom)):
                    flag = False
            if (flag == True):
                downloaded+=1
                urllib.request.urlretrieve(i, location + str(time.time()) + "_" + name)

        return downloaded

    def scrap_multiple_images(self, websites_list, file_location=None,min_threshold=0, max_threshold=10000000):
        """
        Analyzes given webpages and returns list of tuples with links and descriptions found,
        optionally saves obtained data to the file
        :param websites_list: list of webpages to scrap
        :param file_location: optional location to which file with, None can be passed
        :return: List of tuples {url : description of link}
        """
        downloaded = 0
        for site in websites_list:
            print("Scraping:", site)
            urls = self.get_images(site, file_location,min_threshold,max_threshold)
            downloaded += urls
        return downloaded


    def get_urls_with_description(self, webpage_url, file_location=None):
        """
        Analyzes given webpage and returns list of tuples with links and descriptions found,
        optionally saves obtained data to the file
        :param webpage_url: URL to the webpage to process
        :param file_location: optional location to which file with, None can be passed
        :return: list of tuples {url : description of link}
        """

        webpage_source, webpage_url_from_request = self.get_webpage_source(webpage_url)

        soup = bs4.BeautifulSoup(webpage_source, features="html.parser")
        output_tuple_list = []
        for a in soup.find_all('a', href=True):
            if a['href'][:4] != "http":
                # if url does not start with a word "http" add webpage address to the beginning
                result_tuple = (webpage_url_from_request + a['href'], a.contents)
            else:
                result_tuple = (a['href'], a.contents)
            output_tuple_list.append(result_tuple)

        downloaded=0

        if file_location:
            # save results in the file
            flag = True
            file = open(file_location, 'a+',encoding='utf-8')
            if (os.stat(file_location).st_size != 0):
                with open(file_location, encoding='utf-8') as f:
                    lines = f.readlines()
                for item in output_tuple_list:
                    for line in lines:
                        regex = line.split('\t')[0]
                        if item[0] == regex:
                            flag=False
                    if flag == True:
                        downloaded+=1
                        file.write(item[0] + "\t" + str(item[1]) + "\n")
            else:
                for item in output_tuple_list:
                    downloaded+=1
                    file.write(item[0] + "\t" + str(item[1]) + "\n")
        return output_tuple_list, downloaded

    def scrap_multiple_websites(self, websites_list, file_location=None):
        """
        Analyzes given webpages and returns list of tuples with links and descriptions found,
        optionally saves obtained data to the file
        :param websites_list: list of webpages to scrap
        :param file_location: optional location to which file with, None can be passed
        :return: List of tuples {url : description of link}
        """
        output_tuple_list = []
        result=0
        for site in websites_list:
            print("Scraping:", site)
            urls, number = self.get_urls_with_description(site, file_location)
            output_tuple_list += urls
            result+=number
        return output_tuple_list, result

    def scrap_subpages(self, depth, website, file_location=None):
        output = dict()
        output[website] = 0
        for _ in range(depth):
            for key, value in output.copy().items():
                if value == 0:
                    try:
                        subpages, _ = self.get_urls_with_description(key, file_location)
                        for subpage in subpages:
                            if subpage[0] not in output.keys():
                                output[subpage[0]] = 0
                                print(".", end='')
                    except Exception as e:
                        print("e")
                output[key] = value + 1
        from pprint import pprint
        pprint(output)
        return output


if __name__ == "__main__":
    anal = WebpageAnalyzer()
    #
    # websites_list = ["http://www.pyszne.pl", "http://fee.put.poznan.pl/index.php/en/", "http://wykop.pl"]
    #
    # #images = anal.get_images("http://wykop.pl", "images/",10000,100000)
    # urls,ilosc = anal.scrap_multiple_websites(websites_list, "file.txt")
    #
    # print(ilosc)

    print(anal.scrap_subpages(1, "http://info.cern.ch/"))

    #anal.get_urls_with_description("http://www.pyszne.pl")
