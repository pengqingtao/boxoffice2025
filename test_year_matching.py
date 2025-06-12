#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from boxoffice_scraper import BoxOfficeScraper

def test_year_matching():
    """测试年份匹配功能"""
    print("=== 测试年份匹配功能 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    # 测试同名电影的不同版本
    test_cases = [
        {
            'movie': 'The Lion King',
            'test_years': [1994, 2019, 2010],  # 分别测试1994年、2019年、中间年份
            'expected': {
                1994: ('狮子王', '9.1'),  # 应该匹配经典动画版
                2019: ('狮子王', '7.4'),  # 应该匹配CG版
                2010: ('狮子王', '9.1')   # 应该匹配较近的经典版
            }
        },
        {
            'movie': 'Spider-Man',
            'test_years': [2002, 2012, 2017],
            'expected': {
                2002: ('蜘蛛侠', '7.4'),
                2012: ('超凡蜘蛛侠', '7.4'),
                2017: ('蜘蛛侠：英雄归来', '7.4')
            }
        },
        {
            'movie': 'Batman',
            'test_years': [1989, 2005, 2008, 2016],
            'expected': {
                1989: ('蝙蝠侠', '7.5'),
                2005: ('蝙蝠侠：侠影之谜', '8.4'),
                2008: ('蝙蝠侠：黑暗骑士', '9.3'),
                2016: ('蝙蝠侠大战超人', '6.4')
            }
        }
    ]
    
    for test_case in test_cases:
        movie = test_case['movie']
        print(f"\n🎬 测试电影: {movie}")
        print("-" * 60)
        
        for target_year in test_case['test_years']:
            print(f"\n📅 目标年份: {target_year}")
            
            # 测试豆瓣匹配
            chinese_title, douban_rating = scraper.search_douban_movie(movie, target_year)
            
            expected = test_case['expected'].get(target_year, ('N/A', 'N/A'))
            expected_title, expected_rating = expected
            
            # 检查匹配结果
            if chinese_title == expected_title and douban_rating == expected_rating:
                print(f"✅ 豆瓣匹配正确: {chinese_title} (评分: {douban_rating})")
            else:
                print(f"❌ 豆瓣匹配不正确:")
                print(f"   期望: {expected_title} (评分: {expected_rating})")
                print(f"   实际: {chinese_title} (评分: {douban_rating})")

def test_single_version_movies():
    """测试单一版本电影的年份匹配"""
    print("\n=== 测试单一版本电影 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    single_movies = [
        ('Avatar', 2009, '阿凡达', '8.8'),
        ('Titanic', 1997, '泰坦尼克号', '9.4'),
        ('Avatar', 2015, '阿凡达', '8.8'),  # 即使年份不匹配，也应该返回唯一版本
    ]
    
    for movie, target_year, expected_title, expected_rating in single_movies:
        print(f"\n🎬 测试: {movie} (目标年份: {target_year})")
        chinese_title, douban_rating = scraper.search_douban_movie(movie, target_year)
        
        if chinese_title == expected_title and douban_rating == expected_rating:
            print(f"✅ 匹配正确: {chinese_title} (评分: {douban_rating})")
        else:
            print(f"❌ 匹配不正确:")
            print(f"   期望: {expected_title} (评分: {expected_rating})")
            print(f"   实际: {chinese_title} (评分: {douban_rating})")

def test_imdb_year_matching():
    """测试IMDb年份匹配功能（模拟）"""
    print("\n=== 测试IMDb年份匹配功能 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    # 由于IMDb需要实际网络请求，这里只测试一个电影
    test_movie = "The Lion King"
    test_years = [1994, 2019]
    
    for target_year in test_years:
        print(f"\n🎬 测试IMDb搜索: {test_movie} (目标年份: {target_year})")
        # 注意：这会发起真实的网络请求
        try:
            imdb_rating = scraper.search_imdb_rating(test_movie, target_year)
            print(f"IMDb评分结果: {imdb_rating}")
        except Exception as e:
            print(f"IMDb搜索出错: {e}")

def test_no_year_fallback():
    """测试不提供年份时的回退机制"""
    print("\n=== 测试无年份回退机制 ===")
    
    scraper = BoxOfficeScraper(debug=False)
    
    test_movies = ['The Lion King', 'Spider-Man', 'Avatar']
    
    for movie in test_movies:
        print(f"\n🎬 测试电影: {movie} (无目标年份)")
        chinese_title, douban_rating = scraper.search_douban_movie(movie)  # 不传年份
        print(f"结果: {chinese_title} (评分: {douban_rating})")

if __name__ == "__main__":
    # 测试豆瓣年份匹配
    test_year_matching()
    
    # 测试单一版本电影
    test_single_version_movies()
    
    # 测试无年份回退
    test_no_year_fallback()
    
    # 可选：测试IMDb年份匹配（需要网络）
    test_imdb_choice = input("\n是否测试IMDb年份匹配功能？(需要网络连接，y/n): ").lower().strip()
    if test_imdb_choice == 'y':
        test_imdb_year_matching()
    
    print("\n✅ 年份匹配功能测试完成！") 