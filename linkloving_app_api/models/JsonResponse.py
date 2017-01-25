# -*- coding: utf-8 -*-
import json


class JsonResponse(object):
    @classmethod
    def send_response(cls, res_code, res_msg='', res_data=None):
        data_dic = {'res_code': res_code,
                    'res_msg': res_msg,}
        if res_data:
            data_dic['res_data'] = res_data
        return json.dumps(data_dic)