odoo.define('linkloving_core.notify', function (require) {
    "use strict";

    var core = require('web.core');
    core.action_registry.add('action_notify', function (element, action) {
        var params = action.params;
        if (params) {
            element.do_notify(params.title, params.text, params.sticky);
        }
        return {'type': 'ir.actions.act_window_close'};
    });


});