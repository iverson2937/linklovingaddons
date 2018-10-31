odoo.define('linkloving_core.archive_confirm)', function (require) {
    "use strict";

    /**
     * 归档与否前加个确认的弹框
     * */

    var Dialog = require('web.Dialog');
    var form_widgets = require('web.form_widgets');


    form_widgets.WidgetButton.prototype.execute_action = function () {
        var self = this;
        var exec_action = function () {
            if (self.node.attrs.confirm) {
                var def = $.Deferred();
                Dialog.confirm(self, self.node.attrs.confirm, {confirm_callback: self.on_confirmed})
                    .on("closed", null, function () {
                        def.resolve();
                    });
                return def.promise();
            } else if (self.node.attrs.name == 'toggle_active') {
                var def = $.Deferred();
                Dialog.confirm(self, '确定你的操作吗', {confirm_callback: self.on_confirmed})
                    .on("closed", null, function () {
                        def.resolve();
                    });
                return def.promise();
            }
            else {
                return self.on_confirmed();
            }
        };
        if (!this.node.attrs.special) {
            return this.view.recursive_save().then(exec_action);
        } else {
            return exec_action();
        }
    }
});