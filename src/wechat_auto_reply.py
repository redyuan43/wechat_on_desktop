import time
import logging
import random
import uiautomation as auto
from typing import Optional

from .utils.config import setup_logging, DEFAULT_REPLY_INTERVAL, MIN_OPERATION_INTERVAL
from .services.llm_service import LLMService
from .services.ui_automation import UIAutomation
from .handlers.message_handler import MessageHandler

class WeChatAutoReply:
    def __init__(self):
        self.running = True
        self.last_reply_time = {}
        self.reply_interval = DEFAULT_REPLY_INTERVAL
        self.last_operation_time = 0
        self.min_operation_interval = MIN_OPERATION_INTERVAL
        self.current_window_index = 0
        
        self.llm_service = LLMService()
        self.ui_automation = UIAutomation()
        self.message_handler = MessageHandler()

    def ensure_operation_interval(self):
        """确保操作之间有足够的间隔"""
        current_time = time.time()
        if current_time - self.last_operation_time < self.min_operation_interval:
            time.sleep(self.min_operation_interval)
        self.last_operation_time = time.time()

    def switch_to_next_window(self, wechat_windows):
        """切换到下一个微信窗口"""
        if not wechat_windows:
            return None
        
        self.current_window_index = (self.current_window_index + 1) % len(wechat_windows)
        current_window = wechat_windows[self.current_window_index]
        
        try:
            if current_window.SetFocus():
                logging.info(f"切换到第 {self.current_window_index + 1} 个微信窗口")
                time.sleep(1)
                
                try:
                    rect = current_window.BoundingRectangle
                    x = rect.left + 100
                    y = (rect.top + rect.bottom) // 2
                    auto.Click(x, y)
                    self.ui_automation.random_sleep(0.5, 1)
                    
                    auto.SendKeys('{Alt}1')
                    self.ui_automation.random_sleep(0.5, 1)
                except Exception as e:
                    logging.warning(f"尝试点击左侧区域时出错: {str(e)}")
                
                return current_window
            else:
                logging.warning(f"无法将第 {self.current_window_index + 1} 个微信窗口置于前台")
                return None
        except Exception as e:
            logging.error(f"切换窗口时出错: {str(e)}")
            return None

    def check_new_message(self, wechat_window):
        """检查新消息"""
        try:
            chat_list_panel = self.ui_automation.find_chat_list_panel(wechat_window)
            if not chat_list_panel:
                return None
            
            chat_items = chat_list_panel.GetChildren()
            logging.info(f"找到 {len(chat_items)} 个会话项")
            
            for i, item in enumerate(chat_items):
                try:
                    item_name = item.Name
                    item_value = ""
                    try:
                        item_value = item.GetValuePattern().Value
                    except:
                        pass

                    if self.message_handler.is_special_account(item_name):
                        logging.info(f"跳过特殊账号: {item_name}")
                        continue
                    
                    contact_name, has_new_message = self.message_handler.parse_contact_info(item_name)
                    
                    if has_new_message and contact_name:
                        logging.info(f"发现新消息，联系人: {contact_name}")
                        
                        current_time = time.time()
                        if contact_name in self.last_reply_time:
                            time_diff = current_time - self.last_reply_time[contact_name]
                            if time_diff < self.reply_interval:
                                logging.info(f"跳过 {contact_name} 的消息（还需等待 {int(self.reply_interval - time_diff)} 秒）")
                                continue

                        if not self.click_chat_item(wechat_window, item, contact_name):
                            continue

                        last_message = self.ui_automation.get_last_message(wechat_window)
                        if not last_message:
                            logging.error("无法获取最后一条消息")
                            continue

                        if not self.llm_service.is_new_year_greeting(last_message):
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
            
            wechat_window.SetFocus()
            self.ui_automation.random_sleep(0.3, 0.8)
            
            item.SetFocus()
            self.ui_automation.random_sleep(0.2, 0.5)
            
            click_success = False
            
            try:
                if item.Click():
                    click_success = True
                    logging.info(f"成功点击会话(方法1): {contact_name}")
            except:
                self.ui_automation.random_sleep(0.1, 0.3)
            
            if not click_success:
                try:
                    item.Click(simulateMove=True)
                    click_success = True
                    logging.info(f"成功点击会话(方法2): {contact_name}")
                except:
                    pass
            
            if click_success:
                self.ui_automation.random_sleep(1.5, 2.5)
                return True
            else:
                logging.error(f"所有点击方法都失败: {contact_name}")
                return False
                
        except Exception as e:
            logging.error(f"点击会话失败: {contact_name}, 错误: {str(e)}")
            return False

    def send_auto_reply(self, wechat_window, contact_name):
        """发送自动回复"""
        try:
            last_message = self.ui_automation.get_last_message(wechat_window)
            if not last_message:
                logging.error("无法获取最后一条消息")
                return False

            if not self.llm_service.is_new_year_greeting(last_message):
                logging.info("不是拜年信息，跳过回复")
                return False

            reply_message = self.llm_service.generate_greeting_reply(last_message)
            
            try:
                window_pattern = wechat_window.GetWindowPattern()
                if window_pattern and window_pattern.Current.WindowVisualState != auto.WindowVisualState.Maximized:
                    wechat_window.Maximize()
                    self.ui_automation.random_sleep(0.5, 1)
            except:
                wechat_window.Maximize()
                self.ui_automation.random_sleep(0.5, 1)
            
            logging.info("准备在右下角输入消息...")
            
            try:
                rect = wechat_window.BoundingRectangle
                x = rect.right - 100
                y = rect.bottom - 100
                auto.Click(x, y)
                time.sleep(0.5)
                
                for char in reply_message:
                    if char == '\n':
                        auto.SendKeys('{ENTER}')
                    else:
                        auto.SendKeys(char)
                    self.ui_automation.random_sleep(0.05, 0.15)
                
                self.ui_automation.random_sleep(0.5, 1)
                
                logging.info("消息已输入，等待3秒后发送（按Ctrl+Q取消）...")
                print(f"\n准备向 {contact_name} 发送消息：{reply_message}")
                print("按 Ctrl+Q 取消发送...")
                
                cancel_key_pressed = False
                check_times = 30
                for _ in range(check_times):
                    if auto.IsKeyPressed(auto.Keys.VK_Q) and auto.IsKeyPressed(auto.Keys.VK_CONTROL):
                        cancel_key_pressed = True
                        break
                    self.ui_automation.random_sleep(0.08, 0.12)
                
                if cancel_key_pressed:
                    logging.info("用户取消发送")
                    print("已取消发送")
                    return False
                
                self.ui_automation.random_sleep(0.3, 0.8)
                auto.SendKeys('{Enter}')
                logging.info("消息已发送")
                print(f"消息已发送给 {contact_name}")
                
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
        time.sleep(1)
        
        logging.info("正在启动自动回复程序...")
        print("\n使用说明：")
        print("1. 请确保微信已登录并保持打开状态")
        print("2. 不要最小化微信窗口")
        print("3. 程序运行时请不要手动操作微信窗口")
        print("4. 按 Ctrl+C 可以退出程序\n")
        
        check_interval = random.randint(8, 15)
        last_check_time = 0
        consecutive_errors = 0
        
        while self.running:
            try:
                current_time = time.time()
                if current_time - last_check_time < check_interval:
                    time.sleep(0.1)
                    continue
                
                last_check_time = current_time
                check_interval = random.randint(8, 15)
                
                wechat_windows = self.ui_automation.find_all_wechat_windows()
                if not wechat_windows:
                    print("等待微信窗口...")
                    time.sleep(check_interval)
                    continue
                
                current_window = self.switch_to_next_window(wechat_windows)
                if not current_window:
                    self.ui_automation.random_sleep(1, 2)
                    continue
                
                contact_name = self.check_new_message(current_window)
                if contact_name:
                    self.send_auto_reply(current_window, contact_name)
                    consecutive_errors = 0
                else:
                    self.ui_automation.random_sleep(1, 3)
                
                self.ui_automation.random_sleep(check_interval * 0.8, check_interval * 1.2)
                
            except KeyboardInterrupt:
                print("\n正在停止程序...")
                logging.info("程序正在退出...")
                self.running = False
                break
            except Exception as e:
                logging.error(f"程序运行出错: {str(e)}")
                consecutive_errors += 1
                
                if consecutive_errors >= 3:
                    wait_time = min(300, check_interval * consecutive_errors)
                    logging.info(f"连续出错{consecutive_errors}次，等待{wait_time}秒后继续...")
                    time.sleep(wait_time)
                else:
                    time.sleep(check_interval)
        
        print("程序已退出。")
        logging.info("程序已退出")