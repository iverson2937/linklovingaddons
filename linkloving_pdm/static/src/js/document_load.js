/**
 * Created by 123 on 2017/5/10.
 */
odoo.define('linkloving_pdm.document_manage', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    var framework = require('web.framework');
    var QWeb = core.qweb;
    var _t = core._t;

    var DocumentManage = Widget.extend({
        template: 'document_load_page',
        events: {
            'show.bs.tab .tab_toggle_a': 'document_change_tabs',
            'click .document_manage_btn': 'document_form_pop',
            'click .create_document_btn': 'create_document_fn',
            'click .load_container_close': 'close_document_container',
            'click .submit_file_no':'close_document_container',
            'change .my_load_file': 'get_file_name',
            'click .submit_file_yes': 'load_file',
            'change .document_modify': 'document_modify_fn',
            'click .document_download': 'document_download_fn',
            'click .review_cancel': 'cancel_review',
            'click #my_load_file__a_1': 'request_local_server_pdm',
        },
        request_local_server_pdm: function (e) {
            framework.blockUI();
            var self = this;
            console.log(self.product_info);
            $.ajax({
                type: "GET",
                url: "http://localhost:8088",
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
                            var default_code = self.product_info.default_code.trim()
                            var remote_file = cur_type.toUpperCase() + '/' + default_code.split('.').join('/') +
                                '/' + cur_type.toUpperCase() + '_' + default_code.split('.').join('_') + '_v' + ret
                            console.log(ret);
                            $.ajax({
                            type: "GET",
                                url: "http://localhost:8088/uploadfile?id=" + this.product_id + "&remotefile=" + remote_file,
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
                                Dialog.alert("上传失败");
                                console.log(error);
                            }
                        });
                        })

                    }
                    else {
                        framework.unblockUI();
                        Dialog.alert("请打开代理软件!");
                    }
                },
                error: function (error) {
                    framework.unblockUI();
                    Dialog.alert(e.target, "上传失败");
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
        document_download_fn: function () {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            // console.log(new_file_id)
            console.log($(target))
            var type = $(target).attr("data").toUpperCase()
            var remote_path = $("#remote_path").text()
            if (remote_path[0] == '/') {
                remote_path[0] = '';
            }
            console.log(remote_path)
            if (type == 'SIP' || type == 'SOP' || type == 'IPQC') {
                window.location.href = '/download_file/?download=true&id=' + new_file_id;
            } else {
                $.ajax({
                    type: "GET",
                    url: "http://localhost:8088/downloadfile?remotefile=" + remote_path,
                    success: function (data) {
                        console.log(data);
                        if (data.result == '1') {
                            Dialog.alert("已下载至指定目录");
                        }
                        else if (data.result == '2') {
                            Dialog.alert("下载失败, 未选择存储路径");
                        }
                        else {
                            Dialog.alert("下载失败");
                        }
                    },
                    error: function (error) {
                        Dialog.alert("下载失败,请检查是否打开了代理软件");
                    }
                })
            }
        },
        document_modify_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            console.log($(target).parents(".tab_pane_display").children(".tab_message_display"));
            $(target).parents(".tab_pane_display").children(".tab_message_display").prepend("<div class='document_modify_name'>新修改的文件：<span>" + target.files[0].name + "</span></div>");
            $(".document_modify span").val(target.files[0].name);
            var new_file_id = $(target).parents(".tab_pane_display").attr("data-id");
            console.log(new_file_id);
            console.log(target.files[0]);
            var new_file = target.files[0];

            var reader = new FileReader();
            reader.readAsDataURL(new_file);
            reader.onload = function () {
                var encoded_file = reader.result;
                var result = btoa(encoded_file);
                return new Model("product.attachment.info")
                    .call("update_attachment", [parseInt(new_file_id)], {file_binary: result, file_name: new_file.name})
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
        create_document_fn: function () {
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
            var cur_type = $("#document_tab li.active>a").attr("data");
            console.log(cur_type);
            if (cur_type == 'sip' ||
                cur_type == 'sop' ||
                cur_type == 'ipqc') {
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
                    Dialog.alert(result.error)
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
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var file_type = $(target).attr("data");
            self.$("#document_tab").attr("data-now-tab", file_type);
            self.$("#document_tab").attr("data-product-id", this.product_id);
            return new Model("product.template")
                .call("get_attachemnt_info_list", [this.product_id], {type: file_type})
                .then(function (result) {
                    console.log(result)
                    self.$("#" + file_type).html("");
                    self.$("#" + file_type).append(QWeb.render('active_document_tab', {result: result}));
                })
        },
        init: function (parent, action) {
            this._super.apply(this, arguments);
            if (action.product_id) {
                this.product_id = action.product_id;
            } else {
                this.product_id = action.params.active_id;
            }
            var self = this;
        },
        start: function () {
            var self = this;
            // console.log($("body"))
            $("body").attr("data-product-id", this.product_id);
            return new Model("product.template")
                .call("get_file_type_list", [this.product_id])
                .then(function (result) {
                    console.log(result)
                    self.$el.append(QWeb.render('document_load_detail', {result: result.list}));
                    self.product_info = result.info;
                })
        }

    })

    core.action_registry.add('document_manage', DocumentManage);

    return DocumentManage;
})