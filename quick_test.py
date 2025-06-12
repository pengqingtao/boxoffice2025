#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from boxoffice_scraper import BoxOfficeScraper

def quick_test():
    """快速测试列索引修复"""
    print("=== 快速测试 - 验证列索引修复 ===")
    
    scraper = BoxOfficeScraper(debug=True)
    
    # 测试2024年5月的数据
    year = 2024
    month = 5
    
    print(f"\n测试 {year}年{month}月...")
    
    try:
        # 首先显示页面结构
        scraper.debug_page_structure(year, month)
        
        print("\n" + "="*60)
        print("开始数据抓取...")
        
        # 尝试抓取数据
        data = scraper.scrape_monthly_data(year, month)
        
        if data:
            print(f"\n✅ 成功！抓取到 {len(data)} 条数据")
            print("\n📊 数据预览:")
            print(f"{'排名':<4} {'英文片名':<25} {'中文片名':<20} {'累计票房':<15} {'首映日期':<10} {'IMDb':<6} {'豆瓣':<6}")
            print("-" * 92)
            
            for movie in data[:5]:  # 显示前5条
                rank = movie['排名']
                en_name = movie['英文片名'][:20] + "..." if len(movie['英文片名']) > 20 else movie['英文片名']
                cn_name = movie['中文片名'][:15] + "..." if len(movie['中文片名']) > 15 else movie['中文片名']
                gross = movie['累计票房']
                date = movie['首映日期']
                imdb_rating = movie['IMDb评分']
                douban_rating = movie['豆瓣评分']
                print(f"{rank:<4} {en_name:<25} {cn_name:<20} {gross:<15} {date:<10} {imdb_rating:<6} {douban_rating:<6}")
                
            print(f"\n💾 准备保存数据...")
            filename = scraper.save_to_csv(data, year, month)
            print(f"✅ 数据已保存到: {filename}")
            
        else:
            print("❌ 未抓取到数据")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_test() 