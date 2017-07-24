# from controllers import STATUS_CODE_OK, JsonResponse
# from odoo import http
# from odoo.http import request
#
#
# class file_manager(http.controller):
#
#     @http.route('/linkloving_app_api/download_pdm_file', type='http', auth='none')
#     def download_pdm_file(self,product_id, type=None, model='product.attachment.info', **kw):
#         pass
# if content:
#
#     content = odoo.tools.image_resize_image(base64_source=content, size=( None, None),
#                                             encoding='base64', filetype='PNG')
#     # resize force png as filetype
#     headers = self.force_contenttype(headers, contenttype='image/png')
#
# if content:
#     image_base64 = base64.b64decode(content)
# else:
#     image_base64 = self.placeholder(image='placeholder.png')  # could return (contenttype, content) in master
#     headers = self.force_contenttype(headers, contenttype='image/png')
#
#
# headers.append(('Content-Length', len(image_base64)))
# response = request.make_response(image_base64, headers)
# response.status_code = status
# return response
