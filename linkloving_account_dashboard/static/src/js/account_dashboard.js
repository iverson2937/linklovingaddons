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
        // template: "AccountDashboard",
        events: {
            'change .Account_Time_sel': 'sel_func'
        },
        sel_func: function () {
            var time_id = $('.Account_Time_sel option:selected').attr('data-id');
            new Model("account.account")
                .call("get_dashboard_datas", [[]])
                .then(function (result) {
                    $('#account_dashboard').html('');
                    $('#account_dashboard').append(QWeb.render('account_table_tmp', result));
                });

        },

        build_widget: function () {
            return new datepicker.DateTimeWidget(this);
        },
        init_date_widget: function (node) {
            var self = this;
            this.datewidget = this.build_widget();
            this.datewidget.on('datetime_changed', this, function () {
                self.chose_date = self.datewidget.get_value()
            });
            // console.log(self.$el.eq(0))
            this.datewidget.appendTo(self.$el.eq(0).find('.assets_time')).done(function () {
                console.log(self.datewidget.$el);
                self.setupFocus(self.datewidget.$input);

                self.datewidget.set_datetime_default();
            });
        },
        setupFocus: function ($e) {
            var self = this;
            $e.on({
                focus: function () {
                    self.trigger('focused');
                },
                blur: function () {
                    self.trigger('blurred');
                }
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
                .call("get_dashboard_datas", [[]])
                .then(function (result) {
                    self.$el.eq(0).append(QWeb.render('AccountDashboard', result));

                    new Model("account.account")
                        .call("get_period", [[]])
                        .then(function (x) {
                            console.log(x);
                            self.$('.Account_Time_sel').append(QWeb.render('AccountDashboardTimeSelect', {result: x.periods,current:x.current_period}));
                        })
                });
        },
    });

    core.action_registry.add('account_dashboard', AccountDashboard);

    return AccountDashboard;


});
