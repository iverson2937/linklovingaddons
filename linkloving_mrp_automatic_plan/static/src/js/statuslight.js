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
            console.log(row_data['status_light']["value"]);
            //
            var value = row_data['status_light']["value"];
            var color = 'red'
            if (value == 1) {
                color = 'green'
            }
            else if (value == 2) {
                color = 'yellow'
            }
            else if (value == 3) {
                color = 'red'
            } else {
                color = 'transparent'
            }
            console.log(color);
            return _.template(
                '<span class="fa fa-circle"  style="color:<%-value%>"></span>')({
                value: color
                });
        }
    })

    list_widget_registry
    .add('field.statuslight',StatusLight)


});