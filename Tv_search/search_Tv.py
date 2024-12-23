import requests
from lxml import etree
import os
import threading
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def get_url(name):
    try:
        # 配置ChromeOptions以启用无头模式
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # 设置ChromeDriver
        driver = webdriver.Chrome(options=chrome_options)

        # 创建Chrome WebDriver 实例
        # driver = webdriver.Chrome(options=options)

        # 打开指定页面
        driver.get('http://tonkiang.us/')

        username_input = driver.find_element(By.ID, 'search')
        username_input.send_keys(f'{name}')
        submit_button = driver.find_element(By.NAME, 'Submit')
        submit_button.click()

        # 获取页面的源代码
        page_source = driver.page_source

        # 打印源代码
        print(type(page_source))
        m3u8_list = []
        # 将 HTML 转换为 Element 对象
        root = etree.HTML(page_source)
        result_divs = root.xpath("//div[@class='resultplus']")
        print(f"搜索结果页数: {len(result_divs)}")
        # 打印提取到的 <div class="result"> 标签
        for div in result_divs:
            # 如果要获取标签内的文本内容
            # print(etree.tostring(div, pretty_print=True).decode())
            for element in div.xpath(".//tba"):
                if element.text is not None:
                    # m3u8_list.append(element.text.strip())
                    print(element.text.strip())
                    m3u8_list.append(element.text.strip())
                    with open('m3u8_list.txt', 'a', encoding='utf-8') as f:
                        f.write(f'{name},{element.text.strip()}' + '\n')

        # 关闭WebDriver
        driver.quit()
        return m3u8_list

    except requests.exceptions.RequestException as e:
        print(f"Error: 请求异常. Exception: {e}")
        return


def download_m3u8(url, name, initial_url=None):
    try:
        # 下载M3U8文件
        # with requests.get(url, timeout=10) as response:
        #     response.raise_for_status()
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()  # 检查请求是否成功
        m3u8_content = response.text
    except requests.exceptions.Timeout as e:
        print(f"{url}\nError: 请求超时. Exception: {e}")
        return
    except requests.exceptions.RequestException as e:
        print(f"{url}\nError: 请求异常. Exception: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return
    else:
        # 解析M3U8文件，获取视频片段链接
        lines = m3u8_content.split('\n')
        segments = [line.strip() for line in lines if line and not line.startswith('#')]
        if len(segments) == 1:
            # 在递归调用时传递 initial_url 参数
            return download_m3u8(segments[0], name, initial_url=initial_url if initial_url is not None else url)

        # 下载指定数量的视频片段并计算下载速度
        total_size = 0
        total_time = 0
        for i, segment in enumerate(segments[:3]):
            start_time = time.time()
            segment_url = url.rsplit('/', 1)[0] + '/' + segment
            response = requests.get(segment_url)
            end_time = time.time()

            # 将视频片段保存到本地
            with open('video.ts', 'wb') as f:
                f.write(response.content)

            # 计算下载速度
            segment_size = len(response.content)
            segment_time = end_time - start_time
            segment_speed = segment_size / segment_time / (1024 * 1024)  # 转换为MB/s

            total_size += segment_size
            total_time += segment_time

            print(f"Downloaded segment {i + 1}/3: {segment_speed:.2f} MB/s")

        # 计算平均下载速度
        average_speed = total_size / total_time / (1024 * 1024)  # 转换为MB/s
        print(f"---{name}---Average Download Speed: {average_speed:.2f} MB/s")
        # print(f"---{name}---平均速度: {average_speed:.2f} MB/s")

        # 速度阈值，默认1MB/s
        if average_speed >= speed:
            valid_url = initial_url if initial_url is not None else url
            if not os.path.exists(f'{TV_name}'):
                os.makedirs(f'{TV_name}')
            with open(os.path.join(f'{TV_name}', f'{name}.txt'), 'a', encoding='utf-8') as file:
                file.write(f'{name},{valid_url}\n')
            print(f"---{name}---链接有效源已保存---\n"
                  f"----{valid_url}---")
            return


def detectLinks(name, m3u8_list):
    thread = []
    for m3u8_url in m3u8_list:
        t = threading.Thread(target=download_m3u8, args=(m3u8_url, name,))
        t.daemon = True  # 设置为守护线程,确保在主线程退出时，所有子线程都会被强制终止
        t.start()
        thread.append(t)
    # 等待所有线程完成
    for t in thread:
        try:
            print(f"Waiting for thread {t} to finish")
            t.join(timeout=10)  # 等待线程超时
        except Exception as e:
            print(f"Thread {t.name} raised an exception: {e}")


def mer_links(tv):
    # 获取文件夹中的所有 txt 文件
    txt_files = [f for f in os.listdir(os.path.join(current_directory, f'{tv}'))]
    print(txt_files)
    # 打开合并后的文件，使用 'a' 模式以追加的方式写入
    with open(output_file_path, 'a', encoding='utf-8') as output_file:
        output_file.write(f'{tv},#genre#' + '\n')
        for txt_file in txt_files:
            # 拼接文件的完整路径
            file_path = os.path.join(os.path.join(current_directory, f'{tv}'), txt_file)

            # 打开当前 txt 文件并读取内容
            with open(file_path, 'r', encoding='utf-8') as input_file:
                file_content = input_file.read()

                # 将当前 txt 文件的内容写入合并后的文件
                output_file.write(file_content)

                # 可以选择在每个文件之间加入换行，使合并后的内容更清晰
                output_file.write('\n')

    print(f'Merged content from {len(txt_files)} files into {output_file_path}')


def re_dup(filepath):
    from collections import OrderedDict
    # 读取文本文件
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 保持原始顺序的去重
    unique_lines_ordered = list(OrderedDict.fromkeys(lines))
    # 将去重后的内容写回文件
    with open(filepath, 'w', encoding='utf-8') as file:
        file.writelines(unique_lines_ordered)
    print('-----直播源去重完成！------')


if __name__ == '__main__':
    # print('说明：\n'
    #       '速度阈值默认为1\n'
    #       '阈值越大，直播流速度越快，检索出的直播流数量越少\n'
    #       '建议日常阈值最小0.3，能够满足日常播放流不卡顿\n')
    # speed = input('请直接回车确定或输入阈值:  ')
    # if speed == '':
    #     speed = 1
    # else:
    #     speed = float(speed)
    speed = 1
    # 获取当前工作目录
    current_directory = os.getcwd()
    # 构造上级目录的路径
    parent_dir = os.path.dirname(current_directory)
    output_file_path = os.path.join(parent_dir, 'live.txt')
    # 清空live.txt内容
    with open(output_file_path, 'w', encoding='utf-8') as f:
        pass
    with open('m3u8_list.txt', 'w', encoding='utf-8') as file:
        pass
    tv_dict = {}
    # 遍历当前文件下的txt文件,提取文件名
    TV_names = [os.path.splitext(f)[0] for f in os.listdir(current_directory) if f.endswith(".txt")]
    # '🇭🇰港台'  '🇨🇳卫视频道'  '🇨🇳央视频道'
    # TV_names = ['🇨🇳央视频道','🇭🇰港台']
    for TV_name in TV_names:
        # 删除历史测试记录，防止文件追加写入
        if os.path.exists(TV_name):
            import shutil

            # 删除文件夹及其内容
            try:
                shutil.rmtree(TV_name)
                print(f"Folder '{TV_name}' deleted successfully.")
            except OSError as e:
                print(f"Error deleting folder '{TV_name}': {e}")
        time.sleep(1)
        if not os.path.exists(TV_name):
            os.makedirs(TV_name)
        # 读取文件并逐行处理ls
        with open(f'{TV_name}.txt', 'r', encoding='utf-8') as file:
            names = [line.strip() for line in file]
            for name in names:
                m3u8_list = get_url(name)
                tv_dict[name] = m3u8_list
                print(name)
            print('---------字典加载完成！------------')
        for name, m3u8_list in tv_dict.items():
            detectLinks(name, m3u8_list)
        # 合并有效直播源m3u8链接
        mer_links(TV_name)
        tv_dict.clear()

    time.sleep(10)
    os.remove('video.ts')
    # 直播源去重
    re_dup(output_file_path)

    sys.exit()
