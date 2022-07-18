import time
import requests
import pandas as pd
from funcs import *
import os
import sys
import json

apt_links_path = "scrap_data/apt_urls.txt"
apt_infos_path = "scrap_data/apt_infos.tsv"
bairros_json_path = "bairros_indesejados.json"
urls_json_path = "pesquisas.json"

infos_titles = ['title', 'price', 'date', 'cond', 'area', 'rooms', 'bathrooms', 
                'garage_slots', 'address', 'bairro', 'CEP',  'apartment_url']
max_price = 700
stopwords = {'praia', '/dia', 'temporada', 'comerciais', 'final de semana',
             'diária', 'mobiliado', 'bananeiras', 'psicologico', 'diaria',
             'frete', 'luxo'}

def has_stopword(title):
    for word in stopwords:
        if word in title.lower():
            return True
    return False

def area_not_big(area):
    try:
        area_n = float(area)
        return area_n <= 70
    except Exception:
        return True
    
def area_not_small(area):
    try:
        area_n = float(area)
        return area_n > 22 or area_n < 10
    except Exception:
        return True

def analyze_apts(apts_url):
    apt_urls = walk_apt_pages(apts_url)
    print(len(apt_urls))
    apt_infos = scrap_all_apartments(apt_urls, 20)
    
    apts = []
    
    for info in apt_infos:
        apts.append({infos_titles[i]: info[i] for i in range(len(info))})
    return apts

def replace_max_price(olx_url: str):
    if 'pe=' in olx_url:
        url, params = olx_url.split('?')
        params = params.split('&')
        for i in range(len(params)):
            param_str = params[i]
            if 'pe=' in param_str:
                params[i] = 'pe='+str(max_price)
                break
        params_str = "&".join(params)
        return url+"?"+params_str
    else:
        return olx_url
#%%
if __name__ == "__main__":
    assert os.path.exists(bairros_json_path)
    assert os.path.exists(urls_json_path)
    
    apt_url_pages = json.loads(open(urls_json_path, 'r', encoding='utf-8').read())
    print(apt_url_pages)
    apt_url_pages = [replace_max_price(apt_url) for apt_url in apt_url_pages]
    print("Urls de busca:")
    print(apt_url_pages)
    
    bairros_proibidos = json.loads(open(bairros_json_path, 'r', encoding='utf-8').read())
    print("Bairros proibidos:")
    print(bairros_proibidos)
    if os.path.exists(apt_links_path):
        os.remove(apt_links_path)
    if os.path.exists(apt_infos_path):
        os.remove(apt_infos_path)
    
    print("Encontrando URLs de apartamentos")
    all_apts = []
    for url in apt_url_pages:
        print(url)
        all_apts += analyze_apts(url)
    
    #%%
    
    apts_filtered = [apt for apt in all_apts if not(has_stopword(apt['title']))]
    apts_filtered = [apt for apt in apts_filtered if apt['price'] <= max_price]
    apts_filtered = [apt for apt in apts_filtered if apt['price'] >= 350]
    apts_filtered = [apt for apt in apts_filtered if area_not_big(apt['area'])]
    apts_filtered = [apt for apt in apts_filtered if area_not_small(apt['area'])]
    apts_filtered = [apt for apt in apts_filtered if not(apt['bairro'] in bairros_proibidos)]
    
    for apt in apts_filtered:
        apt['size_class'] = int(apt['area']/8)
        apt['city'] = apt['address'].split(',')[0]
    
    apts_filtered.sort(key = lambda apt: ((apt['city'],apt['rooms'], 
                                           apt['size_class']), 
                                          -(apt['price']), 
                                          apt['bairro']), reverse=True)
    
    titles = [apt['title'] for apt in apts_filtered]
    for title in titles:
        print(title)
    
    table = pd.DataFrame(apts_filtered)
    table.to_csv('apts_filtered.csv', sep=';')