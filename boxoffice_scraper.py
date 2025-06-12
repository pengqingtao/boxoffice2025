import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import os
from datetime import datetime
import time


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
                    
                    movie_data = {
                        '排名': rank,
                        '英文片名': release_name,
                        '累计票房': total_gross_text,
                        '首映日期': release_date
                    }
                    
                    movies_data.append(movie_data)
                    print(f"已抓取: {rank}. {release_name}")
                    
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
        # 只保留需要的四列，按指定顺序
        columns_order = ['排名', '英文片名', '累计票房', '首映日期']
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
                print(f"{movie['排名']}. {movie['英文片名']} - {movie['累计票房']} ({movie['首映日期']})")
            
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