# AutoReannounce

qBittorrent 自动化工具集，包含两个独立脚本，共用同一份配置文件和 cookie，支持同时管理多个 qBittorrent 实例。

| 脚本 | 功能 |
|------|------|
| `reannounce.py` | 对所有种子执行强制汇报（Force Reannounce），解决 tracker 汇报不及时导致的掉速问题 |
| `auto_delete.py` | 自动检测并删除满足条件的种子：**进度(%) × 分享率 ≥ 300** 时删除种子及本地文件 |

---

## 功能特性

**通用：**
- 自动登录 qBittorrent Web UI，获取并持久化保存 cookie
- cookie 有效时直接复用，失效或不存在时自动重新登录
- 支持配置多个 qBittorrent 实例，两个脚本共用同一套 cookie 文件
- 单个实例失败（网络异常、密码错误等）自动跳过，不影响其他实例

**reannounce.py（强制汇报）：**
- 获取当前所有种子，逐一执行强制汇报，每次间隔 3 秒
- 所有种子汇报完成后自动退出

**auto_delete.py（自动删除）：**
- 获取每个种子的下载进度和分享率，计算得分：`进度(%) × 分享率`
- 得分 ≥ 300 时自动删除种子及本地文件（例：进度 30% × 分享率 10 = 300）
- 打印每个被删除种子的名称、hash、进度、分享率和得分

---

## 环境要求

- Python 3.7 及以上
- 第三方库：`requests`

安装依赖：

```bash
pip3 install requests
```

---

## 目录结构

```
AutoReannounce/
├── reannounce.py     # 强制汇报脚本
├── auto_delete.py    # 自动删除脚本
├── config.json       # 配置文件（实例地址、账号密码）
├── cookie_qbit1      # 自动生成，实例 qbit1 的登录 cookie
├── cookie_qbit2      # 自动生成，实例 qbit2 的登录 cookie
└── README.md
```

> cookie 文件由脚本自动创建和维护，无需手动操作。

---

## 配置说明

编辑项目根目录下的 `config.json`：

```json
{
    "instances": [
        {
            "name": "qbit1",
            "url": "http://127.0.0.1:8080",
            "username": "admin",
            "password": "123456"
        },
        {
            "name": "qbit2",
            "url": "http://127.0.0.2:8080",
            "username": "admin",
            "password": "123456"
        }
    ]
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 否 | 实例标识名，用于区分 cookie 文件，不填则自动命名为 `instance_1`、`instance_2`…，建议填写 |
| `url` | 是 | qBittorrent Web UI 的完整地址，末尾不需要加 `/` |
| `username` | 是 | Web UI 登录用户名 |
| `password` | 是 | Web UI 登录密码 |

### 只有一个实例时

`instances` 数组中只保留一项即可：

```json
{
    "instances": [
        {
            "name": "home",
            "url": "http://192.168.1.100:8080",
            "username": "admin",
            "password": "yourpassword"
        }
    ]
}
```

---

## 使用方法

### 强制汇报（reannounce.py）

```bash
python reannounce.py
```

**输出示例：**

```
共读取到 2 个实例配置

==================================================
[1/2] 实例：qbit1  (http://127.0.0.1:8080)
==================================================
cookie 无效或不存在，正在登录...
登录成功，cookie 已保存
正在获取种子列表...
共获取到 5 个种子，开始强制汇报...

  [1/5] a357577fca1d0c98d7f9e6c21ef2285205daf1ee  成功
  [2/5] 4ae4c34480e9b81388a26cf55beb9cfc38dc67b7  成功
  [3/5] df309c02009ef47156b3c4d58124aa397276b179  成功
  [4/5] 5588fec30163c67811365d616edd36e03e19b95f  成功
  [5/5] be5f191d13a440272d3de9bfe1be64efc6328664  成功

实例 [qbit1] 所有种子汇报完成

全部实例汇报完成
```

---

### 自动删除（auto_delete.py）

```bash
python auto_delete.py
```

**删除判断公式：**

```
进度(%) × 分享率 ≥ 300
```

| 进度 | 分享率 | 得分 | 结果 |
|------|--------|------|------|
| 100% | 3.0 | 300 | 删除 |
| 30% | 10.0 | 300 | 删除 |
| 100% | 2.9 | 290 | 保留 |
| 50% | 5.0 | 250 | 保留 |

**输出示例：**

```
[AutoDelete] 阈值：进度(%) × 分享率 >= 300% 时删除种子及文件
共读取到 1 个实例配置

==================================================
[1/1] 实例：qbit1  (http://127.0.0.1:8080)
==================================================
使用已保存的 cookie
正在获取种子列表...
共获取到 15 个种子，开始检查分享率...

  [删除] Silent.Wedding.2008.1080p.GER.BluRay.AVC
         hash: b1f8aa5c2801aebdd40f12f9cef57f50deb5a6c0
         进度: 100.0%  分享率: 21.9637  得分: 2196.4%  已删除
  [删除] CCTV-5+.2026.Chinese.Womens.Super.League
         hash: d93d3f46f46adf52d30f5bc471a70f5431636d49
         进度: 100.0%  分享率: 27.4425  得分: 2744.3%  已删除

实例 [qbit1] 检查完成：共 15 个种子，删除 2 个，保留 13 个

全部实例检查完成
```

> **注意**：删除操作会同时删除本地文件，请确认阈值设置合理后再运行。如需修改阈值，编辑 `auto_delete.py` 顶部的 `DELETE_THRESHOLD = 300`。

---

## 设置定时自动运行（Windows 任务计划程序）

如果希望脚本定期自动执行，可以使用 Windows 任务计划程序，以下以 `reannounce.py` 每 30 分钟运行一次为例，`auto_delete.py` 配置方式相同。

1. 按 `Win + S` 搜索并打开 **任务计划程序**

2. 点击右侧 **创建基本任务**，填写名称（如 `AutoReannounce`）

3. **触发器** 选择 **每天**，然后在下一步选择 **重复任务间隔** 为 `30 分钟`（在任务属性中设置）

4. **操作** 选择 **启动程序**：
   - 程序或脚本：填写 Python 可执行文件路径，例如：
     ```
     C:\Python311\python.exe
     ```
   - 添加参数（`reannounce.py` 或 `auto_delete.py`）：
     ```
     reannounce.py
     ```
   - 起始于（工作目录）：
     ```
     C:\Users\Administrator\Documents\Project\AutoReannounce
     ```

5. 完成创建后，右键任务选择 **运行** 测试是否正常执行

> **提示**：Python 路径可通过在命令行执行 `where python` 查询。

---

## qBittorrent Web UI 开启方式

若 Web UI 尚未开启，请在 qBittorrent 中按以下步骤操作：

1. 打开 qBittorrent，点击顶部菜单 **工具 → 选项**
2. 切换到 **Web UI** 标签页
3. 勾选 **启用 Web 用户界面（远程控制）**
4. 设置端口（默认 `8080`）、用户名和密码
5. 点击 **应用** 保存

---

## 常见问题

**Q：运行提示「登录失败」**  
A：检查 `config.json` 中的 `url`、`username`、`password` 是否正确；确认 qBittorrent Web UI 已开启且可以用浏览器正常访问。

**Q：运行提示「获取种子列表失败」**  
A：通常是网络不通或 qBittorrent 未运行，检查 `url` 地址是否可以在浏览器中打开。

**Q：cookie 文件是什么，可以删除吗？**  
A：cookie 文件保存登录会话，下次运行时复用以避免重复登录。删除后脚本会在下次运行时重新登录并自动生成。两个脚本共用同一个 cookie 文件，任意一个脚本登录后另一个可直接复用。

**Q：如何强制重新登录？**  
A：删除对应实例的 cookie 文件（如 `cookie_qbit1`）即可，下次运行会自动重新登录。

**Q：auto_delete.py 删除阈值 300 如何修改？**  
A：编辑 `auto_delete.py` 文件顶部的 `DELETE_THRESHOLD = 300`，改为需要的数值即可。

**Q：auto_delete.py 会删除正在下载的种子吗？**  
A：会按公式判断。若种子下载进度为 50%（progress=0.5），分享率需达到 6.0 才会触发删除（0.5×100×6=300），正常下载中的种子分享率通常较低，一般不会被误删。
