# -*- coding: utf-8 -*-

from odoo import http
import datetime
import time
import jpush

app_key = "f2ae889d6e4c3400fef49696"
master_secret = "e1d3af4d5ab66d45f6255c18"
_jpush = jpush.JPush(app_key, master_secret)
push = _jpush.create_push()
_jpush.set_logging("DEBUG")

need_sound = "a.caf"
apns_production = True
from odoo.http import content_disposition, dispatch_rpc, request


class LinklovingGetImageUrl(http.Controller):
    # 获取数据库列表

    @classmethod
    def get_img_url(cls, id, model, field):
        url = '%slinkloving_app_api/get_worker_image?worker_id=%s&model=%s&field=%s&time=%s' % (
            request.httprequest.host_url, str(id), model, field, str(time.mktime(datetime.datetime.now().timetuple())))
        if not url:
            return ''
        return url


class JPushExtend:
    @classmethod
    def send_notification_push(cls, platform=jpush.all_, audience=None, notification=None, body='', message=None,
                               apns_production=True):
        push.audience = audience
        ios = jpush.ios(alert={"title": notification,
                               "body": body,
                               }, sound=need_sound)
        android = jpush.android(alert=body, title=notification)
        push.notification = jpush.notification(ios=ios, android=android)
        push.options = {"apns_production": apns_production, }
        push.platform = platform
        try:
            response = push.send()
        except jpush.common.Unauthorized:
            print ("Unauthorized")
        except jpush.common.APIConnectionException:
            print ("APIConnectionException")
        except jpush.common.JPushFailure:
            print ("JPushFailure")
        except:
            print ("Exception")
