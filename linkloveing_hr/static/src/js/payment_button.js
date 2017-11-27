odoo.define('prepayment_button', function (require) {
    "use strict";

    var core = require('web.core');
    var form_common = require('web.form_common');
    var formats = require('web.formats');
    var Model = require('web.Model');

    var QWeb = core.qweb;

    var ShowPrePaymentWidget = form_common.AbstractField.extend({
        render_value: function () {
            var self = this;

            var info = JSON.parse(this.get('value'));
            console.log(this);
            this.$el.html(QWeb.render('ShowPrePayment', {
                'pre_payment_amount': info.pre_payment_amount,
                'payment_line_amount': info.payment_line_amount,
            }));

            // var action = {
            //     type: 'ir.actions.act_window',
            //     res_model: 'hr.expense.sheet',
            //     views: [[false, 'form']],
            //     res_id: info.sheet_id,
            //     context: {
            //         'default_payment_ids': info.payment_ids,
            //     },
            //     target: 'new'
            // };
            this.$('.to_deduct_payment').click(function () {

                new Model('hr.expense.sheet').call('get_formview_id', [[info.sheet_id], {'show_custom_form': true}]).then(function (view_id) {
                    var action = {
                        name: "详细",
                        type: 'ir.actions.act_window',
                        res_model: 'hr.expense.sheet',
                        view_type: 'form',
                        view_mode: 'tree,form',
                        views: [[view_id, 'form']],
                        res_id: info.sheet_id,
                        target: "new"
                    };

                    self.do_action(action);
                });
            });
            //     _.each(this.$('.js_payment_info'), function(k, v){
            //         var options = {
            //             'content': QWeb.render('PaymentPopOver', {
            //                     'name': info.content[v].name,
            //                     'journal_name': info.content[v].journal_name,
            //                     'date': info.content[v].date,
            //                     'amount': info.content[v].amount,
            //                     'currency': info.content[v].currency,
            //                     'position': info.content[v].position,
            //                     'payment_id': info.content[v].payment_id,
            //                     'move_id': info.content[v].move_id,
            //                     'ref': info.content[v].ref,
            //                     }),
            //             'html': true,
            //             'placement': 'left',
            //             'title': 'Payment Information',
            //             'trigger': 'focus',
            //             'delay': { "show": 0, "hide": 100 },
            //         };
            //         $(k).popover(options);
            //         $(k).on('shown.bs.popover', function(event){
            //             $(this).parent().find('.js_unreconcile_payment').click(function(){
            //                 var payment_id = parseInt($(this).attr('payment-id'))
            //                 if (payment_id !== undefined && payment_id !== NaN){
            //                     new Model("account.move.line")
            //                         .call("remove_move_reconcile", [payment_id, {'invoice_id': self.view.datarecord.id}])
            //                         .then(function (result) {
            //                             self.view.reload();
            //                         });
            //                 }
            //             });
            //             $(this).parent().find('.js_open_payment').click(function(){
            //                 var move_id = parseInt($(this).attr('move-id'))
            //                 if (move_id !== undefined && move_id !== NaN){
            //                     //Open form view of account.move with id = move_id
            //                     self.do_action({
            //                         type: 'ir.actions.act_window',
            //                         res_model: 'account.move',
            //                         res_id: move_id,
            //                         views: [[false, 'form']],
            //                         target: 'current'
            //                     });
            //                 }
            //             });
            //         });
            //     });
            // }
            // else {
            //     this.$el.html('');
            // }
        },
    });

    core.form_widget_registry.add('prepayment_button', ShowPrePaymentWidget);

});