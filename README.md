# 研究生择校数据系统

这是一个独立于 `finai` 的新项目骨架，包含：

- `miniapp/`：微信小程序前端，首页是 AI 解读
- `backend/`：FastAPI 后端，提供择校查询与推荐 API

当前版本已切换到 MySQL 数据库结构，后端默认连接 `kaoyan_system_v2`。

## 目录

```text
grad-school-data-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── data/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   └── requirements.txt
└── miniapp/
    ├── app.js
    ├── app.json
    ├── app.wxss
    ├── project.config.json
    ├── pages/
    └── utils/
```

## 后端启动

```bash
cd /Users/face/Desktop/grad-school-data-system/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 可参考 backend/.env.example
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=你的数据库密码
export DB_NAME=kaoyan_system_v2
uvicorn app.main:app --reload
```

默认地址：

- API 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 健康检查：[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## 小程序打开方式

1. 用微信开发者工具打开 `/Users/face/Desktop/grad-school-data-system/miniapp`
2. 把 `miniapp/utils/request.js` 里的 `BASE_URL` 改成你的本机局域网地址，例如 `http://192.168.1.8:8000/api/v1`
3. 在开发者工具里关闭或配置合法域名校验用于本地调试

启动前请先在 MySQL 中执行：

- [kaoyan_system_v2_fresh_schema.sql](/Users/face/Desktop/grad-school-data-system/backend/sql/kaoyan_system_v2_fresh_schema.sql)
- [kaoyan_system_v2_reporting.sql](/Users/face/Desktop/grad-school-data-system/backend/sql/kaoyan_system_v2_reporting.sql)

并导入至少一批基础数据到：

- `schools`
- `majors`
- `school_majors`
- `enrollment_records`
- `score_lines`

## 当前已实现

- AI 解读首页
- 院校列表
- 院校详情
- 专业列表
- 我的页面占位
- FastAPI MySQL 查询接口
- 基于真实库的冲稳保推荐接口
- AI 解读编排接口

## 下一步建议

1. 增加旧表到新表的迁移脚本
2. 增加管理后台导入与审核
3. 接入真实微信登录
4. 用更细的规则引擎增强 AI 推荐解释
