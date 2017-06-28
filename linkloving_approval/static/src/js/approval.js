/**
 * Created by 123 on 2017/6/26.
 */
odoo.define('linkloving_approval.approval_core', function (require){
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var Approval = Widget.extend({
        template:'approval_load_page',
        events:{
            'show.bs.tab .tab_toggle_a': 'approval_change_tabs',
        },
        //切换选项卡时重新渲染
        approval_change_tabs:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var approval_type = $(target).attr("data");
            console.log(approval_type);
            self.$("#approval_tab").attr("data-now-tab", approval_type);

            var model = new Model("approval.center");
            return model.call("create", [{res_model: 'product.attachment.info', type: approval_type}])
                .then(function (result) {
                    model.call('get_attachment_info_by_type', [result])
                        .then(function (result) {
                            console.log(result);
                            self.$("#"+approval_type).append(QWeb.render('approval_tab_content', {result:result}));
                        })
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

            var model = new Model("approval.center");
            //var info_model = new Model("product.attachment.info")
            model.call("fields_get", ["", ['type']]).then(function (result) {
                console.log(result);
                self.$el.append(QWeb.render('approval_load_detail', {result:result.type.selection}));
            });

            return model.call("create", [{res_model: 'product.attachment.info', type: 'waiting_submit'}])
                .then(function (result) {
                    model.call('get_attachment_info_by_type', [result])
                        .then(function (result) {
                            console.log(result.length);
                            self.$("#waiting_submit").append(QWeb.render('approval_tab_content', {result:result}));
                        })
                })
        }
    });

    core.action_registry.add('approval_core', Approval);

    return Approval;

})