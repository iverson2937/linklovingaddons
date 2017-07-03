odoo.define('linkloving_core.employee_kanban_view_handler', function (require) {
    "use strict";

    var KanbanRecord = require('web_kanban.Record');

    KanbanRecord.include({
        on_card_clicked: function () {
            if (this.model === 'product.template') {
                // needed to diffentiate : check in/out kanban view of employees <-> standard employee kanban view
                var action = {
                    type: 'ir.actions.client',
                    tag: 'product_detail',
                    // tag: 'hr_attendance_kiosk_confirm',
                    product_id: this.record.id.raw_value,
                    // employee_name: this.record.name.raw_value,
                    // employee_state: this.record.attendance_state.raw_value,
                };
                this.do_action(action);
            } else {
                this._super.apply(this, arguments);
            }
        }
    });

});