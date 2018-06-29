/**
 * Created by Administrator on 2017/7/3.
 */
odoo.define('linkloving_crm.list_viewsss', function (require) {
    "use strict";


    var core = require('web.core');
    var data = require('web.data');
    var data_manager = require('web.data_manager');
    var DataExport = require('web.DataExport');
    var formats = require('web.formats');
    var common = require('web.list_common');
    var Model = require('web.DataModel');
    var Pager = require('web.Pager');
    var pyeval = require('web.pyeval');
    var session = require('web.session');
    var Sidebar = require('web.Sidebar');
    var utils = require('web.utils');
    var View = require('web.View');
    var ListView = require('web.ListView');
    var Widget = require('web.Widget');
    var Priority = require('web.Priority');


    var Composer = require('mail.composer');


    var Class = core.Class;
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;
    var list_widget_registry = core.list_widget_registry;

    var ListView = core.view_registry.get('list');
    var Column = ListView.Column;


    var PriorityStar = Column.extend({
        _format: function (row_data, options) {
            var value = '';
            var result = ' ';

            console.log('dddddddddddd')
            var value = row_data['priority']['value'];
            if (value) {
                for (var i = 0; i < value; i++) {
                    result += ' <a class="o_priority_star fa fa-star" style="color:gold"></a> '
                }
            }
            return result
        }
    });


    ListView.include({
        do_delete: function (ids) {
            if (!(ids.length)) {
                return;
            }
            var self = this;

            return $.when(this.dataset.unlink(ids)).done(function () {
                _(ids).each(function (id) {
                    self.records.remove(self.records.get(id));
                });
                // Hide the table if there is no more record in the dataset
                if (self.display_nocontent_helper()) {
                    self.no_result();
                } else {
                    if (self.records.length && self.current_min === 1) {
                        // Reload the list view if we delete all the records of the first page
                        self.reload();
                    } else if (self.records.length && self.dataset.size() > 0) {
                        // Load previous page if the current one is empty
                        self.pager.previous();
                    }
                    // Reload the list view if we are not on the last page
                    if (self.current_min + self._limit - 1 < self.dataset.size()) {
                        self.reload();
                    }
                }
                self.update_pager(self.dataset);
                self.compute_aggregates();
            });
        },
    });


    Composer.BasicComposer.include({
        focus: function () {
            if (this.$input) {
                this.$input.focus();
            }
        },
    })


    list_widget_registry
        .add('field.priority_star', PriorityStar)
})




