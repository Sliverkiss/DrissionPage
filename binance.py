from DrissionPage import Chromium,ChromiumOptions
from DrissionPage.common import Settings
import logging
import requests
import time


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
        self.page=self.browser.new_tab("https://www.binance.com/zh-CN/my/dashboard")
        self.username=username
        self.password=passowed
        self.bark_key=bark_key
        self.push_content = ''
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
        }
        try:
            response = requests.post(bark_url, headers=headers, json=data)
            print("Bark 推送响应:", response.text)
            print("Bark 推送内容:", self.push_content)
        except Exception as e:
            print("Bark 推送失败:", str(e))
    
    def login(self,count=0):
        try:
            #输入用户名
            self.page.ele('tag:input@name=username').input(self.username)
            self.page.ele('@text()=下一步').click()
            time.sleep(5)
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
            text=f"用户名:{nickname} 状态:在线"
            logging.info(text)
            self.push_content += f"{text}\n"
            return True
        except Exception as e:
            logging.info(f"登录错误: 账号已掉线\n{e}")
            return False
    
    def reward_signin(self):
        try:
            # 跳转到奖励中心页面
            self.page.get("https://www.binance.com/zh-CN/rewards-hub")
            time.sleep(2)
            sign_button=self.page.ele('tag:button@aria-label=签到')
            
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
            self.push_content += f"积分: {point}"
            return True
        except Exception as e:
            logging.info(f"签到错误: \n{e}")
            return False
    
    def get_water_count(self,log=True):
        try:
            count=self.page.ele('tag:div@class=opBtn waterBtn ng-scope').ele('tag:i@class=water_num ng-binding').text            
            return int(count)>0
        except Exception as e:
            return False
    

    def run(self):
        self.get_user_info()   
        self.reward_signin()
        time.sleep(5)
        self.browser.quit()

if __name__ == "__main__":
    #在accounts填入bark_key,username和password暂时没用
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
        
