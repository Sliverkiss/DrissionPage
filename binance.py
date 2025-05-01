from DrissionPage import Chromium,ChromiumOptions
from DrissionPage.common import Settings
import logging
import requests
import time
import json
import re
import tkinter as tk



# Logger setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "[%(asctime)s %(levelname)s] %(message)s", datefmt="%H:%M:%S"
)
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

Settings.set_singleton_tab_obj(False)

#设置浏览器配置
co = ChromiumOptions()
#co.incognito()  # 匿名模式
# 设置不加载图片、静音
#co.no_imgs(True).mute(True)
#co.headless()  # 无头模式
co.set_argument('--no-sandbox')  # 无沙盒模式

# 以该配置创建页面对象

class UserInfo:
    def __init__(self,username,passowed,bark_key) -> None:
        self.browser = Chromium(addr_or_opts=co)
        self.page=self.browser.new_tab()
        self.username=username
        self.password=passowed
        self.bark_key=bark_key
        self.push_content = ''
        self.share_url=""
        self.push_title = '币安-奖励中心'
    
    # Bark 推送函数
    def bark_send(self):
            # Bark 推送配置
        bark_url = f'https://api.day.app/{self.bark_key}'
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        data = {
            "title": self.push_title,
            "body": self.push_content,
            "badge": 1,
            "sound": "minuet.caf",
            "icon": "https://avatars.githubusercontent.com/u/70052878?s=400&u=03695bc2a094d4608f7eda6486cd0c7370e75b8b&v=4",
            "group": "sliverkiss",
            "url":self.share_url
        }
        try:
            response = requests.post(bark_url, headers=headers, json=data)
            print("Bark 推送响应:", response.text)
            print("Bark 推送内容:", self.push_content)
        except Exception as e:
            print("Bark 推送失败:", str(e))
    
    def get_user_info(self):
        try:
            #跳转到个人中心页面，查询用户信息
            self.page.get("https://www.binance.com/zh-CN/my/dashboard")
            nickname=self.page.ele('tag:div@id=dashboard-userinfo-nickname').text
            logging.info(f"用户名: {nickname} 状态: 在线")
            self.push_content += f"用户: {nickname}\n"
            return True
        except Exception as e:
            logging.info(f"登录错误: 账号已掉线\n{e}")
            return False
    
    def reward_signin(self):
        try:
            # 跳转到奖励中心页面
            self.page.get("https://www.binance.com/zh-CN/rewards-hub")
            time.sleep(2)
            sign_button=self.page.ele('tag:button@text()=签到')
            
            if "disabled" in sign_button.attrs:
                logger.info(f"签到: 今日已签到")
                self.push_content += "签到: 今日已签到\n"
            else:
                sign_button.click()    
                logger.info(f"签到: 签到成功!")
                self.push_content += "签到: 签到成功！\n"
                time.sleep(2)
                
            point=self.page.ele('tag:div@class=HomeBannerSummaryItem-data').text
            logger.info(f"积分: {point}")
            self.push_content += f"积分: {point}\n"
            return True
        except Exception as e:
            logging.info(f"签到错误: \n{e}")
            return False
        
    def wotd(self):
        try:
            logger.info("开始执行每日一词任务")
            #打开每日一词网站，获取数据
            self.page.get("https://wotd-ten.vercel.app")
            logger.info("🔍 正在查询词库数据，请稍等...")
            time.sleep(2)
            iframe=self.page.get_frame("tag:iframe@title=币安 WOTD 答案 - 每日一词")
            words=iframe.eles('tag:p')
            
            result = {}
            for word in words:
                line = word.text.strip()
                match = re.match(r"✅(\d+)\s+Letters:\s+(.+)", line)
                if match:
                    length = match.group(1)
                    words_list = [w.strip() for w in match.group(2).split(',')]
                    result[length] = words_list
   
            if result:
                logger.info("✅ 获取词库数据成功！")
                self.wotd_list=result
                return True
        except Exception as e:
            return False
        
    # 获取每日一词的单词长度    
    def get_wotd_length(self):
        try:
            self.page.get("https://www.binance.com/en/activity/word-of-the-day/entry?utm_source=muses")
            #获取每日一词信息
            theme=self.page.ele('tag:span@class=css-14pe3hg').text
            date=self.page.ele('tag:span@class=css-w2z2xi').text
            box_div=self.page.eles('tag:div@class=css-fiugn9')
            wo=box_div[0].eles("tag:div@class: css-1ej260s")
            logger.info(f"主题: {theme}")
            logger.info(f"活动时间: {date} ")
            logger.info(f"单词长度: {len(wo)}")
            self.wotd_length=len(wo)
            print(self.wotd_list[f"{self.wotd_length}"])
            self.wotd_result=self.wotd_list[f"{self.wotd_length}"]
            return True
        except Exception as e:
            return False
    
    def into_wotd(self):
        try:
            self.page.get("https://www.binance.com/en/activity/word-of-the-day/entry?utm_source=muses")
            logger.info("正在检查#检查每日一词状态。。。")
            self.page("tag:button@class= css-25llw").click()
            return True
        except Exception as e:
            try:
                finish_activity=self.page("tag:h2@class=css-1pv82nm").text
                if finish_activity=="Good Things Take Time":
                    logger.info("本期活动已结束，请等待下一期活动开始...")                    
                    self.push_content += "每日一词: 活动未开始"
                return False    
            except Exception as e:
                logger.info("✅ 已完成每日一词状态初始化")
                return True
    
    def check_wotd_status(self):
        try:
            self.page.refresh()
            time.sleep(1)
            status_text= self.page.ele("tag:div@class=css-r6zbz9").text
            if status_text == "Correct Word of the Day":
                return True

        except Exception as e:
            return False
        
    def share_wotd(self):
        try:
            self.page.ele("tag:div@class=css-rjqmed").click()
            button=self.page.ele("tag:div@class=css-ots3l4")
            
            logger.info(button.text)
            button.click()
            root = tk.Tk()
            root.withdraw()  # 不显示主窗口
            clipboard_content = root.clipboard_get()
            print("剪贴板内容:", clipboard_content)
            self.page.get(clipboard_content)        
            self.share_url=clipboard_content
            if(clipboard_content):
                logger.info("每日一词: 已完成(1/2)")
                self.push_content += "每日一词: 已完成(1/2)\n"
                self.push_content +=f"分享链接: {clipboard_content}"
            else:
                logger.info("每日一词: 已完成(2/2)")
                self.push_content += "每日一词: 已完成(2/2)"
                
        except Exception as e:
            logger.info("每日一词: 已完成(2/2)")
            self.push_content += "每日一词: 已完成(2/2)"
            return False
    
    def wotd_click_str(self,word):
        try:
            logger.info(f"输入单词: {word}")
            #将单词分割成字符
            str_word=list(word)
            for i in str_word:
                #点击单词
                button=self.page.eles(f'tag:button@class: css-wrg6pl').filter_one.text(f"{i}")
                button.click()
                
            time.sleep(0.5)
            self.page.ele('tag:button@class= css-i4rvme').click()
            return True
        except Exception as e:
            logging.info(f"{e}")
            return False

    def run(self):
        if not self.get_user_info():
            self.push_content += "登录失败，账号已掉线"
            return

        if not self.reward_signin():
            logger.info("执行任务失败，请先完成 KYC 身份验证")
            self.push_content += "执行任务失败，请先完成 KYC 身份验证"
            return

        if not self.into_wotd():
            logger.info("进入 WOTD 失败")
            return

        if self.check_wotd_status():
            logger.info("WOTD 已完成，无需继续")
            self.share_wotd()
            return

        self.wotd()

        if not self.get_wotd_length():
            logger.info("未获取到 WOTD 单词列表")
            return

        for word in self.wotd_result:
            # 输入单词
            self.wotd_click_str(word)
            # 检查是否完成
            if self.check_wotd_status():
                logger.info("WOTD 任务已完成")
                self.share_wotd()
                break

        time.sleep(5)

if __name__ == "__main__":
    
    accounts = [
        {'username': '', 'password': '',"bark_key":''},
        # Add more accounts here as needed
    ]
    # Iterate over the accounts list
    for i, account in enumerate(accounts):
        logger.info(f"------  开始执行第{i+1}个账号  ------")
        user = UserInfo(account['username'], account['password'],account['bark_key'])
        user.run()
        user.bark_send()
        user.browser.quit()
        
