odoo.define('web.CustomerUserMenu', function (require) {
"use strict";

var core = require('web.core');
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var Model = require('web.DataModel');
var session = require('web.session');
var Widget = require('web.Widget');
var UserMenu = require('web.UserMenu');

var _t = core._t;
var QWeb = core.qweb;

UserMenu.include({
    on_menu_bill: function() {
        var self = this;
        console.log('bill');
        this.getParent().clear_uncommitted_changes().then(function() {
            self.rpc("/web/action/load", { action_id: "ljwj_core.action_window_company_account_customer" }).done(function(result) {
                var Partner = new Model('res.partner');
                Partner.query(['ljwj_company_id']).filter([['id','=',session.partner_id]]).first().then(function (partner) {
                    var company_id = partner['ljwj_company_id'][0];
                    console.log(company_id);
                    if (!company_id) {
                        alert('您还未设置所属公司，谢谢！');
                    }
                    else {
                        var Company = new Model('ljwj.company');
                        Company.query(['company_account']).filter([['id','=',company_id]]).first().then(function (company) {
                            console.log(company);
                            var account_id = company['company_account'][0];
                            if (!account_id) {
                                alert('您所在公司并未开通钱包功能，谢谢！');
                            }
                            else {
                                result.res_id = account_id;
                                result.limit = 10;
                                console.log(result);
                                console.log(session);
                                self.getParent().action_manager.do_action(result);
                            };
                        });
                    }
                });

            });
        });
    },
});
});