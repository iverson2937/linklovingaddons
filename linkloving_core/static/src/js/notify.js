odoo.define('linkloving_core.notify', function (require) {
    "use strict";
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    core.action_registry.add('action_notify', function (element, action) {
        var params = action.params;
        if (params) {
            var dialog = new Dialog(this, {
                'title': params.title,
                // 'subtitle': params.text,
                $content: $("<div/>").html(params.text)
            }).open()
        }
        ;
        return {'type': 'ir.actions.act_window_close'};
    });
});