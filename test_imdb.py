#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from boxoffice_scraper import BoxOfficeScraper

def test_imdb_feature():
    """测试IMDb评分功能"""
    print("=== 测试 IMDb 评分功能 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    # 测试2025年5月数据（只抓取前3部电影）
    year = 2025
    month = 5
    
    print(f"\n测试 {year}年{month}月 数据（前3部电影）...")
    
    try:
        # 修改抓取逻辑，只获取前3部电影
        month_name = scraper.get_month_name(month)
        url = scraper.base_url.format(month=month_name, year=year)
        print(f"正在抓取: {url}")
        
        import requests
        response = requests.get(url, headers=scraper.headers, timeout=10)
        response.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找票房数据表格
        table = soup.find('table', class_='a-bordered')
        if not table:
            table = soup.find('table', class_='mojo-body-table')
        if not table:
            table = soup.find('table')
        
        if not table:
            print("未找到数据表格")
            return
        
        # 获取表格行
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            rows = table.find_all('tr')
            if rows and rows[0].find('th'):
                rows = rows[1:]
        
        movies_data = []
        
        # 只处理前3行数据
        for i, row in enumerate(rows[:3]):
            cells = row.find_all('td')
            if len(cells) >= 7:
                try:
                    # 排名
                    rank = cells[0].get_text(strip=True)
                    
                    # 电影名称
                    release_cell = cells[1]
                    release_link = release_cell.find('a')
                    release_name = release_link.get_text(strip=True) if release_link else release_cell.get_text(strip=True)
                    
                    # 累计票房
                    total_gross_text = cells[7].get_text(strip=True)
                    
                    # 首映日期
                    release_date_raw = cells[8].get_text(strip=True) if len(cells) > 8 else "N/A"
                    release_date = scraper.convert_date_to_chinese(release_date_raw)
                    
                    print(f"\n--- 处理第{i+1}部电影: {release_name} ---")
                    
                    # 获取IMDb评分
                    imdb_rating = scraper.search_imdb_rating(release_name)
                    
                    movie_data = {
                        '排名': rank,
                        '英文片名': release_name,
                        '累计票房': total_gross_text,
                        '首映日期': release_date,
                        '评分': imdb_rating
                    }
                    
                    movies_data.append(movie_data)
                    print(f"✅ 完成: {rank}. {release_name} (评分: {imdb_rating})")
                    
                except Exception as e:
                    print(f"❌ 处理第{i+1}行数据时出错: {e}")
                    continue
        
        # 显示结果
        if movies_data:
            print(f"\n🎉 成功获取 {len(movies_data)} 部电影的数据！")
            print("\n📊 详细结果:")
            print(f"{'排名':<4} {'电影名称':<35} {'累计票房':<15} {'首映日期':<10} {'IMDb评分':<8}")
            print("-" * 80)
            
            for movie in movies_data:
                rank = movie['排名']
                name = movie['英文片名'][:30] + "..." if len(movie['英文片名']) > 30 else movie['英文片名']
                gross = movie['累计票房']
                date = movie['首映日期']
                rating = movie['评分']
                print(f"{rank:<4} {name:<35} {gross:<15} {date:<10} {rating:<8}")
            
            # 保存测试数据
            filename = scraper.save_to_csv(movies_data, year, month, "data/test_imdb_2025_05.csv")
            print(f"\n💾 测试数据已保存到: {filename}")
        else:
            print("❌ 未获取到任何数据")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imdb_feature() 