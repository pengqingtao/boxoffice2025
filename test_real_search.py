#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from boxoffice_scraper import BoxOfficeScraper

def test_imdb_real_search():
    """测试真实的IMDb搜索功能"""
    print("=== 测试真实IMDb搜索功能 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    # 测试有年份匹配需求的电影
    test_cases = [
        {
            'movie': 'The Lion King',
            'target_years': [1994, 2019],
            'description': '狮子王 (经典版 vs CG版)'
        },
        {
            'movie': 'Spider-Man',
            'target_years': [2002, 2017],
            'description': '蜘蛛侠 (托比版 vs 汤姆版)'
        },
        {
            'movie': 'Avatar',
            'target_years': [2009],
            'description': '阿凡达 (单一版本)'
        }
    ]
    
    for test_case in test_cases:
        movie = test_case['movie']
        print(f"\n🎬 测试电影: {movie} ({test_case['description']})")
        print("-" * 60)
        
        for target_year in test_case['target_years']:
            print(f"\n📅 搜索年份: {target_year}")
            
            try:
                rating = scraper.search_imdb_rating(movie, target_year)
                print(f"📊 结果: IMDb评分 = {rating}")
                
                # 添加延时避免请求过频
                import time
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ 搜索失败: {e}")

def test_douban_real_search():
    """测试真实的豆瓣搜索功能"""
    print("\n=== 测试真实豆瓣搜索功能 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    # 测试一些英文电影名
    test_movies = [
        ('Avatar', 2009, '阿凡达'),
        ('Titanic', 1997, '泰坦尼克号'),
        ('The Lion King', 2019, '狮子王'),
        ('Iron Man', 2008, '钢铁侠'),
        ('Frozen', 2013, '冰雪奇缘')
    ]
    
    print(f"\n测试豆瓣在线搜索...")
    print(f"{'英文片名':<20} {'目标年份':<8} {'中文片名':<15} {'豆瓣评分':<8} {'状态':<10}")
    print("-" * 70)
    
    for movie, target_year, expected_title in test_movies:
        try:
            print(f"\n🎬 搜索: {movie} (目标年份: {target_year})")
            chinese_title, douban_rating = scraper.search_douban_movie(movie, target_year)
            
            status = "✅成功" if chinese_title != "N/A" else "❌失败"
            print(f"{movie:<20} {target_year:<8} {chinese_title:<15} {douban_rating:<8} {status:<10}")
            
            # 添加延时避免请求过频
            import time
            time.sleep(5)
            
        except Exception as e:
            print(f"{movie:<20} {target_year:<8} {'N/A':<15} {'N/A':<8} {'❌错误':<10}")
            print(f"错误信息: {e}")

def test_combined_search():
    """测试组合搜索功能"""
    print("\n=== 测试组合搜索功能 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    # 测试同时获取IMDb和豆瓣信息
    test_movie = "Avatar"
    target_year = 2009
    
    print(f"\n🎬 测试电影: {test_movie} (目标年份: {target_year})")
    print("-" * 50)
    
    try:
        print("1. 获取IMDb评分...")
        imdb_rating = scraper.search_imdb_rating(test_movie, target_year)
        print(f"   IMDb评分: {imdb_rating}")
        
        print("\n2. 获取豆瓣信息...")
        chinese_title, douban_rating = scraper.search_douban_movie(test_movie, target_year)
        print(f"   中文片名: {chinese_title}")
        print(f"   豆瓣评分: {douban_rating}")
        
        print(f"\n📊 完整结果:")
        print(f"   英文片名: {test_movie}")
        print(f"   中文片名: {chinese_title}")
        print(f"   目标年份: {target_year}")
        print(f"   IMDb评分: {imdb_rating}")
        print(f"   豆瓣评分: {douban_rating}")
        
    except Exception as e:
        print(f"❌ 组合搜索失败: {e}")

def test_fallback_mechanism():
    """测试回退机制"""
    print("\n=== 测试回退机制 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    # 测试一个不太可能在豆瓣搜到的电影
    test_movie = "Unknown Movie 12345"
    target_year = 2024
    
    print(f"\n🎬 测试不存在的电影: {test_movie}")
    print("预期：在线搜索失败，回退到静态映射")
    
    try:
        chinese_title, douban_rating = scraper.search_douban_movie(test_movie, target_year)
        print(f"结果: {chinese_title} / {douban_rating}")
        
        if chinese_title == "N/A" and douban_rating == "N/A":
            print("✅ 回退机制正常工作")
        else:
            print("❓ 意外获得结果")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    import time
    
    print("🚀 开始测试真实搜索功能")
    print("=" * 60)
    
    # 询问用户想要测试的功能
    print("\n请选择要测试的功能:")
    print("1. IMDb真实搜索")
    print("2. 豆瓣真实搜索") 
    print("3. 组合搜索功能")
    print("4. 回退机制测试")
    print("5. 全部测试")
    
    choice = input("\n输入选择 (1-5): ").strip()
    
    if choice == "1" or choice == "5":
        test_imdb_real_search()
    
    if choice == "2" or choice == "5":
        test_douban_real_search()
    
    if choice == "3" or choice == "5":
        test_combined_search()
    
    if choice == "4" or choice == "5":
        test_fallback_mechanism()
    
    print(f"\n✅ 测试完成！")
    print("注意：由于网络限制和反爬虫机制，部分功能可能无法正常工作。") 