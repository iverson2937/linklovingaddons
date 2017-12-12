odoo.define('linkloving_core.product_cost', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var ControlPanel = require('web.ControlPanel');
    var QWeb = core.qweb;
    var _t = core._t;

    var ProductCost = Widget.extend(ControlPanelMixin, {
        template: "ProductCost",
        events: {
            'click .click_tag_a': 'show_bom_line',
            'click .show_po_number': 'to_po_page',
            'click .show_mo_number': 'to_mo_page',
            'click .chk_all': 'check_all',
            'click .chk_all_mo': 'check_all',
            // 'click .send-po-btn':'get_po_id',
            'click .send-mo-btn': 'get_mo_id',
            'click .refresh_tree': 'refresh_trees',
            'click .click_mo_a': 'show_mo_lists',
            'click .click_po_a': 'show_mo_lists',
            'click .product_name': 'to_product_name',
            'click .click_po_detail_a': 'show_po_detail_line',
            'click .click_po_detail_a_add': 'show_po_detail_line_add',
            'click .click_mo_detail_a': 'show_mo_detail_line',
            'click .po_mo_target': 'to_po_or_mo_page',
            'click .part_refresh': 'refresh_part_func',
            'click .create_mo_btn': 'click_create_mo',
            'click .delete_mo_btn': 'click_delete_mo',
            'click .create_po_btn': 'click_create_po',
            'click .delete_po_btn': 'click_delete_po',
            'mouseenter .trace_back': 'mouseenter_ev',
            'click .demand_confirm': 'action_demand_confirm',

        },

        action_demand_confirm: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;

            if ($(target).data('id')) {

                new Model("mrp.production")
                    .call("set_to_confirm", [$(target).data('id')])
                    .then(function (result) {
                        $(target).hide();
                        $(target).parents('h4').children(".state").text('需求确认');
                    })
            }
        },
        mouseenter_ev: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            if ($(target).hasClass('mo_trace')) {
                var trace_id = $(target).parents('h4').children('.show_mo_number').attr('data-id');
                console.log(parseInt(trace_id));
                new Model("mrp.production")
                    .call("get_mail_message", [parseInt(trace_id)])
                    .then(function (result) {
                        console.log(result);
                        $(target).attr('title', result[0].name + ',' + result[0].time + ',' + result[0].description)
                    })
            } else if ($(target).hasClass('po_trace')) {
                var trace_id = $(target).parents('h4').children('.show_po_number').attr('data-id');
                console.log(parseInt(trace_id));
                new Model("purchase.order")
                    .call("get_mail_message", [parseInt(trace_id)])
                    .then(function (result) {
                        console.log(result);
                        $(target).attr('title', result[0].name + ',' + result[0].time + ',' + result[0].description)
                    })
            }
        },

        click_create_po: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;

            if ($(target).data('product-tmpl')) {
                var create_po_view = {
                    type: 'ir.actions.act_window',
                    res_model: 'purchase.order.line.wizard',
                    view_mode: 'form',
                    views: [[false, 'form']],
                    context: {'default_product_id': parseInt($(target).data('product-tmpl'))},
                    target: 'new'
                };
                var self = this;
                self.do_action(create_po_view, {
                    on_close: function () {
                        console.log('just to close it ')
                    },
                }).then(function () {
                    console.log('this is just')
                });
            }

        },

        click_delete_mo: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;


            var check_name = target.getAttribute("check-name");
            var selected_mos = [];
            var mo_merge_inputs = $("input[name=" + check_name + "]");
            mo_merge_inputs.each(function () {
                if ($(this).prop("checked")) {
                    selected_mos.push(parseInt($(this).attr("mo-id")))
                }
            });


            if (selected_mos.length > 0) {
                var def = $.Deferred();
                var message = '确定要删除选中的mo?';
                var options = {
                    title: _t("Warning"),
                    //确认删除的操作
                    confirm_callback: function () {

                        new Model("mrp.production")
                            .call("delete_mos", [selected_mos])
                            .then(function (result) {

                            })
                    },
                    cancel_callback: function () {
                        def.reject();
                    },
                };
                var dialog = Dialog.confirm(this, message, options);
                dialog.$modal.on('hidden.bs.modal', function () {
                    def.reject();
                });
                return def;

            } else {
                alert("请选择要删除的MO")
            }

        },


        click_create_mo: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            if ($(target).data('product-tmpl')) {
                var create_mo_view = {
                    type: 'ir.actions.act_window',
                    res_model: 'mrp.production',
                    view_mode: 'form',
                    views: [[false, 'form']],
                    context: {'default_product_id': parseInt($(target).data('product-tmpl'))},
                    target: 'new'
                };
                var self = this;
                self.do_action(create_mo_view, {
                    on_close: function () {
                        console.log('just to close it ')
                    },
                }).then(function () {
                    console.log('this is just')
                });
            }


        },


        refresh_part_func: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            target = $(target).parents('.show_bom_line_one').prevAll('.click_tag_a');
            if (target.attr('data-product-id')) {
                var product_id = target.attr('data-product-id');
                var transform_service = "";
                product_id = parseInt(product_id);
                // console.log(product_id);
                new Model("product.template")
                    .call("get_cost", [product_id])
                    .then(function (result) {
                        console.log(result);
                        var bom_length = result.bom_lines.length;
                        self.$("#" + product_id + ">.panel-body").html(" ");


                        self.$("#" + product_id + ">.panel-body").append(QWeb.render('show_cost_line_tr', {
                            bom_lines: result.bom_lines,
                            result: result,
                            bom_length: bom_length,

                        }));
                    });
            }
        },
        to_po_or_mo_page: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var model_name = target.attributes['data-model'].nodeValue;
            var to_page_id = target.attributes['data-id'].nodeValue;
            to_page_id = parseInt(to_page_id)
            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: model_name,
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: to_page_id,
                target: "new"
            };
            this.do_action(action);
        },
        show_mo_detail_line: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
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
            var mo_id = target.attributes['data-mo-id'].nodeValue;
            var return_origin = target.attributes['data-origin'].nodeValue;
            var more_mo = target.attributes['data-more-mo'].nodeValue;
            mo_id = parseInt(mo_id);
            // console.log(more_mo);
            new Model("purchase.order.line")
                .call("get_source_list", [return_origin, mo_id])
                .then(function (result) {
                    console.log(result)
                    for (var i = 0; i < result.length; i++) {
                        result[i].date = result[i].date.substr(0, 10);
                    }
                    self.$("#mo_detail" + more_mo + ">.panel-body").html(" ")
                    self.$("#mo_detail" + more_mo + ">.panel-body").append(QWeb.render('show_mo_detail_add', {
                        result: result,
                        selection: self.selection
                    }));
                })
        },
        show_po_detail_line: function (e) {
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
            var po_id = target.attributes['data-po-id'].nodeValue;
            po_id = parseInt(po_id);
            console.log(po_id);
            new Model("purchase.order.line")
                .call("get_mo_list", [po_id])
                .then(function (result) {
                    console.log(result)
                    for (var i = 0; i < result.length; i++) {
                        result[i].date = result[i].date.substr(0, 10);
                    }
                    // self.$("#po_detail"+po_id+">.panel-body").html(" ")
                    // self.$("#po_detail"+po_id+">.panel-body").append(QWeb.render('show_po_detail_add', {result:result}));
                })
        },
        show_po_detail_line_add: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
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
            var product_id = target.attributes['data-product-id'].nodeValue;
            var return_origin = target.attributes['data-origin'].nodeValue;
            var mo_id = target.attributes['mo-id'].nodeValue;
            product_id = parseInt(product_id);
            new Model("purchase.order.line")
                .call("get_source_list", [return_origin, product_id])
                .then(function (result) {
                    console.log(result)
                    for (var i = 0; i < result.length; i++) {
                        result[i].date = result[i].date.substr(0, 10);
                    }
                    self.$("#mo_source" + mo_id + ">.panel-body").html(" ")
                    self.$("#mo_source" + mo_id + ">.panel-body").append(QWeb.render('show_cost_line_tr', {
                        result: result,
                        selection: self.selection
                    }));
                })
        },


        check_all: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var chk_id = target.getAttribute("id");
            var abc = $("input[name=" + chk_id + "]");
            abc.each(function () {
                $(this).prop("checked", target.checked)
            })
        },
        // get_po_id:function (e) {
        //     var e = e || window.event;
        //     var target = e.target || e.srcElement;
        //     var check_name =  target.getAttribute("check-name");
        //     // console.log(check_name);
        //     var merge_inputs_ids = [];
        //     var merge_inputs = $("input[name="+check_name+"]");
        //     merge_inputs.each(function () {
        //         if($(this).prop("checked")){
        //             merge_inputs_ids.push(parseInt($(this).attr("po-id")))
        //         }
        //     })
        //     console.log(merge_inputs_ids)
        //      new Model("product.template").call("action_combine",[merge_inputs_ids]).then(function (result) {
        //          console.log(result);
        //      })


        to_po_page: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var act_id = target.getAttribute("data-id");
            act_id = parseInt(act_id);
            var action = {
                name: "采购订单",
                type: 'ir.actions.act_window',
                res_model: 'purchase.order',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: act_id,
                target: "new"
                // employee_name: this.record.name.raw_value,
                // employee_state: this.record.attendance_state.raw_value,
            };
            this.do_action(action);
        },
        to_mo_page: function (e) {
            var e = e || window.event;
            var self = this;
            var target = e.target || e.srcElement;
            var act_id = target.getAttribute("data-id");

            act_id = parseInt(act_id);
            new Model('mrp.production').call('get_formview_id', [[act_id], {'show_custom_form': true}]).then(function (view_id) {
                var action = {
                    name: "详细",
                    type: 'ir.actions.act_window',
                    res_model: 'mrp.production',
                    view_type: 'form',
                    view_mode: 'tree,form',
                    views: [[view_id, 'form']],
                    res_id: act_id,
                    target: "new"
                };

                self.do_action(action);
            });
        },
        to_product_name: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var act_id = target.getAttribute("data-id");
            act_id = parseInt(act_id);
            var action = {
                name: "产品",
                type: 'ir.actions.act_window',
                res_model: 'product.template',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: act_id,
                target: "new"
            };
            this.do_action(action);
        },

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
            var self = this;
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
                    .call("get_cost", [product_id])
                    .then(function (result) {
                        console.log(result);


                        self.$("#" + product_id + ">.panel-body").append(QWeb.render('show_cost_line_tr_add', {
                            bom_lines: result.bom_lines,
                            result: result,
                        }));
                    });
            }
            // }
        },
        start: function () {
            var self = this;
            var cp_status = {
                breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
                // cp_content: _.extend({}, self.searchview_elements, {}),
            };
            self.update_control_panel(cp_status);
            if (this.product_id) {
                return new Model("product.template")
                    .call("get_cost", [this.product_id])
                    .then(function (result) {
                        console.log(result);


                        new Model("mrp.production").call("fields_get", [], {allfields: ['state', 'product_order_type', 'availability']}).then(function (r) {
                            console.log(r);
                            self.selection = r.state.selection;
                            console.log(self.selection);

                            self.$el.append(QWeb.render('show_cost_line_tr', {
                                bom_lines: result.bom_lines,
                                result: result,
                                selection: self.selection,
                                po_length: 0,
                                bom_length: 0,
                                mo_length: 0,
                            }));
                        })

                    });
            }
        },
    });

    core.action_registry.add('cost_detail', ProductCost);

    return ProductCost;

});
