from urllib.parse import urljoin

from bs4 import BeautifulSoup
from tornado import gen, httpclient, ioloop, queues

base_url = "http://tornadoweb.org/en/stable/"
concurrency = 3


async def get_link_url(url):
    reponse = await httpclient.AsyncHTTPClient().fetch("http://tornadoweb.org/en/stable/")
    html = reponse.body.decode('utf8')
    soup = BeautifulSoup(html)
    links = [urljoin(base_url, a.get("href")) for a in soup.find_all("a", href=True)]
    return links


async def main():
    q = queues.Queue()
    seent_set = set()

    async def fetch_url(current_url):
        # 生产者
        if current_url in seent_set:
            return

        print("获取：{}".format(current_url))
        seent_set.add(current_url)
        next_urls = await get_link_url(current_url)
        for new_url in next_urls:
            if new_url.startswith(base_url):
                # 放入队列 单线程 (全局的 变量呢--内从操作 没法切换)
                # 这是队列 提供了很多 方法
                await q.put(new_url)

    async def worker():

        async for url in q:
            if url is None:
                return
            try:
                await fetch_url(url)
            except Exception as e:
                print()
            finally:
                q.task_done()

    # 放入初始化 url 放到队列
    await q.put(base_url)

    # 启动协程
    workers = gen.multi([worker() for i in range(concurrency)])
    await q.join()

    for _ in range(concurrency):
        await q.put(None)

    await workers


if __name__ == '__main__':
    # base_url = "http://baidu.com"
    # next_url = "http://taobao.com/bobby/"
    # print(urljoin(base_url, next_url))
    io_loop = ioloop.IOLoop.current()
    io_loop.run_sync(main)
