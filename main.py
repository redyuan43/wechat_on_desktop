from src import WeChatAutoReply, setup_logging

if __name__ == "__main__":
    setup_logging()
    auto_reply = WeChatAutoReply()
    auto_reply.start() 