# from bs4 import BeautifulSoup as bs
# import requests
# from django.shortcuts import render
# import pandas as pd
# from sqlalchemy import create_engine, exc


# url = 'https://markets.businessinsider.com/commodities'
# response = requests.get(url)

# soup = bs(response.content, 'html.parser')
# # print(soup)
# table = soup.find('table', class_='table table--col-1-font-color-black table--suppresses-line-breaks ')
# # print(table)
# df = pd.DataFrame()
# for row in table.tbody.find_all('tr'):
#     # Find all data for each column
#     columns = row.find_all('td')
#     # print(columns[4].text)
#     if (columns != []):
#         precious_metal = columns[0].text.strip()
#         price = columns[1].text.strip()
#         percentage = columns[2].text.strip()
#         increase_decrease = columns[3].text.strip()
#         unit = columns[4].text.strip()
#         date = columns[5].text.strip()

#         df = df.append({'precious_metal':precious_metal,'price': price,'percentage': percentage,
#                         'increase_decrease':increase_decrease,'unit':unit,'date': date},ignore_index=True )
#         print(df)

# table2 = soup.find('table', class_="table table--col-1-font-color-black table--suppresses-line-breaks margin-vertical--medium")
# df2 = pd.DataFrame()
# # print(table2)
# for row in table2.tbody.find_all('tr'):
#     # Find all data for each column
#     columns = row.find_all('td')
#     # print(columns[4].text)
#     if (columns != []):
#         energy = columns[0].text.strip()
#         price = columns[1].text.strip()
#         percentage = columns[2].text.strip()
#         increase_decrease = columns[3].text.strip()
#         unit = columns[4].text.strip()
#         date = columns[5].text.strip()

#         df2 = df2.append({'energy': energy, 'price': price, 'percentage': percentage,
#                         'increase_decrease': increase_decrease, 'unit': unit, 'date': date}, ignore_index=True)
#         print(df2)
