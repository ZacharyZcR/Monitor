from flask import Flask, request, Response, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# 检查URL是否有效
def is_valid_url(url):
    return re.match(r'^(http|https)://', url) is not None

# 将相对链接转换为绝对链接
def make_links_absolute(soup, base_url):
    # 处理常见资源标签
    tags_attributes = {
        'a': 'href',
        'link': 'href',
        'script': 'src',
        'img': 'src',
        'iframe': 'src',
        'video': 'src',
        'audio': 'src',
        'source': 'src',
        'track': 'src',
        'embed': 'src',
        'object': 'data',
        'form': 'action',
        'input': 'src'
    }

    for tag, attribute in tags_attributes.items():
        for element in soup.find_all(tag, **{attribute: True}):
            element[attribute] = requests.compat.urljoin(base_url, element[attribute])

    return soup


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if not is_valid_url(url):
        return "无效的URL。请包括http://或https://", 400

    headers = {
        'User-Agent': request.headers.get('User-Agent'),
        'Accept': request.headers.get('Accept'),
        'Accept-Language': request.headers.get('Accept-Language'),
        'Referer': url,
    }

    try:
        response = requests.get(url, headers=headers, allow_redirects=True)
        response.raise_for_status()  # 检查请求是否成功
    except requests.exceptions.RequestException as e:
        return f"请求错误: {str(e)}", 500

    if 'text/html' in response.headers['Content-Type']:
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        soup = make_links_absolute(soup, url)
        return Response(str(soup), content_type=response.headers['Content-Type'])
    else:
        return Response(response.content, content_type=response.headers['Content-Type'])

@app.route('/get_selector', methods=['POST'])
def get_selector():
    selector = request.form['selector']
    content = request.form['content']
    try:
        # 打印接收到的选择器和内容
        print('接收到的选择器:', selector)
        print('接收到的内容:', content)
        return jsonify({'status': 'success', 'selector': selector, 'content': content})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
