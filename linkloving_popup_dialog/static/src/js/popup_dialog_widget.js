/***
 * 使用方法:<field name="incoming_qty" string="在产" info_field="mos_info" widget="popup_dialog_widget"/>
 * info_field: 所要关联的字段
 * widget:popup_dialog_widget

 ***/
odoo.define('linkloving_popup_dialog.popup_dialog_widget', function (require) {
    "use strict";
    var core = require('web.core');
    var session = require('web.session');
    var ListView = require('web.ListView');
    var list_widget_registry = core.list_widget_registry;
    var Column = list_widget_registry.get('field');
    var translation = require('web.translation');
    var time = require('web.time');
    var utils = require('web.utils');
    var _t = translation._t;
    var formats = require('web.formats');

    function format_value(value, descriptor, value_if_empty) {
        var l10n = _t.database.parameters;
        var date_format = time.strftime_to_moment_format(l10n.date_format);
        var time_format = time.strftime_to_moment_format(l10n.time_format);
        // If NaN value, display as with a `false` (empty cell)
        if (typeof value === 'number' && isNaN(value)) {
            value = false;
        }
        //noinspection FallthroughInSwitchStatementJS
        switch (value) {
            case '':
                if (descriptor.type === 'char' || descriptor.type === 'text') {
                    return '';
                }
                console.warn('Field', descriptor, 'had an empty string as value, treating as false...');
                return value_if_empty === undefined ? '' : value_if_empty;
            case false:
            case undefined:
            case Infinity:
            case -Infinity:
                return value_if_empty === undefined ? '' : value_if_empty;
        }
        switch ((descriptor.widget && descriptor.widget != 'popup_dialog_widget') || descriptor.type || (descriptor.field && descriptor.field.type)) {
            case 'id':
                return value.toString();
            case 'integer':
                return utils.insert_thousand_seps(
                    _.str.sprintf('%d', value));
            case 'monetary':
            case 'float':
                var digits = descriptor.digits ? descriptor.digits : [69, 2];
                digits = typeof digits === "string" ? py.eval(digits) : digits;
                var precision = digits[1];
                var formatted = _.str.sprintf('%.' + precision + 'f', value).split('.');
                formatted[0] = utils.insert_thousand_seps(formatted[0]);
                return formatted.join(l10n.decimal_point);
            case 'float_time':
                var pattern = '%02d:%02d';
                if (value < 0) {
                    value = Math.abs(value);
                    pattern = '-' + pattern;
                }
                var hour = Math.floor(value);
                var min = Math.round((value % 1) * 60);
                if (min == 60) {
                    min = 0;
                    hour = hour + 1;
                }
                return _.str.sprintf(pattern, hour, min);
            case 'many2one':
                // name_get value format
                return value[1] ? value[1].split("\n")[0] : value[1];
            case 'one2many':
            case 'many2many':
                if (typeof value === 'string') {
                    return value;
                }
                return _.str.sprintf(_t("(%d records)"), value.length);
            case 'datetime':
                if (typeof(value) == "string")
                    value = moment(time.auto_str_to_date(value));
                else {
                    value = moment(value);
                }
                return value.format(date_format + ' ' + time_format);
            case 'date':
                if (typeof(value) == "string")
                    value = moment(time.auto_str_to_date(value));
                else {
                    value = moment(value);
                }
                return value.format(date_format);
            case 'time':
                if (typeof(value) == "string")
                    value = moment(time.auto_str_to_date(value));
                else {
                    value = moment(value);
                }
                return value.format(time_format);
            case 'selection':
            case 'statusbar':
                // Each choice is [value, label]
                if (_.isArray(value)) {
                    return value[1];
                }
                var result = _(descriptor.selection).detect(function (choice) {
                    return choice[0] === value;
                });
                if (result) {
                    return result[1];
                }
                return;
            default:
                return value;
        }
    }

    var ColumnPopup = Column.extend({
        init: function () {
            this._super.apply(this, arguments);
            // Handle overrides the field to not be form-editable.
            this.modifiers.readonly = true;
            //this.string = ""; // Don't display the column header
            console.log("----------------------");
        },
        //heading: function () {
        //    return '<span class="o_row_handle fa fa-eye"></span>';
        //},
        width: function () {
            return 1;
        },
        /**
         * Return styling hooks for a drag handle
         *
         * @private
         */
        _format: function (row_data, options) {
            var info = row_data[this.info_field].value;
            var value = _.escape(format_value(
                row_data[this.id].value, this, options.value_if_empty));
            var html = '<span class="popup_dialog" data-html="true" data-toggle="tooltip" title="' + info + '">' + value + '</span>'
            return html;
        }
    });
    list_widget_registry.add('field.popup_dialog_widget', ColumnPopup);

});