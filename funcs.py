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

def get_apt_links(apts_soup, conf):
    links = []
    apts_a = apts_soup.find_all("a", {conf["apt_link_key"]: conf["apt_link_value"]})
    print("Apts in page:", len(apts_a))
    for apt_a in apts_a:
        link = apt_a.get("href")
        links.append(link)
    return links

def scrap_apts_page(apts_page, conf):
    html = requestHTMLPage(apts_page)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        apts = get_apt_links(soup, conf)
        next_page_a = soup.find("a", {conf["next_page_key"]: conf["next_page_value"]})
        if next_page_a:
            next_page = next_page_a.get("href")
        else:
            next_page = None
        #print(len(apts), " apartment urls read")
        return apts, next_page
    else:
        return [], None

def walk_apt_pages(apts_url, conf):
    apt_urls = []
    next_page = apts_url
    apt_pages_read = 0
    while next_page and apt_pages_read < conf['max_olx_pages']:
        print(next_page)
        apt_pages_read += 1
        apts, next_page = scrap_apts_page(next_page, conf)
        apt_urls += apts
        print(apt_pages_read, "pages read.")
        time.sleep(0.25)
    apt_urls = list(set(apt_urls))
    print(len(apt_urls), " unique apartment announcements obtained.")
    print(apt_pages_read, " pages read.")
    return apt_urls

def scrap_apartment(apartment_url, infos, scrap_config):
    #print(apartment_url)
    html = requestHTMLPage(apartment_url, max_tries = 3)
    if html == None:
        return
    soup = BeautifulSoup(html, "html.parser")
    
    price = None
    cond = 0
    area = None
    rooms = 0
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

    title_h1 = soup.find("h1",{"class": scrap_config['title_class']})
    if title_h1:
        title = title_h1.contents[0]
        #print(title)

    publication_span = soup.find("span", {"class": scrap_config['publication_class']})
    if publication_span:
        date = publication_span.contents[-1]
        #print(date)
        day, minute = date.split(" às ")
        date_parts = [int(x) for x in day.split("/")]
        if date_parts[1] > todays_date.month and len(date_parts) == 2:
            date_parts += [todays_date.year-1]
        elif len(date_parts) == 2:
            date_parts += [todays_date.year]
        date = minute + " " + str(date_parts[2]) + "/" + str(date_parts[1]) + "/" + str(date_parts[0])
        #day = "/".join(date_parts)

    price_h2 = soup.find_all("h2", {"class": scrap_config['price_class']})
    if price_h2:
        try:
            content = " ".join([" ".join(h2.contents) for h2 in price_h2])
            print(content)
            price = int(content.split(" ")[-1])
        except TypeError as ex:
            print(price_h2.contents[0].split(" ")[-1])
            price = 0
    else:
        print('invalid price class')

    detail_divs = soup.find_all("div", {"class": scrap_config['details_class']})
    for detail_div in detail_divs:
        ps = detail_div.find_all("p")
        print(detail_div, ps)
        category = ps[-1].contents[0]
        content = None
        if category == "Quarto":
            content = detail_div.find("a").contents[0]
        else:
            content = ps[0].contents[0]
        '''inner_a = detail_div.find("a")
        #print(str(inner_dt))
        if inner_a:
            content = inner_a.contents[0]
        else:
            inner_dd = detail_div.find("dd")
            if inner_dd:
                content = inner_dd.contents[0]'''
        if content:
            #print(category, content)
            if category == "Banheiro":
                bathrooms = content
            elif "Condom" in category:
                cond = int(content.split(" ")[-1].replace(".", ""))
            elif category == "Área útil":
                area = content
            elif category == "Quarto":
                rooms = int(content)
            elif category == "Vaga":
                if content == '-':
                    content = "0"
                garage_slots = int(content)
            elif category == "IPTU":
                IPTU = int(content.split(" ")[-1].replace(".", ""))
        #else:
        #    print("No inner content in category")
    
    adress_div = soup.find("div", {"class": scrap_config['address_class']})
    if adress_div:
        adress_str_list = [" ".join(p.contents) for p in adress_div.find_all('p')]
        if len(adress_str_list) == 3:
            logradouro = adress_str_list[0]
            bairro = adress_str_list[1].split('-')[0].lstrip().rstrip()
            cidade = adress_str_list[1].split('-')[1].split(',')[0].lstrip().rstrip()
            #estado = adress_str_list[1].split('-')[1].split(',')[1].lstrip().rstrip()
            CEP = adress_str_list[2].lstrip('CEP: ')
            print([logradouro, bairro, cidade, CEP])
        else:
            '''print(str(adress_div))
            print("Incorrect adress div", apartment_url)'''
            adress_str_list = [" ".join(p.contents) for p in adress_div.find_all('dd')]
            logradouro = adress_str_list[-1]
            bairro = adress_str_list[-2]
            cidade = adress_str_list[-3]
            CEP = adress_str_list[-4]
    else:
        print("No adress", scrap_config['address_class'], "in", apartment_url)
    
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
                  address, bairro, CEP, apartment_url, 0])
    print(infos[-1])


def scrap_all_apartments(urls, scrap_config):
    url_chunks = chunks(urls, 3)
    infos = []
    url_chunks_list = list(url_chunks)
    #scrap_apartment(url_chunks_list[0][0], infos)
    for chunk in tqdm(url_chunks_list):
        threads = list()
        for url in chunk:
            thread = Thread(target=scrap_apartment, args=(url, infos, scrap_config))
            threads.append(thread)
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        time.sleep(5)
    return infos