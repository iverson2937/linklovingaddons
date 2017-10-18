# -*- coding: utf-8 -*-
import json
import re
import sys

import datetime
import traceback

from odoo import models, fields, api
from selenium import webdriver
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

driver = webdriver.Chrome()
driver.maximize_window()


class ImportSaleOrderSetting(models.Model):
    _name = 'import.sale.order.setting'
    login_url = fields.Char(string=u'登录地址')
    common_url = fields.Char(string=u'访问地址')
    partner_id = fields.Many2one('res.partner', string=u'客户名称')
    username = fields.Char(string=u'用户名')
    password = fields.Char(string=u'密码')
    retail_type = fields.Selection([
        ('tb', u'淘宝'),
        ('jd', u'京东'),
    ])

    def _login_name(self):
        try:
            # driver.find_element_by_xpath('//*[@id="loginname"]').click()
            time.sleep(3)
            driver.find_element_by_xpath('//*[@id="loginname"]').clear()
            # driver.find_element_by_xpath('//*[@id="TPL_username_1"]').send_keys(u'若态旗舰店')
            driver.find_element_by_xpath('//*[@id="loginname"]').send_keys(self.username)
            print 'user success!'
        except:
            print 'user error!'
        time.sleep(3)

    def _login_password(self):
        # sign in the pasword
        try:
            driver.find_element_by_xpath('//*[@id="nloginpwd"]').clear()
            # driver.find_element_by_xpath('//*[@id="TPL_password_1"]').send_keys('szrtkjqjd@123!!')
            driver.find_element_by_xpath('//*[@id="nloginpwd"]').send_keys(self.password)
            print 'pw success!'
        except:
            print 'pw error!'
        time.sleep(3)

    def _click_and_login(self):
        # click to login
        try:
            driver.find_element_by_xpath('//*[@id="paipaiLoginSubmit"]').click()
            print 'click success!'
        except:
            print 'click error!'
        time.sleep(3)

    @staticmethod
    def _verify_span_slider():
        try:
            span_slider = driver.find_element_by_xpath('//*[@id="nc_1_n1z"]')
            ActionChains(driver).drag_and_drop_by_offset(span_slider, 258, 0).perform()
            time.sleep(3)
            print u'滑块运行成功!'
        except:
            print u'滑块运行失败!'
        time.sleep(3)

    # 京东登录

    def jdlogin(self):
        # open the login in page
        driver.get(self.login_url)
        try:
            driver.find_element_by_xpath('//*[@id="account-login"]').click()
        except:
            print u'京东登录界面出现改版,需要把用户登陆界面切换出来'
        time.sleep(3)
        # sign in the username

        # 由于京东中使用frame来再次加载一个网页，所以，在选择元素的时候会出现选择不到的结果，所以，我们需要把视图窗口切换到frame中
        driver.switch_to.frame(u'loginFrame')

        self._login_name()
        self._login_password()
        self._click_and_login()

        curpage_url = driver.current_url
        print 'currpage_url ' + curpage_url

        while (curpage_url == self.login_url):
            # print 'please input the verify code:'
            print '京东登录中的滑块验证已经出现需要去做验证:'
            self._login_name()
            self._login_password()
            self._click_and_login()
            self._verify_span_slider()

            curpage_url = driver.current_url

    @api.multi
    def start(self):
        # 京东业务
        self.jdlogin()
        orders = get_all()
        # 根据获得的订单编号,来获取每个订单编号中关于京东的商品编号
        results = []
        for order_number in set(orders):
            self.env['retail.order'].create_retail_sale_order(process_order_detail(order_number),
                                                              partner_id=self.partner_id.id)

            time.sleep(1)
            break


def process_items(is_first, orders, total_pages_list=None):
    if is_first:
        # 对于第一次打开网页的时候,会出现操作教程,这个界面我们只需要第一次去处理即可
        try:
            driver.find_element_by_xpath('/html/body/div[7]/div/div[4]/a').click()
            time.sleep(3)
            driver.find_element_by_xpath('/html/body/div[3]/div[2]/div[3]/ul/li[1]/a').click()
            time.sleep(3)
            print '成功'

        except:
            print u'error'

        # 也是在第一次的时候，处理搜索的范围 接下来的操作在于是通过获取所需求的30天之内数据
        limit_scrapy_data_in_days_jd()
        print ''
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
        orders.append(order_number)

        # 这个地方先把各个的订单号拿到手，最后再去做各个的汇总操作
        # processOrderDetail(order_number)


def get_all_infomations_from_jd(jingdong_url, orders):
    driver.get(jingdong_url)
    time.sleep(5)

    total_pages_list = []

    def click_next_page(page_num):
        # 由于京东在做下一页的这种设计的时候，基于自定义操作的步骤，所以对于在下一页的的这个按钮在其他表中是看不到的，所以使用
        # 这种方法在解决问题
        print u'正在处理当前的页码是%s' % page
        driver.find_element_by_xpath('//input[@name="toPage"]').send_keys(page_num)
        driver.find_element_by_xpath(
            '/html/body/div[2]/div/div[3]/div[1]/div/div/div[2]/div[3]/div/em/input[2]').click()

    # 对于第一次打开网页,我们特殊做一次处理,网页中有一些关于初学者的指南的学习步骤,会影响爬虫的爬去工作
    process_items(True, orders, total_pages_list)
    page = 2
    total_pages = total_pages_list[0]
    while page <= total_pages:
        try:
            click_next_page(page)
            # time.sleep(3)
            process_items(False, orders)
        except Exception:
            # 如果到了最后一页,我们就完成这次的处理需求
            break

        page += 1

    @api.multi
    def login(self):
        for data in self:
            # open the login in page
            driver.get(data.login_url)
            time.sleep(3)
            # sign in the username
            try:
                driver.find_element_by_xpath('//*[@id="J_QRCodeLogin"]/div[5]/a[1]').click()
                time.sleep(3)
                driver.find_element_by_xpath('//*[@id="TPL_username_1"]').send_keys(u'若态旗舰店')
                print 'user success!'
            except:
                print 'user error!'
            time.sleep(3)

            # sign in the pasword
            try:
                driver.find_element_by_xpath('//*[@id="TPL_password_1"]').send_keys('szrtkjqjd@123!!')
                print 'pw success!'
            except:
                print 'pw error!'
            time.sleep(3)
            # click to login
            try:
                driver.find_element_by_xpath('//*[@id="J_SubmitStatic"]').click()
                print 'click success!'
            except:
                print 'click error!'
            time.sleep(3)

            curpage_url = driver.current_url
            print 'currpage_url ' + curpage_url
            while (curpage_url == data.login_url):
                # print 'please input the verify code:'
                print 'please input the verify code:'
                verifycode = sys.stdin.readline()  # 关于验证码中的需求,在目前的的爬虫中没有,但是可能在以后的场景出现,所以还是放在其中
                driver.find_element_by_xpath("//div[@id='pl_login_form']/div/div[2]/div[3]/div[1]/input").send_keys(
                    verifycode)
                try:
                    driver.find_element_by_xpath("//div[@id='pl_login_form']/div/div[2]/div[6]/a").click()
                    print 'click success!'
                except:
                    print 'click error!'
                time.sleep(3)
                curpage_url = driver.current_url

    @api.multi
    def get_all_infomations_from_tiaomao(self):
        for order in self:
            driver.get(order.common_url)
            time.sleep(5)

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

                    # 也是在第一次的时候，处理搜索的范围 接下来的操作在于是通过获取所需求的30天之内数据来
                    limit_scrapy_data_in_days_tb()
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
                    order_detail_info['SN'] = order_distribution_code.split(u':')[1]

                    # 在天猫获取的数据中订单数据的格式为 '订单编号：30801863041516905'  可以通过正则表达式来获取
                    # 这里有一个坑,这里的'订单编号：'中的冒号是中文字符的冒号,所以在想匹配的时候,需要写到正则实例中
                    order_code = re.match(r'.*(%s\d+)' % u'订单编号：', items_top).group(1)
                    print '\n' + order_code + '\n'

                    # 把订单编号放入到order_detail_info结构中，以便写入redis
                    order_detail_info['name'] = order_code.split(u'：')[1]

                    # 把收货人放入到order_detail_info结构中，以便写入到redis中
                    buyer_person = order_list.find_element_by_xpath('./td[1]/span[4]').text

                    # 在天猫获取的数据中订单数据的格式为 '成交时间: 2017-07-12 04:29'  可以通过正则表达式来获取
                    deal_time = re.match(r'.*(%s: \d{4}-\d{2}-\d{2} \d{2}:\d{2})' % u'成交时间', items_top).group(1)
                    print '\n' + deal_time + '\n'

                    # 把成交时间放入到order_detail_info结构中，以便写入redis
                    order_detail_info['deal_date'] = deal_time[deal_time.find(u':') + 1:]

                    # 获取每个订单号的详细的信息
                    order_info = order_list.find_element_by_xpath('./following-sibling::tr[@class="item "][1]')
                    # print '*' * 20 + '\n' + order_info + '\n' + '*' * 20
                    # 获取消费者买的所有商家的商品列表
                    items = order_info.find_elements_by_xpath('./td[1]/ul')

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
                        # single_item[u'商家编码'] = seller_name
                        # single_item[u'单价'] = price
                        # single_item[u'优惠价'] = concessional_rate
                        # single_item[u'调价'] = adjust_price
                        # single_item[u'采购价'] = purchase
                        # single_item[u'购买数量'] = num
                        single_item.update({
                            'code': seller_name,
                            'price_unit': purchase,
                            'product_qty': num,

                        })

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
                    print u'收货人: %s 最后交易的状态:%s 大订单的价格:%.2f' % (buyer_person, purchage_result, total_price_and_delivery)
                    order_detail_info['state'] = purchage_result
                    order_detail_info['total_amount'] = total_price_and_delivery
                    order_detail_info['customer_info'] = buyer_person
                    print order_detail_info
                    self.env['eb.order'].create_eb_sale_order(order_detail_info)

                    # 这是一步真正的存储的过程
                    # save_to_redis(order_detail_info[u'订单编号'], order_detail_info)
                print '*' * 50

            def click_next_page():
                driver.find_element_by_xpath('//a[@class="page-next"]').click()

            # def init_redis():
            #     print '初始化redis客户端!!!'
            #     r = redis.Redis(host='localhost', port=6379)
            #     try:
            #         r.client_list()
            #     except redis.ConnectionError:
            #         print u'redis 客户端没有连接成功!!!'
            #         print u'redis 客户端没有连接成功!!!'
            #         print u'redis 客户端没有连接成功!!!'
            #         print u'关闭浏览器!!!'
            #         driver.quit()
            #
            #         sys.exit(-1)
            #
            #     # 把连接池对象放入到redis_list列表中
            #     redis_list.append(r)

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
            # init_redis()

            # 对于第一次打开网页,我们特殊做一次处理,网页中有一些关于初学者的指南的学习步骤,会影响爬虫的爬去工作
            process_items(True)

            page = 0
            while True:
                page += 1
                print '当前的页码是%s' % page
                try:
                    click_next_page()
                    time.sleep(3)
                    process_items(False)
                except Exception:
                    # 如果到了最后一页,我们就完成这次的处理需求
                    break

            # 关闭redis 连接池
            close_redis(redis_list)


def limit_scrapy_data_in_days_tb():
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

    time.sleep(3)
    # 过滤出30天的数据
    # driver.find_element_by_xpath('//*[@id="J_searchb"]/tbody/tr[3]/td[4]/span/button').click()
    driver.find_element_by_xpath('//button[@class="sui-btn btn-primary btn-large"]').click()
    print u'点击搜索之后,获得需要的结果'


# 此方法有递归,目的在与在订单中所要查找的小定单可能不在当前销售的数据之中(数据先去在售的管理界面中寻找),可能在下架的产品之中,如果有recursion == 2 那么,
# 就该去下架的产品中寻找数据
def processJingDongSkuToJiongDongItemCode(orderId, sku_number, total_title,
                                          onSale_url='https://ware.shop.jd.com/onSaleWare/onSaleWare_newDoSearch.action',
                                          recurison_depth=1
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

        return processJingDongSkuToJiongDongItemCode(orderId, sku_number, total_title,
                                                     'https://ware.shop.jd.com/forSaleWare/forSaleWare_newDoSearch.action',
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
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="nav-0"]/div/ul/li[2]/div[2]/div/div/div/div[1]/div/input'))
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


def process_order_detail(order_id):
    # 该url所要做的事情在于是获取详细的订单的详情
    order_url = 'https://neworder.shop.jd.com/order/orderDetail?orderId=%s' % order_id
    driver.get(order_url)
    res = {}
    items = []
    sku_numbers_info = driver.find_elements_by_xpath('/html/body/div[1]/div[5]/table/tbody')
    pay_info = driver.find_element_by_xpath('/html/body/div[1]/div[4]/table/tbody/tr/td[3]/table/tbody')
    # 付款时间 商品总额 运费总额 促销优惠 优惠券 应支付金额
    order_time = driver.find_element_by_xpath('/html/body/div[1]/div[1]/ul/li[1]/p[2]').text.strip()
    payment_time = pay_info.find_element_by_xpath('./tr[2]/td[2]').text.strip()
    finish_time = pay_info.find_element_by_xpath('/html/body/div[1]/div[1]/ul/li[5]/p[2]').text.strip()
    order_status = pay_info.find_element_by_xpath('/html/body/div[1]/div[2]/p[1]/span[4]').text.strip()
    amount_price = pay_info.find_element_by_xpath('./tr[3]/td[2]').text.replace(u'￥', '').strip()
    total_freight = pay_info.find_element_by_xpath('./tr[4]/td[2]').text.replace(u'￥', '').strip()
    total_sales_promotion = pay_info.find_element_by_xpath('./tr[5]/td[2]').text.replace(u'￥', '').strip()
    coupon_price = pay_info.find_element_by_xpath('./tr[6]/td[2]').text.replace(u'￥', '').strip()
    actual_payment = pay_info.find_element_by_xpath('./tr[9]/td[2]').text.replace(u'￥', '').strip()

    for sku_number_info in sku_numbers_info:
        item = {}
        jingdong_sku_number = sku_number_info.find_element_by_xpath('./tr/td[1]').text.strip()
        # 京东的sku商品编号
        # order_detail[orderId][u'商品编号'] = sku_number
        # order_detail[orderId][jingdong_sku_number] = {}
        entity_item_price = sku_number_info.find_element_by_xpath('./tr/td[3]').text.replace(u'￥', '').strip()
        entity_discount_amount = sku_number_info.find_element_by_xpath('./tr/td[4]').text.replace(u'￥', '').strip()
        entity_item_count = sku_number_info.find_element_by_xpath('./tr/td[7]').text.replace(u'￥', '').strip()
        entity_item_code_temp = sku_number_info.find_element_by_xpath('./tr/td[2]/a').text.strip()
        print u'商品总称为:%s' % entity_item_code_temp
        # entity_item_code = ' '.join(entity_item_code_temp.strip().split(' ')[2:])
        entity_item_code = processJingDongSkuToJiongDongItemCode(order_id, jingdong_sku_number, entity_item_code_temp)
        item.update({
            'default_code': entity_item_code,
            'product_name': entity_item_code_temp,
            'price_unit': entity_item_price,
            'discount': entity_discount_amount,
            'product_qty': entity_item_count,
        })
        items.append(item)
        print u'商家编码:%s\t商品价格:%s\t优惠金额:%s\t商品数量:%s' % (
            entity_item_code, entity_item_price, entity_discount_amount, entity_item_count)
    print order_time, '44444444444'
    res.update({
        'order_date': datetime.datetime.strptime(order_time, "%Y-%m-%d %H:%M:%S") if order_time else False,
        'payment_date': datetime.datetime.strptime(payment_time, "%Y-%m-%d %H:%M:%S") if payment_time else False,
        'finish_date': datetime.datetime.strptime(finish_time, "%Y-%m-%d %H:%M:%S") if finish_time else False,
        'order_status': order_status,
        'total_amount': amount_price,
        'delivery_fee': total_freight,
        'sales_promotion': total_sales_promotion,
        'coupon_price': coupon_price,
        'actual_payment': actual_payment,
        'items': items,
    })
    print u'下单时间:%s\t付款时间:%s\t完成时间:%s\t订单状态:%s\t商品总额:%s\t运费总额:%s\t促销优惠:%s\t优惠券:%s\t应支付金额:%s' % (
        order_time, payment_time, finish_time, order_status, amount_price, total_freight, total_sales_promotion,
        coupon_price,
        actual_payment
    )
    return {order_id: res}


def limit_scrapy_data_in_days_jd():
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


def get_all():
    orders = []
    waitting_export_url = 'https://order.shop.jd.com/order/sopUp_waitOutList.action'
    alerady_export_url = 'https://order.shop.jd.com/order/sSopUp_newYiShipList.action'
    buyer_alerady_accetped_url = 'https://order.shop.jd.com/order/sSopUp_yiReceivingList.action'
    lock_order_during_url = 'https://order.shop.jd.com/order/sSopUp_lockOrderList.action'
    refund_order_during_url = 'https://order.shop.jd.com/order/sSopUp_refundingList.action'

    urls = [waitting_export_url, alerady_export_url, buyer_alerady_accetped_url, lock_order_during_url,
            refund_order_during_url]
    for url in urls:
        print u'*' * 100 + u'   %s' % url
        try:
            get_all_infomations_from_jd(url, orders)
        except Exception, e:
            print e
    return orders
