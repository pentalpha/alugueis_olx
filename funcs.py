import time
import requests
from bs4 import BeautifulSoup
from threading import Thread
from tqdm import tqdm
from datetime import date 

todays_date = date.today()

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def requestHTMLPage(url, max_tries = 4):
    #print("Retrieving", url)
    hdr = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=hdr)
    tries = 1
    while r.status_code != 200:
        if tries >= max_tries:
            break
        time.sleep(10)
        print("return status from", url, "is", r.status_code)
        r = requests.get(url)
        print("loop em potencial ("+str(tries)+") - " + url)
        tries += 1
    if r.status_code == 200:
        return r.content
    else:
        return None

def get_apt_links(apts_soup):
    links = []
    apts_a = apts_soup.find_all("a", {"data-lurker-detail":"list_id"})
    for apt_a in apts_a:
        link = apt_a.get("href")
        links.append(link)
    return links

def scrap_apts_page(apts_page):
    html = requestHTMLPage(apts_page)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        apts = get_apt_links(soup)
        next_page_a = soup.find("a", {"data-lurker-detail":"next_page"})
        if next_page_a:
            next_page = next_page_a.get("href")
        else:
            next_page = None
        #print(len(apts), " apartment urls read")
        return apts, next_page
    else:
        return [], None

def walk_apt_pages(apts_url):
    apt_urls = []
    next_page = apts_url
    apt_pages_read = 0
    while next_page:
        apt_pages_read += 1
        apts, next_page = scrap_apts_page(next_page)
        apt_urls += apts
        print(apt_pages_read, "pages read.")
        time.sleep(0.1)
    apt_urls = list(set(apt_urls))
    print(len(apt_urls), " unique apartment announcements obtained.")
    print(apt_pages_read, " pages read.")
    return apt_urls

def scrap_apartment(apartment_url, infos):
    html = requestHTMLPage(apartment_url, max_tries = 3)
    if html == None:
        return
    soup = BeautifulSoup(html, "html.parser")
    
    price = None
    cond = 0
    area = None
    rooms = None
    bathrooms = None
    garage_slots = 0
    title = None
    address = None
    date = None

    IPTU = 0
    CEP = None
    municipio = None
    bairro = None
    logradouro = None

    title_h1 = soup.find("h1",{"class": "sc-45jt43-0 eCghYu sc-ifAKCX cmFKIN"})
    if title_h1:
        title = title_h1.contents[0]

    publication_span = soup.find("span", {"class": "sc-1oq8jzc-0 jvuXUB sc-ifAKCX fizSrB"})
    if publication_span:
        date = publication_span.contents[-1]
        day, minute = date.split(" às ")
        date_parts = [int(x) for x in day.split("/")]
        if date_parts[1] > todays_date.month and len(date_parts) == 2:
            date_parts += [todays_date.year-1]
        elif len(date_parts) == 2:
            date_parts += [todays_date.year]
        date = minute + " " + str(date_parts[2]) + "/" + str(date_parts[1]) + "/" + str(date_parts[0])
        #day = "/".join(date_parts)

    price_h2 = soup.find("h2", {"class": "sc-ifAKCX eQLrcK"})
    if price_h2:
        try:
            price = int(price_h2.contents[0].split(" ")[-1])
        except TypeError as ex:
            print(price_h2.contents[0].split(" ")[-1])
            price = 0

    detail_divs = soup.find_all("div", {"class": "duvuxf-0 h3us20-0 jyICCp"})
    #print(len(detail_divs), "detail divs")
    for detail_div in detail_divs:
        inner_dt = detail_div.find("dt")
        category = inner_dt.contents[0]
        #print("category is", category)
        content = None
        inner_a = detail_div.find("a")
        #print(str(inner_dt))
        if inner_a:
            content = inner_a.contents[0]
        else:
            inner_dd = detail_div.find("dd")
            if inner_dd:
                content = inner_dd.contents[0]
        if content:
            if category == "Banheiros":
                bathrooms = content
            elif "Condom" in category:
                cond = int(content.split(" ")[-1].replace(".", ""))
            elif category == "Área útil":
                area = content
            elif category == "Quartos":
                rooms = content
            elif category == "Vagas na garagem":
                garage_slots = content
            elif category == "IPTU":
                IPTU = int(content.split(" ")[-1].replace(".", ""))
            elif category == "CEP":
                CEP = content
            elif category == "Município":
                municipio = content
            elif category == "Bairro":
                bairro = content
            elif category == "Logradouro":
                logradouro = content
        #else:
        #    print("No inner content in category")
    
    cond += IPTU
    
    address = []
    if municipio:
        address.append(municipio)
    if bairro:
        address.append(bairro)
    if logradouro:
        address.append(logradouro)
    address = ", ".join(address)
    
    
    try:
        if area == area:
            area = area.lower().rstrip('m²').rstrip('m2').split('m')[0]
        area = float(area)
    except Exception:
        #print(area)
        area = 0
    assert isinstance(price, int)
    assert isinstance(cond, int)
    price = price+cond
    infos.append([title, price, date, cond, area, rooms, bathrooms, garage_slots, 
                  address, bairro, CEP, apartment_url])


def scrap_all_apartments(urls, max_threads):
    url_chunks = chunks(urls, max_threads)
    infos = []
    for chunk in tqdm(list(url_chunks)):
        threads = list()
        for url in chunk:
            thread = Thread(target=scrap_apartment, args=(url, infos))
            threads.append(thread)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        time.sleep(2)
    return infos