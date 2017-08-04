odoo.define('web.TreeEditor', function (require) {
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
    var utils = require('web.utils');
    var Widget = require('web.Widget');

    var _t = core._t;

    function execute_edit_action() {
        var self = this;
        this.do_action({
            type: 'ir.actions.client',
            tag: 'import',
            params: {
                model: this.dataset.model,
                // this.dataset.get_context() could be a compound?
                // not sure. action's context should be evaluated
                // so safer bet. Odd that timezone & al in it
                // though
                context: this.getParent().action.context,
            }
        }, {
            on_reverse_breadcrumb: function () {
                return self.reload();
            },
        });
        return false;
    }


    ListView.List.include(/** @lends instance.web.ListView.List# */{

        render_buttons: function () {
            alert('ddddsdads')
            var self = this;
            var add_button = false;
            if (!this.$buttons) { // Ensures that this is only done once
                add_button = true;
            }
            this._super.apply(this, arguments); // Sets this.$buttons
            if (add_button) {
                this.$buttons.on('click', '.o_list_button_edit', execute_import_action.bind(this));
            }
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
        }
    });
});