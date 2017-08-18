# -*- coding: utf-8 -*-
import json
import re
import sys

from fetch_tianmao_data2 import limit_scrapy_data_in_days
from odoo import models, fields, api
from selenium import webdriver
import time

driver = webdriver.Chrome()


class ImportSaleOrderSetting(models.Model):
    _name = 'import.sale.order.setting'
    login_url = fields.Char(string=u'登录地址')
    common_url = fields.Char(string=u'访问地址')

    @api.multi
    def login(self):
        for data in self:
            # open the login in page
            driver.get(data.loginurl)
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
            while (curpage_url == data.loginurl):
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

    @api.multi
    def import_tb_sale_order(self):
        for line in self:
            line.login()
            line.get_all_infomations_from_tiaomao()

            time.sleep(10)
            driver.quit()
            print u'爬虫工作完成!!!'
