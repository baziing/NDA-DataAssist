# NDA 数据报表自动化系统

本项目是一个基于 [vue-element-admin](https://github.com/PanJiaChen/vue-element-admin) 框架构建的数据报表自动化系统。vue-element-admin 是一个基于 Vue.js 和 Element UI 的后台前端解决方案。本项目提供了一个用户友好的界面，用于生成定制化的数据报表。

## 功能特性

-   **报表模板上传：** 上传 Excel 模板以定义报表结构和数据源。
-   **变量上传：** 上传包含变量的 Excel 文件以定制报表内容。
-   **自动报表生成：** 根据上传的模板和变量自动生成报表。
-   **报表下载：** 下载生成的 Excel 格式报表。
-   **进度跟踪：** 监控报表生成进度。

## 项目结构

```
.
├── backend/             # 后端 Python 代码 (Flask)
│   ├── report_generator_v2.py   # 报表生成逻辑
│   ├── report_task.py          # 报表任务管理
│   ├── config/                 # 配置文件
│   └── tools/                  # 实用工具脚本
├── src/
│   ├── api/
│   │   └── report_api.py       # Flask API 端点
│   ├── assets/                 # 静态资源
│   ├── components/             # Vue 组件
│   ├── router/                 # Vue Router 配置
│   ├── store/                  # Vuex store
│   ├── styles/                 # 样式表
│   ├── utils/                  # 实用工具函数
│   ├── views/                  # Vue 视图
│   ├── App.vue                 # Vue 主组件
│   ├── main.js                 # 应用入口点
│   └── permission.js           # 权限控制
├── .env                    # 环境变量
├── package.json            # 项目依赖和脚本
└── vue.config.js           # Vue CLI 配置
```

## 快速开始

### 前提条件

-   [Node.js](https://nodejs.org/) (>= 8.9) 和 npm (>= 3.0.0)
-   [Git](https://git-scm.com/)
-   [Python](https://www.python.org/) (>= 3.6)
-   数据库 (在 `.env` 中配置)

### 安装

1.  克隆仓库：

    ```bash
    git clone <repository_url>
    cd <project_directory>
    ```

2.  安装前端依赖：

    ```bash
    npm install
    ```

3.  安装后端依赖：
    ```bash
     pip install -r backend/requirements.txt
     # 创建 backend/requirements.txt 并添加以下内容：
     # Flask
     # Flask-CORS
     # python-dotenv
     # pandas
     # openpyxl
     # pymysql  # 如果你使用 MySQL
    ```

### 配置 (.env)

`.env` 文件包含特定于环境的设置。您可能需要根据您的环境创建和修改它。

```
# 数据库配置
DB_HOST='your_db_host'
DB_PORT=3306
DB_USER='your_db_user'
DB_PASSWORD='your_db_password'
DB_DATABASE='your_db_name'

# 邮件配置 (用于发送报表，如果适用)
SMTP_SERVER='your_smtp_server'
SMTP_PORT=465
MAIL_USERNAME='your_email_username'
MAIL_PASSWORD='your_email_password'

# 后端服务器地址和端口
VUE_APP_SERVER_ADDRESS=your_server_ip  # 部署的服务器 IP 地址
VUE_APP_API_PORT=5002
```

### 开发环境

1.  启动开发服务器（前端和后端）：

    ```bash
    npm run start
    ```

    这将同时启动前端开发服务器（通常在端口 9527 上）和后端 Flask 服务器（在端口 5002 上）。

2.  在浏览器中访问应用程序：`http://localhost:9527`（或终端中显示的地址）。

### 构建和部署

1.  构建生产环境的前端：

    ```bash
    npm run build:prod
    ```

    这将在 `dist` 目录中创建包含优化后的前端资源的目录。

2.  以生产模式启动后端服务器：
     - 设置环境变量：`FLASK_ENV=production`
    - 使用 Gunicorn 启动：
    ```
    pip install gunicorn
    gunicorn --bind 0.0.0.0:5002 "src.api.report_api:app"
    ```

3.  通过服务器的 IP 地址和端口访问应用程序。

## 浏览器支持

现代浏览器和 Internet Explorer 10+。

| [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/edge/edge_48x48.png" alt="IE / Edge" width="24px" height="24px" />](https://godban.github.io/browsers-support-badges/)</br>IE / Edge | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/firefox/firefox_48x48.png" alt="Firefox" width="24px" height="24px" />](https://godban.github.io/browsers-support-badges/)</br>Firefox | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/chrome/chrome_48x48.png" alt="Chrome" width="24px" height="24px" />](https://godban.github.io/browsers-support-badges/)</br>Chrome | [<img src="https://raw.githubusercontent.com/alrra/browser-logos/master/src/safari/safari_48x48.png" alt="Safari" width="24px" height="24px" />](https://godban.github.io/browsers-support-badges/)</br>Safari |
| --------- | --------- | --------- | --------- |
| IE10, IE11, Edge | last 2 versions | last 2 versions | last 2 versions |

## 许可证

[MIT](https://github.com/PanJiaChen/vue-element-admin/blob/master/LICENSE)

Copyright (c) 2017-present PanJiaChen (vue-element-admin framework)
