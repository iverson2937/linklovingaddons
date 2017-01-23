# -*- coding: utf-8 -*-
import base64
import os

import sys
import textwrap

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

class ProductTemplateExtend(models.Model):
    _inherit = 'product.template'

    qrcode_img = fields.Binary(u'二维码图片', compute='_create_qrcode')

    def _create_qrcode(self):
            str_to_code = self.default_code
            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=8,
                border=2
            )
            qr.add_data(str_to_code)
            img = qr.make_image()
            new_img = ProductTemplateExtend.create_product_info_image(self, img)
            buffer = cStringIO.StringIO()
            new_img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue())
            self.qrcode_img = img_str

    #create a new image white bg to contain qrcode and spec
    # def create_bg_image(self):

    @classmethod
    def create_product_info_image(cls, product_tmpl, qr_img):
        img = Image.new("RGB", (450, 250), (255, 255, 255))
        font_size = 13  # 字体大小
        start_x = 250  # 文字起始位置
        line_start_x = 300  # 直线起始位置
        line_width = 120
        l1 = 50  # 第一行ｙ
        l2 = l1 + 50  # ２ｙ
        l3 = l2 + 50  # ３ｙ
        l4 = l3 + 50  # ４ｙ
        font = ImageFont.truetype(ProductTemplateExtend.cur_file_dir()+'/linklovingaddons/linkloving_qrcode_create/models/simsun.ttc', font_size)
        draw = ImageDraw.Draw(img)

        draw.text(xy=(start_x, l1), text=u'料号:', font=font, fill='black')
        draw.text(xy=(start_x, l2), text=u'品名:', font=font, fill='black')
        draw.text(xy=(start_x, l3), text=u'规格:', font=font, fill='black')
        draw.text(xy=(start_x, l4), text=u'位置:', font=font, fill='black')

        draw.text(xy=(line_start_x, l1), text=product_tmpl.default_code, font=font, fill='black')

        lines = textwrap.wrap(product_tmpl.name, width=10)
        y_text = l2 - (len(lines) -1) * font_size
        for line in lines:
            width, height = font.getsize(line)
            draw.text((line_start_x, y_text), line, font=font, fill='black')
            y_text += height

        # draw.text(xy=(line_start_x, l2), text=product_tmpl.name, font=font, fill='black')
        ProductTemplateExtend.auto_spilt_lines(draw,
                                               product_tmpl.product_specs,
                                               line_start_x,
                                               l3,
                                               font_size,
                                               font)
        # draw.text(xy=(line_start_x, l3), text=product_tmpl.product_specs, font=font, fill='black')
        draw.text(xy=(line_start_x, l4), text=product_tmpl.area_id.name if product_tmpl.area_id else '' , font=font, fill='black')

        draw.line(((line_start_x, l1 + font_size), (line_start_x + line_width, l1 + font_size)), fill='black', width=1)
        draw.line(((line_start_x, l2 + font_size), (line_start_x + line_width, l2 + font_size)), fill='black', width=1)
        draw.line(((line_start_x, l3 + font_size), (line_start_x + line_width, l3 + font_size)), fill='black', width=1)
        draw.line(((line_start_x, l4 + font_size), (line_start_x + line_width, l4 + font_size)), fill='black', width=1)

        img.paste(qr_img, (0, 0))
        return img

    @classmethod
    def auto_spilt_lines(cls, draw, text, x, y, font_size, font):
        lines3 = textwrap.wrap(text, width=13)
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
        # 判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
        if os.path.isdir(path):
            return path
        elif os.path.isfile(path):
            return os.path.dirname(path)