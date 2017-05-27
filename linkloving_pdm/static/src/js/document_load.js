/**
 * Created by 123 on 2017/5/10.
 */
odoo.define('linkloving_pdm.document_manage', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var DocumentManage = Widget.extend({
        template: 'document_load_page',
        events:{
            'show.bs.tab .tab_toggle_a':'document_change_tabs',
            'click .document_manage_btn':'document_form_pop',
            'click .create_document_btn':'create_document_fn',
            'click .load_container_close':'close_document_container',
            'change .my_load_file':'get_file_name',
            'click .submit_file_yes': 'load_file',
            'change .document_modify':'document_modify_fn'
        },
        document_modify_fn:function (e) {
            var e = e||window.event;
            var target = e.target||e.srcElement;
            console.log($(target).parents(".tab_pane_display").children(".tab_message_display"));
            $(target).parents(".tab_pane_display").children(".tab_message_display").prepend("<div class='document_modify_name'>新修改的文件：<span>" + target.files[0].name + "</span></div>");
            $(".document_modify span").val(target.files[0].name);
            var new_file_id = $(".tab_pane_display").attr("data-id");
            console.log(new_file_id)
            console.log(target.files[0])
            var new_file = target.files[0]
            $.ajax({
                type:"post",
                url:"",
                async:true,
                data:{
                    'new_file':new_file,
                    'new_file_id': new_file_id
                },
            })

        },
        load_file:function () {
            $(".my_load_file_name").val("");
            $(".my_load_file_remote_path").val("");
            $(".my_load_file_version").val("");
            $(".load_container").hide();
        },
        get_file_name:function (e) {
            var e = e||window.event;
            var target = e.target||e.srcElement;
            $(".my_load_file_name").val(target.files[0].name)
        },
        close_document_container:function () {
            $(".load_container").hide()
        },
        create_document_fn:function () {
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
            $(".load_container").show();
            $(".file_active_id").val($(this)[0].product_id);
            $(".file_active_type").val($("li.active a").attr("data"));

            var callback = _.uniqueId('func_');
            $(".file_func").val(callback);
            window[callback] = function () {
                // window.location.reload()
                var file_type = self.$("#document_tab").attr("data-now-tab");
                var product_id = parseInt(self.$("#document_tab").attr("data-product-id"));
                return new Model("product.template")
                    .call("get_attachemnt_info_list", [product_id], {type: file_type})
                    .then(function (result) {
                        console.log(result);
                        self.$("#" + file_type).html("");
                        self.$("#" + file_type).append(QWeb.render('active_document_tab', {result: result}));
                    })
            }
        },
        document_form_pop:function (e) {
            var e = e||window.event;
            var target = e.target||e.srcElement;
            var file_id = $(target).attr("data-id");
            var action = {
                name:"详细",
                type: 'ir.actions.act_window',
                res_model:'review.process.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {'default_product_attachment_info_id':file_id} ,
                target: "new",
            };
            this.do_action(action);
            self.$(document).ajaxComplete(function ( event, xhr, settings) {
                // "{"jsonrpc":"2.0","method":"call","params":{"model":"review.process.wizard","method":"search_read","args":[[["id","in",[10]]],["remark","partner_id","display_name","__last_update"]],"kwargs":{"context":{"lang":"zh_CN","tz":"Asia/Shanghai","uid":1,"default_product_attachment_info_id":"4","params":{},"bin_size":true,"active_test":false}}},"id":980816587}"
                var data = JSON.parse(settings.data)
                if(data.params.model == 'review.process.wizard'){
                    if(data.params.method == 'action_to_next' ||
                        data.params.method == 'action_pass' ||
                        data.params.method == 'action_deny'
                    ){
                        var file_type = self.$("#document_tab").attr("data-now-tab");
                        var product_id = parseInt(self.$("#document_tab").attr("data-product-id"));
                        return new Model("product.template")
                            .call("get_attachemnt_info_list", [product_id], {type:file_type})
                            .then(function (result) {
                                console.log(result);
                                self.$("#"+file_type).html("");
                                self.$("#"+file_type).append(QWeb.render('active_document_tab', {result: result}));
                            })
                    }
                }
            })
        },
        document_change_tabs:function (e) {
            var e = e||window.event;
            var target = e.target||e.srcElement;
            var file_type = $(target).attr("data");
            self.$("#document_tab").attr("data-now-tab",file_type);
            self.$("#document_tab").attr("data-product-id",this.product_id);
            return new Model("product.template")
                .call("get_attachemnt_info_list", [this.product_id], {type:file_type})
                .then(function (result) {
                    console.log(result)
                    self.$("#"+file_type).html("");
                    self.$("#"+file_type).append(QWeb.render('active_document_tab', {result: result}));
                })
        },
        init: function (parent, action) {
            this._super.apply(this, arguments);
            if(action.product_id) {
                this.product_id = action.product_id;
            }else {
                this.product_id = action.params.active_id;
            }
            var self = this;
        },
        start: function () {
            var self = this;
            return new Model("product.template")
                .call("get_file_type_list", [this.product_id])
                .then(function (result) {
                    console.log(result);
                    self.$el.append(QWeb.render('document_load_detail', {result: result}));
                })
        }

    })

    core.action_registry.add('document_manage', DocumentManage);

    return DocumentManage;
})