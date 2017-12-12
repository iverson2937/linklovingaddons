odoo.define('web.OLListEditor', function (require) {
    "use strict";
    /*---------------------------------------------------------
     * Odoo Editable List view linkloving version
     *---------------------------------------------------------*/
    /**
     * handles editability case for lists, because it depends on form and forms already depends on lists it had to be split out
     * @namespace
     */

    var core = require('web.core');
    var data = require('web.data');
    var FormView = require('web.FormView');
    var common = require('web.list_common');
    var ListView = require('web.ListView');
    var Model = require('web.Model');
    var utils = require('web.utils');
    var Widget = require('web.Widget');

    var _t = core._t;

    ListView.List.include(/** @lends instance.web.ListView.List# */{
        row_clicked: function (event) {
            if (!this.view.editable() || !this.view.is_action_enabled('edit')) {
                return this._super.apply(this, arguments);
            }

            var self = this;
            var args = arguments;
            var _super = self._super;

            var record_id = $(event.currentTarget).data('id');
            return this.view.start_edition(
                ((record_id) ? this.records.get(record_id) : null), {
                    focus_field: $(event.target).not(".o_readonly").data('field'),
                })
        },
        /**
         * If a row mapping to the record (@data-id matching the record's id or
         * no @data-id if the record has no id), returns it. Otherwise returns
         * ``null``.
         *
         * @param {Record} record the record to get a row for
         * @return {jQuery|null}
         */
        get_row_for: function (record) {
            var $row = this.$current.children('[data-id=' + record.get('id') + ']');
            return (($row.length) ? $row : null);
        },
    });
});
