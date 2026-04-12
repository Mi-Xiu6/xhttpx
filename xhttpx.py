import threading
import csv
import time
import os

import urllib3
import requests
import xlrd

# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置
thread_num = 150
timeout = 5
lock = threading.Lock()
targets = []
result_hosts = []

text = """\033[33m
'##::::'##:'##::::'##:'########:'########:'########::'##::::'##:
. ##::'##:: ##:::: ##:... ##..::... ##..:: ##.... ##:. ##::'##::
:. ##'##::: ##:::: ##:::: ##::::::: ##:::: ##:::: ##::. ##'##:::
::. ###:::: #########:::: ##::::::: ##:::: ########::::. ###::::
:: ## ##::: ##.... ##:::: ##::::::: ##:::: ##.....::::: ## ##:::
: ##:. ##:: ##:::: ##:::: ##::::::: ##:::: ##::::::::: ##:. ##::
 ##:::. ##: ##:::: ##:::: ##::::::: ##:::: ##:::::::: ##:::. ##:
..:::::..::..:::::..:::::..::::::::..:::::..:::::::::..:::::..::
\033[0m\033[31m
[*]免责声明：本工具仅用于学习和合法的安全测试，使用本工具需遵守相关法律法规，因滥用本工具造成的一切后果由使用者自行承担
[*] 一款批量探测域名存活的httpx工具，支持txt、scv、xlsx格式\033[0m\033[32m
[*] BY.米修
[*] 联系方式: Dr-xiu6
[*] https://github.com/Mi-Xiu6/xhttpx\033[0m
"""
print(text, end="")
host = input('\033[32m[*]请输入需要探测的文件:\033[0m')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:148.0) Gecko/20100101 Firefox/148.0'
}

txt_file = host
csv_file = host
xlsx_file = host
result_file = "存活域名.txt"

# 清空结果文件
if os.path.exists(result_file):
    open(result_file, 'w').close()

# 根据文件扩展名选择读取方式
file_ext = os.path.splitext(host)[1].lower()

if file_ext == '.txt':
    # 读取txt文件
    try:
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    targets.append(line)
        print(f'[*] 从txt文件读取了 {len(targets)} 个目标')
    except Exception as e:
        print(f'[!] 读取txt文件失败: {e}')

elif file_ext == '.csv':
    # 读取csv文件
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for line in reader:
                if line:
                    url = str(line[0]).strip()
                    if url and url != 'None':
                        targets.append(url)
        print(f'[*] 从csv文件读取了 {len(targets)} 个目标')
    except Exception as e:
        print(f'[!] 读取csv文件失败: {e}')

elif file_ext in ['.xlsx', '.xls']:
    # 读取xlsx文件
    try:
        workbook = xlrd.open_workbook(xlsx_file)
        sheet = workbook.sheet_by_index(0)
        for line in range(sheet.nrows):
            url = str(sheet.cell_value(line, 0)).strip()
            if url and url != 'None':
                targets.append(url)
        print(f'[*] 从xlsx文件读取了 {len(targets)} 个目标')
    except Exception as e:
        print(f'[!] 读取xlsx文件失败: {e}')
else:
    # 默认按txt格式读取
    try:
        with open(host, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    targets.append(line)
        print(f'[*] 从文件读取了 {len(targets)} 个目标')
    except Exception as e:
        print(f'[!] 读取文件失败: {e}')

# 去重
targets = list(set(targets))
print(f'[*] 待探测的域名数量: {len(targets)}')
print('[*] 开始探测...\n')

start_time = time.time()
threads = []

def scan(target_url):
    # 添加协议前缀
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    
    try:
        response = requests.get(target_url, headers=headers, timeout=timeout, verify=False)
        response.encoding = 'utf-8'
        if response.status_code in [200, 301, 302]:
            msg = f'[*]响应[{response.status_code}] -> {target_url} -> \033[32m存活\033[0m'
            with lock:
                result_hosts.append(target_url)
                with open(result_file, 'a', encoding='utf-8') as f:
                    f.write(f'{target_url}\n')
                print(msg)
        else:
            msg = f'[*]响应[{response.status_code}] -> {target_url} -> \033[31m死亡\033[0m'
            with lock:
                print(msg)
    except:
        # HTTPS失败则尝试HTTP
        if target_url.startswith('https://'):
            http_url = target_url.replace('https://', 'http://')
            try:
                response = requests.get(http_url, headers=headers, timeout=timeout, verify=False)
                response.encoding = 'utf-8'
                if response.status_code in [200, 301, 302]:
                    msg = f'[*]响应[{response.status_code}] -> {http_url} -> \033[32m存活\033[0m'
                    with lock:
                        result_hosts.append(http_url)
                        with open(result_file, 'a', encoding='utf-8') as f:
                            f.write(f'{http_url}\n')
                        print(msg)
                    return
            except:
                pass
        
        msg = f'[*]请求失败 -> {target_url} -> \033[31m死亡\033[0m'
        with lock:
            print(msg)

# 启动多线程探测
for target in targets:
    t = threading.Thread(target=scan, args=(target,))
    threads.append(t)
    t.start()
    # 控制并发线程数
    if len(threads) >= thread_num:
        for t in threads:
            t.join()
        threads.clear()
for t in threads:
    t.join()

end_time = time.time()
finish_time = end_time - start_time

print(f'\n{"="*50}')
print(f'[*] 探测完成！')
print(f'[*] 存活域名数量: {len(result_hosts)} 个')
print(f'[*] 总耗时: {finish_time:.2f} 秒')
print(f'[*] 结果已保存到: {result_file}')
print(f'{"="*50}')
