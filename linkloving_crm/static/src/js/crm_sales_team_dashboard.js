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

        edit_schedule_report_fn: function () {
            var action = {
                name: "工作报告",
                type: 'ir.actions.act_window',
                res_model: 'crm.sale.daily',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                target: "new"
            };
            this.do_action(action);
        },

        set_invoiced_target_fn: function () {

            $('.set_user_target').show();
        },

        submit_set_target_no_fn: function () {

            $('.set_user_target').hide();
        },
        submit_set_target_summit_fn: function (e) {

            console.log($('.salesman_one'))


        },

    });


});



