import logging
import ollama
from ..utils.config import TEXT_MODEL, IMAGE_MODEL, NEW_YEAR_KEYWORDS

class LLMService:
    def __init__(self):
        try:
            self.ollama_client = ollama
            self.text_model = TEXT_MODEL
            self.image_model = IMAGE_MODEL
            logging.info("成功初始化Ollama客户端")
        except Exception as e:
            logging.error(f"初始化Ollama客户端失败: {str(e)}")
            raise

    def is_new_year_greeting(self, message):
        """判断是否是拜年信息"""
        try:
            # 关键词匹配
            if any(keyword in message for keyword in NEW_YEAR_KEYWORDS):
                logging.info(f"通过关键词匹配判定为拜年信息 - 消息：{message}")
                return True
            
            # LLM判断
            prompt = """请判断以下消息是否是拜年信息或新年祝福。请只回答"是"或"否"，不要有任何解释或其他内容。

判断标准：
1. 包含新年、春节、年等相关祝福
2. 表达了祝福、问候的意思
3. 节日相关的祝愿（如：恭喜发财、大吉大利等）

消息内容：{message}

只需要回答一个字："是"或"否"："""
            
            response = self.ollama_client.generate(
                model=self.text_model, 
                prompt=prompt.format(message=message)
            )
            result = response['response'].strip().lower()
            result = result.replace('<think>', '').replace('</think>', '')
            result = result.split('\n')[0].strip()
            
            logging.info(f"LLM判断结果 - 消息：{message} - 清理后的结果：{result}")
            
            return result == '是' if result else False

        except Exception as e:
            logging.error(f"检测拜年信息时出错: {str(e)}")
            return any(keyword in message for keyword in NEW_YEAR_KEYWORDS)

    def generate_greeting_reply(self, original_message):
        """生成拜年回复"""
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

3. 格式：
   - 字数限制在40字以内
   - 语言优美，感情真挚

直接输出祝福语，不要有任何解释、标点符号或引号。"""

            user_prompt = f"收到的拜年祝福：{original_message}\n请生成回复："
            
            response = self.ollama_client.generate(
                model=self.text_model,
                prompt=f"{system_prompt}\n\n{user_prompt}"
            )
            
            reply = response['response'].strip()
            lines = [line.strip() for line in reply.split('\n') if line.strip()]
            
            start_idx = -1
            for i, line in enumerate(lines):
                if any(line.startswith(word) for word in ["谢谢", "感谢", "感恩"]):
                    start_idx = i
                    break
            
            if start_idx != -1:
                actual_reply = ' '.join(lines[start_idx:])
            else:
                actual_reply = lines[-1] if lines else ""
            
            actual_reply = actual_reply.replace('<think>', '').replace('</think>', '')
            actual_reply = actual_reply.strip('"')
            
            if not actual_reply:
                return "谢谢您的祝福！祝您蛇年大吉，万事如意！"
            
            logging.info(f"生成的回复：{actual_reply}")
            return actual_reply
            
        except Exception as e:
            logging.error(f"生成拜年回复时出错: {str(e)}")
            return "谢谢您的祝福！祝您蛇年大吉，万事如意！" 