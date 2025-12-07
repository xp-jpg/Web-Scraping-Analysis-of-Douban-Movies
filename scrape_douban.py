import os
import random
import re
import time
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# 加载 Cookie 配置
try:
    from config import DOUBAN_COOKIE
except ImportError:
    DOUBAN_COOKIE = ""
    print("[提示] 未找到 config.py，将使用空 Cookie，请在 config.py 中配置。")

"""
豆瓣电影 Top250 爬取流程（增强反爬 + 调试）：
    1. 使用 Session 保持会话
    2. 随机延迟 + 重试机制
    3. 多种解析策略，适应页面结构变化
    4. 调试：保存第一页 HTML，便于检查是否被拦截
"""

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    # 只保留 gzip/deflate，避免 brotli 解析乱码
    "accept-encoding": "gzip, deflate",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "cache-control": "max-age=0",
    "cookie": DOUBAN_COOKIE,
    "priority": "u=0, i",
    "referer": "https://movie.douban.com/top250",
    "sec-ch-ua": '"Chromium";v="122", "Google Chrome";v="122", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}

session = requests.Session()
session.headers.update(HEADERS)


def init_session() -> None:
    """先访问首页建立会话，成功率更高。"""
    try:
        for url in ["https://www.douban.com", "https://movie.douban.com"]:
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            time.sleep(random.uniform(1, 2))
        print("[成功] 会话初始化完成。")
    except Exception as exc:  # noqa: BLE001
        print(f"[警告] 会话初始化失败：{exc}，将直接尝试爬取。")


def check_cookie_valid(html: str) -> tuple[bool, str]:
    if not html:
        return False, "HTML 为空"
    anti = ["检测到异常请求", "请登录", "出错了", "访问被拒绝", "Access Denied"]
    for k in anti:
        if k in html:
            return False, f"检测到反爬提示：{k}"
    has_list = any(
        kw in html
        for kw in ['class="item"', 'class="grid_view"', 'class="title"', 'class="rating_num"']
    )
    return (True, "Cookie 有效") if has_list else (False, "页面不包含电影列表元素，可能被拦截")


def get_html(url: str, timeout: int = 15, retries: int = 3, save_debug: bool = False, referer: Optional[str] = None) -> str:
    for attempt in range(retries):
        try:
            if attempt > 0:
                delay = random.uniform(2, 4)
                print(f"  重试 {attempt + 1}/{retries}，等待 {delay:.1f} 秒...")
                time.sleep(delay)
            else:
                time.sleep(random.uniform(1, 2))

            # 动态 referer
            if referer:
                session.headers["referer"] = referer

            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            html = resp.text

            if save_debug:
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print("  [调试] 已保存 debug_page.html，请用浏览器查看。")

            ok, msg = check_cookie_valid(html)
            if not ok:
                print(f"  [警告] {msg}")
                if save_debug:
                    preview = html[:500].replace("\n", "")
                    print(f"  [调试] HTML 预览: {preview}...")
            return html
        except Exception as exc:  # noqa: BLE001
            print(f"  请求错误（尝试 {attempt + 1}/{retries}）：{exc}")
    return ""


def parse_movies(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("div.item")
    if not items:
        # 尝试备用结构
        items = soup.select("ol.grid_view li")
    movies: List[Dict] = []
    for it in items:
        info: Dict = {}
        try:
            title_el = it.find("span", class_="title")
            if title_el:
                info["title"] = title_el.text.strip()

            rating_el = it.find("span", class_="rating_num")
            if rating_el:
                try:
                    info["rating"] = float(rating_el.text.strip())
                except ValueError:
                    pass

            # 评价人数
            rating_count = None
            count_el = it.find(string=re.compile(r"\d+人评价"))
            if count_el:
                m = re.search(r"(\d+)", count_el)
                if m:
                    rating_count = int(m.group(1))
            if rating_count is not None:
                info["rating_count"] = rating_count

            bd_el = it.find("div", class_="bd")
            if bd_el:
                text = " ".join(bd_el.text.split())
                info["info"] = text
                year_match = re.search(r"\b(19|20)\d{2}\b", text)
                if year_match:
                    info["year"] = int(year_match.group())

            link_el = it.find("a")
            if link_el and link_el.get("href"):
                info["url"] = link_el["href"]

            img_el = it.find("img")
            if img_el:
                cover = img_el.get("data-src") or img_el.get("src")
                if cover:
                    info["cover"] = cover

            quote_el = it.find("span", class_="inq")
            if quote_el:
                info["quote"] = quote_el.text.strip()

            if info.get("title"):
                movies.append(info)
        except Exception as exc:  # noqa: BLE001
            print(f"  解析出错：{exc}")
            continue
    return movies


def crawl_top250(delay: float = 1.5) -> List[Dict]:
    base = "https://movie.douban.com/top250"
    all_movies: List[Dict] = []
    print("=" * 60)
    print("开始爬取豆瓣 Top250（增强反爬版）")
    print("=" * 60)
    init_session()

    for page in range(10):
        start = page * 25
        url = f"{base}?start={start}&filter="
        prev = f"{base}?start={(page - 1) * 25}&filter=" if page > 0 else base
        print(f"\n===== 正在爬取第 {page + 1}/10 页：{url} =====")
        html = get_html(url, save_debug=(page == 0), referer=prev)
        if not html:
            print(f"  [错误] 第 {page + 1} 页获取失败，跳过。")
            continue
        movies = parse_movies(html)
        print(f"  本页解析到 {len(movies)} 部电影。")
        all_movies.extend(movies)
        if page != 9:
            wait = delay + random.uniform(0.5, 1.5)
            print(f"  等待 {wait:.1f} 秒后继续...")
            time.sleep(wait)

    print("\n" + "=" * 60)
    print(f"爬取完成，共 {len(all_movies)} 条电影数据。")
    print("=" * 60)
    return all_movies


def save_csv(movies: List[Dict], path: str = "douban_top250.csv") -> None:
    import csv

    fields = ["title", "rating", "rating_count", "year", "url", "cover", "quote", "info"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for m in movies:
            w.writerow({k: m.get(k, "") for k in fields})
    print(f"电影数据已保存：{path}")


def save_text(movies: List[Dict], path: str = "豆瓣电影Top250信息.txt") -> None:
    lines = []
    for idx, m in enumerate(movies, 1):
        lines.append(
            f"{idx:03d}. 《{m.get('title','')}》 | 评分：{m.get('rating','')} | "
            f"评价人数：{m.get('rating_count','')} | 年份：{m.get('year','')} | 短评：{m.get('quote','')}\n"
        )
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"电影文本信息已保存：{path}")


def main() -> None:
    movies = crawl_top250(delay=1.8)
    if not movies:
        print("未获取到数据，请检查 Cookie 或网络。")
        return
    save_csv(movies)
    save_text(movies)


if __name__ == "__main__":
    main()


