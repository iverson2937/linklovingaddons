# -*- coding: utf-8 -*-
import base64
import gzip
import logging
import os

import sys
import textwrap
import zipfile

import zlib
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from odoo import models, fields, api
import qrcode
# class linkloving_qrcode_create(models.Model):
#     _name = 'linkloving_qrcode_create.linkloving_qrcode_create'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
import cStringIO

from odoo.http import request, Response

_logger = logging.getLogger(__name__)
class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    # qrcode_img = fields.Binary(u'二维码图片')

    @api.multi
    def get_product_qrcode(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_qrcode?model=product.template&field=qrcode_img&id=%s&filename=%s.png' % (
            self.id, self.default_code.replace('.', '_')),
            'target': 'new',
        }
    def action_qrcode_download1(self):
        pass
    # @api.multi
    def action_qrcode_download(self):
            str_to_code = self.default_code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=4,
                border=1
            )
            qr.add_data(str_to_code)
            img = qr.make_image()
            new_img = ProductTemplateExtend.create_product_info_image(self, img)
            buffer = cStringIO.StringIO()
            new_img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue())
            return img_str
            # self.qrcode_img = img_str
    @api.multi
    def multi_create_qrcode(self):
        zip_buffer = cStringIO.StringIO()
        f = zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED)
        for product in self:
            str_to_code = product.default_code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=4,
                border=1
            )
            qr.add_data(str_to_code)
            img = qr.make_image()
            new_img = ProductTemplateExtend.create_product_info_image(product, img)
            buffer = cStringIO.StringIO()
            new_img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue())
            f.writestr(str_to_code.replace('.', '_')+'.png', buffer.getvalue())
        f.close()
        return zip_buffer
    #create a new image white bg to contain qrcode and spec
    # def create_bg_image(self):

    @classmethod
    def create_product_info_image(cls, product_tmpl, qr_img):
        img = Image.new("RGB", (450, 230), (255, 255, 255))
        font_size = 25  # 字体大小
        start_x = 140  # 文字起始位置
        line_start_x = 200  # 直线起始位置
        line_width = 220
        l1 = 35  # 第一行ｙ
        l2 = l1 + 80  # ２ｙ
        l3 = l2 + 80  # ３ｙ
        l4 = l3  # ４ｙ
        path = ProductTemplateExtend.cur_file_dir()+'/linklovingaddons/linkloving_qrcode_create/models/simhei.ttf'
        _logger.warning(path)

        font = ImageFont.truetype(path, font_size, encoding='utf-8')
        draw = ImageDraw.Draw(img)

        draw.text(xy=(start_x, l1), text=u'料号:', font=font, fill='black')
        draw.text(xy=(start_x, l2), text=u'品名:', font=font, fill='black')
        # draw.text(xy=(start_x, l3), text=u'规格:', font=font, fill='black')
        draw.text(xy=(start_x, l4), text=u'位置:', font=font, fill='black')

        draw.text(xy=(line_start_x, l1), text=product_tmpl.default_code, font=font, fill='black')

        ProductTemplateExtend.auto_spilt_lines(draw,
                                               product_tmpl.name,
                                               line_start_x,
                                               l2,
                                               font_size,
                                               font)

        # ProductTemplateExtend.auto_spilt_lines(draw,
        #                                        product_tmpl.product_specs,
        #                                        line_start_x,
        #                                        l3,
        #                                        font_size,
        #                                        font)
        # draw.text(xy=(line_start_x, l3), text=product_tmpl.product_specs, font=font, fill='black')
        draw.text(xy=(line_start_x, l4), text=product_tmpl.area_id.name if product_tmpl.area_id else '' , font=font, fill='black')

        draw.line(((line_start_x, l1 + font_size), (line_start_x + line_width, l1 + font_size)), fill='black', width=1)
        draw.line(((line_start_x, l2 + font_size), (line_start_x + line_width, l2 + font_size)), fill='black', width=1)
        draw.line(((line_start_x, l3 + font_size), (line_start_x + line_width, l3 + font_size)), fill='black', width=1)
        draw.line(((line_start_x, l4 + font_size), (line_start_x + line_width, l4 + font_size)), fill='black', width=1)

        img.paste(qr_img, (10,(img.size[1] - qr_img.size[1])/2))
        return img

    @classmethod
    def auto_spilt_lines(cls, draw, text, x, y, font_size, font):
        if not text:
            text = ''
        lines3 = textwrap.wrap(text, width=15)
        if len(lines3) > 3:
            lines3 = lines3[0:3]
        y_text3 = y - (len(lines3) - 1) * font_size
        for line in lines3[0:3]:
            width, height = font.getsize(line)
            draw.text((x, y_text3), line, font=font, fill='black')
            y_text3 += height

    @classmethod
    def cur_file_dir(cls):
        # 获取脚本路径
        path = sys.path[0]
        _logger.warning(path)
        print os.getcwd()
        print os.path.abspath(os.curdir)
        # 判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
        return os.path.abspath(os.curdir)
        # if os.path.isdir(path):
        #     return path
        # elif os.path.isfile(path):
        #     return os.path.dirname(path)

class MultiCreateQRCode(models.TransientModel):
    _name = 'multi.create.qrcode'

    @api.multi
    def action_create_qrcode(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_multi_qrcode?model=product.template&field=qrcode_img&ids=%s&filename=%s' % (
            active_ids, 'qrcode.zip'),
            'target': 'new',
        }

# buffer1 = cStringIO.StringIO()
# zip = zipfile.ZipFile('C:\\ac.zip', 'w',zipfile.ZIP_DEFLATED)
# qr = qrcode.QRCode(
#     version=2,
#     error_correction=qrcode.constants.ERROR_CORRECT_H,
#     box_size=8,
#     border=2
# )
# qr.add_data('123')
# img = qr.make_image()
# buffer = cStringIO.StringIO()
# img.save(buffer, format='PNG')
# img_str = base64.b64encode(buffer.getvalue())
# zip.writestr('ddd.png', buffer.getvalue())
#
# zip.close()
