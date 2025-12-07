"""
一键入口：先爬取，再分析。
"""
from scrape_douban import main as crawl_main
from analyze_douban import main as analyze_main


def main() -> None:
    print("====== 第一步：开始爬取豆瓣 Top250 ======")
    crawl_main()
    print("\n====== 第二步：开始分析与可视化 ======")
    analyze_main()
    print("\n全部流程结束。")


if __name__ == "__main__":
    main()



