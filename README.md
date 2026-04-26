# AutoReannounce

自动对 qBittorrent 中所有种子执行强制汇报（Force Reannounce），解决因 tracker 汇报不及时导致的下载/上传速度下降问题。支持同时管理多个 qBittorrent 实例。

---

## 功能特性

- 自动登录 qBittorrent Web UI，获取并持久化保存 cookie
- cookie 有效时直接复用，失效或不存在时自动重新登录
- 获取当前所有种子，逐一执行强制汇报，每次间隔 3 秒
- 支持配置多个 qBittorrent 实例，依次完成汇报后自动退出
- 单个实例失败（网络异常、密码错误等）自动跳过，不影响其他实例

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
├── run.py            # 主脚本
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

### 直接运行

在项目目录下执行：

```bash
python run.py
```

### 运行输出示例

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

==================================================
[2/2] 实例：qbit2  (http://127.0.0.2:8080)
==================================================
使用已保存的 cookie
正在获取种子列表...
...

全部实例汇报完成
```

---

## 设置定时自动运行（Windows 任务计划程序）

如果希望脚本定期自动执行（例如每隔 30 分钟运行一次），可以使用 Windows 任务计划程序：

1. 按 `Win + S` 搜索并打开 **任务计划程序**

2. 点击右侧 **创建基本任务**，填写名称（如 `AutoReannounce`）

3. **触发器** 选择 **每天**，然后在下一步选择 **重复任务间隔** 为 `30 分钟`（在任务属性中设置）

4. **操作** 选择 **启动程序**：
   - 程序或脚本：填写 Python 可执行文件路径，例如：
     ```
     C:\Python311\python.exe
     ```
   - 添加参数：
     ```
     run.py
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
A：cookie 文件保存登录会话，下次运行时复用以避免重复登录。删除后脚本会在下次运行时重新登录并自动生成。

**Q：如何强制重新登录？**  
A：删除对应实例的 cookie 文件（如 `cookie_qbit1`）即可，下次运行会自动重新登录。
