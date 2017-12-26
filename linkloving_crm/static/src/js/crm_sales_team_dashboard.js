odoo.define('linkloving_crm.crm_dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var formats = require('web.formats');
    var Model = require('web.Model');
    var session = require('web.session');

    var Dashboard_crm = require('sales_team.dashboard');

    var QWeb = core.qweb;

    var _t = core._t;
    var _lt = core._lt;

    var UsersModel = new Model('res.users', session.user_context);

    // var crm_dashboard = Dashboard_crm.extend({
    //
    //     events: {
    //         'click .set_invoiced_target': 'set_invoiced_target_fn',
    //     },
    //
    //     set_invoiced_target_fn: function () {
    //         alert(11)
    //     },
    //
    //
    // });


    Dashboard_crm.include({

        events: {
            'click .o_dashboard_action': 'on_dashboard_action_clicked',
            'click .o_target_to_set': 'on_dashboard_target_clicked',
            'click .set_invoiced_target': 'set_invoiced_target_fn',
            'click .edit_schedule_report': 'edit_schedule_report_fn',

            'click .submit_set_target_no': 'submit_set_target_no_fn',
            'click .submit_set_target_summit': 'submit_set_target_summit_fn',

        },

        edit_schedule_report_fn: function (e) {

            var self = this;
            var $input = $(e.target);
            var target_name = $input.attr('id');


            var action = {
                name: "工作报告",
                type: 'ir.actions.act_window',
                res_model: 'crm.sale.daily',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                target: "new",
                context: {
                    'default_type': target_name
                }
            };
            self.do_action(action);
        },

        set_invoiced_target_fn: function () {

            $('.set_user_target').show();
        },

        submit_set_target_no_fn: function () {

            $('.set_user_target').hide();
        },
        submit_set_target_summit_fn: function (e) {


            var salesman_data = $('.set_user_body >table tr');

            var data = [];

            for (var i = 1; i < salesman_data.length; i++) {
                console.log($(salesman_data[i]));

                data.push({
                    'id': $(salesman_data[i]).attr('class'),
                    'order_name': $(salesman_data[i])["0"].children[1].children["0"].value,
                    'opportunity_name': $(salesman_data[i])["0"].children[2].children["0"].value,
                    'year_order_name': $(salesman_data[i])["0"].children[3].children["0"].value,
                });
            }
            UsersModel.call('set_salesman_target', [], {
                data: data,
            }).then(function (msgs) {
                if (msgs == 'ok') {
                    $('.set_user_target').hide();
                }
            });
        },

    });


})
;



