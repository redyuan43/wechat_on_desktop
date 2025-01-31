# 微信自动拜年回复程序

这是一个基于Python的微信自动拜年回复程序，可以自动检测并回复新年祝福消息。

## 功能特点

- 自动检测新的微信消息
- 智能识别拜年祝福
- 使用LLM生成个性化回复
- 支持多个微信窗口
- 防止重复回复
- 人性化的操作间隔
- 支持手动取消发送

## 系统要求

- Windows 10/11
- Python 3.8+
- 微信PC版

## 依赖安装

```bash
pip install -r requirements.txt
```

## 使用说明

1. 确保已安装所有依赖
2. 确保微信已登录并保持打开状态
3. 运行程序：

```bash
python main.py
```

## 注意事项

1. 请确保微信窗口不要最小化
2. 程序运行时请不要手动操作微信窗口
3. 按Ctrl+C可以退出程序
4. 发送消息前有3秒确认时间，可按Ctrl+Q取消发送

## 目录结构

```
.
├── main.py                 # 主运行文件
├── requirements.txt        # 依赖文件
├── README.md              # 说明文档
└── src/                   # 源代码目录
    ├── __init__.py       # 包初始化文件
    ├── wechat_auto_reply.py  # 主程序文件
    ├── services/         # 服务模块
    │   ├── llm_service.py    # LLM服务
    │   └── ui_automation.py  # UI自动化服务
    ├── handlers/         # 处理器模块
    │   └── message_handler.py # 消息处理
    └── utils/            # 工具模块
        └── config.py     # 配置文件
```

## 配置说明

- 在`src/utils/config.py`中可以修改：
  - 回复间隔时间
  - 特殊账号列表
  - 新年关键词
  - LLM模型配置

## 许可证

MIT License 