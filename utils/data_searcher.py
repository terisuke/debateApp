from typing import Dict, List
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from newsapi.newsapi_client import NewsApiClient
from datetime import datetime, timedelta

class DataSearcher:
    def __init__(self, news_api_key: str):
        self.news_api = NewsApiClient(api_key=news_api_key)
    
    def search_news(self, query: str, days: int = 7) -> List[Dict]:
        """ニュース記事を検索"""
        from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        news = self.news_api.get_everything(
            q=query,
            language=None,
            sort_by='relevancy',
            from_param=from_date
        )
        return news['articles']

    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        """株価データを取得"""
        stock = yf.Ticker(symbol)
        return stock.history(period="1mo")

    def scrape_web_data(self, url: str) -> str:
        """Webページからデータをスクレイピング"""
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
