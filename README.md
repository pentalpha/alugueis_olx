# Aluguel OLX

O objetivo deste projeto é obter os dados de aluguel de casas/apartamentos na OLX.
Para executar o scrapping, basta rodar o script:

$ python scrap.py

Resultados estão no arquivo apts_filtered.csv. Ele contém informações como título
do anúncio, URL, preço total, área construída, número de quartos, número de banheiros e
endereço. Os melhores anúncios ficam no topo da tabela.

Bibliotecas utilizadas: requests, pandas, BeaultifulSoup e tqdm. Listagem no arquivo
requirements.txt.

## Personalizar cidades:

A pesquisa é feita a partir de links para páginas de pesquisa por imoveis na OLX.
Para pesquisar em diversas cidades, basta adicionar um link para cada.
Os links ficam no arquivo pesquisas.json.

## Personalizar bairros:

Caso deseje excluir ofertas de aluguel em bairros especificos, é só adicionar o 
nome do bairro em bairros indesejados.json.

## Preço máximo

O preço máximo é definido pela variável 'max_price' em scrap.py. Já leva em conta
condomínimo e cobrança mensal de IPTU.

## Ordenação

Os critérios de ordenação podem ser personalizados na linha 103 do arquivo scrap.py.
