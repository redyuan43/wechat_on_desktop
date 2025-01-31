from typing import Optional, Tuple
import logging
from ..utils.config import SPECIAL_ACCOUNTS

class MessageHandler:
    @staticmethod
    def is_special_account(item_name: str) -> bool:
        """判断是否为特殊账号"""
        return item_name in SPECIAL_ACCOUNTS

    @staticmethod
    def is_group_chat(item_name: str, item_value: str) -> bool:
        """判断是否为群聊"""
        if not item_name:
            return False
            
        group_indicators = [
            '群聊', '群', '交流群', '讨论组', '社群',
            '商会', '协会', '班级', '支部', '联盟',
            '内购群', '粉丝群'
        ]
        
        message_indicators = [
            '个成员', '[群消息]', '条]', '消息免打扰'
        ]
        
        is_group_by_name = any(indicator in item_name for indicator in group_indicators)
        is_group_by_value = False
        if item_value:
            is_group_by_value = any(indicator in item_value for indicator in message_indicators)
        
        return is_group_by_name or is_group_by_value

    @staticmethod
    def parse_contact_info(item_name: str) -> Tuple[str, bool]:
        """解析联系人信息"""
        clean_name = item_name.replace("已置顶", "").strip()
        has_new_message = False
        contact_name = None
        
        if "条新消息" in clean_name:
            name_parts = clean_name.split("条新消息")[0]
            contact_name = ''.join([i for i in name_parts if not i.isdigit()]).strip()
            has_new_message = True
        else:
            contact_name = clean_name
            
        return contact_name, has_new_message 