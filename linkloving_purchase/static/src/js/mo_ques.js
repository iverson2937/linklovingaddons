/**
 * Created by 123 on 2017/7/26.
 */
odoo.define('linkloving_purchase.pantner_order_view', function (require) {

    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var PantnerOrderQuestion = Widget.extend({
        template: "HomePageQuestion",
        events: {
            'click .click_tag_a': 'show_bom_line',
            'click .show_msg_number': 'to_msg_page',
        },


        to_msg_page: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var act_id = target.getAttribute("data-id");
            act_id = parseInt(act_id);
            var action = {
                name: "问题详情",
                type: 'ir.actions.act_window',
                res_model: 'mail.message',
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


        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.product_id = action.partner_msg_id;
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
        },
        start: function () {
            var self = this;

            var order_data = []
            for (var val in self.product_id) {
                order_data.splice(0, 0, self.product_id[val]);
            }


            self.$el.append(QWeb.render('show_bom_line_tr_ggg', {
                sale_partner_msg: order_data
            }));

        },
    });

    core.action_registry.add('pantner_order_view', PantnerOrderQuestion);

    return PantnerOrderQuestion;

});