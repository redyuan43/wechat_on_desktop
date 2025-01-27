import ollama
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_llm.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def test_greeting_generation():
    """测试拜年祝福生成"""
    try:
        # 测试消息
        test_messages = [
            "新年快乐！",
            "祝你蛇年大吉！",
            "恭喜发财，万事如意！",
            "祝你在新的一年里事业腾达，身体健康！"
        ]
        
        system_prompt = """你是一个春节祝福助手。请生成2025蛇年春节拜年回复。

1. 核心主题：
   - 围绕"蛇年祥瑞"展开，使用灵蛇、金蛇、祥蛇等意象
   - 突出智慧（如"灵蛇献智"）、灵活（如"蛇行顺畅"）、吉祥（如"福寿双全"）等关键词
   - 结合对方的祝福内容，体现感谢和互祝的情感
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
   - 字数限制在30字以内
   - 语言优美，感情真挚

示例回复：
"谢谢您的祝福！祝您蛇年智慧永伴，事业蒸蒸日上，家庭幸福安康！"
"感谢美好祝愿！愿您蛇年福气蜿蜒来，智慧如灵蛇，事业展宏图！"

直接输出祝福语，不要有任何解释。"""
        
        for message in test_messages:
            print("\n" + "="*30)
            print(f"收到：{message}")
            
            user_prompt = f"收到的拜年祝福：{message}\n请生成回复："
            
            # 调用LLM
            response = ollama.generate(
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
            
            print(f"回复：{actual_reply}")
            print(f"字数：{len(actual_reply)}")
            
    except Exception as e:
        logging.error(f"测试过程出错: {str(e)}")

if __name__ == "__main__":
    test_greeting_generation() 