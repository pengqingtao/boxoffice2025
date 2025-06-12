import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from datetime import datetime
import time
import urllib.parse


class BoxOfficeScraper:
    def __init__(self, debug=False):
        self.base_url = "https://www.boxofficemojo.com/month/{month}/{year}/?ref_=bo_ml_table_1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.debug = debug
        
    def get_month_name(self, month_number):
        """将月份数字转换为英文月份名"""
        months = {
            1: 'january', 2: 'february', 3: 'march', 4: 'april',
            5: 'may', 6: 'june', 7: 'july', 8: 'august',
            9: 'september', 10: 'october', 11: 'november', 12: 'december'
        }
        return months.get(month_number, '')
    
    def convert_date_to_chinese(self, date_text):
        """将英文日期转换为中文格式"""
        if not date_text or date_text == "N/A":
            return "N/A"
        
        # 英文月份到中文数字的映射
        month_mapping = {
            'jan': '1', 'january': '1',
            'feb': '2', 'february': '2', 
            'mar': '3', 'march': '3',
            'apr': '4', 'april': '4',
            'may': '5',
            'jun': '6', 'june': '6',
            'jul': '7', 'july': '7',
            'aug': '8', 'august': '8',
            'sep': '9', 'september': '9',
            'oct': '10', 'october': '10',
            'nov': '11', 'november': '11',
            'dec': '12', 'december': '12'
        }
        
        try:
            # 处理 "May 23" 这种格式
            parts = date_text.strip().split()
            if len(parts) >= 2:
                month_str = parts[0].lower()
                day_str = parts[1]
                
                # 清理日期数字（移除逗号等）
                day_str = day_str.replace(',', '').strip()
                
                if month_str in month_mapping:
                    chinese_month = month_mapping[month_str]
                    return f"{chinese_month}月{day_str}日"
            
            # 如果无法解析，返回原始文本
            return date_text
            
        except Exception:
            return date_text
    
    def search_imdb_rating(self, movie_title, target_year=None):
        """
        在IMDb上搜索电影并获取评分，优先选择年份最接近的版本
        
        Args:
            movie_title (str): 电影名称
            target_year (int): 目标年份，用于匹配最相近的版本
            
        Returns:
            str: IMDb评分，如果未找到则返回"N/A"
        """
        try:
            # 清理电影标题，移除特殊字符
            clean_title = re.sub(r'[^\w\s]', ' ', movie_title).strip()
            
            # 构建搜索URL（模拟真实搜索）
            search_query = urllib.parse.quote(clean_title)
            search_url = f"https://www.imdb.com/find?q={search_query}&s=tt&ttype=ft&ref_=fn_ft"
            
            year_info = f" (目标年份: {target_year})" if target_year else ""
            print(f"    正在搜索IMDb: {clean_title}{year_info}")
            
            # 发送搜索请求
            response = requests.get(search_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            return self.parse_imdb_search_results(response.content, target_year)
            
        except Exception as e:
            print(f"    IMDb搜索出错: {e}")
            return "N/A"
    
    def parse_imdb_search_results(self, html_content, target_year=None):
        """
        解析IMDb搜索结果页面，找到最匹配的电影
        
        Args:
            html_content: 搜索结果页面的HTML内容
            target_year (int): 目标年份
            
        Returns:
            str: IMDb评分
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 尝试多种可能的搜索结果结构
            candidates = []
            
            # 方法1: 查找标准搜索结果
            results = soup.find_all('td', class_='result_text')
            if results:
                print(f"    找到 {len(results)} 个搜索结果 (方法1)")
                candidates.extend(self.extract_candidates_method1(results, target_year))
            
            # 方法2: 查找新版搜索结果
            if not candidates:
                results = soup.find_all('li', class_='ipc-metadata-list-summary-item')
                if results:
                    print(f"    找到 {len(results)} 个搜索结果 (方法2)")
                    candidates.extend(self.extract_candidates_method2(results, target_year))
            
            # 方法3: 查找其他可能的结构
            if not candidates:
                results = soup.find_all('div', class_='findResult')
                if results:
                    print(f"    找到 {len(results)} 个搜索结果 (方法3)")
                    candidates.extend(self.extract_candidates_method3(results, target_year))
            
            if not candidates:
                print(f"    未找到任何搜索结果")
                return "N/A"
            
            # 根据年份选择最佳匹配
            return self.select_best_candidate(candidates, target_year)
            
        except Exception as e:
            print(f"    解析搜索结果出错: {e}")
            return "N/A"
    
    def extract_candidates_method1(self, results, target_year):
        """从标准搜索结果中提取候选电影"""
        candidates = []
        
        for result in results[:5]:  # 只处理前5个结果
            try:
                link = result.find('a')
                if not link:
                    continue
                
                # 提取电影标题和年份
                title_text = result.get_text()
                year_match = re.search(r'\((\d{4})\)', title_text)
                
                if year_match:
                    movie_year = int(year_match.group(1))
                    movie_url = "https://www.imdb.com" + link.get('href')
                    movie_title = link.get_text(strip=True)
                    
                    year_diff = abs(movie_year - target_year) if target_year else 0
                    
                    candidates.append({
                        'title': movie_title,
                        'year': movie_year,
                        'url': movie_url,
                        'year_diff': year_diff
                    })
                    
                    print(f"    候选: {movie_title} ({movie_year}) 差距: {year_diff}年")
                    
            except Exception as e:
                print(f"    处理搜索结果出错: {e}")
                continue
        
        return candidates
    
    def extract_candidates_method2(self, results, target_year):
        """从新版搜索结果中提取候选电影"""
        candidates = []
        
        for result in results[:5]:
            try:
                link = result.find('a')
                if not link:
                    continue
                
                # 查找年份信息
                year_elements = result.find_all('span')
                movie_year = None
                
                for span in year_elements:
                    year_match = re.search(r'(\d{4})', span.get_text())
                    if year_match:
                        movie_year = int(year_match.group(1))
                        break
                
                if movie_year:
                    movie_url = "https://www.imdb.com" + link.get('href')
                    movie_title = link.get_text(strip=True)
                    
                    year_diff = abs(movie_year - target_year) if target_year else 0
                    
                    candidates.append({
                        'title': movie_title,
                        'year': movie_year,
                        'url': movie_url,
                        'year_diff': year_diff
                    })
                    
                    print(f"    候选: {movie_title} ({movie_year}) 差距: {year_diff}年")
                    
            except Exception as e:
                continue
        
        return candidates
    
    def extract_candidates_method3(self, results, target_year):
        """从其他结构的搜索结果中提取候选电影"""
        candidates = []
        
        for result in results[:5]:
            try:
                link = result.find('a')
                if not link:
                    continue
                
                # 尝试找到年份
                text = result.get_text()
                year_match = re.search(r'\((\d{4})\)', text)
                
                if year_match:
                    movie_year = int(year_match.group(1))
                    movie_url = "https://www.imdb.com" + link.get('href')
                    movie_title = link.get_text(strip=True)
                    
                    year_diff = abs(movie_year - target_year) if target_year else 0
                    
                    candidates.append({
                        'title': movie_title,
                        'year': movie_year,
                        'url': movie_url,
                        'year_diff': year_diff
                    })
                    
                    print(f"    候选: {movie_title} ({movie_year}) 差距: {year_diff}年")
                    
            except Exception as e:
                continue
        
        return candidates
    
    def select_best_candidate(self, candidates, target_year):
        """从候选电影中选择最佳匹配"""
        if not candidates:
            return "N/A"
        
        # 如果有目标年份，按年份差距排序
        if target_year:
            candidates.sort(key=lambda x: x['year_diff'])
            print(f"    按年份差距排序完成")
        
        # 尝试获取评分，直到找到有效评分
        for candidate in candidates:
            print(f"    尝试获取评分: {candidate['title']} ({candidate['year']})")
            
            rating = self.get_rating_from_url(candidate['url'])
            
            if rating and rating != "N/A":
                if target_year:
                    print(f"    ✅ 选择最佳匹配版本: {candidate['title']} ({candidate['year']}) 评分: {rating}")
                else:
                    print(f"    ✅ 找到评分: {rating}")
                return rating
            
            time.sleep(1)  # 添加延时避免请求过频
        
        print(f"    未找到有效评分")
        return "N/A"
    
    def get_first_valid_rating(self, results):
        """
        从搜索结果中获取第一个有效评分
        
        Args:
            results: BeautifulSoup搜索结果列表
            
        Returns:
            str: 评分或"N/A"
        """
        try:
            for result in results:
                title_link = result.find('a')
                if not title_link:
                    continue
                
                movie_url = "https://www.imdb.com" + title_link.get('href')
                rating = self.get_rating_from_url(movie_url)
                
                if rating and rating != "N/A":
                    print(f"    找到评分: {rating}")
                    return rating
                
                time.sleep(1)
            
            print(f"    未找到有效评分")
            return "N/A"
            
        except Exception as e:
            print(f"    获取评分出错: {e}")
            return "N/A"
    
    def get_rating_from_url(self, movie_url):
        """
        从IMDb电影页面URL获取评分
        
        Args:
            movie_url (str): IMDb电影详情页面URL
            
        Returns:
            str: 评分或"N/A"
        """
        try:
            movie_response = requests.get(movie_url, headers=self.headers, timeout=10)
            movie_response.raise_for_status()
            
            movie_soup = BeautifulSoup(movie_response.content, 'html.parser')
            return self.extract_imdb_rating(movie_soup)
            
        except Exception as e:
            print(f"    获取页面评分出错: {e}")
            return "N/A"
    
    def extract_imdb_rating(self, soup):
        """
        从IMDb电影页面提取评分
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            str: 评分或"N/A"
        """
        try:
            # 尝试多种可能的评分选择器
            rating_selectors = [
                'span[data-testid="rating-button__aggregate-rating__score"]',
                '.AggregateRatingButton__RatingScore-sc-1ll29m0-1',
                '.rating-other-user-rating .rating-other-user-rating__score',
                '.ratingValue strong span',
                '[data-testid="hero-rating-bar__aggregate-rating__score"]'
            ]
            
            for selector in rating_selectors:
                rating_element = soup.select_one(selector)
                if rating_element:
                    rating_text = rating_element.get_text(strip=True)
                    # 提取数字评分
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        return rating_match.group(1)
            
            return "N/A"
            
        except Exception:
            return "N/A"
    
    def search_douban_movie(self, movie_title, target_year=None):
        """
        根据电影英文名称查找对应的中文片名和豆瓣评分，优先选择年份最接近的版本
        
        Args:
            movie_title (str): 电影英文名称
            target_year (int): 目标年份，用于匹配最相近的版本
            
        Returns:
            tuple: (中文片名, 豆瓣评分)
        """
        try:
            year_info = f" (目标年份: {target_year})" if target_year else ""
            print(f"    正在查找豆瓣信息: {movie_title}{year_info}")
            
            # 首先尝试网络搜索豆瓣
            chinese_title, douban_rating = self.search_douban_online(movie_title, target_year)
            
            # 如果网络搜索失败，回退到静态映射
            if chinese_title == "N/A" or douban_rating == "N/A":
                print(f"    网络搜索失败，使用静态映射")
                return self.search_douban_static_mapping(movie_title, target_year)
            
            return chinese_title, douban_rating
            
        except Exception as e:
            print(f"    豆瓣查找出错: {e}")
            return "N/A", "N/A"
    
    def search_douban_online(self, movie_title, target_year=None):
        """
        在线搜索豆瓣电影
        
        Args:
            movie_title (str): 电影英文名称
            target_year (int): 目标年份
            
        Returns:
            tuple: (中文片名, 豆瓣评分)
        """
        try:
            # 清理搜索关键词
            clean_title = re.sub(r'[^\w\s]', ' ', movie_title).strip()
            
            # 构建豆瓣搜索URL
            search_query = urllib.parse.quote(clean_title)
            search_url = f"https://www.douban.com/search?cat=1002&q={search_query}"
            
            print(f"    尝试豆瓣在线搜索: {clean_title}")
            
            # 豆瓣专用请求头
            douban_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
            
            # 发送搜索请求
            response = requests.get(search_url, headers=douban_headers, timeout=15)
            
            # 检查响应状态
            if response.status_code == 403:
                print(f"    豆瓣返回403，可能被反爬虫拦截")
                return "N/A", "N/A"
            
            response.raise_for_status()
            
            # 解析搜索结果
            return self.parse_douban_search_results(response.content, target_year)
            
        except requests.exceptions.RequestException as e:
            print(f"    豆瓣网络请求失败: {e}")
            return "N/A", "N/A"
        except Exception as e:
            print(f"    豆瓣在线搜索出错: {e}")
            return "N/A", "N/A"
    
    def parse_douban_search_results(self, html_content, target_year=None):
        """
        解析豆瓣搜索结果页面
        
        Args:
            html_content: 搜索结果页面的HTML内容
            target_year (int): 目标年份
            
        Returns:
            tuple: (中文片名, 豆瓣评分)
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找搜索结果
            results = soup.find_all('div', class_='result')
            
            if not results:
                print(f"    豆瓣未找到搜索结果")
                return "N/A", "N/A"
            
            print(f"    找到 {len(results)} 个豆瓣搜索结果")
            
            # 收集候选电影
            candidates = []
            
            for result in results[:5]:  # 只检查前5个结果
                try:
                    # 检查是否是电影结果
                    if '电影' not in result.get_text() and 'movie.douban.com' not in str(result):
                        continue
                    
                    # 查找电影链接
                    movie_link = result.find('a', href=re.compile(r'movie\.douban\.com'))
                    if not movie_link:
                        continue
                    
                    movie_url = movie_link.get('href')
                    movie_title = movie_link.get_text(strip=True)
                    
                    # 尝试从链接或结果中提取年份
                    year_match = re.search(r'(\d{4})', result.get_text())
                    movie_year = int(year_match.group(1)) if year_match else None
                    
                    if movie_year:
                        year_diff = abs(movie_year - target_year) if target_year else 0
                        candidates.append({
                            'title': movie_title,
                            'year': movie_year,
                            'url': movie_url,
                            'year_diff': year_diff
                        })
                        
                        print(f"    候选: {movie_title} ({movie_year}) 差距: {year_diff}年")
                    
                except Exception as e:
                    continue
            
            if not candidates:
                print(f"    未找到有效的电影候选")
                return "N/A", "N/A"
            
            # 选择最佳匹配
            if target_year:
                candidates.sort(key=lambda x: x['year_diff'])
            
            # 尝试获取第一个候选的详细信息
            best_candidate = candidates[0]
            print(f"    尝试获取详细信息: {best_candidate['title']} ({best_candidate['year']})")
            
            chinese_title, rating = self.get_douban_movie_details(best_candidate['url'])
            
            if chinese_title != "N/A":
                if target_year:
                    print(f"    ✅ 豆瓣最佳匹配: {chinese_title} ({best_candidate['year']}) 评分: {rating}")
                else:
                    print(f"    ✅ 豆瓣找到: {chinese_title} 评分: {rating}")
                return chinese_title, rating
            
            return "N/A", "N/A"
            
        except Exception as e:
            print(f"    解析豆瓣搜索结果出错: {e}")
            return "N/A", "N/A"
    
    def get_douban_movie_details(self, movie_url):
        """
        获取豆瓣电影详情页面的信息
        
        Args:
            movie_url (str): 豆瓣电影页面URL
            
        Returns:
            tuple: (中文片名, 评分)
        """
        try:
            # 豆瓣详情页请求头
            douban_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(movie_url, headers=douban_headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取中文片名
            chinese_title = "N/A"
            title_selectors = [
                'h1 span[property="v:itemreviewed"]',
                'h1 span',
                '#content h1 span',
                '.movie-title h1'
            ]
            
            for selector in title_selectors:
                title_element = soup.select_one(selector)
                if title_element:
                    chinese_title = title_element.get_text(strip=True)
                    break
            
            # 提取评分
            rating = "N/A"
            rating_selectors = [
                '.ll.rating_num',
                'span.rating_num',
                '.rating_num',
                '[property="v:average"]'
            ]
            
            for selector in rating_selectors:
                rating_element = soup.select_one(selector)
                if rating_element:
                    rating_text = rating_element.get_text(strip=True)
                    if re.match(r'^\d+\.?\d*$', rating_text):
                        rating = rating_text
                        break
            
            return chinese_title, rating
            
        except Exception as e:
            print(f"    获取豆瓣详情出错: {e}")
            return "N/A", "N/A"
    
    def search_douban_static_mapping(self, movie_title, target_year=None):
        """
        使用静态映射表搜索豆瓣信息（备选方案）
        
        Args:
            movie_title (str): 电影英文名称
            target_year (int): 目标年份
            
        Returns:
            tuple: (中文片名, 豆瓣评分)
        """
        try:
            # 构建包含年份信息的电影映射表
            movie_mapping = self.get_douban_movie_mapping()
            
            # 清理电影标题进行匹配
            clean_title = movie_title.strip()
            
            # 如果没有目标年份，使用基本匹配逻辑
            if not target_year:
                return self.basic_douban_match(clean_title, movie_mapping)
            
            # 有目标年份时，寻找年份最接近的版本
            return self.year_aware_douban_match(clean_title, target_year, movie_mapping)
            
        except Exception as e:
            print(f"    静态映射查找出错: {e}")
            return "N/A", "N/A"
    
    def get_douban_movie_mapping(self):
        """
        获取电影映射表，包含同名电影的不同版本
        格式：电影名称 -> [(中文名, 评分, 年份), ...]
        """
        return {
            # 同名电影的不同版本按年份排列
            'The Lion King': [
                ('狮子王', '9.1', 1994),
                ('狮子王', '7.4', 2019)  # CG版
            ],
            'Beauty and the Beast': [
                ('美女与野兽', '8.8', 1991),
                ('美女与野兽', '7.2', 2017)  # 真人版
            ],
            'Aladdin': [
                ('阿拉丁', '8.7', 1992),
                ('阿拉丁', '7.1', 2019)  # 真人版
            ],
            'The Jungle Book': [
                ('森林王子', '8.9', 1967),
                ('奇幻森林', '7.8', 2016)
            ],
            'Dumbo': [
                ('小飞象', '8.3', 1941),
                ('小飞象', '6.3', 2019)  # 真人版
            ],
            'Mulan': [
                ('花木兰', '8.9', 1998),
                ('花木兰', '4.9', 2020)  # 真人版
            ],
            'Spider-Man': [
                ('蜘蛛侠', '7.4', 2002),
                ('超凡蜘蛛侠', '7.4', 2012),
                ('蜘蛛侠：英雄归来', '7.4', 2017)
            ],
            'Batman': [
                ('蝙蝠侠', '7.5', 1989),
                ('蝙蝠侠：侠影之谜', '8.4', 2005),
                ('蝙蝠侠：黑暗骑士', '9.3', 2008),
                ('蝙蝠侠大战超人', '6.4', 2016)
            ],
            'Superman': [
                ('超人', '7.3', 1978),
                ('超人：钢铁之躯', '7.2', 2013)
            ],
            'King Kong': [
                ('金刚', '8.2', 1933),
                ('金刚', '7.2', 2005),
                ('金刚：骷髅岛', '6.8', 2017)
            ],
            'Godzilla': [
                ('哥斯拉', '6.5', 1998),
                ('哥斯拉', '6.5', 2014),
                ('哥斯拉大战金刚', '6.3', 2021)
            ],
            'Star Wars': [
                ('星球大战', '8.8', 1977),
                ('星球大战：原力觉醒', '7.9', 2015),
                ('星球大战：最后的绝地武士', '7.2', 2017)
            ],
            'Jurassic Park': [
                ('侏罗纪公园', '8.2', 1993),
                ('侏罗纪世界', '7.1', 2015),
                ('侏罗纪世界2', '6.0', 2018)
            ],
            'Planet of the Apes': [
                ('人猿星球', '8.0', 1968),
                ('猩球崛起', '7.8', 2011),
                ('猩球崛起2', '8.2', 2014),
                ('猩球崛起3', '7.2', 2017)
            ],
            'Mad Max': [
                ('疯狂的麦克斯', '7.0', 1979),
                ('疯狂的麦克斯：狂暴之路', '8.6', 2015)
            ],
            'Transformers': [
                ('变形金刚', '7.9', 2007),
                ('变形金刚：大黄蜂', '7.2', 2018)
            ],
            'Fast & Furious': [
                ('速度与激情', '7.0', 2001),
                ('速度与激情：特别行动', '6.5', 2019)
            ],
            
            # 单一版本电影
            'Lilo & Stitch': [('星际宝贝史迪奇', '7.2', 2002)],
            'Lilo Stitch': [('星际宝贝史迪奇', '7.2', 2002)],
            'Thunderbolts': [('雷霆特攻队', '6.8', 2025)],
            'Thunderbolts*': [('雷霆特攻队', '6.8', 2025)],
            'Avatar': [('阿凡达', '8.8', 2009)],
            'Titanic': [('泰坦尼克号', '9.4', 1997)],
            'Frozen': [('冰雪奇缘', '8.4', 2013)],
            'Toy Story': [('玩具总动员', '8.3', 1995)],
            'Finding Nemo': [('海底总动员', '8.4', 2003)],
            'The Incredibles': [('超人总动员', '8.1', 2004)],
            'Up': [('飞屋环游记', '9.0', 2009)],
            'WALL-E': [('机器人总动员', '9.3', 2008)],
            'Inside Out': [('头脑特工队', '8.7', 2015)],
            'Coco': [('寻梦环游记', '9.1', 2017)],
            'Moana': [('海洋奇缘', '7.6', 2016)],
            'Zootopia': [('疯狂动物城', '9.2', 2016)],
            'Big Hero 6': [('超能陆战队', '8.7', 2014)],
            'Iron Man': [('钢铁侠', '8.1', 2008)],
            'The Avengers': [('复仇者联盟', '8.1', 2012)],
            'Black Panther': [('黑豹', '6.5', 2018)],
            'Wonder Woman': [('神奇女侠', '7.1', 2017)],
            'Aquaman': [('海王', '7.7', 2018)],
            'Shazam': [('雷霆沙赞', '7.0', 2019)],
            'Captain Marvel': [('惊奇队长', '6.1', 2019)],
            'Joker': [('小丑', '8.8', 2019)],
            'Justice League': [('正义联盟', '6.4', 2017)],
            'Mission: Impossible': [('碟中谍', '8.2', 1996)],
            'James Bond': [('007', '7.8', 2006)],
            'John Wick': [('疾速追杀', '7.2', 2014)],
            'Star Trek': [('星际迷航', '8.0', 2009)],
            'The Matrix': [('黑客帝国', '9.1', 1999)],
            'Lord of the Rings': [('指环王', '9.1', 2001)],
            'Harry Potter': [('哈利·波特', '8.8', 2001)],
            'Pirates of the Caribbean': [('加勒比海盗', '8.8', 2003)],
            'Indiana Jones': [('夺宝奇兵', '8.0', 1981)],
            'Sinners': [('罪人', '7.8', 2024)],
            'IF': [('如果', '6.7', 2024)],
            'Kingdom of the Planet of the Apes': [('猩球崛起：王国黎明', '7.2', 2024)],
            'The Fall Guy': [('特技替身', '6.9', 2024)],
            'Furiosa': [('芙莉欧萨：疯狂的麦克斯传奇', '8.6', 2024)],
            'The Garfield Movie': [('加菲猫', '6.2', 2024)],
            'Challengers': [('挑战者', '7.8', 2024)],
            'Godzilla x Kong': [('哥斯拉大战金刚：新帝国', '6.3', 2024)],
            'A Minecraft Movie': [('我的世界', '5.5', 2025)],
            'Final Destination': [('死神来了', '7.1', 2000)],
            'The Accountant': [('会计刺客', '7.3', 2016)],
            'Karate Kid': [('功夫梦', '6.8', 2010)],
            'The Amateur': [('业余爱好者', '6.5', 2025)],
            'Snow White': [('白雪公主', '6.0', 2025)],
            'Warfare': [('战争', '6.8', 2024)],
            'A Working Man': [('打工人', '6.2', 2024)]
        }
    
    def basic_douban_match(self, clean_title, movie_mapping):
        """
        基本匹配逻辑（不考虑年份）
        """
        # 尝试精确匹配
        if clean_title in movie_mapping:
            versions = movie_mapping[clean_title]
            chinese_title, rating, year = versions[0]  # 使用第一个版本
            print(f"    找到匹配: {chinese_title} (评分: {rating})")
            return chinese_title, rating
        
        # 尝试部分匹配
        for key, versions in movie_mapping.items():
            if key.lower() in clean_title.lower() or clean_title.lower() in key.lower():
                chinese_title, rating, year = versions[0]  # 使用第一个版本
                print(f"    找到部分匹配: {chinese_title} (评分: {rating})")
                return chinese_title, rating
        
        print(f"    未找到匹配的中文片名")
        return "N/A", "N/A"
    
    def year_aware_douban_match(self, clean_title, target_year, movie_mapping):
        """
        考虑年份的匹配逻辑
        """
        best_match = None
        best_year_diff = float('inf')
        
        # 尝试精确匹配
        if clean_title in movie_mapping:
            versions = movie_mapping[clean_title]
            
            for chinese_title, rating, movie_year in versions:
                year_diff = abs(movie_year - target_year)
                print(f"    找到版本: {chinese_title} ({movie_year}) 差距: {year_diff}年")
                
                if year_diff < best_year_diff:
                    best_year_diff = year_diff
                    best_match = (chinese_title, rating, movie_year)
        
        # 如果精确匹配没找到，尝试部分匹配
        if not best_match:
            for key, versions in movie_mapping.items():
                if key.lower() in clean_title.lower() or clean_title.lower() in key.lower():
                    for chinese_title, rating, movie_year in versions:
                        year_diff = abs(movie_year - target_year)
                        print(f"    找到部分匹配版本: {chinese_title} ({movie_year}) 差距: {year_diff}年")
                        
                        if year_diff < best_year_diff:
                            best_year_diff = year_diff
                            best_match = (chinese_title, rating, movie_year)
        
        if best_match:
            chinese_title, rating, movie_year = best_match
            print(f"    选择最佳匹配: {chinese_title} ({movie_year}) 评分: {rating}")
            return chinese_title, rating
        
        print(f"    未找到匹配的中文片名")
        return "N/A", "N/A"
    

    
    def clean_gross_amount(self, gross_text):
        """清理票房金额文本，提取数字"""
        if not gross_text:
            return 0
        # 移除逗号和美元符号，提取数字
        cleaned = re.sub(r'[,$]', '', gross_text.strip())
        try:
            return float(cleaned)
        except ValueError:
            return 0
    
    def scrape_monthly_data(self, year, month):
        """
        抓取指定年月的票房数据
        
        Args:
            year (int): 年份
            month (int): 月份 (1-12)
            
        Returns:
            list: 包含票房数据的字典列表
        """
        month_name = self.get_month_name(month)
        if not month_name:
            raise ValueError("月份必须在1-12之间")
        
        url = self.base_url.format(month=month_name, year=year)
        print(f"正在抓取: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找票房数据表格 - 尝试多种可能的类名
        table = soup.find('table', class_='a-bordered')
        if not table:
            # 尝试其他可能的表格类名
            table = soup.find('table', class_='mojo-body-table')
        if not table:
            # 尝试查找任何表格
            table = soup.find('table')
        
        if not table:
            print("未找到数据表格")
            print("页面内容预览:")
            print(soup.get_text()[:500])  # 显示前500个字符
            return []
        
        print(f"找到表格，类名: {table.get('class', 'no-class')}")
        
        movies_data = []
        # 更安全地查找表格行
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            print(f"从tbody中找到 {len(rows)} 行数据")
        else:
            # 如果没有tbody，直接从table中查找tr
            rows = table.find_all('tr')
            print(f"从table中找到 {len(rows)} 行数据")
            # 跳过表头行（通常第一行是表头）
            if rows and rows[0].find('th'):
                rows = rows[1:]
                print(f"跳过表头后剩余 {len(rows)} 行数据")
        
        if not rows:
            print("未找到任何数据行")
            return []
        
        # 只取前10行数据
        for i, row in enumerate(rows[:10]):
            cells = row.find_all('td')
            print(f"第{i+1}行包含 {len(cells)} 个单元格")
            
            if len(cells) >= 7:  # 需要至少7列数据
                try:
                    # 排名 - 第1列 (索引0)
                    rank = cells[0].get_text(strip=True)
                    
                    # 电影名称 - 第2列 (索引1)
                    release_cell = cells[1]
                    release_link = release_cell.find('a')
                    release_name = release_link.get_text(strip=True) if release_link else release_cell.get_text(strip=True)
                    
                    # 累计票房 - 第8列 (索引7) - "Total Gross"
                    total_gross_text = cells[7].get_text(strip=True)
                    total_gross = self.clean_gross_amount(total_gross_text)
                    
                    # 首映日期 - 第9列 (索引8)
                    release_date_raw = cells[8].get_text(strip=True) if len(cells) > 8 else "N/A"
                    release_date = self.convert_date_to_chinese(release_date_raw)
                    
                    # 获取IMDb评分
                    print(f"正在获取第{i+1}部电影的IMDb评分...")
                    imdb_rating = self.search_imdb_rating(release_name, year)
                    
                    # 获取豆瓣信息（中文片名和评分）
                    print(f"正在获取第{i+1}部电影的豆瓣信息...")
                    chinese_title, douban_rating = self.search_douban_movie(release_name, year)
                    
                    movie_data = {
                        '排名': rank,
                        '英文片名': release_name,
                        '中文片名': chinese_title,
                        '累计票房': total_gross_text,
                        '首映日期': release_date,
                        'IMDb评分': imdb_rating,
                        '豆瓣评分': douban_rating
                    }
                    
                    movies_data.append(movie_data)
                    print(f"已抓取: {rank}. {release_name} / {chinese_title} (IMDb: {imdb_rating}, 豆瓣: {douban_rating})")
                    
                    # 添加延时，避免请求过于频繁
                    if i < 9:  # 不是最后一部电影
                        print(f"等待5秒...")
                        time.sleep(5)
                    
                except Exception as e:
                    print(f"处理第{i+1}行数据时出错: {e}")
                    continue
        
        print(f"成功抓取 {len(movies_data)} 条电影数据")
        return movies_data
    
    def save_to_csv(self, data, year, month, filename=None):
        """
        将数据保存到CSV文件
        
        Args:
            data (list): 电影数据列表
            year (int): 年份
            month (int): 月份
            filename (str): 保存的文件名，如果为None则自动生成
        """
        if not data:
            print("没有数据可保存")
            return
        
        if filename is None:
            # 创建data目录
            os.makedirs('data', exist_ok=True)
            
            # 生成固定格式的文件名（相同年月会覆盖）
            filename = f"data/boxoffice_{year}_{month:02d}.csv"
        
        df = pd.DataFrame(data)
        # 保留需要的七列，按指定顺序
        columns_order = ['排名', '英文片名', '中文片名', '累计票房', '首映日期', 'IMDb评分', '豆瓣评分']
        df = df.reindex(columns=columns_order)
        
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"数据已保存到: {filename}")
        return filename
    
    def debug_page_structure(self, year, month):
        """调试模式：分析页面结构"""
        month_name = self.get_month_name(month)
        if not month_name:
            raise ValueError("月份必须在1-12之间")
        
        url = self.base_url.format(month=month_name, year=year)
        print(f"调试模式 - 分析页面: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("\n=== 页面结构分析 ===")
        print("所有表格:")
        tables = soup.find_all('table')
        for i, table in enumerate(tables):
            print(f"  表格 {i+1}: class={table.get('class')}, id={table.get('id')}")
            if i == 0:  # 分析第一个表格
                print(f"    行数: {len(table.find_all('tr'))}")
                first_row = table.find('tr')
                if first_row:
                    cells = first_row.find_all(['td', 'th'])
                    print(f"    第一行单元格数: {len(cells)}")
                    print("    列标题/内容:")
                    for idx, cell in enumerate(cells[:8]):  # 显示前8列
                        content = cell.get_text(strip=True)[:30]
                        print(f"      第{idx+1}列: {content}")
                
                # 分析数据行
                data_rows = table.find_all('tr')[1:3]  # 取前2行数据行
                for row_idx, row in enumerate(data_rows):
                    cells = row.find_all('td')
                    if cells:
                        print(f"    数据行{row_idx+1} ({len(cells)}列):")
                        for idx, cell in enumerate(cells):  # 显示所有列
                            content = cell.get_text(strip=True)[:30]
                            print(f"      第{idx+1}列: {content}")


def main():
    """主函数"""
    print("=== BoxOfficeMojo 票房数据抓取工具 ===")
    print()
    
    try:
        # 获取用户输入
        year = int(input("请输入年份 (例如: 2025): "))
        month = int(input("请输入月份 (1-12): "))
        
        if not (1 <= month <= 12):
            print("月份必须在1-12之间")
            return
        
        if year < 1980 or year > 2030:
            print("请输入合理的年份范围")
            return
        
        # 询问是否启用调试模式
        debug_choice = input("是否启用调试模式？(y/n，默认n): ").lower().strip()
        debug_mode = debug_choice == 'y'
        
        scraper = BoxOfficeScraper(debug=debug_mode)
        
        if debug_mode:
            print("\n启用调试模式，分析页面结构...")
            scraper.debug_page_structure(year, month)
            print("\n" + "="*50)
        
        print(f"\n开始抓取 {year}年{month}月 的票房数据...")
        print("-" * 50)
        
        # 抓取数据
        data = scraper.scrape_monthly_data(year, month)
        
        if data:
            print("-" * 50)
            print(f"抓取完成！共获得 {len(data)} 条电影数据")
            
            # 显示预览
            print("\n数据预览:")
            for movie in data[:3]:  # 显示前3条
                print(f"{movie['排名']}. {movie['英文片名']} / {movie['中文片名']} - {movie['累计票房']} ({movie['首映日期']}) [IMDb: {movie['IMDb评分']}, 豆瓣: {movie['豆瓣评分']}]")
            
            if len(data) > 3:
                print("...")
            
            # 保存数据
            filename = scraper.save_to_csv(data, year, month)
            print(f"\n所有数据已保存到: {filename}")
        else:
            print("未能获取到数据，请检查网络连接或稍后重试")
            
    except ValueError as e:
        print(f"输入错误: {e}")
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    main() 