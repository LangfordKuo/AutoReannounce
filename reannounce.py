import requests
import json
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config.json')


def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_cookie_file(name):
    # 用实例 name 作为 cookie 文件名后缀，避免多实例冲突
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


def get_torrent_hashes(base_url, cookie_str):
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
    return list(data.get('torrents', {}).keys())


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


def process_instance(instance, idx, total_instances):
    name = instance.get('name') or f'instance_{idx}'
    base_url = instance['url'].rstrip('/')
    username = instance['username']
    password = instance['password']

    print(f"{'=' * 50}")
    print(f"[{idx}/{total_instances}] 实例：{name}  ({base_url})")
    print(f"{'=' * 50}")

    # 尝试读取已保存的 cookie
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

    # 获取所有种子 hash
    print("正在获取种子列表...")
    try:
        hashes = get_torrent_hashes(base_url, cookie)
    except Exception as e:
        print(f"获取种子列表失败：{e}，跳过此实例")
        return

    if not hashes:
        print("未获取到任何种子")
        return

    total = len(hashes)
    print(f"共获取到 {total} 个种子，开始强制汇报...\n")

    for i, h in enumerate(hashes, 1):
        success = reannounce(base_url, cookie, h)
        status = "成功" if success else "失败"
        print(f"  [{i}/{total}] {h}  {status}")
        if i < total:
            time.sleep(3)

    print(f"\n实例 [{name}] 所有种子汇报完成")


def main():
    config = load_config()
    instances = config.get('instances', [])

    if not instances:
        print("config.json 中未配置任何实例，请在 instances 数组中添加配置")
        return

    total_instances = len(instances)
    print(f"共读取到 {total_instances} 个实例配置\n")

    for idx, instance in enumerate(instances, 1):
        process_instance(instance, idx, total_instances)
        if idx < total_instances:
            print()

    print("\n全部实例汇报完成")


if __name__ == '__main__':
    main()
