/**
 * Created by 123 on 2017/5/10.
 */
odoo.define('linkloving_mrp_automatic_plan.date_manage', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');

    var QWeb = core.qweb;
    var _t = core._t;

    var DateManage = Widget.extend({
        template: '',

        event:{
          // 'click .load_file_submit':'load_file'
        },
        init: function (parent, action) {
            this._super.apply(this, arguments);
            // this.product_id = action.product_id;
            var self = this;
        },
        start: function () {
            var self = this;

        }

    })

    core.action_registry.add('date_manage', DateManage);

    return DateManage;
})