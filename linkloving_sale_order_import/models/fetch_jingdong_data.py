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
from termcolor import colored


'''
    注意:此模块没有做多线程并发问题,所以，强烈建议多进程模式启动!!!
'''


#display = Display(visible=0, size=(1366, 768))
#display.start()

driver = webdriver.Chrome()
# driver = webdriver.PhantomJS()

loginurl = 'https://passport.shop.jd.com/login/index.action'

# 让浏览器窗口最大化
#driver.maximize_window()
driver.set_window_size(1366, 768)

# 天猫界面中页面做了防爬虫的手段，所以需要使用虚拟浏览器来模拟js定位到制定的位置界面和翻页功能
common_url = 'https://order.shop.jd.com/order/sSopUp_allList.action'
waitting_export_url = 'https://order.shop.jd.com/order/sopUp_waitOutList.action'
alerady_export_url = 'https://order.shop.jd.com/order/sSopUp_newYiShipList.action'
buyer_alerady_accetped_url = 'https://order.shop.jd.com/order/sSopUp_yiReceivingList.action'
lock_order_during_url = 'https://order.shop.jd.com/order/sSopUp_lockOrderList.action'
refund_order_during_url = 'https://order.shop.jd.com/order/sSopUp_refundingList.action'

urls = [waitting_export_url, alerady_export_url, buyer_alerady_accetped_url, lock_order_during_url, refund_order_during_url]

order_detail = {}

# redis_entity 实体,我们需要通过链表的模式来做传递,因为python本身的设计模式就是基于引用(指针)之间的传递
redis_list = []


# 限定抓取数据的天数
def limit_scrapy_data_in_days():
    # 获取当前的日期时间 如: xxxx-xx-xx
    today = datetime.date.today()

    # 默认获取前30天的日期的时间

    prev30_today = today - datetime.timedelta(days=30)

    print 'today is %s   prev30_today is %s' % (prev30_today, today)

    # 京东中的日历控件有只读属性，所以，需要把只读属性去除，才能对控件中数据进行操作
    jsString_createStartDate = 'document.getElementById("createStartDate").removeAttribute("readonly")'
    jsString_createEndDate = 'document.getElementById("createEndDate").removeAttribute("readonly")'

    driver.execute_script(jsString_createStartDate)
    driver.execute_script(jsString_createEndDate)

    # 输入开始日期
    driver.find_element_by_xpath('//*[@id="createStartDate"]').send_keys(u'%s %s' % (str(prev30_today), '00:00:00'))




    # 输入结束时间
    driver.find_element_by_xpath('//*[@id="createEndDate"]').send_keys(u'%s %s' % (str(today), '00:00:00'))

    time.sleep(3)
    # 过滤出30天的数据
    # driver.find_element_by_xpath('//*[@id="J_searchb"]/tbody/tr[3]/td[4]/span/button').click()
    driver.find_element_by_xpath('//*[@id="orderQueryBtn"]').click()
    print u'点击搜索之后,获得需要的结果'


# login in tianmao

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

    while (curpage_url == loginurl):
        # print 'please input the verify code:'
        print '京东登录中的滑块验证已经出现需要去做验证:'

        def verify_span_slider():
            try:
                span_slider = driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
                ActionChains(driver).drag_and_drop_by_offset(span_slider, 258, 0).perform()
                time.sleep(3)
                print u'滑块运行成功!'
            except:
                print u'滑块运行失败!'
            time.sleep(3)

        login_name()
        login_password()
        click_and_login()
        verify_span_slider()

        curpage_url = driver.current_url


def get_all_infomations_from_tiaomao(jingdong_url):
    driver.get(jingdong_url)
    time.sleep(5)


    total_pages_list = []

    def process_items(is_first, total_pages_list=None):
        if is_first:
            # 对于第一次打开网页的时候,会出现操作教程,这个界面我们只需要第一次去处理即可
            try:
                driver.find_element_by_xpath('/html/body/div[7]/div/div[4]/a').click()
                time.sleep(3)
                driver.find_element_by_xpath('/html/body/div[3]/div[2]/div[3]/ul/li[1]/a').click()
                time.sleep(3)

            except:
                print u'可能在某些时候京东会去除这些演示教程,所以需要进行异常处理机制'


            # 也是在第一次的时候，处理搜索的范围 接下来的操作在于是通过获取所需求的30天之内数据
            limit_scrapy_data_in_days()

            # 在页面的底层，京东有完整的页码，方便我们对总的页数进行处理分析的过程!!!
            tmp = driver.find_element_by_xpath('//div[@class="pagin fr"]/span[2]').text.strip()
            # res_str = ur'共(\d+)页'
            res_str = r'%s(\d+)%s' % (u'共', u'页')
            total_pages = re.match(res_str, tmp).groups()[0]
            print u'总共的页码数是 %s' % total_pages

            # 千万要记得,要把内容转换为整形数值.
            total_pages_list.append(int(total_pages))


        # time.sleep(3)


        # 注意,最后一个并没有我们要求的数据，所以，我们把该数据去除掉
        order_lists = driver.find_elements_by_xpath('//tr[@class="head"]')[:-1]

        for order_list in order_lists:
            print order_list.text
            # 获得隐藏属性值中的订单号来对数据进行操作
            order_number = order_list.find_element_by_xpath('./td/input').get_attribute('value').strip()
            print u'order_number is %s' % order_number

            # 这个地方先把各个的订单号拿到手，最后再去做各个的汇总操作
            order_detail[order_number] = ''
            # processOrderDetail(order_number)


    def click_next_page(page_num):
        # 由于京东在做下一页的这种设计的时候，基于自定义操作的步骤，所以对于在下一页的的这个按钮在其他表中是看不到的，所以使用
        # 这种方法在解决问题
        print u'正在处理当前的页码是%s' % page
        driver.find_element_by_xpath('//input[@name="toPage"]').send_keys(page_num)
        driver.find_element_by_xpath('/html/body/div[2]/div/div[3]/div[1]/div/div/div[2]/div[3]/div/em/input[2]').click()





    # 对于第一次打开网页,我们特殊做一次处理,网页中有一些关于初学者的指南的学习步骤,会影响爬虫的爬去工作
    process_items(True, total_pages_list)

    page = 2
    total_pages = total_pages_list[0]
    while page <= total_pages:
        try:
            click_next_page(page)
            # time.sleep(3)
            process_items(False)
        except Exception:
            # 如果到了最后一页,我们就完成这次的处理需求
            break

        page += 1



# 在process_items函数中,把获得的数据保存下来,放入到redis中,使用redis的键值对技术
# 注意这里面存储的key是字符串
def save_to_redis(order_key, order_value):
    # k_v = {order_key: order_value}
    # k_v_str = json.dumps(k_v)
    k_v_str = json.dumps(order_value)
    redis_list[0].set(order_key, k_v_str)
    print '把数据存储到redis中' + '*' * 30



# 处理订单详情界面信息
def processOrderDetail(orderId):
    # 该url所要做的事情在于是获取详细的订单的详情
    order_url = 'https://neworder.shop.jd.com/order/orderDetail?orderId=%s' % orderId
    driver.get(order_url)

    sku_numbers_info = driver.find_elements_by_xpath('/html/body/div[1]/div[5]/table/tbody/tr')
    print colored('*', 'red') * 50 + u'订单的结构' + colored('*', 'red') * 50
    order_detail[orderId] = {}

    pay_info = driver.find_element_by_xpath('/html/body/div[1]/div[4]/table/tbody/tr/td[3]/table/tbody')

    # 付款时间 商品总额 运费总额 促销优惠 优惠券 应支付金额
    order_time = driver.find_element_by_xpath('/html/body/div[1]/div[1]/ul/li[1]/p[2]').text.strip()
    payment_time = pay_info.find_element_by_xpath('./tr[2]/td[2]').text.strip()
    finish_time = pay_info.find_element_by_xpath('/html/body/div[1]/div[1]/ul/li[5]/p[2]').text.strip()
    order_status = pay_info.find_element_by_xpath('/html/body/div[1]/div[2]/p[1]/span[4]').text.strip()
    amount_price = pay_info.find_element_by_xpath('./tr[3]/td[2]').text.strip()
    total_freight = pay_info.find_element_by_xpath('./tr[4]/td[2]').text.strip()
    total_sales_promotion = pay_info.find_element_by_xpath('./tr[5]/td[2]').text.strip()
    coupon_price = pay_info.find_element_by_xpath('./tr[6]/td[2]').text.strip()
    actual_payment = pay_info.find_element_by_xpath('./tr[9]/td[2]').text.strip()

    order_detail[orderId][u'order_time'] = order_time
    order_detail[orderId][u'payment_time'] = payment_time
    order_detail[orderId][u'finish_time'] = finish_time
    order_detail[orderId][u'order_status'] = order_status

    order_detail[orderId][u'amount'] = amount_price
    order_detail[orderId][u'total_freight'] = total_freight
    order_detail[orderId][u'sales_promotion'] = total_sales_promotion
    order_detail[orderId][u'coupon_price'] = coupon_price

    order_detail[orderId][u'actual_payment'] = actual_payment
    order_detail[orderId][u'smalloder'] = []
    print u'订单编号为: %s' % orderId
    print u'下单时间:%s\t付款时间:%s\t完成时间:%s\t订单状态:%s\t商品总额:%s\t运费总额:%s\t促销优惠:%s\t优惠券:%s\t应支付金额:%s' %(
        order_time, payment_time, finish_time, order_status, amount_price, total_freight, total_sales_promotion, coupon_price,
        actual_payment
        )

    print u'小订单的个数为%s' % len(sku_numbers_info)

    for sku_number_info in sku_numbers_info:
        jingdong_sku_number = sku_number_info.find_element_by_xpath('./td[1]').text.strip()
        # 京东的sku商品编号
        # order_detail[orderId][u'商品编号'] = sku_number
        # order_detail[orderId][jingdong_sku_number] = {}
        entity_item_price = sku_number_info.find_element_by_xpath('./td[3]').text.replace(u'￥', '').strip()
        entity_discount_amount = sku_number_info.find_element_by_xpath('./td[4]').text.strip()
        entity_item_count = sku_number_info.find_element_by_xpath('./td[7]').text.strip()
        entity_item_code_temp = sku_number_info.find_element_by_xpath('./td[2]/a').text.strip()
        print u'商品总称为:%s' % entity_item_code_temp
        # entity_item_code = ' '.join(entity_item_code_temp.strip().split(' ')[2:])
        entity_item_code = processJingDongSkuToJiongDongItemCode(orderId, jingdong_sku_number, entity_item_code_temp)
        smallorder = {}
        smallorder[u'entity_item_code'] = entity_item_code
        smallorder[u'entity_item_price'] = entity_item_price
        smallorder[u'entity_discount_amount'] = entity_discount_amount
        smallorder[u'entity_item_count'] = entity_item_count
        order_detail[orderId][u'smalloder'].append(smallorder)

        print colored('*', 'blue') * 40 + u'小订单的结构' + colored('*', 'green') * 40
        print u'商家编码:%s\t商品价格:%s\t优惠金额:%s\t商品数量:%s' %(entity_item_code, entity_item_price, entity_discount_amount, entity_item_count)
        # processJingDongSkuToJiongDongItemCode(orderId,jingdong_sku_number)


# 此方法有递归,目的在与在订单中所要查找的小定单可能不在当前销售的数据之中(数据先去在售的管理界面中寻找),可能在下架的产品之中,如果有recursion == 2 那么,
# 就该去下架的产品中寻找数据
def processJingDongSkuToJiongDongItemCode(orderId, sku_number, total_title,
                                          onSale_url='https://ware.shop.jd.com/onSaleWare/onSaleWare_newDoSearch.action',
                                          recurison_depth = 1
                                          ):
    if recurison_depth > 2:
        return


    # 搜索要找的商品编码
    JS_Script = 'window.open("http://www.baidu.com");'
    driver.execute_script(JS_Script)
    driver.switch_to.window(driver.window_handles[-1])
    # driver.get('https://ware.shop.jd.com/onSaleWare/onSaleWare_newDoSearch.action')
    driver.get(onSale_url)

    try:
        element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                        (By.ID, 'skuId'))
        )
        # prefix = driver.find_element_by_xpath('//*[@id="addWareVO.title"]').get_attribute('value').strip()
        element.send_keys(sku_number)
        driver.find_element_by_xpath('//*[@id="search"]').click()
    except:
        print u'有的时候sku列表不能加载出来!!!'
    prefix = ''
    # time.sleep(3)

    # 填入需要写入的sku列表
    # driver.find_element_by_xpath('//*[@id="skuId"]').send_keys(sku_number)

    # 进行对搜索事件的点击操作


    time.sleep(5)


    try:
        tmp = driver.find_element_by_xpath('//*[@id="tbl_type2"]/tbody/tr/td[2]/div[1]/div').text.strip()
    except:
        # print u'从sku列表中,并没有找到所需要的商品,所以会抛出异常错误!!!'
        tmp = None

    if tmp is None:
        print u'该sku列表没有找到所需要的商品的信息,进入深度为1的递归调用!!!'
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])
        # 在这种情况下,我们更换一下要访问的url列表,这个列表的作用就是在已下架的模块中寻找所需的产品是否存在!!!

        return processJingDongSkuToJiongDongItemCode(orderId, sku_number, total_title, 'https://ware.shop.jd.com/forSaleWare/forSaleWare_newDoSearch.action',
                                              recurison_depth + 1
                                              )

    regular_str = ur'商品编码:(\d+)'


    JingDongItemCode = re.match(regular_str, tmp).groups()[0]

    def process_JingDongItemCode(ItemCode):

        JS_Script = 'window.open("http://www.baidu.com");'
        driver.execute_script(JS_Script)
        driver.switch_to.window(driver.window_handles[-1])

        JingDongItem_url = None
        if recurison_depth == 1:
            JingDongItem_url = 'https://ware.shop.jd.com/ware/publish/ware_editWare.action?wid=%s&saleStatus=onSale' % ItemCode
        elif recurison_depth == 2:
            JingDongItem_url = 'https://ware.shop.jd.com/ware/publish/ware_editWare.action?wid=%s&saleStatus=forSale' % ItemCode
        else:
            pass
        print u'京东规则商品的url :%s' % JingDongItem_url
        driver.get(JingDongItem_url)
        try:
            element = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="nav-0"]/div/ul/li[2]/div[2]/div/div/div/div[1]/div/input'))
            )
            # prefix = driver.find_element_by_xpath('//*[@id="addWareVO.title"]').get_attribute('value').strip()
            prefix = element.get_attribute('value').strip()
        except:
	    print u'京东在sku列表在异步加载的过程中可能时间上达不到所期望的要求!!!'
            prefix = ''



        print u'prefix: %s' % prefix

        def find_linkloving_codefromcategory(name):
            sku_list_info = driver.find_elements_by_xpath('//*[@id="container"]/table/tbody/tr')[1:]
            for sku_info in sku_list_info:
                tmp = sku_info.find_element_by_xpath('./td[1]/b').text.strip()
                print u'tmp is %s , name is %s' % (tmp, name)
                if tmp == name:
                    return sku_info.find_element_by_xpath('./td[5]/input').get_attribute('value').strip()
            return None

        name = total_title.replace(prefix, '').strip()
        code = find_linkloving_codefromcategory(name)

        # driver.switch_to.window(driver.window_handles[-1])
        driver.close()
        driver.switch_to.window(driver.window_handles[-1])

        return code

    code = process_JingDongItemCode(JingDongItemCode)


    # driver.switch_to.window(driver.window_handles[-1])
    driver.close()
    driver.switch_to.window(driver.window_handles[-1])
    return code


def init_redis():
    print '初始化redis客户端!!!'
    r = redis.Redis(host='192.168.2.153', port=6379)
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


def close_redis(redis_entity):
    pass


def setup(username, password):
    login(loginurl, username, password)
    init_redis()

    # for test
    # get_all_infomations_from_tiaomao(alerady_export_url)

    # 真实的测验
    def get_all():
        for url in urls:
            print u'*' * 100 + u'   %s' % url
            try:
                get_all_infomations_from_tiaomao(url)
            except:
                print u'某些url中或许没有需求的数据,所以忽略'

    get_all()

    # 根据获得的订单编号,来获取每个订单编号中关于京东的商品编号
    for order_number in order_detail:
        processOrderDetail(order_number)
        time.sleep(1)
        save_to_redis(order_number, order_detail[order_number])



    time.sleep(10)
    # driver.quit()
    close_redis(redis_list)
    print u'爬虫工作完成!!!'
    print order_detail


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


