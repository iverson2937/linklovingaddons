/**
 * Created by 123 on 2017/5/10.
 */
odoo.define('linkloving_employee.employee_index_manage', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var EmpployeeManage = Widget.extend({
        template: 'employee_index_template',
        events: {},


        init: function (parent, action) {
            this._super.apply(this, arguments);
            var self = this;
            self.edit_status = false;
        },
        start: function () {
            var self = this;
        }

    })

    core.action_registry.add('employee_index_manage', EmpployeeManage);

    return EmpployeeManage;
})