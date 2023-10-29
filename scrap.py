import time
import requests
import pandas as pd
from funcs import *
import os
import sys
import json

apt_links_path = "scrap_data/apt_urls.txt"
apt_infos_path = "scrap_data/apt_infos.tsv"
urls_json_path = "pesquisas.json"

'''infos_titles = ['title', 'price', 'date', 'cond', 'area', 'rooms', 'bathrooms', 
                'garage_slots', 'address', 'bairro', 'CEP',  'apartment_url', 'imd_distance']
max_price = 800
min_price = 500
min_area = 33
max_area = 75
stopwords = {'praia', '/dia', 'temporada', 'comerciais', 'final de semana',
             'diária', 'mobiliado', 'bananeiras', 'psicologico', 'diaria',
             'frete', 'luxo'}'''

def has_stopword(title, stopwords):
    for word in stopwords:
        if word in title.lower():
            return True
    return False

def area_not_big(area, max_area):
    try:
        area_n = float(area)
        return area_n <= max_area
    except Exception:
        return True
    
def area_not_small(area, min_area):
    try:
        area_n = float(area)
        return area_n > min_area or area_n < 10
    except Exception:
        return True

def analyze_apts(apts_url, scrap_config):
    print("Listing pagination")
    apt_urls = walk_apt_pages(apts_url, scrap_config)
    #print(apt_urls)
    print(len(apt_urls))
    apt_infos = scrap_all_apartments(apt_urls, scrap_config)
    
    apts = []
    
    for info in apt_infos:
        apts.append({scrap_config['infos_titles'][i]: info[i] for i in range(len(info))})
    return apts

def replace_max_price(olx_url: str, max_price):
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
    
def make_key_list(apt):
    names = ['city', 'rooms', 'size_class', 'price', 'bairro']
    inverted = ['price']
    keys = []
    for name in names:
        val = apt[name]
        if name in inverted:
            val = -val
        keys.append(val)
    print(keys)
    return tuple(keys)

#%%
if __name__ == "__main__":
    assert os.path.exists(urls_json_path)
    
    print("Carregando configuração")
    scrap_config = json.loads(open("scrap_config.json", 'r', encoding='utf-8').read())
    apt_url_pages = json.loads(open(urls_json_path, 'r', encoding='utf-8').read())[:1]
    print(apt_url_pages)
    apt_url_pages = [replace_max_price(apt_url, scrap_config['max_price']) 
                     for apt_url in apt_url_pages]
    print("Urls de busca:")
    print(apt_url_pages)
    
    bairros_proibidos = scrap_config['bairros_proibidos']
    print("Bairros proibidos:")
    print(bairros_proibidos)
    if os.path.exists(apt_links_path):
        os.remove(apt_links_path)
    if os.path.exists(apt_infos_path):
        os.remove(apt_infos_path)
    
    print("Encontrando URLs de apartamentos")
    all_apts = []
    for url in apt_url_pages:
        #print(url)
        all_apts += analyze_apts(url, scrap_config)
    
    #%%
    print("Apartamentos restantes:")
    print(len(all_apts))
    stopwords = set(scrap_config['stopwords'])
    apts_filtered = [apt for apt in all_apts 
                     if not(has_stopword(apt['title'], stopwords))]
    print(len(apts_filtered))
    print('titles', [apt['title'] for apt in apts_filtered])
    apts_filtered = [apt for apt in apts_filtered 
                     if apt['price'] <= scrap_config['max_price']]
    print(len(apts_filtered))
    print(scrap_config['max_price'], [apt['price'] for apt in apts_filtered])
    apts_filtered = [apt for apt in apts_filtered 
                     if apt['price'] >= scrap_config['min_price']]
    print(len(apts_filtered))
    print(scrap_config['min_price'], [apt['price'] for apt in apts_filtered])
    apts_filtered = [apt for apt in apts_filtered 
                     if area_not_big(apt['area'], scrap_config['max_area'])]
    print(len(apts_filtered))
    print(scrap_config['max_area'], [apt['area'] for apt in apts_filtered])
    apts_filtered = [apt for apt in apts_filtered 
                     if area_not_small(apt['area'], scrap_config['min_area'])]
    print(len(apts_filtered))
    print(scrap_config['min_area'], [apt['area'] for apt in apts_filtered])
    apts_filtered = [apt for apt in apts_filtered 
                     if not(apt['bairro'] in bairros_proibidos)]
    print(len(apts_filtered))
    print('bairros', [apt['bairro'] for apt in apts_filtered])
    print('rooms', [apt['rooms'] for apt in apts_filtered])

    for apt in apts_filtered:
        apt['size_class'] = int(apt['area']/8)
        apt['city'] = apt['address'].split(',')[0]
    print('city', [apt['city'] for apt in apts_filtered])

    apts_filtered.sort(key = lambda apt: make_key_list(apt), reverse=True)
    
    '''titles = [apt['title'] for apt in apts_filtered]
    for title in titles:
        print(title)'''
    
    table = pd.DataFrame(apts_filtered)
    table.to_csv('apts_filtered.csv', sep=';')