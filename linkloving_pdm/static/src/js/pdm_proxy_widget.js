/**
 * Created by 123 on 2017/5/10.
 */

odoo.define('linkloving_pdm.pdm_proxy_widget', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var ControlPanel = require('web.ControlPanel');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    var framework = require('web.framework');
    var common = require('web.form_common');
    var QWeb = core.qweb;
    var _t = core._t;
    var PROXY_URL = "http://localhost:8088/";
// static method to open simple confirm dialog
    var FieldPdmProxyFile = core.form_widget_registry.get('binary').extend({
        //template: 'FieldBinaryFile',
        initialize_content: function () {
            var self = this;
            // this._super();
            console.log("pdm_proxy_widget.js");
            self.get_default_pdm_intranet_ip(function (res) {
                self.pdm_info = res;
                console.log(res);
            });
            this.$('.o_select_file_button').click(function (ev) {
                self.request_to_proxy()
                ev.stopPropagation();
            });
        },

        request_to_proxy: function (e) {
            var self = this;
            console.log('new new new');

            $.ajax({
                type: "GET",
                url: PROXY_URL,
                success: function (data) {
                    if (data.result == '1') {

                        var cur_type = self.view.fields.type.get("value");
                        var product_list = self.field_manager.fields['temp_product_tmpl_ids'] ? self.field_manager.fields['temp_product_tmpl_ids'].get_value() : self.field_manager.fields['file_product_tmpl_id'].get_value();

                        if (self.field_manager.fields['file_product_tmpl_id']) {
                            product_list = [['', '', [product_list]]]
                        }

                        if (product_list.length < 1) {
                            Dialog.alert(e, "警告,请选择产品");
                            return;
                        }
                        if (product_list[0][2].length > 1) {
                            Dialog.alert(e, "警告,此类型文件不支持批量上传");
                            return;
                        }

                        if (product_list[0][2].length == 1) {

                            var product_id = product_list[0][2][0];


                            new Model("product.attachment.info").call('default_version', [self.view.options.action.res_id], {
                                context: {
                                    "product_id": parseInt(product_id),
                                    type: cur_type,
                                    'is_update': self.view.fields.temp_product_tmpl_ids ? 'true' : 'false',
                                    'attachment_info_id': self.view.options.action.res_id,
                                }
                            }).then(function (ret) {

                                var default_code = ret.default_code;
                                var default_version = ret.version;
                                var remote_file = cur_type.toUpperCase() + '/' + default_code.split('.').join('/') + '/v' + default_version +
                                    '/' + cur_type.toUpperCase() + '_' + default_code.split('.').join('_') + '_v' + default_version
                                console.log(default_code);
                                $.ajax({
                                    type: "GET",
                                    url: PROXY_URL + "uploadfile",//http://localhost:8088/uploadfile?id=" + this.product_id + "&remotefile=" + remote_file,
                                    data: $.extend(self.pdm_info, {id: parseInt(product_id), remotefile: remote_file}),// "http://localhost:8088/downloadfile?remotefile=" + remote_path,
                                    success: function (data) {
                                        framework.unblockUI();
                                        console.log(data);
                                        if (data.result == '1') {
                                            // $(".this_my_filename").val(data.choose_file_name)
                                            // $(".this_my_remote_path").val(data.path)
                                            $('.this_my_filename').prop('readOnly', true);
                                            $(".this_my_remote_path").prop('readOnly', true);
                                            self.field_manager.fields['file_name'].set_value(data.choose_file_name);
                                            self.field_manager.fields['remote_path'].set_value(data.path);
                                        }
                                    },
                                    error: function (error) {
                                        framework.unblockUI();
                                        Dialog.alert(e, "上传失败,请打开代理软件");
                                        console.log(error);
                                    }
                                });
                            })
                        }
                    }
                    else {
                        framework.unblockUI();
                        Dialog.alert(e, "请打开代理软件!");
                    }
                },
                error: function (error) {
                    framework.unblockUI();
                    Dialog.alert(e, "上传失败,请打开代理软件");
                    console.log(error);
                }
            });
        },

        get_default_pdm_intranet_ip: function (then_cb) {
            var m_fields = ['pdm_intranet_ip', 'pdm_external_ip', 'pdm_port', 'op_path', 'pdm_account', 'pdm_pwd']
            return new Model("pdm.config.settings")
                .call("get_default_pdm_intranet_ip", [m_fields])
                .then(function (res) {
                    then_cb(res);
                });
        },

        request_to_proxy1: function () {
            var self = this;

            console.log('newnewn');
            $.ajax({
                type: "GET",
                url: "http://localhost:8088",
                // dataType: 'json/html',
                success: function (data) {
                    if (data.result == '1') {



                        //var cur_type = $("select.this_my_type").val();
                        var cur_type = self.view.fields.type.get("value");
                        var default_codes_dict = self.view.fields.temp_product_tmpl_ids.dataset.cache;
                        // for (var key in default_codes_dict) {
                        //    var default_codes
                        // }
                        if (Object.keys(default_codes_dict).length != 1) {
                            self.do_warn("警告", "此类型文件不支持批量上传");
                            return;
                        }
                        var product_id = Object.keys(default_codes_dict)[0];
                        new Model("product.attachment.info").call('default_version', [], {
                            context: {
                                "product_id": parseInt(product_id),
                                type: cur_type
                            }
                        }).then(function (ret) {
                            var version = ret["version"];
                            var default_code = ret["default_code"];
                            var remote_file = cur_type.toUpperCase() + '/' + default_code.split('.').join('/') + '/v' + version +
                                '/' + cur_type.toUpperCase() + '_' + default_code.split('.').join('_') + '_v' + version;

                            $.ajax({
                                type: "GET",
                                url: "http://localhost:8088/uploadfile?id=" + product_id_list + "&remotefile=" + remote_file,

                                success: function (data) {
                                    console.log(data);
                                    if (data.result == '1') {
                                        console.log(data.path)
                                        $(".this_my_filename").val(data.choose_file_name)
                                        $(".this_my_remote_path").val(data.path)
                                    }
                                },
                                error: function (error) {
                                    alert("上传失败,请打开代理软件");
                                    console.log(error);
                                }
                            });
                        })

                        // cur_type = cur_type.replace(/"/g, '');
                        // var remote_file = cur_type.toUpperCase() + '/' + cur_type.toUpperCase() + '_' + product_code_str.replace(/\./g, '_') + '_v';


                    }
                    else {
                        alert("请打开代理软件!");
                    }
                },
                error: function (error) {
                    alert("上传失败,请打开代理软件");
                }
            });

        },
        //render_value: function() {
        //    var filename = this.view.datarecord[this.node.attrs.filename];
        //    if (this.get("effective_readonly")) {
        //        this.do_toggle(!!this.get('value'));
        //        if (this.get('value')) {
        //            this.$el.empty().append($("<span/>").addClass('fa fa-download'));
        //            if (filename) {
        //                this.$el.append(" " + filename);
        //            }
        //        }
        //    } else {
        //        if(this.get('value')) {
        //            this.$el.children().removeClass('o_hidden');
        //            this.$('.o_select_file_button').first().addClass('o_hidden');
        //            this.$input.val(filename || this.get('value'));
        //        } else {
        //            this.$el.children().addClass('o_hidden');
        //            this.$('.o_select_file_button').first().removeClass('o_hidden');
        //        }
        //    }
        //}
    });
    core.form_widget_registry.add('pdm_proxy_widget', FieldPdmProxyFile)


    return FieldPdmProxyFile;
})