# -*- coding: utf-8 -*-
import jpush
from odoo import models, fields, api
app_key = "6e6ce8723531335ce45edd34"
master_secret = "64ec88028aac4dda6286400e"
_jpush = jpush.JPush(app_key, master_secret)
push = _jpush.create_push()
_jpush.set_logging("DEBUG")

need_sound = "a.caf"
apns_production = False
class JPushExtend:
    @classmethod
    def send_notification_push(cls, platform=jpush.all_, audience=None, notification=None, body='', message=None, apns_production=False):
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