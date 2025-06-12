import time
from boxoffice_scraper import BoxOfficeScraper


def batch_scrape_multiple_months(year, start_month, end_month):
    """
    批量抓取多个月份的票房数据
    
    Args:
        year (int): 年份
        start_month (int): 开始月份
        end_month (int): 结束月份
    """
    scraper = BoxOfficeScraper()
    all_data = []
    
    print(f"=== 批量抓取 {year}年 {start_month}月 到 {end_month}月 的票房数据 ===")
    print()
    
    for month in range(start_month, end_month + 1):
        print(f"正在抓取 {year}年{month}月...")
        
        try:
            # 抓取当月数据
            monthly_data = scraper.scrape_monthly_data(year, month)
            
            if monthly_data:
                all_data.extend(monthly_data)
                print(f"✓ {year}年{month}月 抓取成功：{len(monthly_data)} 条数据")
            else:
                print(f"✗ {year}年{month}月 抓取失败")
            
            # 添加延时，避免请求过于频繁
            if month < end_month:
                print("等待 2 秒...")
                time.sleep(2)
                
        except Exception as e:
            print(f"✗ {year}年{month}月 抓取出错: {e}")
        
        print("-" * 30)
    
    # 保存所有数据
    if all_data:
        # 为批量数据创建特殊的文件名
        filename = f"data/batch_boxoffice_{year}_{start_month:02d}_to_{end_month:02d}.csv"
        saved_filename = scraper.save_to_csv(all_data, year, start_month, filename)
        
        print(f"\n总计抓取了 {len(all_data)} 条电影数据")
        print(f"所有数据已保存到: {saved_filename}")
        
        # 显示统计信息
        print(f"\n数据统计:")
        print(f"  时间范围: {year}年{start_month}月 到 {end_month}月")
        print(f"  总电影数: {len(all_data)} 条")
        
        # 按月份统计（基于抓取的月份范围）
        months_covered = end_month - start_month + 1
        avg_per_month = len(all_data) / months_covered
        print(f"  平均每月: {avg_per_month:.1f} 条数据")
    else:
        print("\n未获取到任何数据")


def main():
    """主函数"""
    print("=== BoxOfficeMojo 批量票房数据抓取工具 ===")
    print()
    
    try:
        year = int(input("请输入年份 (例如: 2024): "))
        start_month = int(input("请输入开始月份 (1-12): "))
        end_month = int(input("请输入结束月份 (1-12): "))
        
        if not (1 <= start_month <= 12) or not (1 <= end_month <= 12):
            print("月份必须在1-12之间")
            return
        
        if start_month > end_month:
            print("开始月份不能大于结束月份")
            return
        
        if year < 1980 or year > 2030:
            print("请输入合理的年份范围")
            return
        
        print()
        batch_scrape_multiple_months(year, start_month, end_month)
        
    except ValueError as e:
        print(f"输入错误: {e}")
    except KeyboardInterrupt:
        print("\n用户取消操作")
    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    main() 