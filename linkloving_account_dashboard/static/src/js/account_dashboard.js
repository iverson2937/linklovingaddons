/**
 * Created by allen on 2017/11/22.
 */
odoo.define('linkloving_account_dashboard.account_dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var AccountDashboard = Widget.extend({
        template: "AccountDashboard",


        init: function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
            if (parent && parent.action_stack.length > 0) {
                this.action_manager = parent.action_stack[0].widget.action_manager
            }
            this.product_id = action.product_id;
            var self = this;
        },
        show_bom_line: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            //若点击的是
            if (target.classList.contains('show_bom_line_one') || target.classList.contains('show_bom_line_two')) {
                target = target.parentNode;
            }
            //小三角的变化
            if (target.childNodes.length > 1) {
                if (target.childNodes[1].classList.contains("fa-caret-right")) {
                    target.childNodes[1].classList.remove("fa-caret-right");
                    target.childNodes[1].classList.add("fa-caret-down");
                } else if (target.childNodes[1].classList.contains("fa-caret-down")) {
                    target.childNodes[1].classList.remove("fa-caret-down");
                    target.childNodes[1].classList.add("fa-caret-right");
                }
            }
            if (target.classList.contains('open-sign')) {
                if (target.classList.contains("fa-caret-right")) {
                    target.classList.remove("fa-caret-right");
                    target.classList.add("fa-caret-down");
                } else if (target.classList.contains("fa-caret-down")) {
                    target.classList.remove("fa-caret-down");
                    target.classList.add("fa-caret-right");
                }
                target = target.parentNode;
            }
            // if(target.attributes['data-level'] && target.attributes['data-level'].nodeValue=='true'){
            if (target.attributes['data-product-id']) {
                var product_id = target.attributes['data-product-id'].nodeValue;
                var transform_service = "";
                product_id = parseInt(product_id);
                // console.log(product_id);
                new Model("product.template")
                    .call("get_detail", [product_id])
                    .then(function (result) {
                        console.log(result);
                        var po_length = result.po_lines.length;
                        var bom_length = result.bom_lines.length;
                        var mo_length = result.mo_ids.length;
                        self.$("#" + product_id + ">.panel-body").html(" ");
                        if (result.po_lines.length > 0) {
                            for (var i = 0; i < result.po_lines.length; i++) {
                                result.po_lines[i].date_planned = result.po_lines[i].date_planned.substr(0, 10);
                            }
                        }
                        if (result.mo_ids.length > 0) {
                            for (var i = 0; i < result.mo_ids.length; i++) {
                                result.mo_ids[i].date_planned_finished = result.mo_ids[i].date_planned_finished.substr(0, 10);
                                result.mo_ids[i].date_planned_start = result.mo_ids[i].date_planned_start.substr(0, 10);
                                result.mo_ids[i].planned_start_backup = result.mo_ids[i].planned_start_backup.substr(0, 10);
                            }
                        }
                        var service = {
                            'ordering': '订单制',
                            'stock': '备货制'
                        }
                        if (result.service == 'ordering') {
                            result.service = '订单制'
                        } else if (result.service == 'stock') {
                            result.service = '备货制'
                        }
                        if (result.type == '半成品') {
                            result.service = '备货制';
                        }
                        for (var i = 0; i < result.bom_lines.length; i++) {
                            if (result.bom_lines[i].type == '半成品') {
                                result.bom_lines[i].service = '备货制';
                            }
                            if (result.bom_lines[i].service == 'ordering') {
                                result.service = '订单制'
                            } else if (result.service == 'stock') {
                                result.bom_lines[i].service = '备货制'
                            }
                        }

                        self.$("#" + product_id + ">.panel-body").append(QWeb.render('show_bom_line_tr_add', {
                            bom_lines: result.bom_lines,
                            result: result,
                            po_length: po_length,
                            bom_length: bom_length,
                            mo_length: mo_length,
                            service: service
                        }));
                    });
            }
            // }
        },
        start: function () {
            var self = this;
            // var cp_status = {
            //     breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
            //     // cp_content: _.extend({}, self.searchview_elements, {}),
            // };
            // console.log(cp_status);
            // self.update_control_panel(cp_status);
            // if (this.product_id) {
            //     return new Model("product.template")
            //         .call("get_detail", [this.product_id])
            //         .then(function (result) {
            //             console.log(result);
            //             var transform_service = "";
            //             var po_length = result.po_lines.length;
            //             var bom_length = result.bom_lines.length;
            //             var mo_length = result.mo_ids.length;
            //             //时间截取
            //             if (result.mo_ids.length > 0) {
            //                 for (var i = 0; i < result.mo_ids.length; i++) {
            //                     result.mo_ids[i].date_planned_finished = result.mo_ids[i].date_planned_finished.substr(0, 10);
            //                     result.mo_ids[i].date_planned_start = result.mo_ids[i].date_planned_start.substr(0, 10);
            //                     result.mo_ids[i].planned_start_backup = result.mo_ids[i].planned_start_backup.substr(0, 10);
            //                 }
            //             }
            //             if (result.po_lines.length > 0) {
            //                 for (var i = 0; i < result.po_lines.length; i++) {
            //                     result.po_lines[i].date_planned = result.po_lines[i].date_planned.substr(0, 10);
            //                 }
            //             }
            //             var service = {
            //                 'ordering': '订单制',
            //                 'stock': '备货制'
            //             }
            //             if (result.service == 'ordering') {
            //                 result.service = '订单制'
            //             } else if (result.service == 'stock') {
            //                 result.service = '备货制'
            //             }
            //             if (result.type == '半成品') {
            //                 result.service = '备货制';
            //             }
            //             for (var i = 0; i < result.bom_lines.length; i++) {
            //                 if (result.bom_lines[i].type == '半成品') {
            //                     result.bom_lines[i].service = '备货制';
            //                 }
            //                 if (result.bom_lines[i].service == 'ordering') {
            //                     result.service = '订单制'
            //                 } else if (result.service == 'stock') {
            //                     result.bom_lines[i].service = '备货制'
            //                 }
            //             }
            //             self.$el.append(QWeb.render('show_bom_line_tr', {
            //                 bom_lines: result.bom_lines,
            //                 result: result,
            //                 po_length: po_length,
            //                 bom_length: bom_length,
            //                 mo_length: mo_length,
            //                 service: service
            //             }));
            //
            //         });
            // }
        },
    });

    core.action_registry.add('account_dashboard', AccountDashboard);

    return AccountDashboard;


});
