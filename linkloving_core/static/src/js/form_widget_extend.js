odoo.define('linkloving_core.form_widget_extend', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var FormView = require('web.FormView');
    var ajax = require('web.ajax');
    var crash_manager = require('web.crash_manager');
    var data = require('web.data');
    var datepicker = require('web.datepicker');
    var dom_utils = require('web.dom_utils');
    var Priority = require('web.Priority');
    var ProgressBar = require('web.ProgressBar');
    var Dialog = require('web.Dialog');
    var common = require('web.form_common');
    var formats = require('web.formats');
    var framework = require('web.framework');
    var pyeval = require('web.pyeval');
    var session = require('web.session');
    var utils = require('web.utils');

    var QWeb = core.qweb;
    var _t = core._t;

    var FieldDates = common.fieldDate;
    var form_widget_registry = core.form_widget_registry;

    var substr_time = form_widget_registry.get('date').include({
        render_value: function() {
            if (this.get("effective_readonly")) {
                //add code 2017/5/9 only show year,month,day
                this.$el.text(formats.format_value(this.get('value'), this, '').substring(0,11));
            } else {
                this.datewidget.set_value(this.get('value'));
            }
            // console.log("opopopop")
        }
    });
    FormView.include({
        load_record: function (record) {
            var res1 = this._super.apply(this, arguments);
            var self = this;
            console.log("----load_record-----")
            if (self.fields_view.arch.attrs['edit']) {
                var edit = JSON.parse(self.fields_view.arch.attrs['edit'])
                if (edit instanceof Array) {
                    var res = self.compute_domain([edit])
                    if (res) {
                        self.$buttons.find('.o_form_button_edit').show()
                    } else {
                        self.$buttons.find('.o_form_button_edit').hide()
                    }
                }
            }
            return res1;

        }
    });

    core.action_registry.add('form_widget_extend', substr_time);

    return substr_time
});