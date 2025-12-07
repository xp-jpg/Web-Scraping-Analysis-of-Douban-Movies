import os
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

DATA_FILE = "douban_top250.csv"


def _setup_style() -> None:
    # 更鲜艳的主题
    sns.set_theme(style="whitegrid", context="talk", palette="Spectral")
    try:
        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
        plt.rcParams["axes.unicode_minus"] = False
    except Exception:
        pass


def load_data(path: str = DATA_FILE) -> Optional[pd.DataFrame]:
    if not os.path.exists(path):
        print(f"数据文件不存在：{path}，请先运行爬虫。")
        return None
    df = pd.read_csv(path)
    df["rating"] = pd.to_numeric(df.get("rating"), errors="coerce")
    df["rating_count"] = pd.to_numeric(df.get("rating_count"), errors="coerce")
    df["year"] = pd.to_numeric(df.get("year"), errors="coerce")
    return df


def basic_stats(df: pd.DataFrame) -> None:
    print("\n=== 基础信息预览 ===")
    print(df[["title", "rating", "rating_count", "year"]].head())
    print("\n=== 评分统计 ===")
    print(df["rating"].describe())
    print("\n=== 评价人数统计 ===")
    print(df["rating_count"].describe())
    print("\n=== 年份分布（Top10） ===")
    print(df["year"].value_counts().head(10))


def plot_rating_hist(df: pd.DataFrame, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    plt.figure(figsize=(9, 5))
    sns.histplot(df["rating"].dropna(), bins=12, kde=True, color="#ff6f91", edgecolor="white")
    plt.title("评分分布")
    plt.xlabel("评分")
    plt.ylabel("数量")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "rating_distribution.png"), dpi=150)
    plt.close()


def plot_year_line(df: pd.DataFrame, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    year_counts = (
        df.dropna(subset=["year"])
        .groupby("year")["title"]
        .count()
        .reset_index(name="count")
        .sort_values("year")
    )
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=year_counts, x="year", y="count", marker="o", color="#845ef7", linewidth=2.5)
    plt.title("每年入选影片数量")
    plt.xlabel("年份")
    plt.ylabel("数量")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "year_distribution.png"), dpi=150)
    plt.close()


def plot_decade_mix(df: pd.DataFrame, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    dd = df.dropna(subset=["year"]).copy()
    dd["decade"] = (dd["year"] // 10) * 10
    stat = (
        dd.groupby("decade")
        .agg(count=("title", "count"), avg_rating=("rating", "mean"))
        .reset_index()
        .sort_values("decade")
    )
    fig, ax1 = plt.subplots(figsize=(10, 5))
    cmap = sns.color_palette("coolwarm", len(stat))
    sns.barplot(data=stat, x="decade", y="count", ax=ax1, palette=cmap)
    ax1.set_xlabel("年代")
    ax1.set_ylabel("影片数量")
    ax2 = ax1.twinx()
    sns.lineplot(data=stat, x="decade", y="avg_rating", ax=ax2, color="#ffa600", marker="o", linewidth=2.2)
    ax2.set_ylabel("平均评分")
    plt.title("各年代数量与平均评分（双轴）")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "decade_distribution.png"), dpi=150)
    plt.close()


def plot_top_rating(df: pd.DataFrame, out_dir: str, top_n: int = 20) -> None:
    os.makedirs(out_dir, exist_ok=True)
    top_df = (
        df.dropna(subset=["rating"])
        .sort_values(["rating", "rating_count"], ascending=[False, False])
        .head(top_n)
    )
    plt.figure(figsize=(10, 8))
    sns.barplot(data=top_df, x="rating", y="title", hue="year", dodge=False, palette="Spectral")
    plt.title(f"评分最高的 Top{top_n} 影片（彩色年份）")
    plt.xlabel("评分")
    plt.ylabel("影片")
    plt.legend(title="年份", fontsize=9)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "top_movies_by_rating.png"), dpi=150)
    plt.close()


def plot_rating_vs_count(df: pd.DataFrame, out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    plot_df = df.dropna(subset=["rating", "rating_count"]).copy()
    plot_df["log_count"] = plot_df["rating_count"].clip(lower=1).map(np.log10)
    plt.figure(figsize=(9, 6))
    sns.scatterplot(
        data=plot_df,
        x="rating",
        y="log_count",
        hue="year",
        palette="mako",
        alpha=0.75,
        edgecolor="black",
        linewidth=0.3,
    )
    plt.xlabel("评分")
    plt.ylabel("评价人数（log10）")
    plt.title("评分 vs 评价人数（对数刻度）")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "rating_vs_count.png"), dpi=150)
    plt.close()


def plot_category_wordcloud(df: pd.DataFrame, out_dir: str) -> None:
    """
    用类型字段简单做一个彩色“条形+色块”组合，模拟词云效果但避免额外依赖。
    """
    os.makedirs(out_dir, exist_ok=True)
    cat_series = df["info"].fillna("").map(lambda x: x.split("/")[-1].strip() if "/" in x else "")
    cat_counts = cat_series.value_counts().head(15)
    plt.figure(figsize=(10, 6))
    sns.barplot(x=cat_counts.values, y=cat_counts.index, palette="cubehelix")
    plt.title("类型出现频次 Top15（多彩方案）")
    plt.xlabel("出现次数")
    plt.ylabel("类型")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "category_colorful.png"), dpi=150)
    plt.close()


def generate_json_data(df: pd.DataFrame) -> None:
    """
    生成JSON格式的数据文件，供可视化界面使用
    """
    import json
    
    # 评分分布
    rating_bins = [8.0, 8.5, 9.0, 9.5, 10.0]
    rating_labels = ['8.0-8.4', '8.5-8.9', '9.0-9.4', '9.5-9.9']
    df['rating_group'] = pd.cut(df['rating'], bins=rating_bins, labels=rating_labels, right=False)
    rating_distribution = df['rating_group'].value_counts().sort_index().reset_index()
    rating_distribution.columns = ['rating', 'count']
    
    # 年份分布
    year_distribution = df['year'].value_counts().sort_index().reset_index()
    year_distribution.columns = ['year', 'count']
    year_distribution = year_distribution.tail(10)  # 只取最近10年
    
    # 类型分布
    def extract_genre(info_str):
        if not info_str or '/' not in info_str:
            return ''
        
        # 查找评分部分的位置
        rating_pos = info_str.find('人评价')
        if rating_pos == -1:
            rating_pos = info_str.find('评分')
        
        if rating_pos != -1:
            # 从评分部分向前查找最后一个/，类型信息在这个/之后
            last_slash_before_rating = info_str.rfind('/', 0, rating_pos)
            if last_slash_before_rating != -1:
                # 提取类型信息，可能包含空格分隔的多个类型
                genre_part = info_str[last_slash_before_rating + 1:rating_pos].strip()
                # 清理类型信息，移除可能的数字和评分相关内容
                genre_part = ' '.join([word for word in genre_part.split() if not any(char.isdigit() for char in word) and '.' not in word])
                return genre_part
        
        # 如果没有找到评分部分，尝试从年份后提取
        parts = [part.strip() for part in info_str.split('/')]
        for i, part in enumerate(parts):
            # 找到年份部分
            if any(char.isdigit() and len(word) == 4 for word in part.split() for char in word):
                # 类型通常在年份后的1-2个部分
                if i + 1 < len(parts):
                    genre_part = parts[i + 1].strip()
                    # 清理类型信息
                    genre_part = ' '.join([word for word in genre_part.split() if not any(char.isdigit() for char in word) and '.' not in word])
                    return genre_part
                break
        
        return ''
    
    genre_series = df['info'].fillna('').map(extract_genre)
    genre_distribution = genre_series.value_counts().head(8).reset_index()
    genre_distribution.columns = ['genre', 'count']
    
    # 评分与评价人数关系
    rating_vs_count = df[['rating', 'rating_count']].dropna().head(10)
    rating_vs_count.columns = ['rating', 'count']
    
    # 评分最高的Top10电影
    top_movies = df.sort_values(['rating', 'rating_count'], ascending=[False, False])[['title', 'rating', 'year']].head(10)
    
    # 年代评分趋势
    df['decade'] = (df['year'] // 10) * 10
    decade_rating = df.groupby('decade')['rating'].mean().reset_index()
    decade_rating['decade'] = decade_rating['decade'].astype(str) + 's'
    decade_rating.columns = ['decade', 'avgRating']
    
    # 汇总数据
    movie_data = {
        'ratingDistribution': rating_distribution.to_dict('records'),
        'yearDistribution': year_distribution.to_dict('records'),
        'genreDistribution': genre_distribution.to_dict('records'),
        'ratingVsCount': rating_vs_count.to_dict('records'),
        'topMovies': top_movies.to_dict('records'),
        'decadeRating': decade_rating.to_dict('records')
    }
    
    # 保存JSON文件
    with open('movie_data.json', 'w', encoding='utf-8') as f:
        json.dump(movie_data, f, ensure_ascii=False, indent=2)
    print("\nJSON数据文件已生成：movie_data.json")


def main() -> None:
    _setup_style()
    df = load_data()
    if df is None:
        return
    out_dir = "figures"
    basic_stats(df)
    plot_rating_hist(df, out_dir)
    plot_year_line(df, out_dir)
    plot_decade_mix(df, out_dir)
    plot_top_rating(df, out_dir, top_n=20)
    plot_rating_vs_count(df, out_dir)
    plot_category_wordcloud(df, out_dir)
    generate_json_data(df)
    print("\n全部图表已输出到 figures/，已使用多彩配色与多种形式。")
    print("可视化界面已生成：visualization.html")


if __name__ == "__main__":
    main()



