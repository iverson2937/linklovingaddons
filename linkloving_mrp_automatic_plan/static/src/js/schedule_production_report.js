/**
 * Created by 123 on 2017/8/31.
 */
odoo.define('linkloving_mrp_automatic_plan.schedule_production_report', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var data_manager = require('web.data_manager');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var ControlPanel = require('web.ControlPanel');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ListView = require('web.ListView');
    var common = require('web.form_common');
    var Pager = require('web.Pager');
    var datepicker = require('web.datepicker');
    var Dialog = require('web.Dialog');
    var framework = require('web.framework');
    var SearchView = require('web.SearchView');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var _t = core._t;
    var myself;
    var move_id;

    var Schedule_Production_Report = Widget.extend(ControlPanelMixin, {
        template: 'schedule_production_tmpl',
        events: {},
        init: function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
            console.log("13123")
            if (parent && parent.action_stack.length > 0) {
                this.action_manager = parent.action_stack[0].widget.action_manager
            }
            if (action.process_id) {
                this.process_id = action.process_id;
            } else {
                this.process_id = action.params.active_id;
            }
            var self = this;
            self.limit = 10;
            self.offset = 1;
            self.length = 10;
        },
        start: function () {
            var self = this;
        }


    })

    core.action_registry.add('schedule_production_report', Schedule_Production_Report);

    return Schedule_Production_Report;
})
