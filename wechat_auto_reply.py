import uiautomation as auto
import time
import logging
import sys
from datetime import datetime
import ollama
import random

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 改为DEBUG级别以显示更多信息
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wechat_auto_reply.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 过滤掉 comtypes 的初始化信息
logging.getLogger('comtypes').setLevel(logging.ERROR)

class WeChatAutoReply:
    def __init__(self):
        self.running = True
        self.last_reply_time = {}  # 用于存储对每个联系人的最后回复时间
        self.reply_interval = 60  # 对同一个联系人的回复间隔（秒）
        self.last_operation_time = 0  # 记录上次操作时间
        self.min_operation_interval = 2  # 最小操作间隔
        self.current_window_index = 0  # 当前处理的微信窗口索引
        try:
            self.ollama_client = ollama
            # 初始化两个模型：文本模型和多模态模型
            self.text_model = 'deepseek-r1:8b'
            self.image_model = 'llava'
            logging.info("成功初始化Ollama客户端")
        except Exception as e:
            logging.error(f"初始化Ollama客户端失败: {str(e)}")
            raise
        
    def random_sleep(self, min_seconds=0.5, max_seconds=2):
        """随机休眠一段时间"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        time.sleep(sleep_time)
        return sleep_time

    def ensure_operation_interval(self):
        """确保操作之间有足够的间隔"""
        current_time = time.time()
        if current_time - self.last_operation_time < self.min_operation_interval:
            time.sleep(self.min_operation_interval)
        self.last_operation_time = time.time()

    def find_all_wechat_windows(self):
        """查找所有微信主窗口"""
        try:
            # 查找所有微信主窗口
            wechat_windows = []
            all_windows = auto.GetRootControl().GetChildren()
            for window in all_windows:
                try:
                    if window.ClassName == 'WeChatMainWndForPC':
                        wechat_windows.append(window)
                except:
                    continue
            
            if not wechat_windows:
                logging.error("未找到任何微信窗口，请确保微信已登录并打开")
                return []
            
            logging.info(f"找到 {len(wechat_windows)} 个微信窗口")
            return wechat_windows
        except Exception as e:
            logging.error(f"查找微信窗口时出错: {str(e)}")
            return []

    def switch_to_next_window(self, wechat_windows):
        """切换到下一个微信窗口"""
        if not wechat_windows:
            return None
        
        # 更新当前窗口索引
        self.current_window_index = (self.current_window_index + 1) % len(wechat_windows)
        current_window = wechat_windows[self.current_window_index]
        
        try:
            # 确保窗口处于前台
            if current_window.SetFocus():
                logging.info(f"切换到第 {self.current_window_index + 1} 个微信窗口")
                # 等待窗口完全激活
                time.sleep(1)
                
                # 尝试点击左侧区域以确保焦点回到会话列表
                try:
                    # 获取窗口位置
                    rect = current_window.BoundingRectangle
                    # 计算左侧区域的位置（窗口左边缘往右100像素，垂直中间位置）
                    x = rect.left + 100
                    y = (rect.top + rect.bottom) // 2
                    # 点击左侧区域
                    auto.Click(x, y)
                    self.random_sleep(0.5, 1)
                    
                    # 再次尝试通过快捷键切换到会话列表
                    auto.SendKeys('{Alt}1')
                    self.random_sleep(0.5, 1)
                except Exception as e:
                    logging.warning(f"尝试点击左侧区域时出错: {str(e)}")
                
                return current_window
            else:
                logging.warning(f"无法将第 {self.current_window_index + 1} 个微信窗口置于前台")
                return None
        except Exception as e:
            logging.error(f"切换窗口时出错: {str(e)}")
            return None

    def find_chat_list_panel(self, wechat_window):
        """使用多种方式查找会话列表面板"""
        try:
            # 方法1：直接查找ListBox
            panel = wechat_window.ListControl(Name="会话")
            if panel.Exists():
                logging.info("通过ListControl找到会话列表")
                return panel

            # 方法2：查找特定类名的面板
            panel = wechat_window.PaneControl(ClassName="ListBox")
            if panel.Exists():
                logging.info("通过PaneControl找到会话列表")
                return panel

            # 方法3：通过层级查找
            left_panel = wechat_window.PaneControl(Name="左侧区域")
            if left_panel.Exists():
                panel = left_panel.ListControl()
                if panel.Exists():
                    logging.info("通过左侧区域找到会话列表")
                    return panel

            # 方法4：遍历所有面板
            all_panes = wechat_window.GetChildren()
            logging.info(f"找到 {len(all_panes)} 个顶级面板")
            for pane in all_panes:
                try:
                    # 打印面板信息用于调试
                    logging.debug(f"面板: Name={pane.Name}, ClassName={pane.ClassName}")
                    if pane.ClassName in ["ListBox", "List", "ListView"]:
                        logging.info(f"通过遍历找到可能的会话列表: {pane.ClassName}")
                        return pane
                except:
                    continue

            logging.error("未找到会话列表面板")
            return None
        except Exception as e:
            logging.error(f"查找会话列表面板时出错: {str(e)}")
            return None

    def is_group_chat(self, item_name, item_value):
        """判断是否为群聊"""
        if not item_name:
            return False
            
        # 更严格的群聊检测
        # 1. 检查群聊特征
        group_indicators = [
            '群聊',
            '群',
            '交流群',
            '讨论组',
            '社群',
            '商会',
            '协会',
            '班级',
            '支部',
            '联盟',
            '内购群',
            '粉丝群'
        ]
        
        # 2. 检查消息内容特征
        message_indicators = [
            '个成员',
            '[群消息]',
            '条]',
            '消息免打扰'
        ]
        
        # 检查名称中是否包含群聊特征
        is_group_by_name = any(indicator in item_name for indicator in group_indicators)
        
        # 检查消息内容中的群聊特征
        is_group_by_value = False
        if item_value:
            is_group_by_value = any(indicator in item_value for indicator in message_indicators)
        
        return is_group_by_name or is_group_by_value

    def is_special_account(self, item_name):
        """判断是否为特殊账号（不需要回复的系统账号）"""
        special_accounts = [
            '文件传输助手',
            '订阅号',
            '订阅号消息',
            '微信支付',
            '微信团队',
            '服务通知',
            'QQ邮箱提醒',
            '腾讯新闻'
        ]
        return item_name in special_accounts

    def check_new_message(self, wechat_window):
        """检查是否有新消息"""
        try:
            # 查找会话列表面板
            chat_list_panel = self.find_chat_list_panel(wechat_window)
            if not chat_list_panel:
                return None
            
            # 获取所有聊天项
            chat_items = chat_list_panel.GetChildren()
            logging.info(f"找到 {len(chat_items)} 个会话项")
            
            for i, item in enumerate(chat_items):
                try:
                    item_name = item.Name
                    item_class = item.ClassName
                    item_value = ""
                    
                    try:
                        item_value = item.GetValuePattern().Value
                    except:
                        pass

                    # 检查是否是特殊账号
                    if self.is_special_account(item_name):
                        logging.info(f"跳过特殊账号: {item_name}")
                        continue

                    # # 记录详细的群聊检测信息
                    # if self.is_group_chat(item_name, item_value):
                    #     logging.info(f"跳过群聊 - 名称: {item_name}, 值: {item_value}")
                    #     continue
                    
                    # 检查是否有新消息
                    has_new_message = False
                    contact_name = None
                    
                    # 提取基本名称（移除"已置顶"和数字）
                    clean_name = item_name.replace("已置顶", "").strip()
                    if "条新消息" in clean_name:
                        name_parts = clean_name.split("条新消息")[0]
                        contact_name = ''.join([i for i in name_parts if not i.isdigit()]).strip()
                        has_new_message = True
                    else:
                        contact_name = clean_name
                    
                    # 检查是否真的有新消息 - 只检查"条新消息"标记
                    has_new_message = "条新消息" in item_name
                    
                    if has_new_message and contact_name:
                        logging.info(f"发现新消息，联系人: {contact_name}")
                        
                        # # 再次确认不是群聊
                        # if self.is_group_chat(contact_name, item_value):
                        #     logging.info(f"二次确认为群聊，跳过: {contact_name}")
                        #     continue
                        
                        # 检查回复间隔
                        current_time = time.time()
                        if contact_name in self.last_reply_time:
                            time_diff = current_time - self.last_reply_time[contact_name]
                            if time_diff < self.reply_interval:
                                logging.info(f"跳过 {contact_name} 的消息（还需等待 {int(self.reply_interval - time_diff)} 秒）")
                                continue

                        # 点击会话获取消息
                        if not self.click_chat_item(wechat_window, item, contact_name):
                            continue

                        # 获取最新消息
                        last_message = self.get_last_message(wechat_window)
                        if not last_message:
                            logging.error("无法获取最后一条消息")
                            continue

                        # 判断是否是拜年信息
                        if not self.is_new_year_greeting(last_message):
                            logging.info(f"不是拜年信息，跳过处理: {last_message}")
                            continue

                        return contact_name
                            
                except Exception as e:
                    logging.error(f"处理会话项 {i+1} 时出错: {str(e)}")
                    continue
            
            return None
        except Exception as e:
            logging.error(f"检查新消息时出错: {str(e)}")
            return None

    def click_chat_item(self, wechat_window, item, contact_name):
        """点击会话项"""
        try:
            self.ensure_operation_interval()
            
            # 先尝试激活窗口
            wechat_window.SetFocus()
            self.random_sleep(0.3, 0.8)
            
            # 点击会话项
            item.SetFocus()
            self.random_sleep(0.2, 0.5)
            
            # 尝试不同的点击方法
            click_success = False
            
            # 方法1：普通点击
            try:
                if item.Click():
                    click_success = True
                    logging.info(f"成功点击会话(方法1): {contact_name}")
            except:
                self.random_sleep(0.1, 0.3)
            
            # 方法2：模拟鼠标点击
            if not click_success:
                try:
                    item.Click(simulateMove=True)
                    click_success = True
                    logging.info(f"成功点击会话(方法2): {contact_name}")
                except:
                    pass
            
            if click_success:
                # 随机等待聊天窗口加载
                self.random_sleep(1.5, 2.5)
                return True
            else:
                logging.error(f"所有点击方法都失败: {contact_name}")
                return False
                
        except Exception as e:
            logging.error(f"点击会话失败: {contact_name}, 错误: {str(e)}")
            return False

    def is_new_year_greeting(self, message):
        """使用Ollama检测是否是拜年信息"""
        try:
            # 首先进行关键词匹配
            new_year_keywords = [
                '新年', '春节', '年', '拜年',
                '蛇年', '祝', '福', '恭喜',
                '吉祥', '如意', '快乐', '顺遂',
                '发财', '大吉', '好运', '幸福',
                '祥瑞', '美满', '健康', '平安'
            ]
            
            # 如果包含关键词，直接判定为拜年信息
            if any(keyword in message for keyword in new_year_keywords):
                logging.info(f"通过关键词匹配判定为拜年信息 - 消息：{message}")
                return True
            
            # 如果关键词匹配失败，再使用LLM判断
            prompt = f"""请判断以下消息是否是拜年信息或新年祝福。请只回答"是"或"否"，不要有任何解释或其他内容。

判断标准：
1. 包含新年、春节、年等相关祝福
2. 表达了祝福、问候的意思
3. 节日相关的祝愿（如：恭喜发财、大吉大利等）

消息内容：{message}

只需要回答一个字："是"或"否"："""
            
            response = self.ollama_client.generate(model='deepseek-r1:8b', prompt=prompt)
            result = response['response'].strip().lower()
            
            # 清理结果，移除可能的标签和额外内容
            result = result.replace('<think>', '').replace('</think>', '')
            result = result.split('\n')[0].strip()  # 只取第一行
            
            # 记录判断结果
            logging.info(f"LLM判断结果 - 消息：{message} - 清理后的结果：{result}")
            
            # 如果LLM返回空或无法判断，使用关键词匹配的结果
            if not result:
                return any(keyword in message for keyword in new_year_keywords)
            
            # 严格判断，只有明确返回"是"才认为是拜年信息
            return result == '是'
        except Exception as e:
            logging.error(f"检测拜年信息时出错: {str(e)}")
            # 发生错误时，使用关键词匹配作为备选方案
            return any(keyword in message for keyword in new_year_keywords)

#    - 结合对方的祝福内容，体现感谢和互祝的情感。

    def generate_greeting_reply(self, original_message):
        """使用Ollama生成个性化拜年回复"""
        try:
            system_prompt = """你是一个春节祝福助手。请生成2025蛇年春节拜年回复。

1. 核心主题：
   - 围绕"蛇年祥瑞"展开，使用灵蛇、金蛇、祥蛇等意象
   - 突出智慧（如"灵蛇献智"）、灵活（如"蛇行顺畅"）、吉祥（如"福寿双全"）等关键词
   - 体现感谢和互祝的情感
   - 但是对方说的祝福语，回复的内容里面不要带相同的祝福语
   - 不要使用"如龙"、"似虎"等任何动物比喻

回复要求：
1. 开头：
   - 必须以感谢开始（如"谢谢"、"感恩"等）
   - 然后再送上祝福

2. 内容：
   - 使用蛇年元素（如：智慧、灵动、吉祥）
   - 包含2-3个祝福点（事业、健康、家庭等）
   - 可以用"蒸蒸日上"、"福寿双全"等传统吉祥语
#    - 可以考虑一些幽默的祝福语

3. 格式：
   - 字数限制在40字以内
   - 语言优美，感情真挚

# 示例回复：
# "谢谢您的祝福！祝您蛇年智慧永伴，事业蒸蒸日上，家庭幸福安康！"
# "感谢美好祝愿！愿您蛇年福气蜿蜒来，智慧如灵蛇，事业展宏图！"

直接输出祝福语，不要有任何解释、标点符号或引号。"""

            user_prompt = f"收到的拜年祝福：{original_message}\n请生成回复："
            
            response = self.ollama_client.generate(
                model='deepseek-r1:8b',
                prompt=f"{system_prompt}\n\n{user_prompt}"
            )
            
            # 获取并清理回复
            reply = response['response'].strip()
            
            # 尝试提取完整的祝福语
            lines = [line.strip() for line in reply.split('\n') if line.strip()]
            # 找到第一个以"谢谢"、"感谢"等开头的行
            start_idx = -1
            for i, line in enumerate(lines):
                if any(line.startswith(word) for word in ["谢谢", "感谢", "感恩"]):
                    start_idx = i
                    break
            
            # 如果找到了起始行，合并从该行开始的所有内容
            if start_idx != -1:
                actual_reply = ' '.join(lines[start_idx:])
            else:
                actual_reply = lines[-1] if lines else ""  # 如果没找到，使用最后一行
            
            # 移除可能的标签
            actual_reply = actual_reply.replace('<think>', '').replace('</think>', '')
            
            # 移除外层的双引号（如果存在）
            actual_reply = actual_reply.strip('"')
            
            # 如果生成的回复为空，使用备选回复
            if not actual_reply:
                return "谢谢您的祝福！祝您蛇年大吉，万事如意！".strip('"')
            
            logging.info(f"生成的回复：{actual_reply}")
            logging.info(f"字数：{len(actual_reply)}")
            
            return actual_reply
            
        except Exception as e:
            logging.error(f"生成拜年回复时出错: {str(e)}")
            return "谢谢您的祝福！祝您蛇年大吉，万事如意！".strip('"')

    def get_last_message(self, wechat_window):
        """获取最后一条消息内容，包括文本和图片"""
        try:
            # 等待消息加载
            time.sleep(1)
            
            # 尝试找到消息列表
            message_list = wechat_window.ListControl(Name="消息")
            if message_list.Exists():
                messages = message_list.GetChildren()
                if messages:
                    last_message = messages[-1]
                    message_text = last_message.Name
                    
                    # 检查是否包含[图片]标记
                    if '[图片]' in message_text:
                        try:
                            # 使用llava模型解析图片内容
                            image_prompt = "请描述这张图片的内容，特别关注是否包含新年祝福、春节元素等。"
                            # 注意：这里需要实现图片获取的逻辑
                            # response = self.ollama_client.generate(model=self.image_model, prompt=image_prompt, images=[image_path])
                            # image_content = response['response'].strip()
                            # return f"{message_text} (图片内容: {image_content})"
                            return message_text  # 暂时返回原始文本
                        except Exception as e:
                            logging.error(f"解析图片内容失败: {str(e)}")
                            return message_text
                    return message_text
            
            return None
        except Exception as e:
            logging.error(f"获取最后一条消息时出错: {str(e)}")
            return None

    def send_auto_reply(self, wechat_window, contact_name):
        """发送自动回复"""
        try:
            # 获取最后一条消息
            last_message = self.get_last_message(wechat_window)
            if not last_message:
                logging.error("无法获取最后一条消息")
                return False

            # 检查是否是拜年信息
            if not self.is_new_year_greeting(last_message):
                logging.info("不是拜年信息，跳过回复")
                return False

            # 生成个性化拜年回复
            reply_message = self.generate_greeting_reply(last_message)
            
            # 确保窗口最大化
            try:
                window_pattern = wechat_window.GetWindowPattern()
                if window_pattern and window_pattern.Current.WindowVisualState != auto.WindowVisualState.Maximized:
                    wechat_window.Maximize()
                    self.random_sleep(0.5, 1)
            except:
                wechat_window.Maximize()
                self.random_sleep(0.5, 1)
            
            logging.info("准备在右下角输入消息...")
            
            try:
                # 移动到右下角并点击（确保激活输入区域）
                rect = wechat_window.BoundingRectangle
                # 计算右下角位置（距离右边和底部各100像素）
                x = rect.right - 100
                y = rect.bottom - 100
                auto.Click(x, y)
                time.sleep(0.5)
                
                # 模拟人工输入，逐字符发送
                for char in reply_message:
                    if char == '\n':
                        auto.SendKeys('{ENTER}')
                    else:
                        auto.SendKeys(char)
                    self.random_sleep(0.05, 0.15)  # 每个字符之间添加随机延迟
                
                self.random_sleep(0.5, 1)
                
                logging.info("消息已输入，等待3秒后发送（按Ctrl+Q取消）...")
                print(f"\n准备向 {contact_name} 发送消息：{reply_message}")
                print("按 Ctrl+Q 取消发送...")
                
                # 等待3秒，检查是否按下Ctrl+Q
                cancel_key_pressed = False
                check_times = 30
                for _ in range(check_times):
                    if auto.IsKeyPressed(auto.Keys.VK_Q) and auto.IsKeyPressed(auto.Keys.VK_CONTROL):
                        cancel_key_pressed = True
                        break
                    self.random_sleep(0.08, 0.12)  # 随机检查间隔
                
                if cancel_key_pressed:
                    logging.info("用户取消发送")
                    print("已取消发送")
                    return False
                
                # 发送消息
                self.random_sleep(0.3, 0.8)
                auto.SendKeys('{Enter}')
                logging.info("消息已发送")
                print(f"消息已发送给 {contact_name}")
                
                # 更新最后回复时间
                self.last_reply_time[contact_name] = time.time()
                return True
                
            except Exception as e:
                logging.error(f"发送消息失败: {str(e)}")
                return False
            
        except Exception as e:
            logging.error(f"发送自动回复时出错: {str(e)}")
            return False

    def start(self):
        """启动自动回复程序"""
        print("\n=== 微信自动回复程序 ===")
        print("正在初始化...")
        time.sleep(1)  # 等待日志系统初始化
        
        logging.info("正在启动自动回复程序...")
        print("\n使用说明：")
        print("1. 请确保微信已登录并保持打开状态")
        print("2. 不要最小化微信窗口")
        print("3. 程序运行时请不要手动操作微信窗口")
        print("4. 按 Ctrl+C 可以退出程序\n")
        
        check_interval = random.randint(8, 15)  # 随机检查间隔8-15秒
        last_check_time = 0
        consecutive_errors = 0  # 连续错误计数
        
        while self.running:
            try:
                current_time = time.time()
                # 检查是否达到检查间隔
                if current_time - last_check_time < check_interval:
                    time.sleep(0.1)  # 短暂休眠以减少CPU使用
                    continue
                
                last_check_time = current_time
                check_interval = random.randint(8, 15)  # 每次检查后重新设置随机间隔
                
                # 查找所有微信窗口
                wechat_windows = self.find_all_wechat_windows()
                if not wechat_windows:
                    print("等待微信窗口...")
                    time.sleep(check_interval)
                    continue
                
                # 切换到下一个微信窗口
                current_window = self.switch_to_next_window(wechat_windows)
                if not current_window:
                    self.random_sleep(1, 2)
                    continue
                
                # 检查新消息
                contact_name = self.check_new_message(current_window)
                if contact_name:
                    self.send_auto_reply(current_window, contact_name)
                    consecutive_errors = 0  # 重置错误计数
                else:
                    self.random_sleep(1, 3)  # 没有新消息时随机休眠
                
                # 主循环休眠时间
                self.random_sleep(check_interval * 0.8, check_interval * 1.2)
                
            except KeyboardInterrupt:
                print("\n正在停止程序...")
                logging.info("程序正在退出...")
                self.running = False
                break
            except Exception as e:
                logging.error(f"程序运行出错: {str(e)}")
                consecutive_errors += 1
                
                # 如果连续出错超过3次，增加等待时间
                if consecutive_errors >= 3:
                    wait_time = min(300, check_interval * consecutive_errors)  # 最多等待5分钟
                    logging.info(f"连续出错{consecutive_errors}次，等待{wait_time}秒后继续...")
                    time.sleep(wait_time)
                else:
                    time.sleep(check_interval)
        
        print("程序已退出。")
        logging.info("程序已退出")

if __name__ == "__main__":
    auto_reply = WeChatAutoReply()
    auto_reply.start() 