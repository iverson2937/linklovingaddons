odoo.define('linkloving.task_kanban_view', function (require) {
    "use strict";
    var core = require('web.core');
    var data = require('web.data');
    var formats = require('web.formats');
    var framework = require('web.framework');
    var session = require('web.session');
    var time = require('web.time');
    var utils = require('web.utils');
    var Widget = require('web.Widget');
    var kanban_widgets = require('web_kanban.widgets');
    var KanbanRecord = require('web_kanban.Record');

    var QWeb = core.qweb;

    var fields_registry = kanban_widgets.registry;
    var kanban_state_selection = fields_registry.get('kanban_state_selection');
    kanban_state_selection.include({
        //加一个点，表面等待审核的任务
        prepare_dropdown_selection: function () {
            var self = this;
            var _data = [];
            var stage_id = self.parent.values.stage_id.value[0];
            var stage_data = {
                id: stage_id,
                legend_normal: self.parent.values.legend_normal ? self.parent.values.legend_normal.value : undefined,
                legend_blocked: self.parent.values.legend_blocked ? self.parent.values.legend_blocked.value : undefined,
                legend_done: self.parent.values.legend_done ? self.parent.values.legend_done.value : undefined,
                legend_audit: self.parent.values.legend_audit ? self.parent.values.legend_audit.value : undefined,
                legend_orange: self.parent.values.legend_orange ? self.parent.values.legend_orange.value : undefined,
                legend_yellow: self.parent.values.legend_yellow ? self.parent.values.legend_yellow.value : undefined,
            };
            _.map(self.field.selection || [], function (res) {
                var value = {
                    'name': res[0],
                    'tooltip': res[1],
                };
                if (res[0] === 'normal') {
                    value.state_class = 'oe_kanban_status_blue';
                    value.state_name = stage_data.legend_blue ? stage_data.legend_blue : res[1];
                } else if (res[0] === 'done') {
                    value.state_class = 'oe_kanban_status_green';
                    value.state_name = stage_data.legend_done ? stage_data.legend_done : res[1];
                }else if (res[0] === 'close') {
                    value.state_class = 'oe_kanban_status_black';
                    value.state_name = stage_data.legend_close ? stage_data.legend_close : res[1];
                }else if (res[0] === 'pending') {
                    value.state_class = 'oe_kanban_status_yellow';
                    value.state_name = stage_data.legend_pending ? stage_data.legend_pending : res[1];
                } else if (res[0] === 'audit') {
                    value.state_class = 'oe_kanban_status_orange';
                    value.state_name = stage_data.legend_orange ? stage_data.legend_orange : res[1];
                } else {
                    value.state_class = 'oe_kanban_status_red';
                    value.state_name = stage_data.legend_blocked ? stage_data.legend_blocked : res[1];
                }
                _data.push(value);
            });
            return _data;
        },

    });


    var form_registry = core.form_widget_registry;
    var form_kanban_state_selection = form_registry.get('kanban_state_selection');
    form_kanban_state_selection.include({
        //加一个点，表面等待审核的任务
        prepare_dropdown_selection: function () {

            var self = this;
            var _data = [];
            var current_stage_id = self.view.datarecord.stage_id[0];
            var stage_data = {
                id: current_stage_id,
                legend_normal: self.view.datarecord.legend_normal || undefined,
                legend_blocked : self.view.datarecord.legend_blocked || undefined,
                legend_done: self.view.datarecord.legend_done || undefined,
                legend_blue: self.view.datarecord.legend_audit || undefined,
                legend_orange: self.view.datarecord.legend_orange || undefined,
                legend_yellow: self.view.datarecord.legend_yellow || undefined,
            };
            _.map(self.field.selection || [], function(selection_item) {
                var value = {
                    'name': selection_item[0],
                    'tooltip': selection_item[1],
                };
                if (selection_item[0] === 'normal') {
                    value.state_class = 'oe_kanban_status_blue';
                    value.state_name = stage_data.legend_blue ? stage_data.legend_blue : selection_item[1];
                } else if (selection_item[0] === 'done') {
                    value.state_class = 'oe_kanban_status_green';
                    value.state_name = stage_data.legend_done ? stage_data.legend_done : selection_item[1];
                }else if (selection_item[0] === 'close') {
                    value.state_class = 'oe_kanban_status_black';
                    value.state_name = stage_data.legend_close ? stage_data.legend_close : selection_item[1];
                }else if (selection_item[0] === 'pending') {
                    value.state_class = 'oe_kanban_status_yellow';
                    value.state_name = stage_data.legend_pending ? stage_data.legend_pending : selection_item[1];
                } else if (selection_item[0] === 'audit') {
                    value.state_class = 'oe_kanban_status_orange';
                    value.state_name = stage_data.legend_orange ? stage_data.legend_orange : selection_item[1];
                } else {
                    value.state_class = 'oe_kanban_status_red';
                    value.state_name = stage_data.legend_blocked ? stage_data.legend_blocked : selection_item[1];
                }
                _data.push(value);
            });

            return _data;
        },

    });

    KanbanRecord.include({
        on_card_clicked: function () {
            if (this.model === 'project.task') {
                var self = this;
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: "project.task",
                    views: [[false, 'gantt']],
                    target: '_blank',
                    domain:[['project_id', '=', self.record.project_id.raw_value[0]]],
                    context:{'group_by' : 'stage_id'}
                });
            } else {
                this._super.apply(this, arguments);
            }
        }
    });


});
