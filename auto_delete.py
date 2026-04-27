import requests
import json
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')

# 删除阈值：progress（百分比）× ratio >= 300
DELETE_THRESHOLD = 300


def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_cookie_file(name):
    safe_name = name.replace('/', '_').replace(':', '_').replace('.', '_')
    return os.path.join(BASE_DIR, f'cookie_{safe_name}')


def load_cookie(name):
    cookie_file = get_cookie_file(name)
    if not os.path.exists(cookie_file):
        return None
    with open(cookie_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    return content if content else None


def save_cookie(name, cookie_str):
    cookie_file = get_cookie_file(name)
    with open(cookie_file, 'w', encoding='utf-8') as f:
        f.write(cookie_str)


def login(base_url, username, password):
    url = f"{base_url}/api/v2/auth/login"
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': f"{base_url}/"
    }
    try:
        resp = requests.post(url, data=f'username={username}&password={password}', headers=headers)
        if resp.text.strip() == 'Ok.':
            sid = resp.cookies.get('SID')
            if sid:
                return f'SID={sid}'
        print(f"登录响应：{resp.text.strip()}")
    except Exception as e:
        print(f"登录请求异常：{e}")
    return None


def is_cookie_valid(base_url, cookie_str):
    url = f"{base_url}/api/v2/app/version"
    headers = {
        'cookie': cookie_str,
        'Referer': f"{base_url}/"
    }
    try:
        resp = requests.get(url, headers=headers)
        return resp.status_code == 200 and resp.text.strip() not in ('', 'Forbidden')
    except Exception:
        return False


def get_torrents(base_url, cookie_str):
    url = f"{base_url}/api/v2/sync/maindata"
    headers = {
        'accept': 'application/json',
        'x-request': 'JSON',
        'x-requested-with': 'XMLHttpRequest',
        'cookie': cookie_str,
        'Referer': f"{base_url}/"
    }
    resp = requests.get(url, headers=headers)
    data = resp.json()
    return data.get('torrents', {})


def reannounce(base_url, cookie_str, torrent_hash):
    url = f"{base_url}/api/v2/torrents/reannounce"
    headers = {
        'accept': 'text/javascript, text/html, application/xml, text/xml, */*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'cookie': cookie_str,
        'Referer': f"{base_url}/"
    }
    resp = requests.post(url, data=f'hashes={torrent_hash}', headers=headers)
    return resp.status_code == 200


def delete_torrent(base_url, cookie_str, torrent_hash):
    url = f"{base_url}/api/v2/torrents/delete"
    headers = {
        'accept': 'text/javascript, text/html, application/xml, text/xml, */*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'x-requested-with': 'XMLHttpRequest',
        'cookie': cookie_str,
        'Referer': f"{base_url}/"
    }
    resp = requests.post(url, data=f'hashes={torrent_hash}&deleteFiles=true', headers=headers)
    return resp.status_code == 200


def process_instance(instance, idx, total_instances):
    name = instance.get('name') or f'instance_{idx}'
    base_url = instance['url'].rstrip('/')
    username = instance['username']
    password = instance['password']

    print(f"{'=' * 50}")
    print(f"[{idx}/{total_instances}] 实例：{name}  ({base_url})")
    print(f"{'=' * 50}")

    # 与 run.py 共用 cookie 文件
    cookie = load_cookie(name)

    if cookie and is_cookie_valid(base_url, cookie):
        print("使用已保存的 cookie")
    else:
        print("cookie 无效或不存在，正在登录...")
        cookie = login(base_url, username, password)
        if not cookie:
            print("登录失败，请检查 config.json 中的用户名和密码，跳过此实例")
            return
        save_cookie(name, cookie)
        print("登录成功，cookie 已保存")

    # 获取所有种子信息
    print("正在获取种子列表...")
    try:
        torrents = get_torrents(base_url, cookie)
    except Exception as e:
        print(f"获取种子列表失败：{e}，跳过此实例")
        return

    if not torrents:
        print("未获取到任何种子")
        return

    total = len(torrents)
    print(f"共获取到 {total} 个种子，开始检查分享率...\n")

    delete_count = 0
    skip_count = 0

    for torrent_hash, info in torrents.items():
        name_torrent = info.get('name', torrent_hash)
        progress = info.get('progress', 0)      # 0.0 ~ 1.0
        ratio = info.get('ratio', 0)
        infohash = info.get('infohash_v1', torrent_hash)

        # progress 转换为百分比后与 ratio 相乘
        score = progress * 100 * ratio

        if score >= DELETE_THRESHOLD:
            print(f"  [待删除] {name_torrent}")
            print(f"           hash: {infohash}")
            print(f"           进度: {progress * 100:.1f}%  分享率: {ratio:.4f}  得分: {score:.1f}%")
            # 先强制汇报一次
            r_ok = reannounce(base_url, cookie, infohash)
            print(f"           强制汇报：{'成功' if r_ok else '失败'}，等待 3 秒后删除...")
            time.sleep(3)
            # 再删除种子和文件
            success = delete_torrent(base_url, cookie, infohash)
            print(f"           删除：{'已删除' if success else '删除失败'}")
            delete_count += 1
        else:
            skip_count += 1

    print(f"\n实例 [{name}] 检查完成：共 {total} 个种子，删除 {delete_count} 个，保留 {skip_count} 个")


def main():
    config = load_config()
    instances = config.get('instances', [])

    if not instances:
        print("config.json 中未配置任何实例，请在 instances 数组中添加配置")
        return

    total_instances = len(instances)
    print(f"[AutoDelete] 阈值：进度(%) × 分享率 >= {DELETE_THRESHOLD}% 时删除种子及文件")
    print(f"共读取到 {total_instances} 个实例配置\n")

    for idx, instance in enumerate(instances, 1):
        process_instance(instance, idx, total_instances)
        if idx < total_instances:
            print()

    print("\n全部实例检查完成")


if __name__ == '__main__':
    main()
