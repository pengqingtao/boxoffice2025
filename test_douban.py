#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from boxoffice_scraper import BoxOfficeScraper

def test_douban_feature():
    """测试豆瓣电影功能"""
    print("=== 测试豆瓣电影功能 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    # 测试一些知名电影
    test_movies = [
        "Lilo & Stitch",
        "Thunderbolts",
        "Avatar",
        "Titanic",
        "The Lion King"
    ]
    
    print(f"\n测试豆瓣搜索功能...")
    print(f"{'英文片名':<25} {'中文片名':<20} {'豆瓣评分':<8}")
    print("-" * 60)
    
    for movie in test_movies:
        try:
            print(f"正在搜索: {movie}")
            chinese_title, douban_rating = scraper.search_douban_movie(movie)
            print(f"{movie:<25} {chinese_title:<20} {douban_rating:<8}")
            print("-" * 60)
            
        except Exception as e:
            print(f"搜索 {movie} 时出错: {e}")
            print("-" * 60)

def test_combined_features():
    """测试IMDb和豆瓣组合功能"""
    print("\n=== 测试组合功能（前2部电影）===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    # 获取最新的票房数据（只抓前2部）
    year = 2025
    month = 5
    
    try:
        month_name = scraper.get_month_name(month)
        url = scraper.base_url.format(month=month_name, year=year)
        print(f"正在抓取: {url}")
        
        import requests
        response = requests.get(url, headers=scraper.headers, timeout=10)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        table = soup.find('table', class_='a-bordered')
        if not table:
            table = soup.find('table')
        
        if not table:
            print("未找到数据表格")
            return
        
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            rows = table.find_all('tr')
            if rows and rows[0].find('th'):
                rows = rows[1:]
        
        movies_data = []
        
        # 只处理前2行数据
        for i, row in enumerate(rows[:2]):
            cells = row.find_all('td')
            if len(cells) >= 7:
                try:
                    rank = cells[0].get_text(strip=True)
                    release_cell = cells[1]
                    release_link = release_cell.find('a')
                    release_name = release_link.get_text(strip=True) if release_link else release_cell.get_text(strip=True)
                    total_gross_text = cells[7].get_text(strip=True)
                    release_date_raw = cells[8].get_text(strip=True) if len(cells) > 8 else "N/A"
                    release_date = scraper.convert_date_to_chinese(release_date_raw)
                    
                    print(f"\n--- 处理第{i+1}部电影: {release_name} ---")
                    
                    # 获取IMDb评分
                    imdb_rating = scraper.search_imdb_rating(release_name)
                    
                    # 获取豆瓣信息
                    chinese_title, douban_rating = scraper.search_douban_movie(release_name)
                    
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
                    print(f"✅ 完成: {rank}. {release_name} / {chinese_title}")
                    print(f"   IMDb: {imdb_rating}, 豆瓣: {douban_rating}")
                    
                except Exception as e:
                    print(f"❌ 处理第{i+1}行数据时出错: {e}")
                    continue
        
        # 显示结果
        if movies_data:
            print(f"\n🎉 成功获取 {len(movies_data)} 部电影的完整数据！")
            print("\n📊 最终结果:")
            print(f"{'排名':<4} {'英文片名':<25} {'中文片名':<20} {'累计票房':<15} {'首映日期':<10} {'IMDb':<6} {'豆瓣':<6}")
            print("-" * 92)
            
            for movie in movies_data:
                rank = movie['排名']
                en_name = movie['英文片名'][:20] + "..." if len(movie['英文片名']) > 20 else movie['英文片名']
                cn_name = movie['中文片名'][:15] + "..." if len(movie['中文片名']) > 15 else movie['中文片名']
                gross = movie['累计票房']
                date = movie['首映日期']
                imdb_rating = movie['IMDb评分']
                douban_rating = movie['豆瓣评分']
                print(f"{rank:<4} {en_name:<25} {cn_name:<20} {gross:<15} {date:<10} {imdb_rating:<6} {douban_rating:<6}")
            
            # 保存测试数据
            filename = scraper.save_to_csv(movies_data, year, month, "data/test_douban_combined.csv")
            print(f"\n💾 测试数据已保存到: {filename}")
        else:
            print("❌ 未获取到任何数据")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 首先测试纯豆瓣搜索功能
    test_douban_feature()
    
    # 然后测试组合功能
    test_combined_features() 