odoo.define('linkloving_core.multi_selection', function (require) {
    "use strict";


    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var ListView = require('web.ListView');
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

    var X2ManyList = ListView.List.include({

        pad_table_to: function (count) {
            if (!this.view.is_action_enabled('create') || this.view.x2m.get('effective_readonly')) {
                this._super(count);
                return;
            }
            console.log('fffffffffffffff');
            this._super(count > 0 ? count - 1 : 0);

            var self = this;
            var columns = _(this.columns).filter(function (column) {
                return column.invisible !== '1';
            }).length;
            if (this.options.selectable) {
                columns++;
            }
            if (this.options.deletable) {
                columns++;
            }

            var class_name = 'o_form_field_x2many_list_row_add';
            var label = '';
            console.log(this.options);
            if (this.options.multi_selectable) {
                class_name = 'ol_form_field_x2many_list_row_add'
            }
            if (this.options.add_label) {
                class_name = 'ol_form_field_x2many_list_row_add'
            }

            var $cell = $('<td>', {
                colspan: columns,
                'class': class_name
            }).append(
                $('<a>', {href: '#'}).text(_t("Add an item"))
                    .click(function (e) {
                        e.preventDefault();
                        e.stopPropagation();
                        var def;
                        if (self.view.editable()) {
                            // FIXME: there should also be an API for that one
                            if (self.view.editor.form.__blur_timeout) {
                                clearTimeout(self.view.editor.form.__blur_timeout);
                                self.view.editor.form.__blur_timeout = false;
                            }
                            def = self.view.save_edition();
                        }
                        $.when(def).done(self.view.do_add_record.bind(self));
                    }));

            var $padding = this.$current.find('tr:not([data-id]):first');
            var $newrow = $('<tr>').append($cell);
            if ($padding.length) {
                $padding.before($newrow);
            } else {
                this.$current.append($newrow);
            }
        },
    });

    console.log(X2ManyList);

    // var substr_time = form_widget_registry.get('date').include({
    //     render_value: function () {
    //         if (this.get("effective_readonly")) {
    //             //add code 2017/5/9 only show year,month,day
    //             this.$el.text(formats.format_value(this.get('value'), this, '').substring(0, 11));
    //         } else {
    //             this.datewidget.set_value(this.get('value'));
    //         }
    //         // console.log("opopopop")
    //     }
    // });
    //
    // core.action_registry.add('form_widget_extend', substr_time);
    //
    // return substr_time
});