# -*- coding:utf-8 -*-

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import sys
import json
import redis
import re
import datetime
import uuid

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities



'''
    注意:此方法可以在并发的模型中运行!!!
'''
dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] = (
    "Mozilla/5.0 (Linux; Android 5.1.1; Nexus 6 Build/LYZ28E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.23 Mobile Safari/537.36"
)


# display = Display(visible=0, size=(1366, 768))
# display.start()


# driver = webdriver.PhantomJS(desired_capabilities=dcap)
driver = webdriver.Chrome()
# driver = webdriver.PhantomJS('phantomjs')

loginurl = 'https://login.taobao.com/member/login.jhtml'

# 让浏览器窗口最大化
#driver.maximize_window()
# driver.set_window_size(2000, 20000)
driver.set_window_size(1366, 768)

# 天猫界面中页面做了防爬虫的手段，所以需要使用虚拟浏览器来模拟js定位到制定的位置界面和翻页功能
common_url = 'https://gongxiao.tmall.com/supplier/order/order_list.htm'

def eliminate_alert_to_target(url):
    # 可能在打开新窗口的时候有一些flahs更新的弹框出来，我们需要谜面这种情况的出现!!!
    driver.get(url)
    time.sleep(15)
    try:
        driver.switch_to.alert.accept()
    except:
        pass
    driver.switch_to.window(driver.window_handles[-1])
    

# 限定抓取数据的天数
def limit_scrapy_data_in_days():
    # 获取当前的日期时间 如: xxxx-xx-xx
    today = datetime.date.today()

    # 默认获取前30天的日期的时间

    prev30_today = today - datetime.timedelta(days=30)

    print 'today is %s   prev30_today is %s' % (prev30_today, today)

    # 输入开始日期
    driver.find_element_by_xpath('//*[@id="J_BeginDate"]').send_keys(str(prev30_today))
    # time.sleep(1)
    # 输入开始小时

    driver.find_element_by_xpath('//select[@name="beginHours"]').send_keys('0')
    # time.sleep(1)
    # 输入开始分钟
    driver.find_element_by_xpath('//select[@name="beginMinutes"]').send_keys('0')
    # time.sleep(1)




    # 输入结束时间
    driver.find_element_by_xpath('//*[@id="J_EndDate"]').send_keys(str(today))
    # time.sleep(1)
    # 输入结束小时
    driver.find_element_by_xpath('//select[@name="endHours"]').send_keys('0')
    # time.sleep(1)
    # 输入结束分钟
    driver.find_element_by_xpath('//select[@name="endMinutes"]').send_keys('0')

    ActionChains(driver).move_by_offset(200, 200).click().perform()

    # 过滤出30天的数据
    # driver.find_element_by_xpath('//*[@id="J_searchb"]/tbody/tr[3]/td[4]/span/button').click()
    driver.find_element_by_xpath('//*[@id="J_searchb"]/tbody/tr[4]/td[2]/span/button').click()
    time.sleep(3)
    print u'点击搜索之后,获得需要的结果'


# login in tianmao

def login(loginurl, username=None, password=None):
    # open the login in page
    eliminate_alert_to_target(loginurl)
    #time.sleep(3)
    # sign in the username


    def login_name():
        try:
            driver.find_element_by_xpath('//*[@id="J_QRCodeLogin"]/div[5]/a[1]').click()
            time.sleep(3)
            driver.find_element_by_xpath('//*[@id="TPL_username_1"]').clear()
            # driver.find_element_by_xpath('//*[@id="TPL_username_1"]').send_keys(u'若态旗舰店')
            driver.find_element_by_xpath('//*[@id="TPL_username_1"]').send_keys(username)
            print 'user success!'
        except:
            print 'user error!'
        time.sleep(3)

    def login_password():
        # sign in the pasword
        try:
            driver.find_element_by_xpath('//*[@id="TPL_password_1"]').clear()
            # driver.find_element_by_xpath('//*[@id="TPL_password_1"]').send_keys('szrtkjqjd@123!!')
            driver.find_element_by_xpath('//*[@id="TPL_password_1"]').send_keys(password)
            print 'pw success!'
        except:
            print 'pw error!'
        time.sleep(3)

    def click_and_login():
        # click to login
        try:
            driver.find_element_by_xpath('//*[@id="J_SubmitStatic"]').click()
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
        print u'登陆失败'
        raise u'爬虫登陆失败!!'
    # while (curpage_url == loginurl):
    #     # print 'please input the verify code:'
    #     print '天猫登录中的滑块验证已经出现需要去做验证:'
    #
    #     def verify_span_slider():
    #         try:
    #             span_slider = driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
    #             ActionChains(driver).drag_and_drop_by_offset(span_slider, 258, 0).perform()
    #             time.sleep(3)
    #             print u'滑块运行成功!'
    #         except:
    #             print u'滑块运行失败!'
    #             raise u'用户登录失败'
    #         time.sleep(3)
    #
    #     login_name()
    #     login_password()
    #     click_and_login()
    #     verify_span_slider()
    #
    #     curpage_url = driver.current_url


def get_all_infomations_from_tiaomao(tianmao_url):
    eliminate_alert_to_target(tianmao_url)
    #time.sleep(5)

    # redis_entity 实体,我们需要通过链表的模式来做传递,因为python本身的设计模式就是基于引用(指针)之间的传递
    redis_list = []

    def process_items(is_first):
        if is_first:
            # 对于第一次打开网页的时候,会出现操作教程,这个界面我们只需要第一次去处理即可
            try:
                driver.find_element_by_xpath('/html/body/div[7]/div/div[4]/a').click()
                time.sleep(3)
                driver.find_element_by_xpath('/html/body/div[3]/div[2]/div[3]/ul/li[1]/a').click()
                time.sleep(3)

            except:
                print u'可能在某些时候天猫会去除这些演示教程,所以需要进行异常处理机制'


            # 也是在第一次的时候，处理搜索的范围 接下来的操作在于是通过获取所需求的30天之内数据
            limit_scrapy_data_in_days()


        time.sleep(5)

        order_lists = driver.find_elements_by_xpath('//tr[@class="itemtop"]')
        for order_list in order_lists:
            # 数据结构 用来存储获得到的每个订单的详细的信息
            order_detail_info = {}


            # print order_list.text
            # 获取其中的分销流水号
            # order_meta_distribution = order_list.find_element_by_xpath('./td/text()[4]')


            # 数据在内存的表示的是unicode编码的格式,所以,在关于中文字符的模式,需要使用Unicode编码的模式,
            # 切记在匹配的过程之中,如果遇到'\n'(换行符)的问题的时候,需要提前把这样的换行符给去除掉
            items_top = order_list.find_element_by_xpath('./td').text.replace('\n', '')

            # print 'find    ' + str(items_top.find(u'成交时间'))
            # print 'items_top' + items_top + 'items_top'
            #
            # print 'items_top code : ' + str(type(items_top))  发顺丰

            # 在天猫获取的数据中订单数据的格式为 '分销流水号: 23116200855921'  可以通过正则表达式来获取

            print '*' * 50

            order_distribution_code = re.match(r'.*(%s: \d+)' % u'分销流水号', items_top).group(1)
            print '\n' + order_distribution_code + '\n'

            # 把分销流水号放入到order_detail_info结构中，以便写入redis
            order_detail_info[u'分销流水号'] = order_distribution_code.split(u':')[1]

            # 在天猫获取的数据中订单数据的格式为 '订单编号：30801863041516905'  可以通过正则表达式来获取
            # 这里有一个坑,这里的'订单编号：'中的冒号是中文字符的冒号,所以在想匹配的时候,需要写到正则实例中
            order_code = re.match(r'.*(%s\d+)' % u'订单编号：', items_top).group(1)
            print '\n' + order_code + '\n'

            # 把订单编号放入到order_detail_info结构中，以便写入redis
            order_detail_info[u'订单编号'] = order_code.split(u'：')[1]

            # 把收货人放入到order_detail_info结构中，以便写入到redis中
            buyer_person = order_list.find_element_by_xpath('./td[1]/span[4]').text

            # 在天猫获取的数据中订单数据的格式为 '成交时间: 2017-07-12 04:29'  可以通过正则表达式来获取
            deal_time = re.match(r'.*(%s: \d{4}-\d{2}-\d{2} \d{2}:\d{2})' % u'成交时间', items_top).group(1)
            print '\n' + deal_time + '\n'

            # 把成交时间放入到order_detail_info结构中，以便写入redis
            order_detail_info[u'成交时间'] = deal_time[deal_time.find(u':') + 1:]

            # 获取每个订单号的详细的信息
            order_info = order_list.find_element_by_xpath('./following-sibling::tr[@class="item "][1]')
            # print '*' * 20 + '\n' + order_info + '\n' + '*' * 20
            # 获取消费者买的所有商家的商品列表
            items = order_info.find_elements_by_xpath('./td[1]/ul')

            # 随着业务需求的增长,需要更加详细的去获取每个订单的详细信息，但这种情况需要另一个网页窗口来做此类业务
            def get_extra_order_detail_info():
                # 这次的点击事件会触发另一个窗口,并且浏览器当前的的操作也是在这个窗口中
                order_info.find_element_by_xpath('./td[4]/p[last()]/a').click()
                time.sleep(2)
                print driver.current_url
                # driver.switch_to_window(driver.window_handles[-1])
                driver.switch_to.window(driver.window_handles[-1])
                print driver.current_url
                order_detail_info[u'收货地址'] = driver.find_element_by_xpath('//table[1]/tbody/tr[1]/td[2]').text
                order_detail_info[u'付款时间'] = driver.find_element_by_xpath('//table[3]/tbody/tr[last()-2]/td').text
                order_detail_info[u'发货时间'] = driver.find_element_by_xpath('//table[3]/tbody/tr[last()-1]/td').text
                order_detail_info[u'确认时间'] = driver.find_element_by_xpath('//table[3]/tbody/tr[last()]/td').text

                print u'收货地址: %s' % order_detail_info[u'收货地址']
                print u'付款时间: %s' % order_detail_info[u'付款时间']
                print u'发货时间: %s' % order_detail_info[u'发货时间']
                print u'确认时间: %s' % order_detail_info[u'确认时间']
                # time.sleep(3)
                driver.close()

                # driver.switch_to_window(driver.window_handles[0])
                driver.switch_to.window(driver.window_handles[0])



            print u'从另一个标签页中'
            get_extra_order_detail_info()


            order_total_deal = 0.0
            # 初始化小订单的数据结构

            order_detail_info['items'] = []
            # tmpitems = order_detail_info['items']

            for item in items:
                '''
                    获得一大串有商家的信息: 如
                    若态科技Robotime3D立体原木拼图木质动物小车飞机模型玩具 特价
                        颜色分类：JP235-跑车
                        商家编码：JP235
                        9.90 (单价) (可能有优惠价和修改价)
                        4.70 (采购价)
                        1    (购买商品数量)
                '''

                # print item.text
                seller_name = item.find_element_by_xpath('./li[2]/span[last()]').text.split(u'：')[1]
                price = item.find_element_by_xpath('./li[3]').text  # 这个价格还有一些额外的调价和优惠价的信息,需要去裁剪
                concessional_rate = u'未有优惠'  # 优惠价
                adjust_price = u'未调价'  # 调价信息

                # 这里面的逻辑在于可能在价格之中夹杂一些优惠价的实体,需要处理,通过观察还有一种调价的处理的业务,在优惠价的后面还
                # 需要有调价的特性
                # if price.find('\n') != -1:
                #     concessional_rate = price[price.find('\n') + 1:]
                #     price = price[:price.find('\n')]
                #
                # print '88' * 10 + price + '88' * 10

                price_list = price.split('\n')

                # print price_list
                price = price_list[0]

                # 通过'\n'进行分割
                if len(price_list) == 2:
                    concessional_rate = price_list[1]
                elif len(price_list) == 3:
                    concessional_rate = price_list[1]
                    adjust_price = price_list[2]
                else:
                    pass

                purchase = item.find_element_by_xpath('./li[4]').text
                num = item.find_element_by_xpath('./li[5]').text
                # total_sum_deal = float(purchase) * int(num)

                # 这条代码目前用不到
                # order_total_deal += total_sum_deal

                print u' ' * 10 + u'商家编码:%s 单价:%s 优惠价:%s 调价:%s 采购价:%s 购买数量:%s' \
                                  % (seller_name, price, concessional_rate, adjust_price, purchase, num)
                single_item = {}

                single_item[u'商家编码'] = seller_name
                single_item[u'单价'] = price
                single_item[u'优惠价'] = concessional_rate
                single_item[u'调价'] = adjust_price
                single_item[u'采购价'] = purchase
                single_item[u'购买数量'] = num

                # 把每个小的item的dict都放入到列表中
                order_detail_info['items'].append(single_item)



            # 获得关于这次大订单最后交易的状态
            purchage_result = order_info.find_element_by_xpath('./td[4]/p').text

            total_price_and_delivery = float(order_info.find_element_by_xpath('./td[3]/span[1]').text)

            delivery_price_text = order_info.find_element_by_xpath('./td[3]/span[2]').text

            # buyer_name = order_info.find_element_by_xpath('./td[2]/a').text

            # 匹配的是小数  关于快递费，也是由我们公司来做问题的处理!!!
            delivery_price = re.match(r'.*%s:(\d+\.\d+)' % u'含快递', delivery_price_text)
            if delivery_price is None:
                delivery_price = 0.0
            else:
                delivery_price = float(delivery_price.group(1))

            # print u'最后交易的状态' + purchage_result
            # print u'最后交易的状态:%s 大订单的价格:%.2f' %(purchage_result, total_price_and_delivery - delivery_price)
            print u'收货人: %s 最后交易的状态:%s 需要付费的价格:%.2f(含快递价:%.2f)' % (buyer_person, purchage_result, total_price_and_delivery, delivery_price)
            order_detail_info[u'最后交易的状态'] = purchage_result
            order_detail_info[u'大订单的价格'] = total_price_and_delivery - delivery_price
            order_detail_info[u'收货人'] = buyer_person
            order_detail_info[u'快递价'] = delivery_price

            # 这是一步真正的存储的过程
            save_to_redis(order_detail_info[u'订单编号'], order_detail_info)
        print '*' * 50

    def click_next_page():
        driver.find_element_by_xpath('//a[@class="page-next"]').click()

    def init_redis():
        print '初始化redis客户端!!!'
        r = redis.Redis(host='localhost', port=6379)
        try:
            r.client_list()
        except redis.ConnectionError:
            print u'redis 客户端没有连接成功!!!'
            print u'redis 客户端没有连接成功!!!'
            print u'redis 客户端没有连接成功!!!'
            print u'关闭浏览器!!!'
            driver.quit()

            sys.exit(-1)

        # 把连接池对象放入到redis_list列表中
        redis_list.append(r)



    # 在process_items函数中,把获得的数据保存下来,放入到redis中,使用redis的键值对技术
    # 注意这里面存储的key是字符串
    def save_to_redis(order_key, order_value):
        # k_v = {order_key: order_value}
        # k_v_str = json.dumps(k_v)
        k_v_str = json.dumps(order_value)
        redis_list[0].set(order_key, k_v_str)
        print '把数据存储到redis中' + '*' * 30

    def close_redis(redis_entity):
        pass

    # ******************  processing ****************** #
    # 初始化redis
    init_redis()

    # 对于第一次打开网页,我们特殊做一次处理,网页中有一些关于初学者的指南的学习步骤,会影响爬虫的爬去工作

    print '当前的页码是%s' % '1'
    process_items(True)

    page = 1
    while True:
        page += 1
        print '当前的页码是%s' % page
        try:
            click_next_page()
            time.sleep(10)
            process_items(False)
        except Exception:
	    print u'我们已经到了最后的一页!!!'
            # 如果到了最后一页,我们就完成这次的处理需求
            break

    # 关闭redis 连接池
    close_redis(redis_list)


# 获取出售中的宝贝的详细信息
seller_baby_url = 'https://sell.tmall.com/auction/item/item_list.htm#' \
                  'sortField=starts&status=item_on_sale&order=desc&currentPage=%s'

def process_seller_baby_info():
    babys_info = {}
    url = seller_baby_url.replace('%s', '1')
    eliminate_alert_to_target(url)
    #time.sleep(10)
    total_pages_str = driver.find_element_by_xpath('//*[@id="rtCtn"]/div/div[5]/div/div[2]/div[1]/' +
                                                'div/div[3]/span[2]/div/div/div/span/span[2]').text.strip()
    print u'总共的页数为:%s' % total_pages_str

    def process(page):
        url = seller_baby_url.replace('%s', page)
        eliminate_alert_to_target(url)
        #########time.sleep(3)
        baby_infos_detail = driver.find_elements_by_xpath('//*[@id="rtCtn"]/div/div[5]/div/div[2]/div[1]/div/div[5]' +
                                                          '/div/div/div/div/table/tbody/tr/td[10]/span/div/div[1]/a')
        for info in baby_infos_detail:
            id = str(uuid.uuid1()).replace('-', '')
            babys_info[id] = {}
            href = info.get_attribute('href').strip()

            JS_Script = 'window.open("http://www.baidu.com");'
            driver.execute_script(JS_Script)
            driver.switch_to.window(driver.window_handles[-1])
	    time.sleep(3)

            # 跳转到另一个界面中做操作!!!
            # info.click()
            # time.sleep(30)
            # driver句柄切换到目标句柄中
            # driver.switch_to.window(driver.window_handles[-1])

            print u'href is %s' % href
            # 开始获取每个宝贝的详细的信息
            eliminate_alert_to_target(href)
            # driver.refresh()
            # print u'所获得的内容为:%s' % driver.find_element_by_xpath('//body').text
            # time.sleep(60)
            rows_info = driver.find_elements_by_xpath('//*[@id="J_SKUTable"]/table/tbody/tr')
            print u'每页中列表的数量为:%s' % len(rows_info)
            if rows_info:
                for row in rows_info:
                    price = row.find_element_by_xpath('./td[4]/div/input').get_attribute('value')
                    linkloving_code = row.find_element_by_xpath('./td[6]/div/input').get_attribute('value')
                    babys_info[id]['itemprice'] = price
                    babys_info[id]['code'] = linkloving_code
                    print u'出售中的宝贝商品的价格为:%s\t商品编码为:%s' % (price, linkloving_code)
            else:
                price = driver.find_element_by_xpath('//*[@id="buynow"]').get_attribute('value')
                linkloving_code = driver.find_element_by_xpath('//*[@id="outerIdId"]').get_attribute('value')
                babys_info[id]['itemprice'] = price
                babys_info[id]['code'] = linkloving_code
                print u'出售中的宝贝商品的价格为:%s\t商品编码为:%s' % (price, linkloving_code)

            driver.close()
            driver.switch_to.window(driver.window_handles[-1])

    page = 1
    total_pages = int(total_pages_str)
    while page <= total_pages:
        print u'当前页为:%s' % page
        process(str(page))
        page += 1

def setup(username, password):
    login(loginurl, username, password)
    get_all_infomations_from_tiaomao(common_url)
    process_seller_baby_info()
    time.sleep(10)
    driver.quit()
    print u'爬虫工作完成!!!'


if __name__ == '__main__':
    print u'main....'
    print '__name__ is %s' % __name__
    print '__file__ is %s' % __file__
    try:

        # username = sys.argv[1]
        username = u'若态旗舰店'
        # password = sys.argv[2]
        password = u'szrtkjqjd@123!!'
        setup(username, password)
    except IndexError:
        print u'缺少必要的参数!!!'


