odoo.define('flow_widget', function (require) {
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
            this.$el.html(QWeb.render('WorkFlow', {}));
        }
    });

    core.form_widget_registry.add('workflow', ShowPrePaymentWidget);

});