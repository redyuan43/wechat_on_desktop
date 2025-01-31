import logging
import sys

def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('wechat_auto_reply.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.getLogger('comtypes').setLevel(logging.ERROR)

# 常量配置
DEFAULT_REPLY_INTERVAL = 60  # 默认回复间隔(秒)
MIN_OPERATION_INTERVAL = 2   # 最小操作间隔
DEFAULT_CHECK_INTERVAL = (8, 15)  # 默认检查间隔范围(秒)

# LLM模型配置
TEXT_MODEL = 'deepseek-r1:8b'
IMAGE_MODEL = 'llava'

# 特殊账号列表
SPECIAL_ACCOUNTS = [
    '文件传输助手',
    '订阅号',
    '订阅号消息',
    '微信支付',
    '微信团队',
    '服务通知',
    'QQ邮箱提醒',
    '腾讯新闻'
]

# 新年关键词
NEW_YEAR_KEYWORDS = [
    '新年', '春节', '年', '拜年',
    '蛇年', '祝', '福', '恭喜',
    '吉祥', '如意', '快乐', '顺遂',
    '发财', '大吉', '好运', '幸福',
    '祥瑞', '美满', '健康', '平安'
] 