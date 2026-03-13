import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime

def create_rss():
    # 櫻坂46の公式ブログ一覧ページ
    list_url = "https://sakurazaka46.com/s/s46/diary/blog/list"
    
    fg = FeedGenerator()
    fg.id("https://sakurazaka46.com/s/s46/diary/blog/list")
    fg.title("櫻坂46 公式ブログ RSS")
    fg.link(href=list_url, rel='alternate')
    fg.description("櫻坂46メンバーの公式ブログの最新更新をお届けします")
    fg.language('ja')

    print(f"--- 櫻坂46ブログ 解析開始: {datetime.datetime.now()} ---")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }

    try:
        # 1. ブログ一覧ページのHTMLをダウンロード
        res = requests.get(list_url, headers=headers, timeout=10)
        res.raise_for_status()
        
        # 2. BeautifulSoupでHTMLを解析（料理）する
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 3. 記事の「箱」を探す
        # ※仮に <li class="box"> や <div class="com-blog-part"> のような構造を想定して、
        # まずは「ブログの詳細ページへのリンク」を持っているタグを全部探します
        article_links = soup.find_all('a', href=True)
        
        # /s/s46/diary/detail/ （詳細ページのURLパターン）を含むリンクだけを抽出
        blog_posts = []
        for a in article_links:
            href = a['href']
            if '/s/s46/diary/detail/' in href:
                full_url = f"https://sakurazaka46.com{href}" if href.startswith('/') else href
                # 重複を避けるためURLで判定
                if not any(post['url'] == full_url for post in blog_posts):
                    blog_posts.append({'url': full_url, 'element': a})

        print(f"見つかった記事の候補数: {len(blog_posts)}件")

        # 4. 最新の5件だけ処理してみる
        for post in blog_posts[:5]:
            url = post['url']
            element = post['element']
            
            # リンクのテキストを無理やりタイトルとして取得
            title = element.get_text(strip=True)
            if not title:
                title = "タイトルなし（画像リンクなどの可能性）"

            print(f"記事を発見: {title[:20]}... (URL: {url})")

            fe = fg.add_entry()
            fe.id(url)
            fe.title(title)
            fe.link(href=url)
            fe.description(f"最新のブログが更新されました。\n\n確認はこちら: {url}")
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

        fg.rss_file('feed.xml')
        print("🎉 feed.xml の生成テスト完了！")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    create_rss()
