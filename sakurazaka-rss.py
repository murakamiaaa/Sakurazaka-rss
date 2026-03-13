import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time

def get_blog_detail(session, url):
    """個別のブログ記事にアクセスして、本文と画像（HTML）を丸ごと抜き出す"""
    try:
        # ⚠️ 連続アクセスでサーバーに負荷をかけないためのマナー（必須）
        time.sleep(1)
        
        res = session.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 櫻坂46のブログ本文が入っている箱（クラス名）を探す
        article_box = soup.find('div', class_='box-article')
        
        if article_box:
            # RSSリーダーで画像が正しく表示されるように、画像のURLを「絶対パス」に修正する
            for img in article_box.find_all('img'):
                src = img.get('src')
                if src and src.startswith('/'):
                    img['src'] = f"https://sakurazaka46.com{src}"
            
            # タグを消さずに、HTMLの構造（文字＋画像）をそのまま文字列として返す
            return str(article_box)
        else:
            return "<p>本文の抽出に失敗しました（HTML構造が異なる可能性があります）。</p>"
            
    except Exception as e:
        print(f"個別ページの取得エラー ({url}): {e}")
        return f"<p>記事データの取得に失敗しました: {e}</p>"

def create_rss():
    list_url = "https://sakurazaka46.com/s/s46/diary/blog/list"
    
    fg = FeedGenerator()
    fg.id(list_url)
    fg.title("櫻坂46 公式ブログ (全文・画像あり)")
    fg.link(href=list_url, rel='alternate')
    fg.description("櫻坂46メンバーの公式ブログを全文と画像付きでお届けします")
    fg.language('ja')

    print(f"--- 櫻坂46ブログ 解析開始: {datetime.datetime.now()} ---")

    # セッションを使って通信を効率化
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    })

    try:
        # 1. 一覧ページを取得
        res = session.get(list_url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        article_links = soup.find_all('a', href=True)
        blog_posts = []
        for a in article_links:
            href = a['href']
            if '/s/s46/diary/detail/' in href:
                full_url = f"https://sakurazaka46.com{href}" if href.startswith('/') else href
                if not any(post['url'] == full_url for post in blog_posts):
                    blog_posts.append({'url': full_url, 'element': a})

        print(f"見つかった記事の候補数: {len(blog_posts)}件")

        # 2. 最新の15件を処理し、個別ページにもアクセスする
        for post in blog_posts[:15]:
            url = post['url']
            element = post['element']
            
            title_tag = element.find('h3', class_='title')
            name_tag = element.find('p', class_='name')
            
            blog_title = title_tag.get_text(strip=True) if title_tag else "タイトルなし"
            member_name = name_tag.get_text(strip=True) if name_tag else "メンバー"
            final_title = f"[{member_name}] {blog_title}"

            print(f"解析中: {final_title} ... ", end="")

            # 💡 ここで個別ページにアクセスして全文と画像を取得！
            full_html_content = get_blog_detail(session, url)
            
            if "抽出に失敗" not in full_html_content:
                print("成功！")
            else:
                print("失敗...")

            fe = fg.add_entry()
            fe.id(url)
            fe.title(final_title)
            fe.link(href=url)
            # RSSの本文に、画像付きのHTMLをそのまま流し込む
            fe.description(full_html_content)
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

        fg.rss_file('feed.xml')
        print("🎉 完璧な feed.xml (全文＆画像版) の生成が完了しました！")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    create_rss()