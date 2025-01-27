# 微信自动回复程序

这是一个基于Python的微信自动回复程序，使用Windows UI Automation实现稳定的自动回复功能。

## 主要特性

- 使用Windows UI Automation技术，更稳定可靠
- 支持检测未读消息并自动回复
- 智能防重复回复机制（默认60秒内不重复回复同一联系人）
- 完整的日志记录系统

## 环境要求

- Python 3.7+
- Windows 11/10 操作系统
- 微信桌面版（请确保已登录）
- Ollama（用于本地LLM支持）

## Ollama 安装

1. 访问 [Ollama官方网站](https://ollama.ai/download) 下载Windows版本安装包
2. 运行安装包完成安装
3. 打开命令行，运行以下命令拉取所需模型：
```bash
ollama pull qwen:7b
```
4. 确认Ollama服务正在运行（默认监听在localhost:11434端口）

## 安装步骤

1. 安装所需依赖：
```bash
pip install -r requirements.txt
```

2. 运行程序：
```bash
python wechat_auto_reply.py
```

## 使用说明

1. 确保微信已登录并保持打开状态
2. 运行程序后，它会自动检测未读消息
3. 当检测到未读消息时，会自动发送回复
4. 按 Ctrl+C 可以退出程序

## 配置说明

可以在代码中修改以下参数：
- `auto_reply_message`: 自动回复的消息内容
- `reply_interval`: 对同一联系人的回复间隔（秒）

## 注意事项

- 请确保微信窗口处于打开状态
- 不要最小化微信窗口
- 程序运行时请不要手动操作微信窗口
- 所有操作日志都会记录在 `wechat_auto_reply.log` 文件中

## 免责声明

本程序仅供学习和个人使用，请勿用于商业用途。使用本程序产生的任何后果由使用者自行承担。 
