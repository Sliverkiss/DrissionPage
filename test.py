from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.headless(True)

co.set_argument('--no-sandbox')
co.set_argument('--incognito')
co.no_imgs(True).mute(True)
tab = ChromiumPage(co)

# 访问网页
tab.get('https://www.baidu.com')  
# 获取文本框元素对象
ele = tab.ele('#kw')
# 向文本框元素对象输入文本
ele.input('DrissionPage')  
# 点击按钮，上两行的代码可以缩写成这样
tab('#su').click()  
# 获取所有<h3>元素
links = tab.eles('tag:h3')  
# 遍历并打印结果
for link in links:  
    print(link.text)
