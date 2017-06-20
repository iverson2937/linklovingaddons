/**
 * Created by 123 on 2017/6/19.
 */
odoo.define('web.StatusLight', function (require) {
    "use strict";
    var core = require('web.core');

    var ListView = core.view_registry.get('list');
    var Column=ListView.Column;
    var list_widget_registry = core.list_widget_registry;

    var StatusLight = Column.extend({
        _format: function (row_data, options) {
            // console.log(row_data);
            return _.template(
                '<span class="fa fa-circle" style="color:<%-value%>"></span>')({
                    value: _.str.sprintf("%.0f", row_data[this.status_light] || 0) == 1 ? 'green' : _.str.sprintf("%.0f", row_data[this.id].value || 0) == 2 ? 'yellow' : 'red'
                });
        }
    })

    list_widget_registry
    .add('field.statuslight',StatusLight)


});