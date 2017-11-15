# -*- coding: utf-8 -*-
import jpush
from odoo import models, fields, api
app_key = "f2ae889d6e4c3400fef49696"
master_secret = "e1d3af4d5ab66d45f6255c18"
_jpush = jpush.JPush(app_key, master_secret)
push = _jpush.create_push()
_jpush.set_logging("DEBUG")

need_sound = "a.caf"
apns_production = True
class JPushExtend:
    @classmethod
    def send_notification_push(cls, platform=jpush.all_, audience=None, notification=None, body='', message=None, apns_production=True):
        push.audience = audience
        ios = jpush.ios(alert={"title":notification,
                                       "body":body,
                                       }, sound=need_sound)
        android = jpush.android(alert={"title":notification,
                                       "body":body,
                                       }, priority=1, style=1)
        push.notification = jpush.notification(ios=ios, android=android)
        push.options = {"apns_production":apns_production,}
        push.platform = platform
        try:
            response = push.send()
        except jpush.common.Unauthorized:
            raise jpush.common.Unauthorized("Unauthorized")
        except jpush.common.APIConnectionException:
            raise jpush.common.APIConnectionException("conn")
        except jpush.common.JPushFailure:
            print ("JPushFailure")
        except:
            print ("Exception")
# JPushExtend.send_push(platform=jpush.all_, audience= "all", notification="My First Push\nMy First Push\nMy First Push\nMy First Push")