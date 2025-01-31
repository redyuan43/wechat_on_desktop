import uiautomation as auto
import time
import logging
import random
from typing import List, Optional, Tuple

class UIAutomation:
    @staticmethod
    def random_sleep(min_seconds: float = 0.5, max_seconds: float = 2.0) -> float:
        """随机休眠一段时间"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        time.sleep(sleep_time)
        return sleep_time

    @staticmethod
    def find_all_wechat_windows() -> List[auto.WindowControl]:
        """查找所有微信主窗口"""
        try:
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

    @staticmethod
    def find_chat_list_panel(wechat_window: auto.WindowControl) -> Optional[auto.ListControl]:
        """查找会话列表面板"""
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
            for pane in all_panes:
                try:
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

    @staticmethod
    def get_last_message(wechat_window: auto.WindowControl) -> Optional[str]:
        """获取最后一条消息内容"""
        try:
            time.sleep(1)
            message_list = wechat_window.ListControl(Name="消息")
            if message_list.Exists():
                messages = message_list.GetChildren()
                if messages:
                    last_message = messages[-1]
                    return last_message.Name
            return None
        except Exception as e:
            logging.error(f"获取最后一条消息时出错: {str(e)}")
            return None 