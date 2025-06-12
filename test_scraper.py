#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from boxoffice_scraper import BoxOfficeScraper

def test_scraper():
    """测试抓取器功能"""
    print("=== 测试 BoxOffice 抓取器 ===")
    
    scraper = BoxOfficeScraper(debug=True)
    
    # 测试一个已知存在数据的月份
    year = 2024
    month = 5  # 2024年5月
    
    print(f"\n测试 {year}年{month}月 数据...")
    
    # 先运行调试模式
    print("\n1. 调试页面结构:")
    scraper.debug_page_structure(year, month)
    
    print("\n" + "="*50)
    print("2. 尝试抓取数据:")
    
    try:
        data = scraper.scrape_monthly_data(year, month)
        
        if data:
            print(f"\n✓ 成功！抓取到 {len(data)} 条数据")
            print("\n前3条数据预览:")
            for i, movie in enumerate(data[:3]):
                print(f"  {i+1}. {movie['英文片名']} - {movie['累计票房']}")
        else:
            print("\n✗ 未能抓取到数据")
            
    except Exception as e:
        print(f"\n✗ 抓取过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper() 