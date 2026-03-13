import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime

def create_rss():
    list_url = "https://sakurazaka46.com/s/s46/diary/blog/list"
    
    fg = FeedGenerator()
    fg.id(list_url)
    fg.title("櫻坂46 公式ブログ RSS")
    fg.link(href=list_url, rel='alternate')
    fg.description("櫻坂46メンバーの公式ブログの最新更新をお届けします")
    fg.language('ja')

    print(f"--- 櫻坂46ブログ 解析開始: {datetime.datetime.now()} ---")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    try:
        res = requests.get(list_url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # ブログの記事リンクを収集
        article_links = soup.find_all('a', href=True)
        blog_posts = []
        for a in article_links:
            href = a['href']
            if '/s/s46/diary/detail/' in href:
                full_url = f"https://sakurazaka46.com{href}" if href.startswith('/') else href
                if not any(post['url'] == full_url for post in blog_posts):
                    blog_posts.append({'url': full_url, 'element': a})

        print(f"見つかった記事の候補数: {len(blog_posts)}件")

        # 最新15件を処理
        for post in blog_posts[:15]:
            url = post['url']
            element = post['element']
            
            # 💡 碧さんが見つけた「魔法の合言葉」でピンポイント抽出！
            title_tag = element.find('h3', class_='title')
            name_tag = element.find('p', class_='name')
            
            # タグの中身のテキストだけを取り出す（もし無ければデフォルト文字を入れる）
            blog_title = title_tag.get_text(strip=True) if title_tag else "タイトルなし"
            member_name = name_tag.get_text(strip=True) if name_tag else "メンバー"

            # RSSのタイトルを「[守屋 麗奈] こんばんは！」のように美しく整形
            final_title = f"[{member_name}] {blog_title}"

            print(f"抽出成功: {final_title}")

            fe = fg.add_entry()
            fe.id(url)
            fe.title(final_title)
            fe.link(href=url)
            fe.description(f"{member_name}のブログが更新されました。\n\nタイトル: {blog_title}\nURL: {url}")
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

        fg.rss_file('feed.xml')
        print("🎉 完璧な feed.xml の生成が完了しました！")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    create_rss()