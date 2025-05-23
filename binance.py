from DrissionPage import Chromium,ChromiumOptions
from DrissionPage.common import Settings
from bs4 import BeautifulSoup
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
            
    def login(self,count=0):
        try:
            self.page.get("https://accounts.binance.com/zh-CN/login/password")
            time.sleep(2)
            #输入用户名
            self.page.ele('tag:input@name=username').input(self.username)
            time.sleep(2)
            self.page.ele('@text()=下一步').click()
            time.sleep(2)
            self.page.get("https://accounts.binance.com/zh-CN/login/password")
            time.sleep(2)
            self.page.ele('tag:input@name=password').input(self.password)
            self.page.ele('@text()=下一步').click()
            if self.page.ele('@text()=我的通行密钥无法使用').click():
                logging.info(f"登录成功！")
                self.push_content += f"登录成功！\n"
                return True
            else:
                logging.info(f"登录失败！")
        except Exception as e:
            logging.info(f"登录错误: {e}")
            self.push_content += f"登录错误: {e}\n"
            return False
    
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
            return 
        
    def reward_week(self):
        try:
            # 跳转到奖励中心页面
            self.page.get("https://www.binance.com/zh-CN/rewards-hub")
            time.sleep(2)
            self.page.ele('tag:button@class:ClaimBigRewardButton DailyCheckIn-Footer-ClaimBigRewardButton').click()
            point=self.page.ele('tag:div@class=HomeBannerSummaryItem-data').text
            return True
        except Exception as e:
            logging.info(f"签到天数不足，无法领取额外10积分奖励")
            return False
        
    def wotd(self):
        try:
            logger.info(f"[{account['username']}] 开始执行每日一词任务")

            # 打开每日一词网站，获取数据
            self.page.get("https://artru.net/zh/dap-an-binance-wotd-word-of-the-day/")
            time.sleep(3)

            # 关闭广告拦截提示
            if self.page.ele("tag:button@id=artru-adblock_button"):
                self.page.ele("tag:button@id=artru-adblock_button").click()

            logger.info(f" 🔍 正在查询词库数据，请稍等10秒加载cache...")
            time.sleep(10)

            # 获取 iframe 并解析 HTML
            iframe = self.page.get_frame("tag:iframe@title:答案")
            soup = BeautifulSoup(iframe.html, 'html.parser')

            result = {}

            # 提取所有包含“✅”的段落
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                logger.info(f"{text}")
                match = re.match(r"✅(\d+)\s+Letters:\s*(.*)", text)
                if match:
                    length = match.group(1)
                    words_str = match.group(2)
                    if words_str:
                        words_list = [w.strip() for w in words_str.split(',')]
                    else:
                        words_list = []
                    result[length] = words_list

            if result:
                logger.info(f"✅ 获取词库数据成功！")
                self.wotd_list = result
                print(self.wotd_list)
                return True

        except Exception as e:
            logger.error(f"❌ 获取每日一词失败: {e}")
            return False
        
    # 获取每日一词的单词长度    
    def get_wotd_length(self):
        try:
            self.page.get("https://www.binance.com/en/activity/word-of-the-day/entry?utm_source=muses")
            #获取每日一词信息
            theme=self.page.ele('xpath://html/body/div[3]/div[1]/div[2]/div[2]/div/div[1]/h5/div/span/span[2]').text
            date=self.page.ele('xpath://html/body/div[3]/div[1]/div[2]/div[2]/div/div[1]/h5/div/div/span').text
            box_div=self.page.ele('xpath://html/body/div[3]/div[1]/div[2]/div[2]/div/div[2]/div[1]/div[1]')
            wo=box_div.eles("tag:div@class:css-56u4e4")
            logger.info(f"主题: {theme}")
            logger.info(f"活动时间: {date} ")
            logger.info(f"单词长度: {len(wo)}")
            self.wotd_length=len(wo)
            print(self.wotd_list[f"{self.wotd_length}"])
            self.wotd_result=self.wotd_list[f"{self.wotd_length}"]
            return True
        except Exception as e:
            print(e)
            return False
    
    def into_wotd(self):
        try:
            self.page.get("https://www.binance.com/en/activity/word-of-the-day/entry?utm_source=muses")
            logger.info("正在检查#检查每日一词状态。。。")
            self.page.ele("xpath://html/body/div[7]/div/div[2]/div/button").click()
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
            status_text= self.page.ele("xpath://html/body/div[3]/div[1]/div[2]/div[2]/div/div/div[2]/div[1]").text
            if status_text == "Correct Word of the Day":
                logger.info("每日一词: 已完成")
                self.push_content += "每日一词: 已完成\n"
                return True

        except Exception as e:
            return False
        
    def share_wotd(self):
        try:
            self.page.ele("xpath://html/body/div[3]/div[1]/div[2]/div[2]/div/div/div[5]/button[2]/div").click()
            button=self.page.ele("xpath:///html/body/div[3]/div[1]/div[2]/div[3]/div/div/div/div[2]/div/div[4]/div[2]/div[2]")
            
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
            keyboard=self.page.eles(f'tag:button@data-type=key')
            for i in str_word:
                #点击单词
                button=keyboard.filter_one.text(f"{i}")
                button.click()
                
            time.sleep(0.5)
            button=keyboard.filter_one.text("Enter").click()
            return True
        except Exception as e:
            logging.info(f"{e}")
            return False

    def run(self):
        if not self.get_user_info():
            self.push_content += "登录失败，账号已掉线"
            if not self.login():
                 return
            else:
                self.get_user_info() 

        if not self.reward_signin():
            logger.info("执行任务失败，请先完成 KYC 身份验证")
            self.push_content += "执行任务失败，请先完成 KYC 身份验证"
            return
        
        self.reward_week()

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
                #self.share_wotd()
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
        
