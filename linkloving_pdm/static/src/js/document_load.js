/**
 * Created by 123 on 2017/5/10.
 */

odoo.define('linkloving_pdm.document_manage', function (require) {
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
    var DocumentManage = Widget.extend(ControlPanelMixin, {
        template: 'document_load_page',
        events: {
            'show.bs.tab .tab_toggle_a': 'document_change_tabs',
            'click .document_manage_btn': 'document_form_pop',
            'click .create_document_btn': 'create_document_fn',
            'click .load_container_close': 'close_document_container',
            'click .submit_file_no': 'close_document_container',
            'change .my_load_file': 'get_file_name',
            'click .submit_file_yes': 'load_file',
            'change .document_modify': 'document_modify_fn',
            'click .document_download': 'document_download_fn',
            'click .review_cancel': 'cancel_review',
            'click #my_load_file__a_1': 'request_local_server_pdm',
            'click .approval_product_name': 'product_pop',
            'click .document_modify_2': 'document_modify_2_fn',
            'click input.o_chat_header_file': 'on_click_inputs_file',
            'click button.delect_document_checked': 'on_click_btn_delect_file',

            'click .document_all_checkbox': 'document_all_checkbox_realize',
            'click .outage_document_file': 'outage_document_file_fn',

            'click .document_yellow_dialog_pdm': 'document_yellow_dialog_pdm_fn',

        },


        document_yellow_dialog_pdm_fn: function (e) {
            var tar = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            console.log(target)
            Dialog.alert(target, $(target)["0"].attributes['data-original-title'].value);

        },

        get_default_pdm_intranet_ip: function (then_cb) {
            var m_fields = ['pdm_intranet_ip', 'pdm_external_ip', 'pdm_port', 'op_path', 'pdm_account', 'pdm_pwd']
            return new Model("pdm.config.settings")
                .call("get_default_pdm_intranet_ip", [m_fields])
                .then(function (res) {
                    then_cb(res);
                });
        },
        // 全选
        document_all_checkbox_realize: function (e) {
            var self = this;

            var e = e || window.event;
            var target = e.target || e.srcElement;
            var approval_type = $("#document_tab").attr("data-now-tab");
            $("#" + approval_type + "  input[type='checkbox']").each(function () {
                $(this).prop('checked', $(target).prop('checked') || false);
                self.on_click_inputs_file(this, 'all_checkbox');
            });
        },


        // 停用
        outage_document_file_fn: function (e) {
            var tar = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var approval_type = $("#approval_tab").attr("data-now-tab");
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            var state_type = $(target).attr("data");
            new Model("product.attachment.info").call("chenge_outage_state", [new_file_id], {
                state_type: state_type,
                new_file_id: new_file_id
            }).then(function (result_info) {
                var file_type = self.$("#document_tab").attr("data-now-tab");
                var product_id = parseInt($("body").attr("data-product-id"));
                return new Model("product.template")
                    .call("get_attachemnt_info_list", [product_id], {type: file_type})
                    .then(function (result) {
                        console.log(result);
                        self.$("#" + file_type).html("");
                        self.$("#" + file_type).append(QWeb.render('active_document_tab', {result: result}));
                    });
            });
        },


        on_click_btn_delect_file: function (e) {
            var self = this;
            var attachment_list = [];
            var cur_type = $("#document_tab li.active>a").attr("load_type");
            var choice = confirm("您确认要删除吗？", function () {
            }, null);
            if (choice) {
                if (e.target.parentNode.className == 'delect_one_document') {
                    var e = e || window.event;
                    var target = e.target || e.srcElement;
                    var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
                    console.log('删除一个' + new_file_id);
                    attachment_list.splice(0, 0, parseInt(new_file_id));
                }
                else {
                    console.log('删除选中' + self.file_checkbox);
                    if (self.file_checkbox) {
                        for (var i = 0; i < self.file_checkbox.length; i++) {
                            attachment_list[i] = parseInt(self.file_checkbox[i])
                        }
                    }
                    $('.delect_hide').hide();
                }
                new Model("product.attachment.info")
                    .call("unlink_attachment_list", [attachment_list], {attachment_list: attachment_list})
                    .then(function (result_info) {
                        console.log(result_info);
                        if (result_info.template_id) {

                            return new Model("product.template")
                                .call("get_attachemnt_info_list", [result_info.template_id], {type: result_info.type})
                                .then(function (result) {
                                    console.log(result);

                                    self.file_checkbox = [];
                                    $('.delect_hide').hide();
                                    $('#top_all_checkbox').prop('checked', false);

                                    self.$("#" + result_info.type).html("");
                                    self.$("#" + result_info.type).append(QWeb.render('active_document_tab', {result: result}));
                                });
                        }
                    });
            }
        },


        on_click_inputs_file: function (event, top_10) {
            var self = this;
            var is_hava = true;
            var input_content;

            top_10 ? input_content = event : input_content = event.target;

            var approval_type = $("#approval_tab").attr("data-now-tab");

            if ($(input_content).prop("checked")) {
                self.file_checkbox.splice(0, 0, input_content.name);
            } else {
                while (is_hava) {
                    if ($.inArray(input_content.name, self.file_checkbox) >= 0)
                        self.file_checkbox.splice($.inArray(input_content.name, self.file_checkbox), 1);
                    else
                        break;
                }
            }
            self.file_checkbox = $.grep(self.file_checkbox, function (n) {
                return $.trim(n).length > 0;
            });
            console.log(self.file_checkbox)
            if (self.file_checkbox.length > 1)
                if (approval_type == 'submitted' || approval_type == 'approval')
                    $('#download_checkbox').show();
                else
                    $('.delect_hide').show();

            else if (self.file_checkbox.length = 1)
                $('.delect_hide').hide();
        },


        //点击产品名弹出框
        product_pop: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var product_id = parseInt($(target).attr('product-id'));
            var action = {
                name: "产品详细",
                type: 'ir.actions.act_window',
                res_model: 'product.template',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: product_id,
                target: "new"
            };
            this.do_action(action);
        },
        request_local_server_pdm: function (e) {
            framework.blockUI();
            var self = this;
            console.log(self.product_info);
            $.ajax({
                type: "GET",
                url: PROXY_URL,
                // dataType: 'json/html',
                success: function (data) {
                    if (data.result == '1') {
                        var cur_type = $("#document_tab li.active>a").attr("data");
                        new Model("product.attachment.info").call('default_version', [self.product_id], {
                            context: {
                                "product_id": self.product_info.product_id,
                                type: cur_type
                            }
                        }).then(function (ret) {
                            var default_code = self.product_info.default_code.trim();
                            var default_version = ret.version;
                            var remote_file = cur_type.toUpperCase() + '/' + default_code.split('.').join('/') + '/v' + default_version +
                                '/' + cur_type.toUpperCase() + '_' + default_code.split('.').join('_') + '_v' + default_version
                            console.log(default_code);
                            $.ajax({
                                type: "GET",
                                url: PROXY_URL + "uploadfile",//http://localhost:8088/uploadfile?id=" + this.product_id + "&remotefile=" + remote_file,
                                data: $.extend(self.pdm_info, {id: this.product_id, remotefile: remote_file}),// "http://localhost:8088/downloadfile?remotefile=" + remote_path,
                                success: function (data) {
                                    framework.unblockUI();
                                    console.log(data);
                                    if (data.result == '1') {
                                        $(".my_load_file_name").val(data.choose_file_name)
                                        $(".my_load_file_remote_path").val(data.path)
                                    }
                                },
                                error: function (error) {
                                    framework.unblockUI();
                                    Dialog.alert(e.target, "上传失败,请打开代理软件");
                                    console.log(error);
                                }
                            });
                        })

                    }
                    else {
                        framework.unblockUI();
                        Dialog.alert(e.target, "请打开代理软件!");
                    }
                },
                error: function (error) {
                    framework.unblockUI();
                    Dialog.alert(e.target, "上传失败,请打开代理软件");
                    console.log(error);
                }
            });
        },
        cancel_review: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            console.log(new_file_id);
            var action = {
                name: "填写取消审核原因",
                type: 'ir.actions.act_window',
                res_model: 'review.process.cancel.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {'default_product_attachment_info_id': parseInt(new_file_id), 'review_type': 'file_review'},
                target: "new",
            };
            this.do_action(action);
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                // "{"jsonrpc":"2.0","method":"call","params":{"model":"review.process.wizard","method":"search_read","args":[[["id","in",[10]]],["remark","partner_id","display_name","__last_update"]],"kwargs":{"context":{"lang":"zh_CN","tz":"Asia/Shanghai","uid":1,"default_product_attachment_info_id":"4","params":{},"bin_size":true,"active_test":false}}},"id":980816587}"
                // console.log(settings)
                var data = JSON.parse(settings.data)
                if (data.params.model == 'review.process.cancel.wizard') {
                    if (data.params.method == 'action_cancel_review') {
                        var file_type = self.$("#document_tab").attr("data-now-tab");
                        var product_id = parseInt($("body").attr("data-product-id"));
                        return new Model("product.template")
                            .call("get_attachemnt_info_list", [product_id], {type: file_type})
                            .then(function (result) {
                                console.log(result);
                                self.$("#" + file_type).html("");
                                self.$("#" + file_type).append(QWeb.render('active_document_tab', {result: result}));
                            })
                    }
                }
            })
        },
        document_download_fn: function (e) {
            var self = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            // console.log(new_file_id)
            console.log($(target))
            var type = $(target).attr("data").toUpperCase()
            var remote_path = $(target).parents(".tab_pane_display").find(".remote_path").text()
            if (remote_path[0] == '/') {
                remote_path[0] = '';
            }
            console.log(remote_path)
            if (type == 'OTHER' || type == 'DESIGN') {
                $.ajax({
                    type: "GET",
                    url: PROXY_URL + "downloadfile",// "http://localhost:8088/downloadfile?remotefile=" + remote_path,
                    data: $.extend(self.pdm_info, {remotefile: remote_path}),
                    success: function (data) {
                        console.log(data);
                        if (data.result == '1') {
                            Dialog.OpenDialog(target, "已下载至指定目录", {
                                open_confirm_callback: function () {
                                    self.open_file_browser(data.chose_path, data.file_name, false);
                                },
                                open_file_callback: function () {
                                    self.open_file_browser(data.chose_path, data.file_name, true);
                                }
                            });
                        }
                        else if (data.result == '2') {
                            Dialog.alert(target, "下载失败, 未选择存储路径");
                        }
                        else {
                            Dialog.alert(target, "下载失败");
                        }
                    },
                    error: function (error) {
                        Dialog.alert(target, "下载失败,请检查是否打开了代理软件");
                    }
                })
            } else {
                window.location.href = '/download_file/?download=true&id=' + new_file_id;

            }
        },
        document_modify_2_fn: function (e) {
            var self = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var default_code = self.product_info.default_code.trim()
            var cur_type = $("#document_tab li.active>a").attr("data");
            var ret = $(target).parents(".tab_pane_display").find(".version_span").text()
            var remote_file = cur_type.toUpperCase() + '/' + default_code.split('.').join('/') + '/v' + ret +
                '/' + cur_type.toUpperCase() + '_' + default_code.split('.').join('_') + '_v' + ret
            console.log(ret);
            $.ajax({
                type: "GET",
                url: PROXY_URL + "uploadfile",//http://localhost:8088/uploadfile?id=" + this.product_id + "&remotefile=" + remote_file,
                data: $.extend(self.pdm_info, {id: this.product_id, remotefile: remote_file}),
                success: function (data) {
                    framework.unblockUI();
                    console.log(data);
                    if (data.result == '1') {
                        $(target).parents(".tab_pane_display").children(".tab_message_display").prepend("<div class='document_modify_name'>新修改的文件：<span>" + data.choose_file_name + "</span></div>");
                        var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
                        console.log(data);
                        return new Model("product.attachment.info")
                            .call("update_attachment", [parseInt(new_file_id)], {remote_path: data.path})
                            .then(function (result) {
                                Dialog.alert(target, "修改成功");
                            })
                        //$(".my_load_file_name").val(data.choose_file_name)
                        //$(".my_load_file_remote_path").val(data.path)
                    }
                },
                error: function (error) {
                    framework.unblockUI();
                    Dialog.alert(target, "上传失败,请打开代理软件");
                    console.log(error);
                }
            })

        },
        document_modify_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            console.log($(target).parents(".tab_pane_display").children(".tab_message_display"));
            $(target).parents(".tab_pane_display").children(".tab_message_display").prepend("<div class='document_modify_name'>新修改的文件：<span>" + target.files[0].name + "</span></div>");
            if (target.files) {
                $(".document_modify span").val(target.files[0].name);
            }
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            console.log(new_file_id);
            console.log(target.files[0]);
            var new_file = target.files[0];

            var reader = new FileReader();
            reader.readAsDataURL(new_file);
            reader.onload = function () {
                var encoded_file = reader.result;
                var position = encoded_file.indexOf("base64,");
                if (position > -1) {
                    encoded_file = encoded_file.slice(position + "base64,".length);
                }
                // var result = btoa(encoded_file);
                return new Model("product.attachment.info")
                    .call("update_attachment", [parseInt(new_file_id)], {
                        file_binary: encoded_file,
                        file_name: new_file.name
                    })
                    .then(function (result) {
                    })
            };
        },
        load_file: function () {
            $(".load_container").hide();
            $.blockUI({message: '<img src="linkloving_pdm/static/src/css/spin.png" style="animation: fa-spin 1s infinite steps(12);"/><h3>请稍后</h3>'});
        },
        get_file_name: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            $(".my_load_file_name").val(target.files[0].name)
        },
        close_document_container: function () {
            $(".load_container").hide()
        },
        create_document_fn: function (e) {
            //   var action = {
            //     name:"详细",
            //     type: 'ir.actions.act_window',
            //     res_model:'product.attachment.info',
            //     view_type: 'form',
            //     view_mode: 'tree,form',
            //     views: [[false, 'form']],
            //     target:"new"
            // };
            // this.do_action(action);
            $("#document_tab").attr("data-product-id", this.product_id);

            document.getElementById("document_form").reset();
            $(".file_active_id").val("");
            $(".file_func").val("");
            $(".file_active_type").val("");
            $(".my_load_file_remote_path").val("");
            $(".my_load_file_version").val("");


            $(".load_container").show();
            var cur_type = $("#document_tab li.active>a").attr("load_type");
            console.log(cur_type);
            if (cur_type == 'sys') {
                $("#my_load_file__a_1").hide();
                $("#my_load_file_a").show();
            }
            else {
                $("#my_load_file__a_1").show();
                $("#my_load_file_a").hide();
            }
            $(".file_active_id").val($(this)[0].product_id);
            $(".file_active_type").val($("li.active>a.tab_toggle_a").attr("data"));
            var callback = _.uniqueId('func_');
            $(".file_func").val(callback);
            window[callback] = function (result) {
                if (result.error) {
                    Dialog.alert(e.target, result.error)
                }
                console.log(result)
                // window.location.reload()
                var file_type = self.$("#document_tab").attr("data-now-tab");
                var product_id = parseInt(self.$("#document_tab").attr("data-product-id"));
                return new Model("product.template")
                    .call("get_attachemnt_info_list", [product_id], {type: file_type})
                    .then(function (result) {
                        $.unblockUI();
                        console.log(result);
                        self.$("#" + file_type).html("");
                        self.$("#" + file_type).append(QWeb.render('active_document_tab', {result: result}));
                    })
            }
        },
        document_form_pop: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var file_id = $(target).attr("data-id");
            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'review.process.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {
                    'default_product_attachment_info_id': file_id,
                    'review_type': 'file_review'
                },
                target: "new",
            };
            this.do_action(action);
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                // "{"jsonrpc":"2.0","method":"call","params":{"model":"review.process.wizard","method":"search_read","args":[[["id","in",[10]]],["remark","partner_id","display_name","__last_update"]],"kwargs":{"context":{"lang":"zh_CN","tz":"Asia/Shanghai","uid":1,"default_product_attachment_info_id":"4","params":{},"bin_size":true,"active_test":false}}},"id":980816587}"
                // console.log(settings)
                var data = JSON.parse(settings.data)
                if (data.params.model == 'review.process.wizard') {
                    if (data.params.method == 'action_to_next' ||
                        data.params.method == 'action_pass' ||
                        data.params.method == 'action_deny'
                    ) {
                        var file_type = self.$("#document_tab").attr("data-now-tab");
                        var product_id = parseInt($("body").attr("data-product-id"));
                        return new Model("product.template")
                            .call("get_attachemnt_info_list", [product_id], {type: file_type})
                            .then(function (result) {
                                console.log(result);
                                self.$("#" + file_type).html("");
                                self.$("#" + file_type).append(QWeb.render('active_document_tab', {result: result}));
                            })
                    }
                }
            })
        },
        document_change_tabs: function (e) {
            var tar = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var file_type = $(target).attr("data");
            self.$("#document_tab").attr("data-now-tab", file_type);
            self.$("#document_tab").attr("data-product-id", this.product_id);
            return new Model("product.template")
                .call("get_attachemnt_info_list", [this.product_id], {type: file_type})
                .then(function (result) {
                    console.log(result)

                    tar.file_checkbox = [];
                    $('.delect_hide').hide();
                    $('#top_all_checkbox').prop('checked', false);

                    self.$("#" + file_type).html("");
                    self.$("#" + file_type).append(QWeb.render('active_document_tab', {result: result}));
                })
        },
        init: function (parent, action) {
            this._super(parent)
            this._super.apply(this, arguments);
            if (parent && parent.action_stack.length > 0) {
                this.action_manager = parent.action_stack[0].widget.action_manager
            }
            console.log(parent);
            if (action.context.active_id) {
                this.product_id = action.context.active_id;
            } else {
                this.product_id = action.params.active_id;
            }
            var self = this;

            this.file_checkbox = new Array();

        },
        start: function () {
            var self = this;

            var cp_status = {
                breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
                // cp_content: _.extend({}, self.searchview_elements, {}),
            };
            self.update_control_panel(cp_status);


            $("body").attr("data-product-id", this.product_id);
            return new Model("product.template")
                .call("get_file_type_list", [this.product_id])
                .then(function (result) {
                    console.log(result)
                    self.$el.append(QWeb.render('document_load_detail', {result: result.list}));
                    self.get_default_pdm_intranet_ip(function (res) {
                        self.pdm_info = res;
                        console.log(res);
                    })
                    self.product_info = result.info;
                });
        }

    });
// static method to open simple confirm dialog
    Dialog.OpenDialog = function (owner, message, options) {
        var buttons = [
            {
                text: _t("Ok"),
                classes: 'btn-primary',
                close: true,
                click: options && options.confirm_callback
            },
            {
                text: "打开所在文件夹",
                classes: 'btn-primary',
                close: true,
                click: options && options.open_confirm_callback
            },
            {
                text: "直接打开文件",
                classes: 'btn-primary',
                close: true,
                click: options && options.open_file_callback
            },
            {
                text: _t("Cancel"),
                close: true,
                click: options && options.cancel_callback
            }
        ];
        return new Dialog(owner, _.extend({
            size: 'medium',
            buttons: buttons,
            $content: $('<div>', {
                text: message,
            }),
            title: _t("Confirmation"),
        }, options)).open();
    };

    core.action_registry.add('document_manage', DocumentManage);

    return DocumentManage;
})