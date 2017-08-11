/**
 * Created by Administrator on 2017/7/18.
 */
/**
 * Created by 123 on 2017/6/26.
 */
odoo.define('linkloving_approval.approval_bom', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var Pager = require('web.Pager');
    var ListView = require('web.ListView');
    var ControlPanelMixin = require('web.ControlPanelMixin');

    var QWeb = core.qweb;
    var _t = core._t;

    var Approval = Widget.extend(ControlPanelMixin, {
        template: 'bom_approve_page',
        events: {
            'show.bs.tab .tab_toggle_a': 'approval_change_tabs',
            'click .document_manage_btn': 'document_form_pop',
            'change .document_modify': 'document_modify_fn',
            'click .approval_product_name': 'product_pop',
            'click .review_cancel': 'cancel_approval',
            'click .bom_view': 'bom_view_fn',
            'click .download_file': 'document_download_fn',
        },


        //查看BOM
        bom_view_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var bom_id = $(target).parents(".tab_pane_display").data("id");
            var action = {
                name: "BOM",
                type: 'ir.actions.client',
                'tag': 'new_bom_update',
                'bom_id': parseInt(bom_id),
                'is_show':false,
                target: "new",
            };
            this.do_action(action);
        },
        //取消审核
        cancel_approval: function (e) {
            var tar = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var new_file_id = $(target).parents(".tab_pane_display").data("id");
            var action = {
                name: "填写取消审核原因",
                type: 'ir.actions.act_window',
                res_model: 'review.process.cancel.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {'default_bom_id': parseInt(new_file_id), 'review_type': 'bom_review'},
                target: "new",
            };
            this.do_action(action);
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                // "{"jsonrpc":"2.0","method":"call","params":{"model":"review.process.wizard","method":"search_read","args":[[["id","in",[10]]],["remark","partner_id","display_name","__last_update"]],"kwargs":{"context":{"lang":"zh_CN","tz":"Asia/Shanghai","uid":1,"default_product_attachment_info_id":"4","params":{},"bin_size":true,"active_test":false}}},"id":980816587}"
                // console.log(settings)
                var data = JSON.parse(settings.data)
                if (data.params.model == 'review.process.cancel.wizard') {
                    if (data.params.method == 'action_cancel_review') {
                        var file_type = self.$("#approval_tab").attr("data-now-tab");

                        return tar.get_datas(tar, 'mrp.bom', file_type);
                    }
                }
            })
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

        //审核操作
        document_form_pop: function (e) {
            var tar = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var bom_id = $(target).parents(".tab_pane_display").data("id");
            var is_show_action_deny = $(target).data("action-deny");
            if (!is_show_action_deny) {
                is_show_action_deny = 'false'
            }
            ;
            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'review.process.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {
                    'default_bom_id': parseInt(bom_id),
                    'is_show_action_deny': is_show_action_deny,
                    'review_type': 'bom_review'
                },
                'target': "new",
            };
            this.do_action(action);
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                var data = JSON.parse(settings.data)
                if (data.params && data.params.model == 'review.process.wizard') {
                    if (data.params.method == 'action_to_next' ||
                        data.params.method == 'action_pass' ||
                        data.params.method == 'action_deny'
                    ) {
                        var approval_type = self.$("#approval_tab").attr("data-now-tab");
                        self.$("#" + approval_type).html("");
                        console.log(approval_type);
                        return tar.get_datas(tar, 'mrp.bom', approval_type);
                    }
                }
            })
        },
        //切换选项卡时重新渲染
        approval_change_tabs: function (e) {
            var self = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var approval_type = $(target).attr("data");
            self.flag = 1;
            self.begin=1;
            // console.log(approval_type);
            self.$("#approval_tab").attr("data-now-tab", approval_type);

            var model = new Model("approval.center");
            return self.get_datas(this, 'mrp.bom', approval_type);
        },

        init: function (parent, action) {
            var self = this;
            self.flag = 1;
            self.begin = 1;
            self.limit = 10;
            this.approval_type = null;
            this._super.apply(this, arguments);
            if (action.product_id) {
                this.product_id = action.product_id;
            } else {
                this.product_id = action.params.active_id;
            }
            //分页
            this.pager = null;
        },
        render_pager: function () {
            console.log(this.length, this.begin, this.limit);
            if (this.flag == 1) {
                if($(".approval_pagination")){
                    $(".approval_pagination").remove()
                }
                var $node = $('<div/>').addClass('approval_pagination').appendTo($("#approval_tab"));
                // if (!this.pager) {
                    this.pager = new Pager(this, this.length, this.begin, this.limit);
                    this.pager.appendTo($node);

                    this.pager.on('pager_changed', this, function (new_state) {
                        var self = this;
                        var limit_changed = (this._limit !== new_state.limit);
                        console.log(new_state);

                        this._limit = new_state.limit;
                        this.current_min = new_state.current_min;
                        self.reload_content(this).then(function () {
                            // if (!limit_changed) {
                            self.$el.animate({"scrollTop": "0px"}, 100);
                            // $(".approval_page_container").offset({ top: 50})
                            // this.set_scrollTop(0);
                            // this.trigger_up('scrollTo', {offset: 0});
                            // }
                        });
                    });
                // }
                this.flag = 2
            }
        },
        reload_content: function (own) {
            var reloaded = $.Deferred();
            own.begin = own.current_min;
            // console.log(this.approval_type)
            var approval_type = own.approval_type[0][0];
            own.get_datas(own, 'mrp.bom', approval_type);
            reloaded.resolve();
            return reloaded.promise();
        },
        set_scrollTop: function (scrollTop) {
            this.scrollTop = scrollTop;
        },
        get_datas: function (own, res_model, approval_type) {
            var model = new Model("approval.center");
            model.call("create", [{res_model: res_model, type: approval_type}])
                .then(function (result) {
                    console.log(result,own.begin,own.limit);
                    model.call('get_bom_info_by_type', [result], {offset: own.begin-1, limit: own.limit})
                        .then(function (result) {
                            console.log(result);
                            own.length = result.length;
                            console.log(own.length,result.length)
                            self.$("#" + approval_type).html("");
                            self.$("#" + approval_type).append(QWeb.render('bom_approval_tab_content', {
                                result: result.bom_list,
                                approval_type: approval_type
                            }));
                            own.render_pager();
                        })
                })
        },


        start: function () {
            var self = this;

            var model = new Model("approval.center");
            model.call("fields_get", ["", ['type']]).then(function (result) {
                console.log(result);
                self.approval_type = result.type.selection;
                // console.log(self);
                self.$el.append(QWeb.render('approval_load_detail', {result: result.type.selection}));
            });
            return self.get_datas(this, 'mrp.bom', 'waiting_submit');

        }
    });

    core.action_registry.add('approval_bom', Approval);

    return Approval;

})
