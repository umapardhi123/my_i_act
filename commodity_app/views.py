from bs4 import BeautifulSoup as bs
import requests as rs
from django.shortcuts import render, redirect
import pandas as pd
from sqlalchemy import create_engine, exc
import urllib.request
from urllib.parse import urlparse
from django.http import HttpRequest, HttpResponse, JsonResponse
import os
import hashlib
from django.core.files.storage import default_storage
from django.shortcuts import render
import requests
import json
import pandas as pd
from .models import *
from bs4 import BeautifulSoup as bs
import requests
from dateutil.relativedelta import relativedelta
import statsmodels.api as sm
import pandas as pd
from sqlalchemy import create_engine, exc
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpRequest, HttpResponse, JsonResponse
from prophet import Prophet
from yahooquery import Ticker
from datetime import datetime, timedelta
import sys
import re
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
import pickle
import re
from .stock_model import ModelPipeline
# from tabula import read_pdf

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable

# from .yahoo_query import *
# import mysql
today = datetime.today()


def connection():
    try:
        conn = create_engine('mysql+pymysql://root:root@localhost/stock')
    except exc.SQLAlchemyError as e:
        print(e)

    return conn


conn = connection()


def error_404_view(request, exception):
    return render(request, '404.html')


def handle_server_error(request):
    return render(request, '500.html')


def login(request):
    request.session.flush()
    return render(request, 'login.html')


def validation(request):
    conn = connection()
    try:
        username = request.POST.dict().get('uname')
        password = request.POST.dict().get('password')
        encpw = hashlib.sha256(password.encode()).hexdigest()
        user_valid = pd.read_sql(f"SELECT * FROM users WHERE username = '{username}' and password = '{encpw}' ", conn)
        if user_valid.shape[0] == 1:
            user_id = str(user_valid['ID'][0])
            print(user_id, '<----u')
            request.session['user_id'] = user_id
            request.session['modules'] = list(map(int, user_valid['modules'][0].split(',')))
            modules = request.session['modules']
            query = pd.read_sql(f"SELECT * FROM users WHERE ID = {user_id}", conn)
            print(request.session['modules'], '<--------------mod')
            msg = "Successful"
            conn.execute(
                f"INSERT into userlogs (username,password,usererror,user_id) VALUES ('{username}','{password}','{msg}','{user_id}')")
            conn.dispose()
            return render(request, 'landingpage.html', {'modules': modules, 'query': query})
        else:
            user_valid = pd.read_sql(f"SELECT * FROM users WHERE username = '{username}'", conn)
            user_id = str(user_valid['ID'][0])
            msg = "Wrong username or password"
            conn.execute(
                f"INSERT into userlogs (username,password,usererror,user_id) VALUES ('{username}','{password}','{msg}','{user_id}')")
            conn.dispose()
            return render(request, 'login.html', {'msg': 'Wrong username or password'})
    except Exception as e:
        print(e)
        username = request.POST.dict().get('uname')
        password = request.POST.dict().get('password')
        encpw = hashlib.sha256(password.encode()).hexdigest()
        user_id = "0"
        msg = "Something went wrong, contact administrator"
        conn.execute(
            f"INSERT into userlogs (username,password,usererror,user_id) VALUES ('{username}','{password}','{msg}','{user_id}')")
        conn.dispose()
    return render(request, 'login.html', {'msg': "Something went wrong, contact administrator"})


def landingpage(request):
    if 'user_id' not in request.session:
        return render(request, 'login.html', {'mssg': 'Please Login..!!'})
    else:
        user_id = request.session['user_id']
        modules = request.session['modules']

        query = pd.read_sql(f"SELECT * FROM users WHERE ID = {user_id}", conn)
        print(query, ",=========Qa")
        print(modules, '<--ldmod')
        return render(request, 'landingpage.html', {'user_id': user_id, 'modules': modules, 'query': query})


def registration(request):
    conn = connection()
    try:
        uname = request.POST.dict().get('username')
        fname = request.POST.dict().get('fname')
        lname = request.POST.dict().get('lname')
        pword = request.POST.dict().get('pword')
        email = request.POST.dict().get('email')
        modules = request.POST.getlist('modules')
        modules = ", ".join(modules)
        encpw = hashlib.sha256(pword.encode()).hexdigest()
        conn.execute(
            f"INSERT into users (username,firstname,lastname,password,email,modules) VALUES ('{uname}','{fname}','{lname}','{encpw}','{email}','{modules}')")
        conn.dispose()
    except Exception as e:
        print(e)
    return render(request, 'login.html')


def commodity(request):
    if 'user_id' not in request.session:
        return render(request, 'login.html', {'mssg': 'Please Login..!!'})
    else:
        user_id = request.session['user_id']
        modules = request.session['modules']
        df = pd.read_sql(f"SELECT * FROM users WHERE ID = {user_id}", conn)
        print(df)
        latest_created_date = pd.read_sql("SELECT MAX(created_date) FROM commodities", conn).iloc[0, 0]
        print(latest_created_date,'latest_created_date')
        # Fetch commodities data for the row(s) with the latest created_date
        com_df = pd.read_sql(f"SELECT * FROM commodities WHERE created_date = '{latest_created_date}'", conn)
        return render(request, "commodity.html", {'user_id': user_id, 'df': df, 'modules': modules,'com_df':com_df})


def uploaddata(request):
    conn = connection()
    if 'myfile' in request.FILES:
        save_file = request.FILES['myfile']
        sheet = pd.read_excel(save_file)
        # print(sheet,'<-------sheet')
        sheet.to_sql('exceldata', conn, index=False, if_exists='append')

    return render(request, 'commodity.html')


def getsheetdata(request):
    file = request.FILES['datasheet']
    sheet1 = pd.read_excel(file)
    # print(sheet1,"<----------sheet1")
    return HttpResponse(sheet1.to_html(index=False, classes="table table-hover table-bordered ", border=0))


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/invoice_ocr/google-cred.json"


# os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/home/azureuser/ersdev/google-cred.json"

def ocr(request):
    if 'user_id' not in request.session:
        return render(request, 'login.html', {'mssg': 'Please Login..!!'})
    else:
        user_id = request.session['user_id']
        modules = request.session['modules']
        print(modules, '<--ocrmod')
        return render(request, 'ocr.html', {'user_id': user_id, 'modules': modules})


def objectcount(request):
    if 'user_id' not in request.session:
        return render(request, 'login.html', {'mssg': 'Please Login..!!'})
    else:
        user_id = request.session['user_id']
        modules = request.session['modules']
        print(modules, '<--ojmod')
        return render(request, 'objectcount.html', {'user_id': user_id, 'modules': modules})


def massupdate(request):
    if 'user_id' not in request.session:
        return render(request, 'login.html', {'mssg': 'Please Login..!!'})
    else:
        user_id = request.session['user_id']
        modules = request.session['modules']
        return render(request, 'massupdate.html', {"user_id": user_id, 'modules': modules})


def detect_document(request):
    """Detects document features in an image."""
    from google.cloud import vision
    import io
    client = vision.ImageAnnotatorClient()

    if 'files' in request.FILES:
        conn = connection()
        imgfile = request.FILES['files']
        print(imgfile, '<-----imgocr')
        user_id = request.session['user_id']
        imgext = request.FILES['files'].name.split('.')[1]
        imgname = f'commodity_app/static/ocrimg/{user_id}.{imgext}'
        imgurl = f'ocrimg/{user_id}.{imgext}'
        conn.execute(f"INSERT into ocrimg(image,user_id) VALUES ('{imgurl}','{user_id}')")
        conn.dispose()

        content = imgfile.read()

        image = vision.Image(content=content)

        response = client.document_text_detection(image=image)

        block_text = {}

        for page in response.full_text_annotation.pages:
            for id, block in enumerate(page.blocks):
                block_text[id] = []
                print('\nBlock confidence: {}\n'.format(block.confidence))
                for paragraph in block.paragraphs:
                    print('Paragraph confidence: {}'.format(
                        paragraph.confidence))

                    for word in paragraph.words:
                        word_text = ''.join([
                            symbol.text for symbol in word.symbols
                        ])
                        block_text[id].append(word_text)
                        print('Word text: {} (confidence: {})'.format(
                            word_text, word.confidence))

                        for symbol in word.symbols:
                            print('\tSymbol: {} (confidence: {})'.format(
                                symbol.text, symbol.confidence))

        items = []
        # print(items)
        acc = ''
        po = ''
        for i in block_text.values():
            # print(block_text.values())
            if 'PO' in i:
                print(i)
                for ele in i:
                    if ele.isdigit():
                        print(ele)
                        po = ele
                        print(po, '<--po')
            elif 'Bill' in i:
                print(i)
                for ele in i:
                    if ele.isdigit():
                        print(ele)
                        acc = ele
            elif 'SN' in i:
                print(i)
                for ele in i:
                    if ele.isdigit() and len(ele) > 3:
                        print(ele)
                        items.append(ele)
        items_str = ", ".join(items)
        data = {'account_no': [acc], 'purchase_order': [po], 'ordered_items': [items_str]}
        order_df = pd.DataFrame(data)
        print(order_df, '<--------order_df')
        # order_df.to_excel('ocr_po.xlsx', index=False)
        if os.path.exists(imgname):
            os.remove(imgname)
        default_storage.save(imgname, imgfile)

        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))
        return HttpResponse(order_df.to_html(index=False, classes="table table-hover table-bordered", border=0))


def localize_objects(request):
    """Localize objects in the local image.

    Args:
    path: The path to the local file.
    """
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    if 'files[]' in request.FILES:
        conn = connection()
        imgfile = request.FILES['files[]']
        print(imgfile, '<-----objcount')
        user_id = request.session['user_id']
        # imgext = request.FILES['files[]'].name.split('.')[1]
        imgname = f'commodity_app/static/objcount/{imgfile}'
        imgurl = f'objcount/{imgfile}'

        # with open(imgfile, 'rb') as image_file:
        content = imgfile.read()
        image = vision.Image(content=content)

        objects = client.object_localization(
            image=image).localized_object_annotations

        if os.path.exists(imgname):
            os.remove(imgname)
        default_storage.save(imgname, imgfile)

        obj_list = [obj.name for obj in objects]
        count = len(obj_list)
        boxcount = {f'No of objects found: {count}'}
        conn.execute(f"INSERT into objectcount(image,output,user_id) VALUES ('{imgurl}','{count}','{user_id}')")
        conn.dispose()

        # print(f'Number of objects found: {boxcount}'.format(len(objects)))
        for object_ in objects:
            # print(type(objects),'<------type')
            # print(f'Number of objects found: {boxcount}'.format(len(objects)))
            print('\n{} (confidence: {})'.format(object_.name, object_.score))
            print('Normalized bounding polygon vertices: ')
            for vertex in object_.bounding_poly.normalized_vertices:
                print(' - ({}, {})'.format(vertex.x, vertex.y))

        return HttpResponse(boxcount)


def stock_screener(request):
    conn = connection()
    url = 'https://www.wallstreetzen.com/stock-screener/stock-forecast'
    response = requests.get(url)

    soup = bs(response.content, 'html.parser')
    # table = soup.find('table', class_='MuiTable-root-445 jss432').find_next('tbody')
    table = soup.find('div', class_="MuiContainer-root-89 jss1 MuiContainer-maxWidthXl-96")
    # soup.find('table', attrs={'class': 'tablesaw', 'data-tablesaw-mode-exclude': 'columntoggle'}).find_next('tbody')
    # yahoo1 = pd.read_sql("SELECT * FROM stock.yahooquery_history",conn)
    # yahoo = yahoo1.tail(1000)
    # yahoo = yahoo1.tail(10)
    # print(yahoo,'<-----yahoo')
    yahoo_stats = pd.read_sql("SELECT * FROM stock.yahoostats", conn)
    # yahoo_stats = yahoo_stat.tail(10)
    stock_marketaux = pd.read_sql("SELECT * FROM stock.marketaux", conn)
    wall = pd.read_sql("SELECT * FROM stock.wallstreetzen", conn)
    wall = wall.tail(100)
    # wall = pd.read_sql("SELECT * FROM wallstreetzen ORDER BY id DESC LIMIT 1;",conn)
    print(len(wall), '<-----wall')

    df = pd.DataFrame(
        columns=['Ticker', 'Company', 'Forecast_Score', 'Market_Cap', 'Price', 'Price_Target', 'Upside_Downside',
                 'Consensus', 'Analysts', 'Fore_Revenue_Growth', 'Fore_Earnings_Growth', 'Forecast_ROE',
                 'Forecast_ROA'])
    for row in table.tbody.find_all('tr'):
        # Find all data for each column
        columns = row.find_all('td')
        if (columns != []):
            Ticker = columns[0].text.strip()
            Company = columns[1].text.strip()
            Forecast_Score = columns[2].text.strip()
            Market_Cap = columns[3].text.strip()
            Price = columns[4].text.strip()
            Price_Target = columns[5].text.strip()
            Upside_Downside = columns[6].text.strip()
            Consensus = columns[7].text.strip()
            Analysts = columns[8].text.strip()
            Fore_Revenue_Growth = columns[9].text.strip()
            Fore_Earnings_Growth = columns[10].text.strip()
            Forecast_ROE = columns[11].text.strip()
            Forecast_ROA = columns[12].text.strip()

            data = {'Ticker': [Ticker], 'Company': [Company], 'Forecast_Score': [Forecast_Score],
                    'Market_Cap': [Market_Cap], 'Price': [Price], 'Price_Target': [Price_Target],
                    'Upside_Downside': [Upside_Downside], 'Consensus': [Consensus], 'Analysts': [Analysts],
                    'Fore_Revenue_Growth': [Fore_Revenue_Growth],
                    'Fore_Earnings_Growth': [Fore_Earnings_Growth], 'Forecast_ROE': [Forecast_ROE],
                    'Forecast_ROA': [Forecast_ROA]}
            print(data, '<------datawall')
            df = pd.DataFrame(data,
                              columns=['Ticker', 'Company', 'Forecast_Score', 'Market_Cap', 'Price', 'Price_Target',
                                       'Upside_Downside', 'Consensus', 'Analysts', 'Fore_Revenue_Growth',
                                       'Fore_Earnings_Growth', 'Forecast_ROE', 'Forecast_ROA'])
            df.to_sql('wallstreetzen', conn, if_exists='append', index=False)

    return render(request, 'stock_screener.html',
                  {'wall': wall, 'data': df, 'yahoo_stats': yahoo_stats, 'stock_marketaux': stock_marketaux})


def stock_predictions(request):
    if 'user_id' not in request.session:
        return render(request, 'login.html', {'mssg': 'Please Login..!!'})
    else:
        # for wallstreetzen strong buy
        modules = request.session['modules']
        company = pd.read_sql(f"SELECT DISTINCT Ticker FROM `wallstreetzen`", conn)
        # print(company)
        user_id = request.session['user_id']
        com_prediction_count = {}
        wdf = pd.DataFrame()

        def convert_to_float(value_str):
            return float(value_str.replace(',', ''))
        for com in company['Ticker']:
            # print(com,'com')
            df1 = pd.read_sql(f"SELECT * FROM `wallstreetzen` WHERE Ticker='{com}'", conn)
            # print(df1,'df1')
            df1['Price'] = df1['Price'].str.replace("$", "")
            # df1['Price'] = df1['Price'].str.replace(" ,", "")
            # df1['Price'] = df1['Price'].astype(float)
            df1['Price'] = df1['Price'].apply(lambda x: convert_to_float(x))
            # df1['Price'] = df1['Price'].str.replace(',','',regex=False)

            # print(amt,'amt')

            if df1.shape:
                ticker = ''
                price = ''
                occurance = 0
                for x in range(len(df1)):
                    # df1.loc[x,'Price'] = df1.loc[x,'Price'].replace("$", "")
                    if float(df1.loc[x, 'Price']) <= 100.00:
                        # print(df1.loc[0, 'Ticker'],df1.loc[x,'Price'])
                        ticker = df1.loc[0, 'Ticker']
                        # print(ticker,'ticker')
                        price = df1.loc[df1.index[-1], 'Price']
                        # print(price,'price')
                        if df1.loc[x, 'Consensus'] == 'Strong Buy':
                            # print(float(df1.loc[x, 'Price']),price,ticker)
                            today_price = float(df1.loc[x, 'Price'])
                            # print(today_price)
                            try:
                                nextday_price = float(df1.loc[x + 1, 'Price'])

                                if nextday_price > today_price:
                                    occurance += 1
                            except Exception as e:
                                print(e)
                                pass
                if occurance > 0:
                    pcent = ((occurance / len(df1)) * 100)
                    # print(pcent,'percent')
                    percent = float("{:.2f}".format(pcent))

                    cmp_data = {"ticker": ticker, "price": price, "occurences": f"{occurance} / {(len(df1) - 1)}",
                                "percentage": percent, 'consensus': 'Strong Buy'}
                    # cmp_data['consensus'] = cmp_data['consensus'].style.set_properties(**{'background-color': 'black',
                    #            'color': 'green'})
                    wdf = wdf.append(cmp_data, ignore_index=True)

        wdf = wdf.sort_values(by="percentage", ascending=False)
        # print(wdf)

        # for wallstreetzen strong sell
        wdf_sell = pd.DataFrame()
        for com in company['Ticker']:
            # print(com,'com')
            sell_df = pd.read_sql(f"SELECT * FROM `wallstreetzen` WHERE Ticker='{com}'", conn)
            # print(df1,'df1')
            sell_df['Price'] = sell_df['Price'].str.replace("$", "")
            sell_df['Price'] = sell_df['Price'].str.replace('"', '')
            sell_df['Price'] = sell_df['Price'].str.replace(",", "")
            sell_df['Price'] = sell_df['Price'].astype(float)
            # for value in sell_df['Price']:
            #     try:
            #         float(value)
            #     except ValueError:
            #         print(value)
            # print(amt,'amt')

            if sell_df.shape:
                ticker = ''
                price = ''
                occurance = 0
                for x in range(len(sell_df)):
                    # sell_df.loc[x,'Price'] = df1.loc[x,'Price'].replace("$", "")
                    if float(sell_df.loc[x, 'Price']) <= 100.00:
                        # print(sell_df.loc[0, 'Ticker'],df1.loc[x,'Price'])
                        ticker = sell_df.loc[0, 'Ticker']
                        # print(ticker,'ticker')
                        price = sell_df.loc[sell_df.index[-1], 'Price']
                        # print(sell_df.loc[x, 'Consensus'],'price')
                        if sell_df.loc[x, 'Consensus'] == 'Strong Sell':
                            # print(float(df1.loc[x, 'Price']),price,ticker)
                            today_price = float(sell_df.loc[x, 'Price'])
                            # print(today_price)
                            try:
                                nextday_price = float(sell_df.loc[x + 1, 'Price'])
                                # print(today_price,nextday_price)

                                if nextday_price <= today_price:
                                    occurance += 1
                            except Exception as e:
                                print(e)
                                pass
                if occurance > 0:
                    pcent = ((occurance / len(sell_df)) * 100)
                    # print(pcent,'percent')
                    percent = float("{:.2f}".format(pcent))
                    cmp_data1 = {"ticker": ticker, "price": price, "occurences": f"{occurance} / {(len(sell_df) - 1)}",
                                 "percentage": percent, 'consensus': 'Strong Sell'}
                    wdf_sell = wdf_sell.append(cmp_data1, ignore_index=True)

        # print(wdf_sell, 'sell')
        wdf = wdf.append(wdf_sell)

        wdf_sell = wdf.sort_values(by="percentage", ascending=False)
        # wdf['consensus'] = wdf['consensus'].style.apply(lambda x: "background-color: red" if 'Strong Buy' in x else "background-color: green")

        # print(wdf_sell, '<------wdfstsell')

        # for yahoostat strong Buy
        ycompany = pd.read_sql(f"SELECT DISTINCT ticker FROM `yahoostats`", conn)
        ydf = pd.DataFrame()
        for com in ycompany['ticker']:
            df2 = pd.read_sql(f"SELECT * FROM `yahoostats` WHERE ticker='{com}'", conn)
            df2['price_now'] = df2['price_now'].astype(float)
            if df2.shape:
                ticker = ''
                price = ''
                occurance2 = 0
                for x in range(len(df2)):
                    if float(df2.loc[x, 'price_now']) <= 100.00:
                        ticker = df2.loc[0, 'ticker']
                        price = df2.loc[df2.index[-1], 'price_now']
                        if df2.loc[x, 'ratingstring'] == 'strong_buy':
                            today_price = float(df2.loc[x, 'price_now'])
                            try:
                                nextday_price = float(df2.loc[x + 1, 'price_now'])
                                if nextday_price > today_price:
                                    occurance2 += 1
                            except:
                                pass
                if occurance2 > 0:
                    pcent = (occurance2 / len(df2)) * 100
                    percent = float("{:.2f}".format(pcent))
                    cmp_data = {"ticker": ticker, "price": price, "occurences": f"{occurance2} / {(len(df2) - 1)}",
                                "percentage": percent, 'consensus': 'Strong Buy'}
                    # yahoo_pred_count.setdefault("company", []).append(cmp_data)
                    ydf = ydf.append(cmp_data, ignore_index=True)
        # print(type(ydf["percentage"]))
        ydf = ydf.sort_values(by="percentage", ascending=False)
        # print(ydf)

        # for yahoostat strong sell
        ydf_hold = pd.DataFrame()
        for com in ycompany['ticker']:
            df_hold = pd.read_sql(f"SELECT * FROM `yahoostats` WHERE ticker='{com}'", conn)
            df_hold['price_now'] = df_hold['price_now'].astype(float)
            if df_hold.shape:
                ticker = ''
                price = ''
                occurance2 = 0
                for x in range(len(df_hold)):
                    if float(df_hold.loc[x, 'price_now']) <= 100.00:
                        ticker = df_hold.loc[0, 'ticker']
                        price = df_hold.loc[df_hold.index[-1], 'price_now']
                        if df_hold.loc[x, 'ratingstring'] == 'hold':
                            today_price = float(df_hold.loc[x, 'price_now'])
                            try:
                                nextday_price = float(df_hold.loc[x + 1, 'price_now'])
                                if nextday_price <= today_price:
                                    occurance2 += 1
                            except:
                                pass
                if occurance2 > 0:
                    pcent = (occurance2 / len(df_hold)) * 100
                    percent = float("{:.2f}".format(pcent))
                    cmp_data = {"ticker": ticker, "price": price, "occurences": f"{occurance2} / {(len(df_hold) - 1)}",
                                "percentage": percent, 'consensus': 'Strong Sell'}
                    # yahoo_pred_count.setdefault("company", []).append(cmp_data)
                    ydf_hold = ydf_hold.append(cmp_data, ignore_index=True)
        # print(type(ydf["percentage"]))

        ydf = ydf.append(ydf_hold)
        ydf_hold = ydf.sort_values(by="percentage", ascending=False)
        # print(ydf_hold, '<------ydf_hold')

        # combine

        # Total Strong Buy
        company = pd.read_sql(f"SELECT DISTINCT Ticker FROM `wallstreetzen`", conn)
        wdf2 = pd.DataFrame()
        for com in company['Ticker']:
            df1 = pd.read_sql(f"SELECT * FROM `wallstreetzen` WHERE Ticker='{com}'", conn)
            df1['Price'] = df1['Price'].str.replace("$", "")
            df1['Price'] = df1['Price'].astype(float)

            df2 = pd.read_sql(f"SELECT * FROM `yahoostats` WHERE ticker='{com}'", conn)
            df2['price_now'] = df2['price_now'].astype(float)

            ticker = ''
            price = ''
            occurance = 0
            occurance2 = 0
            for x in range(len(df1)):
                if float(df1.loc[x, 'Price']) <= 100.00:
                    ticker = df1.loc[0, 'Ticker']
                    price = df1.loc[df1.index[-1], 'Price']
                    if df1.loc[x, 'Consensus'] == 'Strong Buy':
                        today_price = float(df1.loc[x, 'Price'])
                        try:
                            nextday_price = float(df1.loc[x + 1, 'Price'])

                            if nextday_price > today_price:
                                occurance += 1
                        except Exception as e:
                            print(e)
                            pass

            for x in range(len(df2)):
                if float(df2.loc[x, 'price_now']) <= 100.00:
                    ticker = df2.loc[0, 'ticker']
                    price = df2.loc[df2.index[-1], 'price_now']
                    if df2.loc[x, 'ratingstring'] == 'strong_buy':
                        today_price = float(df2.loc[x, 'price_now'])
                        try:
                            nextday_price = float(df2.loc[x + 1, 'price_now'])
                            if nextday_price > today_price:
                                occurance2 += 1
                        except:
                            pass

            if occurance > 0 and occurance2 > 0:
                print(len(df1), len(df2), 'addtion')
                pcent = ((occurance + occurance2) / (len(df1) + len(df2))) * 100
                percent = float("{:.2f}".format(pcent))
                cmp_data = {"ticker": ticker, "price": price,
                            "occurences": f"{(occurance + occurance2)} / {((len(df1) + len(df2)) - 3)}",
                            "percentage": percent, 'consensus': 'Strong Buy'}
                wdf2 = wdf2.append(cmp_data, ignore_index=True)

        wdf2 = wdf2.sort_values(by="percentage", ascending=False)
        # print(wdf2, '<----------wdf2 stbuy')

        # Total Strong Sell
        total_sell = pd.DataFrame()
        for com in company['Ticker']:
            sell_df = pd.read_sql(f"SELECT * FROM `wallstreetzen` WHERE Ticker='{com}'", conn)
            sell_df['Price'] = sell_df['Price'].str.replace("$", "")
            sell_df['Price'] = sell_df['Price'].astype(float)

            df_hold = pd.read_sql(f"SELECT * FROM `yahoostats` WHERE ticker='{com}'", conn)
            df_hold['price_now'] = df_hold['price_now'].astype(float)

            ticker = ''
            price = ''
            occurance = 0
            occurance2 = 0
            for x in range(len(sell_df)):
                if float(sell_df.loc[x, 'Price']) <= 100.00:
                    ticker = sell_df.loc[0, 'Ticker']
                    price = sell_df.loc[sell_df.index[-1], 'Price']
                    if sell_df.loc[x, 'Consensus'] == 'Hold':
                        today_price = float(sell_df.loc[x, 'Price'])
                        try:
                            nextday_price = float(sell_df.loc[x + 1, 'Price'])

                            if nextday_price <= today_price:
                                occurance += 1
                        except Exception as e:
                            print(e)
                            pass
            for x in range(len(df_hold)):
                if float(df_hold.loc[x, 'price_now']) <= 100.00:
                    ticker = df_hold.loc[0, 'ticker']
                    price = df_hold.loc[df_hold.index[-1], 'price_now']
                    if df_hold.loc[x, 'ratingstring'] == 'hold':
                        today_price = float(df_hold.loc[x, 'price_now'])
                        try:
                            nextday_price = float(df_hold.loc[x + 1, 'price_now'])
                            if nextday_price <= today_price:
                                occurance2 += 1
                        except:
                            pass

            if occurance > 0 and occurance2 > 0:
                print(len(sell_df), len(df_hold), 'addtion')
                pcent = ((occurance + occurance2) / (len(sell_df) + len(df_hold))) * 100
                percent = float("{:.2f}".format(pcent))
                cmp_data = {"ticker": ticker, "price": price,
                            "occurences": f"{(occurance + occurance2)} / {((len(sell_df) + len(df_hold)) - 3)}",
                            "percentage": percent, 'consensus': 'Strong Sell'}
                total_sell = total_sell.append(cmp_data, ignore_index=True)

        # total_sell = total_sell.sort_values(by="percentage", ascending=False)
        total = wdf2.append(total_sell)
        total = total.sort_values(by="percentage", ascending=False)
        # print(total, '<-----total')
        # print(total_sell,'<------total sell')

        #stock prediction model
        combine_df = pd.read_csv("commodity_app/merge1.csv",parse_dates=['created_date'])
        combine_df = combine_df.drop(columns=['Unnamed: 0'], axis=1)
        print(combine_df.iloc[[6576, 10]],'combine df')
        unique_tickers = combine_df['Ticker'].unique()

        result_df = pd.DataFrame({'Ticker': unique_tickers})

        for ticker in unique_tickers:
            ticker_data = combine_df.loc[
                combine_df['Ticker'] == ticker, ['open', 'low', 'close', 'volume', 'high', 'adjclose', 'created_date', 'Price',
                                         'Price_Target']].iloc[-1]
            result_df.loc[
                result_df['Ticker'] == ticker, ['open', 'low', 'close', 'volume', 'high', 'adjclose', 'created_date',
                                                'Price', 'Price_Target']] = ticker_data.values
        print(result_df,'resultdf')
        loaded_model = pickle.load(open(BASE_DIR + '/stmodel.pk1', 'rb'))
        # with open('commodity_app/model.pickle', 'rb') as f:
        #     loaded_model = pickle.load(f)
        predicted_values = loaded_model.predict(result_df)
        print(predicted_values)
        print(result_df, 'resultdf')
        pred_df = pd.DataFrame()
        counter = 0
        for val in predicted_values:
            tik = result_df['Ticker'][counter]
            counter = counter+1
            pred_df = pred_df.append({'ticker':tik,'pred_value':val},ignore_index=True)

        print(pred_df)
        total = pd.merge(total,pred_df,on='ticker')
        for rst in total['pred_value']:
            if rst==0:
                total['Consensus']= 'Strong Buy'
            if rst==1:
                total['Consensus'] = 'Buy'
            if rst==2:
                total['Consensus'] = 'Hold'
            if rst==3:
                total['Consensus'] = 'Sell'
        print(total)
        # counter = 0
        # pred_df = pd.DataFrame()
        # for tik in range(len(result_df)):
        #     # combine_df1 = combine_df.iloc[[6576, 10]]
        #     # combine_df1.sample(2)
        #     # combine_df1 = combine_df1.drop(columns=['Consensus'], axis=1)
        #     dfdata = result_df.iloc[counter]
        #     print(dfdata)
        #     predicted_values = loaded_model.predict(tik)
        #     print(tik, 'combine_df1---->')
        #     print(predicted_values)
        #     pred_df = pred_df.append({'Ticker':dfdata['Ticker'],'pred_value':predicted_values})
        #     counter =+1
        # print(pred_df)
        # model_instance = ModelPipeline()
        # model_instance.train(combine_df)
        #
        # # pickle.dump(model_instance,open('stmodel.pk1','wb'))
        #
        # result = model_instance.predict(combine_df1)
        # print(result)

        return render(request, 'stock_predictions.html',
                      {'user_id': user_id, 'modules': modules, 'wdf_sell': wdf_sell, 'ydf_hold': ydf_hold, 'wdf': wdf,
                       'ydf': ydf, 'total': total})


def graph(request, ticker):
    conn = connection()
    com = ticker
    print(com, '<-----com')
    # predictions = pd.DataFrame(columns=['ticker','price','occurences','percentage','consensus'])
    # For Wallstreet Strong Buy
    news = pd.read_sql(f"SELECT * FROM `wallnews` WHERE ticker='{com}'", conn)
    wstdf = pd.DataFrame()
    print(wstdf, '<-----wstdf')
    pdf = pd.read_sql(f"SELECT * FROM `wallstreetzen` WHERE Ticker='{com}'", conn)
    # print(pdf['Company'],'pdf')
    pdf['Price'] = pdf['Price'].str.replace("$", "")
    pdf['Price'] = pdf['Price'].astype(float)

    if pdf.shape:
        ticker = ''
        price = ''
        occurance1 = 0
        for x in range(len(pdf)):
            ticker = pdf.loc[0, 'Ticker']
            price = pdf.loc[pdf.index[-1], 'Price']
            if pdf.loc[x, 'Consensus'] == 'Strong Buy':
                today_price = float(pdf.loc[x, 'Price'])
                try:
                    nextday_price = float(pdf.loc[x + 1, 'Price'])

                    if nextday_price > today_price:
                        occurance1 += 1
                except Exception as e:
                    print(e)
                    pass
        if occurance1 > 0:
            pcent = ((occurance1 / len(pdf)) * 100)
            percent1 = float("{:.2f}".format(pcent))
            cmp_data = {"ticker": ticker, "price": price, "occurences": f"{occurance1} / {(len(pdf) - 1)}",
                        "percentage": percent1}
            wstdf = wstdf.append(cmp_data, ignore_index=True)
    print(wstdf, 'wstrong')

    # For Wallstreet Buy
    wbuydf = pd.DataFrame()
    print(wbuydf, '<------wbuydf')
    if pdf.shape:
        ticker = ''
        price = ''
        occurance2 = 0
        for x in range(len(pdf)):
            ticker = pdf.loc[0, 'Ticker']
            price = pdf.loc[pdf.index[-1], 'Price']
            if pdf.loc[x, 'Consensus'] == 'Buy':
                today_price = float(pdf.loc[x, 'Price'])
                try:
                    nextday_price = float(pdf.loc[x + 1, 'Price'])

                    if nextday_price >= today_price:
                        occurance2 += 1
                except Exception as e:
                    print(e)
                    pass
        if occurance2 > 0:
            pcent = ((occurance2 / len(pdf)) * 100)
            percent2 = float("{:.2f}".format(pcent))
            cmp_data = {"ticker": ticker, "price": price, "occurences": f"{occurance2} / {(len(pdf) - 1)}",
                        "percentage": percent2}
            wbuydf = wbuydf.append(cmp_data, ignore_index=True)
    print(wbuydf, 'wbuydf')

    # For Wallstreet Hold
    wholddf = pd.DataFrame()
    print(wholddf, '<---wholdf')
    if pdf.shape:
        ticker = ''
        price = ''
        occurance3 = 0
        for x in range(len(pdf)):
            ticker = pdf.loc[0, 'Ticker']
            price = pdf.loc[pdf.index[-1], 'Price']
            if pdf.loc[x, 'Consensus'] == 'Hold':
                today_price = float(pdf.loc[x, 'Price'])
                try:
                    nextday_price = float(pdf.loc[x + 1, 'Price'])

                    if nextday_price <= today_price:
                        occurance3 += 1
                except Exception as e:
                    print(e)
                    pass
        if occurance3 > 0:
            pcent = ((occurance3 / len(pdf)) * 100)
            percent3 = float("{:.2f}".format(pcent))
            cmp_data = {"ticker": ticker, "price": price, "occurences": f"{occurance3} / {(len(pdf) - 1)}",
                        "percentage": percent3}
            wholddf = wholddf.append(cmp_data, ignore_index=True)
    print(wholddf, 'wholddf')

    # for wallstreetzen sell
    wdf_sell = pd.DataFrame()
    print(wdf_sell, '<-----wdf_sell')
    if pdf.shape:
        ticker = ''
        price = ''
        occurance4 = 0
        for x in range(len(pdf)):
            ticker = pdf.loc[0, 'Ticker']
            price = pdf.loc[pdf.index[-1], 'Price']
            if pdf.loc[x, 'Consensus'] == 'Sell':
                today_price = float(pdf.loc[x, 'Price'])
                try:
                    nextday_price = float(pdf.loc[x + 1, 'Price'])

                    if nextday_price <= today_price:
                        occurance4 += 1
                except Exception as e:
                    print(e)
                    pass
        if occurance4 > 0:
            pcent = ((occurance4 / len(pdf)) * 100)
            # print(pcent,'percent')
            percent4 = float("{:.2f}".format(pcent))
            cmp_data1 = {"ticker": ticker, "price": price, "occurences": f"{occurance4} / {(len(pdf) - 1)}",
                         "percentage": percent4}
            wdf_sell = wdf_sell.append(cmp_data1, ignore_index=True)
    print(wdf_sell, 'sell')

    # for wallstreetzen strong sell
    wdf_stsell = pd.DataFrame()
    print(wdf_stsell, '<---wdf_stsell')
    if pdf.shape:
        ticker = ''
        price = ''
        occurance5 = 0
        for x in range(len(pdf)):
            ticker = pdf.loc[0, 'Ticker']
            price = pdf.loc[pdf.index[-1], 'Price']
            if pdf.loc[x, 'Consensus'] == 'Strong Sell':
                today_price = float(pdf.loc[x, 'Price'])
                try:
                    nextday_price = float(pdf.loc[x + 1, 'Price'])

                    if nextday_price <= today_price:
                        occurance5 += 1
                except Exception as e:
                    print(e)
                    pass
        if occurance5 > 0:
            pcent = ((occurance5 / len(pdf)) * 100)
            # print(pcent,'percent')
            percent5 = float("{:.2f}".format(pcent))
            cmp_data1 = {"ticker": ticker, "price": price, "occurences": f"{occurance5} / {(len(pdf) - 1)}",
                         "percentage": percent5}
            wdf_stsell = wdf_stsell.append(cmp_data1, ignore_index=True)
    print(wdf_stsell, 'wdf_stsell')
    # data = predictions.append({'ticker':ticker,'price':price,'occurence':[{occurance1},{occurance2},{occurance3},{occurance4},{occurance5}],'percentage':[{percent1},{percent2},{percent3},{percent4},{percent5}],'consensus':['strong buy','buy','hold','sell','strong sell',]}, ignore_index = True)
    # pred = data

    # for yahoostat strong Buy
    ydf_stbuy = pd.DataFrame()
    df2 = pd.read_sql(f"SELECT * FROM `yahoostats` WHERE ticker='{com}'", conn)
    df2['price_now'] = df2['price_now'].astype(float)
    if df2.shape:
        ticker = ''
        price = ''
        occurance2 = 0
        for x in range(len(df2)):
            if df2.loc[x, 'ratingstring'] == 'strong_buy':
                today_price = float(df2.loc[x, 'price_now'])
                try:
                    nextday_price = float(df2.loc[x + 1, 'price_now'])
                    if nextday_price > today_price:
                        occurance2 += 1
                except:
                    pass
        if occurance2 > 0:
            pcent = (occurance2 / len(df2)) * 100
            percent = float("{:.2f}".format(pcent))
            cmp_data = {"ticker": ticker, "price": price, "occurences": f"{occurance2} / {(len(df2) - 1)}",
                        "percentage": percent}
            # yahoo_pred_count.setdefault("company", []).append(cmp_data)
            ydf_stbuy = ydf_stbuy.append(cmp_data, ignore_index=True)
    print(ydf_stbuy, 'ydf strong buy')

    # for yahoostat  Buy
    ydf_buy = pd.DataFrame()
    if df2.shape:
        ticker = ''
        price = ''
        occurance2 = 0
        for x in range(len(df2)):
            if df2.loc[x, 'ratingstring'] == 'buy':
                today_price = float(df2.loc[x, 'price_now'])
                try:
                    nextday_price = float(df2.loc[x + 1, 'price_now'])
                    if nextday_price >= today_price:
                        occurance2 += 1
                except:
                    pass
        if occurance2 > 0:
            pcent = (occurance2 / len(df2)) * 100
            percent = float("{:.2f}".format(pcent))
            cmp_data = {"ticker": ticker, "price": price, "occurences": f"{occurance2} / {(len(df2) - 1)}",
                        "percentage": percent}
            # yahoo_pred_count.setdefault("company", []).append(cmp_data)
            ydf_buy = ydf_buy.append(cmp_data, ignore_index=True)
    print(ydf_buy, 'ydf_buy')

    # for yahoostat  Buy
    ydf_hold = pd.DataFrame()
    if df2.shape:
        ticker = ''
        price = ''
        occurance2 = 0
        for x in range(len(df2)):
            if df2.loc[x, 'ratingstring'] == 'hold':
                today_price = float(df2.loc[x, 'price_now'])
                try:
                    nextday_price = float(df2.loc[x + 1, 'price_now'])
                    if nextday_price >= today_price:
                        occurance2 += 1
                except:
                    pass
        if occurance2 > 0:
            pcent = (occurance2 / len(df2)) * 100
            percent = float("{:.2f}".format(pcent))
            cmp_data = {"ticker": ticker, "price": price, "occurences": f"{occurance2} / {(len(df2) - 1)}",
                        "percentage": percent}
            # yahoo_pred_count.setdefault("company", []).append(cmp_data)
            ydf_hold = ydf_hold.append(cmp_data, ignore_index=True)
    print(ydf_hold, 'ydf_hold')

    # For Stocks and their predictions Graph
    try:
        # modules = request.session['modules']
        print(pdf['Company'][0], '<------pdf')

        comp_dict = {com: pdf['Company'][0]}
        print(comp_dict, '<-------cd')
        pred_dict = {}
        for k, v in comp_dict.items():
            try:
                cur_date = datetime.now()
                presentDate = int(cur_date.timestamp())
                pastDate = int((cur_date - relativedelta(years=1)).timestamp())
                query_string = f'https://query1.finance.yahoo.com/v7/finance/download/{k}?period1={pastDate}&period2' \
                               f'={presentDate}&interval=1d&events=history&includeAdjustedClose=true'
                # ticker = yf.Ticker('HUBG')
                df = pd.read_csv(query_string)  # ticker.history(start=pastDate, end=presentDate)
                # print(df)
                df.Date = pd.to_datetime(df.Date)
                df = df.set_index('Date')
                y = df['Close'].resample('D').mean()
                y = y.fillna(method='bfill').fillna(method='ffill')
                mod = sm.tsa.statespace.SARIMAX(y, order=(1, 1, 0), seasonal_order=(1, 1, 0, 12),
                                                enforce_stationarity=False,
                                                enforce_invertibility=False)
                results = mod.fit()
                pred_uc = results.get_forecast(steps=20)
                analytics_data = pred_uc.predicted_mean
                analytics_data = analytics_data.reset_index()
                analytics_data.rename(columns={'index': 'Date', 'predicted_mean': 'Close'}, inplace=True)
                analytics_data.Date = analytics_data.Date.astype('str')
                analytics_data['color'] = "#b3005e"
                df = df.reset_index()
                df.Date = df.Date.astype('str')
                df = df.iloc[-100:len(df)]
                df['color'] = "#00235B"

                pred_dict[v] = {"predicted": analytics_data.to_dict(orient="list"), "actual": df.to_dict(orient="list")}
                predicts = analytics_data.to_dict(orient='list')
                actual = df.to_dict(orient='list')
                pdate = predicts['Date']
                pclose = predicts['Close']
                pcolor = predicts['color']
                adate = actual['Date']
                aclose = actual['Close']
                acolor = actual['color']
                labels = adate + pdate
                data = aclose + pclose
                colors = acolor + pcolor
                print(labels, '<-labels')




            except Exception as e:
                print(e)
                print("Ticker: " + k)

        # 2nd Graph
        # modules = request.session['modules']
        # print(pdf['Company'][0],'<------pdf')

        comp_dict = {com: pdf['Company'][0]}
        print(comp_dict, '<-------cd')
        pred_dict1 = {}
        for k, v in comp_dict.items():
            try:
                cur_date = datetime.now()
                presentDate = int(cur_date.timestamp())

                pastDate = int((cur_date - relativedelta(days=30)).timestamp())
                query_string = f'https://query1.finance.yahoo.com/v7/finance/download/{k}?period1={pastDate}&period2' \
                               f'={presentDate}&interval=1d&events=history&includeAdjustedClose=true'
                # ticker = yf.Ticker('HUBG')
                df = pd.read_csv(query_string)  # ticker.history(start=pastDate, end=presentDate)
                # print(df)
                df.Date = pd.to_datetime(df.Date)
                df = df.set_index('Date')
                y = df['Close'].resample('D').mean()
                y = y.fillna(method='bfill').fillna(method='ffill')
                mod = sm.tsa.statespace.SARIMAX(y, order=(1, 1, 0), seasonal_order=(1, 1, 0, 12),
                                                enforce_stationarity=False,
                                                enforce_invertibility=False)
                results = mod.fit()
                # pred_uc = results.get_forecast(steps=20)
                # analytics_data = pred_uc.predicted_mean
                # analytics_data = analytics_data.reset_index()
                # analytics_data.rename(columns={'index': 'Date', 'predicted_mean': 'Close'}, inplace=True)
                # analytics_data.Date = analytics_data.Date.astype('str')
                # analytics_data['color'] = "#1cc88a"
                df = df.reset_index()
                df.Date = df.Date.astype('str')
                df = df.iloc[-100:len(df)]
                df['color'] = "#4875aa"

                old_date = datetime.now() - timedelta(days=30)
                print(old_date, 'old_date')
                olderDate1 = int(old_date.timestamp())
                print(olderDate1, 'olderDate1')

                pastDate1 = int((old_date - relativedelta(days=90)).timestamp())

                print(pastDate1, 'pastdate1')
                query_string1 = f'https://query1.finance.yahoo.com/v7/finance/download/{k}?period1={pastDate1}&period2' \
                                f'={olderDate1}&interval=1d&events=history&includeAdjustedClose=true'
                # ticker = yf.Ticker('HUBG')
                df1 = pd.read_csv(query_string1)  # ticker.history(start=pastDate, end=presentDate)
                # print(df)
                df1.Date = pd.to_datetime(df1.Date)
                df1 = df1.set_index('Date')
                y1 = df1['Close'].resample('D').mean()
                y1 = y1.fillna(method='bfill').fillna(method='ffill')
                mod1 = sm.tsa.statespace.SARIMAX(y1, order=(1, 1, 0), seasonal_order=(1, 1, 0, 12),
                                                 enforce_stationarity=False,
                                                 enforce_invertibility=False)
                results = mod1.fit()
                pred_uc = results.get_forecast(steps=30)
                analytics_data = pred_uc.predicted_mean
                analytics_data = analytics_data.reset_index()
                analytics_data.rename(columns={'index': 'Date', 'predicted_mean': 'Close'}, inplace=True)
                analytics_data.Date = analytics_data.Date.astype('str')
                analytics_data['color'] = "#c0504e"
                # df = df.reset_index()
                # df.Date = df.Date.astype('str')
                # df = df.iloc[-100:len(df)]
                # df['color'] = "green"
                pred_dict1[v] = {"actual": df.to_dict(orient="list"),
                                 "predicted": analytics_data.to_dict(orient="list")}
                predicts1 = analytics_data.to_dict(orient='list')
                actual1 = df.to_dict(orient='list')
                pdate1 = predicts1['Date']
                print(pdate1, '<---pdt1')
                pclose1 = predicts1['Close']
                aclose1 = actual1['Close']
                adate1 = actual1['Date']
                print(adate1, '<---adate1')

            except Exception as e:
                print(e)
                print("Ticker: " + k)

        form = {'labels': pdate1, 'data': pclose1, 'colors': colors, 'labels1': adate1, 'data1': aclose1,
                'pred_dict': pred_dict, 'pred_dict1': pred_dict1, 'com': com, 'wstdf': wstdf, 'wbuydf': wbuydf,
                'wholddf': wholddf, 'wdfsell': wdf_sell, 'news': news,
                'wdfstsell': wdf_stsell, 'ydf_stbuy': ydf_stbuy, 'ydf_buy': ydf_buy, 'ydf_hold': ydf_hold, 'pdf': pdf}
    except Exception as e:
        print(e)
        form = {'msg': "Something went wrong, contact administrator"}
    return render(request, 'graph.html', form)


def user_settings(request):
    conn = connection()
    if 'user_id' not in request.session:
        return render(request, 'login.html', {'mssg': 'Please Login..!!'})
    else:
        id = request.session['user_id']
        # print(user_id,'<-------------uidd')
        query = pd.read_sql(f"SELECT * FROM users WHERE ID = {id}", conn)
        print(query, ",=========Qa")
        return render(request, 'user_settings.html', {'query': query, 'user_id': id})


def usersedit(request):
    conn = connection()
    id = request.session['user_id']
    uname = request.POST.dict().get('uname')
    fname = request.POST.dict().get('fname')
    lname = request.POST.dict().get('lname')
    email = request.POST.dict().get('email')
    print(id, uname, fname, lname, email)

    try:
        conn.execute(
            f"UPDATE users SET username = '{uname}',firstname = '{fname}',lastname = '{lname}',email = '{email}' WHERE ID = {id}")
        conn.dispose()
        msg = 'Updated successfully'

    except exc.SQLAlchemyError as e:
        print(e)
        msg = 'Unsuccesful'
    return HttpResponse(msg)


def changepw(request):
    conn = connection()
    id = request.session['user_id']
    npassword = request.POST.dict().get('cpassword')
    cpassword = request.POST.dict().get('npassword')
    if npassword == cpassword and len(cpassword) >= 8:
        encpw = hashlib.sha256(cpassword.encode()).hexdigest()
        conn.execute(f"UPDATE users set password = '{encpw}' WHERE ID = {id}")
        conn.dispose()
    else:
        # print("Please insert valid password..!!")
        msg = "Please insert valid password"
        return JsonResponse({'msg': msg})


def adminpanel(request):
    if 'user_id' not in request.session:
        return render(request, 'login.html', {"mssg": "Please login...!"})
    else:
        user_id = request.session['user_id']
        conn = connection()
        user = pd.read_sql(f'SELECT * From users', conn)

        return render(request, 'adminpanel.html', {'user': user, 'user_id': user_id})


def saveuser(request):
    conn = connection()
    username = request.POST.dict().get('username')
    firstname = request.POST.dict().get('firstname')
    lastname = request.POST.dict().get('lastname')
    modules = request.POST.getlist('modules')
    modules = ", ".join(modules)
    # print(modules, '<---------------------modules')
    password = request.POST.dict().get('password')
    encpw = hashlib.sha256(password.encode()).hexdigest()

    conn.execute(f"INSERT INTO users (username,firstname,lastname,password,modules) "
                 f"VALUES ('{username}','{firstname}','{lastname}','{encpw}','{modules}')")
    conn.dispose()
    # msg = 'Successful'

    return redirect('adminpanel')


def useredit(request):
    conn = connection()
    username = request.POST.dict().get('username')
    firstname = request.POST.dict().get('firstname')
    lastname = request.POST.dict().get('lastname')
    password = request.POST.dict().get('password')
    encpw = hashlib.sha256(password.encode()).hexdigest()
    modules = request.POST.getlist('modules')
    modules = ", ".join(modules)
    userid = request.POST.dict().get('userid')

    try:
        conn.execute(f"UPDATE users SET username = '{username}', firstname = '{firstname}', lastname='{lastname}',"
                     f"password = '{encpw}', modules = '{modules}' WHERE id = {userid}")
        conn.dispose()
        msg = 'Successful'
    except exc.SQLAlchemyError as e:
        print(e)
        msg = 'Unsuccessful'

    return HttpResponse(msg)


def delete_user(request, id):
    conn = connection()
    try:
        conn.execute(f"DELETE FROM users WHERE id = {id}")
        conn.dispose()
        msg = "Successful"
    except exc.SQLAlchemyError as e:
        print(e)
        msg = "Unsuccessful"

    return HttpResponse(msg)


def get_user(request):
    conn = connection()
    # company_id = request.POST.dict().get('company_id')
    # user_id = request.session['user_id']
    user = pd.read_sql(f"SELECT * FROM users", conn)
    user['Action'] = user['ID'].apply(
        lambda x: f'<button class="btn btn-success" onclick="edit_user({x})"><i class="fa fa-edit" '
                  f'aria-hidden="true" style="color:white"></i></button>&#8195;<button class="btn btn-danger" id="{x}" onclick="delete_row({x})" ><i class="fa fa-trash" '
                  f'aria-hidden="true" style="color:white"></i></button>')
    print(user['Action'])
    del user['ID']
    del user['password']
    del user['created_date']
    del user['email']
    user = user.style.set_table_attributes("class='table table-hover tableoption'").hide_index().render()

    return HttpResponse(user)


def customer(request):
    conn = connection()
    data = pd.read_sql(f'''SELECT * FROM salesorders s INNER JOIN customer c ON s.customer_id=c.ID INNER JOIN
                        orderedunits o ON s.ID=o.order_id INNER JOIN products p ON o.unit_id=p.ID INNER JOIN 
                        inventory i ON p.ID=i.inventoryTypeID INNER JOIN warehouse w ON i.warehouseTableID=w.ID''',
                       conn)

    var = pd.DataFrame(data)
    dat = {'order_id': [], 'CustomerName': [], 'Product': [], 'OrderDate': [], 'DeliveryDate': [],
           'value': [], 'status': [], 'risk_score': []}
    for a in range(len(var)):
        ounit = var["No_of_units"].iloc[a]
        iunit = var["inventoryCount"].iloc[a]
        if ounit > iunit:
            oid = var['order_id'].iloc[a]
            cname = var['CustomerName'].iloc[a]
            pname = var['Product'].iloc[a]
            odate = var['OrderDate'].iloc[a]
            ddate = var['DeliveryDate'].iloc[a]
            val = var['value'].iloc[a]
            st = var['status'].iloc[a]

            rst = (iunit / ounit) * 100
            rs = float("{:.2f}".format(rst))

            dat['order_id'].append(oid)
            dat['CustomerName'].append(cname)
            dat['Product'].append(pname)
            dat['OrderDate'].append(odate)
            dat['DeliveryDate'].append(ddate)
            dat['value'].append(val)
            dat['status'].append(st)
            dat['risk_score'].append(rs)

    back = pd.DataFrame.from_dict(dat)

    return render(request, 'customer.html', {'data': data, 'var': back})


def pdf(request):
    if 'pdf_data' in request.FILES:
        pdffile = request.FILES['pdf_data']
        user_id = request.session['user_id']
        pdfext = request.FILES['pdf_data'].name.split('.')[1]
        pdfname = f'commodity_app/static/ocrimg/{user_id}.{pdfext}'
        if os.path.exists(pdfname):
            os.remove(pdfname)
        default_storage.save(pdfname, pdffile)
        # symbol = '$'
        # word = 'copay'
        with open(pdfname, 'rb') as pdf_file:
            pop = extract_text(pdf_file, laparams=LAParams())
            pattern = r"\$([0-9]+(?:\.[0-9]+)?) copay"
            matches = re.findall(pattern, pop)
            data = pd.DataFrame()
            if matches:
                for match in matches:
                    copayment = float(match)
                    if copayment > 0:
                        # pt2 = r"\$" + match + r" copayment\s*(.?)(?=\s[A-Z]|$)"
                        pt2 = r"\$" + match + r" copayment\s*(.*?)(?=2023 Evidence of Coverage|$)"
                        paragraphs = re.findall(pt2, pop, flags=re.DOTALL)
                        if paragraphs:
                            for paragraph in paragraphs:
                                title = "$" + str(copayment) + " copayment"
                                para = paragraph.strip()
                                if title and para:
                                    data = data.append({'title': title, 'paragraph': title+' '+ para}, ignore_index=True)
                # data['paragraph'] = data['paragraph'].str.split()
                # data['paragraph'] = [line for line in data['paragraph'] if line.str.strip()]
                # data['paragraph'] = data['paragraph'].dropna(how='all', inplace=True)
                print(data['paragraph'][0])
                return HttpResponse(
                    data.to_html(index=False, classes="table table-hover table-bordered table-responsive mt-3",
                                 border=0))

            #             else:
            #                 print("No paragraphs found for $" + str(copayment) + " copayment.")
            #     print(data)
            # else:
            #     print("No copayments found in the text.")

            return render(request, 'ocr.html')

