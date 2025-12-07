## 豆瓣电影 Top250 信息分析（多彩可视化版）

本项目爬取豆瓣电影 Top250，并生成多彩、精美、多形式的可视化图表。包含完整爬虫、分析与推荐清单。

---

### 快速使用

1) 安装依赖
```bash
pip install -r requirements.txt
```

2) 配置 Cookie  
编辑 `config.py`，将你在浏览器中复制的豆瓣 Cookie 填入 `DOUBAN_COOKIE` 变量。

3) 一键运行
```bash
python main.py
```

运行后生成：
- 结构化数据：`douban_top250.csv`
- 文本清单：`豆瓣电影Top250信息.txt`
- 图表目录：`figures/`（多彩、多形式图）

---

### 项目结构

- `config.py`：存储 Cookie，便于更新（无需改代码）
- `scrape_douban.py`：增强反爬爬虫（Session、随机延迟、调试、动态 referer）
- `analyze_douban.py`：多彩可视化（多配色、条形/折线/散点/双轴等多形式）
- `main.py`：一键运行入口

---

### 可视化亮点

- 使用多套调色板：`Spectral`、`coolwarm`、`cubehelix` 等，避免单色
- 多形式图表：
  - 评分分布（直方图 + KDE）
  - 年份分布（折线）
  - 年代分布（数量 + 平均评分双轴）
  - 评分 Top20（彩色年份条形图）
  - 评分 vs 评价人数（对数散点，多色渐变）
  - 类型 Top15（多彩条形，模拟“词云感”）
- 图表统一采用较大字号、白底网格、彩色渐变，观感更现代

---

### 常见问题

1) 0 条数据 / 被反爬  
   - 更新 `config.py` 中的 Cookie（浏览器 F12 -> Network -> top250 -> 复制 cookie）  
   - 程序会自动保存 `debug_page.html`（第一页），用浏览器打开检查返回内容。

2) 字体/中文显示  
   - 默认尝试 `SimHei`/`Microsoft YaHei`，如有缺失可安装或在代码中修改。

---

### 说明

- 爬虫遵循轻量访问：Session + 随机延迟 + 重试，解析采用多策略以适应页面结构变化。
- 数据持久化：CSV + 文本；分析基于 pandas + seaborn/matplotlib。
- 可视化强调“多彩 + 精美 + 多形式”，便于在报告/GitHub 中展示。



