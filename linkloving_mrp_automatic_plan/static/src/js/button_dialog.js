odoo.define('linkloving_mrp_automatic_plan.button_dialog', function (require) {
    "use strict";

    var ControlPanel = require('web.ControlPanel');
    var core = require('web.core');
    var data = require('web.data');
    var Dialog = require('web.Dialog');
    var common = require('web.form_common');
    var ListView = require('web.ListView');
    require('web.ListEditor'); // one must be sure that the include of ListView are done (for eg: add start_edition methods)
    var Model = require('web.DataModel');
    var session = require('web.session');
    var utils = require('web.utils');
    var ViewManager = require('web.ViewManager');
    var View = require('web.View');

    var _t = core._t;

    var ButtonDialog = View.include({
        do_execute_action: function (action_data, dataset, record_id, on_closed) {
            var self = this;
            var result_handler = function () {
                if (on_closed) {
                    on_closed.apply(null, arguments);
                }
                if (self.getParent() && self.getParent().on_action_executed) {
                    return self.getParent().on_action_executed.apply(null, arguments);
                }
            };
            if (action_data.type == 'formview_dialog') {
                var model_obj = new Model(dataset.model);
                model_obj.call(action_data.name, [record_id]).then(function (view) {
                    console.log(view)
                    var pop = new common.FormViewDialog(self, view).open();
                    //pop.on('write_completed', self, function(){
                    //    self.display_value = {};
                    //    self.display_value_backup = {};
                    //    self.render_value();
                    //    self.focus();
                    //    self.trigger('changed_value');
                    //});
                });
                return dataset.exec_workflow(record_id, action_data.name);
            }

            return this._super(action_data, dataset, record_id, on_closed);
        }
    });

    return {
        ButtonDialog: ButtonDialog,
    };

});
