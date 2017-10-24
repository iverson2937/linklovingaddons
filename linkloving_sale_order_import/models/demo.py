# -*- coding:utf-8 -*-

from pyvirtualdisplay import Display
from selenium import webdriver

import time

'''
    注意:此模块没有做多线程并发问题,所以，强烈建议多进程模式启动!!!
'''

display = Display(visible=0, size=(1366, 768))
display.start()

driver = webdriver.Chrome()
# driver = webdriver.PhantomJS()

loginurl = 'https://passport.shop.jd.com/login/index.action'

# 让浏览器窗口最大化
# driver.maximize_window()
driver.set_window_size(1366, 768)

# 天猫界面中页面做了防爬虫的手段，所以需要使用虚拟浏览器来模拟js定位到制定的位置界面和翻页功能
common_url = 'https://order.shop.jd.com/order/sSopUp_allList.action'
waitting_export_url = 'https://order.shop.jd.com/order/sopUp_waitOutList.action'
alerady_export_url = 'https://order.shop.jd.com/order/sSopUp_newYiShipList.action'
buyer_alerady_accetped_url = 'https://order.shop.jd.com/order/sSopUp_yiReceivingList.action'
lock_order_during_url = 'https://order.shop.jd.com/order/sSopUp_lockOrderList.action'
refund_order_during_url = 'https://order.shop.jd.com/order/sSopUp_refundingList.action'

urls = [waitting_export_url, alerady_export_url, buyer_alerady_accetped_url, lock_order_during_url,
        refund_order_during_url]

order_detail = {}

# redis_entity 实体,我们需要通过链表的模式来做传递,因为python本身的设计模式就是基于引用(指针)之间的传递
redis_list = []


def login(loginurl, username=None, password=None):
    # open the login in page
    driver.get(loginurl)
    try:
        driver.find_element_by_xpath('//*[@id="account-login"]').click()
    except:
        print u'京东登录界面出现改版,需要把用户登陆界面切换出来'
    time.sleep(3)
    # sign in the username

    # 由于京东中使用frame来再次加载一个网页，所以，在选择元素的时候会出现选择不到的结果，所以，我们需要把视图窗口切换到frame中
    driver.switch_to.frame(u'loginFrame')

    def login_name():
        try:
            # driver.find_element_by_xpath('//*[@id="loginname"]').click()
            time.sleep(3)
            driver.find_element_by_xpath('//*[@id="loginname"]').clear()
            # driver.find_element_by_xpath('//*[@id="TPL_username_1"]').send_keys(u'若态旗舰店')
            driver.find_element_by_xpath('//*[@id="loginname"]').send_keys(username)
            print 'user success!'
        except:
            print 'user error!'
        time.sleep(3)

    def login_password():
        # sign in the pasword
        try:
            driver.find_element_by_xpath('//*[@id="nloginpwd"]').clear()
            # driver.find_element_by_xpath('//*[@id="TPL_password_1"]').send_keys('szrtkjqjd@123!!')
            driver.find_element_by_xpath('//*[@id="nloginpwd"]').send_keys(password)
            print 'pw success!'
        except:
            print 'pw error!'
        time.sleep(3)

    def click_and_login():
        # click to login
        try:
            driver.find_element_by_xpath('//*[@id="paipaiLoginSubmit"]').click()
            print 'click success!'
        except:
            print 'click error!'
        time.sleep(3)

    login_name()
    login_password()
    click_and_login()

    curpage_url = driver.current_url
    print 'currpage_url ' + curpage_url

    if curpage_url == loginurl:
        print u'用户登陆失败'
        raise u'用户登陆失败'


def setup(username, password):
    login(loginurl, username, password)


if __name__ == '__main__':
    print u'main....'
    print '__name__ is %s' % __name__
    print '__file__ is %s' % __file__
    try:

        # username = sys.argv[1]
        username = u'jd_rtkj'
        # password = sys.argv[2]
        password = u'dzswrobotime2016!!'
        setup(username, password)
    except IndexError:
        print u'缺少必要的参数!!!'
