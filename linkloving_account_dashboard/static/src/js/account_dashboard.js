/**
 * Created by allen on 2017/11/22.
 */
odoo.define('linkloving_account_dashboard.account_dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ListView = require('web.ListView');
    var common = require('web.form_common');
    var Pager = require('web.Pager');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var datepicker = require('web.datepicker');

    var AccountDashboard = Widget.extend({
        template: "AccountDashboard",
        events: {
            'change .Account_Time_sel': 'sel_func'
        },
        sel_func: function () {
            var time_id = $('.Account_Time_sel option:selected').attr('data-id');
            new Model("account.account")
                .call("get_dashboard_datas", [])
                .then(function (result) {
                    $('#account_dashboard').html('');
                    $('#account_dashboard').append(QWeb.render('account_table_tmp', result));
                });

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

        start: function () {
            var self = this;

            new Model("account.account")
                .call("get_period", [[]])
                .then(function (x) {
                    console.log(x);
                    $('.Account_Time_sel').append(QWeb.render('AccountDashboardTimeSelect', {result: x.periods,current:x.current_period}));

                    new Model("account.account")
                        .call("get_dashboard_datas", [x.current_period.id])
                        .then(function (result) {
                            $('#account_dashboard').append(QWeb.render('account_table_tmp', result));
                        });
                })
        },
    });

    core.action_registry.add('account_dashboard', AccountDashboard);

    return AccountDashboard;


});
