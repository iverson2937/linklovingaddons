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
    var Gantt = require('web_gantt.GanttView');

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
                } else if (res[0] === 'close') {
                    value.state_class = 'oe_kanban_status_black';
                    value.state_name = stage_data.legend_close ? stage_data.legend_close : res[1];
                } else if (res[0] === 'pending') {
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
                legend_blocked: self.view.datarecord.legend_blocked || undefined,
                legend_done: self.view.datarecord.legend_done || undefined,
                legend_blue: self.view.datarecord.legend_audit || undefined,
                legend_orange: self.view.datarecord.legend_orange || undefined,
                legend_yellow: self.view.datarecord.legend_yellow || undefined,
            };
            _.map(self.field.selection || [], function (selection_item) {
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
                } else if (selection_item[0] === 'close') {
                    value.state_class = 'oe_kanban_status_black';
                    value.state_name = stage_data.legend_close ? stage_data.legend_close : selection_item[1];
                } else if (selection_item[0] === 'pending') {
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
            var self = this;
            if (this.model === 'project.task') {
                this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: "project.task",
                    views: [[false, 'gantt']],
                    target: '_blank',
                    domain: [['project_id', '=', self.record.project_id.raw_value[0]], ['top_task_id', '=', self.record.id.raw_value]],
                    context: {'group_by': 'top_task_id', 'order_by': 'stage_id'}
                });
            } else {
                this._super.apply(this, arguments);
            }
        }
    });

    Gantt.include({
        do_search: function (domains, contexts, group_bys) {
            var self = this;
            if (domains) {
                _.each(domains, function (domain, i) {
                    if (domain && domain[0] == "parent_ids") {
                        domains.splice(i, 1);
                    }
                });
            }
            self.last_domains = domains;
            self.last_contexts = contexts;
            self.last_group_bys = group_bys;
            // select the group by
            var n_group_bys = [];
            if (this.fields_view.arch.attrs.default_group_by) {
                n_group_bys = this.fields_view.arch.attrs.default_group_by.split(',');
            }
            if (group_bys.length) {
                n_group_bys = group_bys;
            }
            // gather the fields to get
            var fields = _.compact(_.map(["date_start", "date_stop", "progress", "child_ids", "parent_ids", "stage_id", "top_task_id"], function (key) {
                return self.fields_view.arch.attrs[key] || '';
            }));
            fields = _.uniq(fields.concat(n_group_bys));

            return $.when(this.has_been_loaded).then(function () {
                return self.dataset.read_slice(fields, {
                    domain: domains,
                    context: contexts
                }).then(function (data) {
                    return self.on_data_loaded(data, n_group_bys);
                });
            });
        },

        on_data_loaded_2: function (tasks, group_bys) {
            var self = this;
            //prevent more that 1 group by
            // if (group_bys.length > 0) {
            //     group_bys = [group_bys[0]];
            // }
            // // if there is no group by, simulate it
            // if (group_bys.length == 0) {
            //     group_bys = ["_pseudo_group_by"];
            //     _.each(tasks, function (el) {
            //         el._pseudo_group_by = "Gantt View";
            //     });
            //     this.fields._pseudo_group_by = {type: "string"};
            // }
            group_bys = ["top_task_id"];

            var child_tasks = [];
            var top_tasks = [];
            if (self.model == 'project.task') {
                _.each(tasks, function (task) {
                    if (task.top_task_id != task.id) {
                        child_tasks.push(task);
                    } else
                        top_tasks.push(task);
                });
            } else {
                child_tasks = tasks;
            }
            var split_groups = function (tasks, group_bys) {
                var groups = [];
                _.each(tasks, function (task) {
                    var group_name;
                    _.each(top_tasks, function (t) {
                        if (t.id == task[_.first(group_bys)])
                            group_name = t.__name;
                    });
                    var group = _.find(groups, function (group) {
                        return _.isEqual(group.name, group_name);
                    });
                    if (group) {
                        var c_group_name = task.stage_id[1];
                        var c_group = _.find(group.tasks, function (group) {
                            return _.isEqual(group.name, c_group_name);
                        });
                        if (c_group === undefined) {
                            c_group = {name: c_group_name, tasks: [], __is_group: true};
                            group.tasks.push(c_group);
                            group.tasks.sort(by("name"));
                        }
                        if (group.__self.stage_id[1] === c_group_name)
                            c_group.current = true;
                        else
                            c_group.current = false;
                        c_group.tasks.push(task);
                    } else {
                        var __self = _.find(top_tasks, function (top) {
                            return _.isEqual(top.__name, group_name);
                        })
                        var task_group = {name: task.stage_id[1], tasks: [task], __is_group: true, current: __self.stage_id[1] == task.stage_id[1]};
                        group = {name: group_name, tasks: [task_group], __is_group: true, __self: __self};
                        groups.push(group);
                    }
                });
                // _.each(groups, function (group) {
                //     group.tasks = split_groups(group.tasks, _.rest(group_bys));
                // });
                groups.sort(by("name"));
                return groups;
            }
            var groups = split_groups(child_tasks, group_bys);

            // track ids of task items for context menu
            var task_ids = {};

            var generated_ids = [];
            // creation of the chart
            var generate_task_info = function (task, plevel) {
                if (task.id && contains(generated_ids, task.id))
                    return;
                generated_ids.push(task.id);

                if (_.isNumber(task[self.fields_view.arch.attrs.progress])) {
                    var percent = task[self.fields_view.arch.attrs.progress] || 0;
                } else {
                    var percent = 100;
                }
                var level = plevel || 0;
                if (task.__is_group) {
                    var task_infos = _.compact(_.map(task.tasks, function (sub_task) {
                        sub_task.siblingTasks = task.tasks;
                        return generate_task_info(sub_task, level + 1);
                    }));
                    if (task_infos.length == 0)
                        return;
                    var task_start, task_stop, duration;
                    task_start = _.reduce(_.pluck(task_infos, "task_start"), function (date, memo) {
                        return memo === undefined || date < memo ? date : memo;
                    }, undefined);
                    task_stop = _.reduce(_.pluck(task_infos, "task_stop"), function (date, memo) {
                        return memo === undefined || date > memo ? date : memo;
                    }, undefined);
                    duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                    duration = (duration / 24) * 8;
                    var group_name = task.name;// ? formats.format_value(task.name, self.fields[group_bys[level]]) : "-";
                    if (level == 0) {
                        var group = new GanttProjectInfo(_.uniqueId("gantt_project_"), group_name, task_start);
                        _.each(task_infos, function (el) {
                            group.addTask(el.task_info);
                        });
                        group.internal_task = task;
                        return group;
                    } else {
                        var id = _.uniqueId("gantt_project_task_");
                        var group = new GanttTaskInfo(id, group_name, task_start, duration || 1, percent, undefined, task_stop, task.current);
                        _.each(task_infos, function (el) {
                            group.addChildTask(el.task_info);
                        });
                        group.internal_task = task;
                        task_ids[id] = group;
                        return {task_info: group, task_start: task_start, task_stop: task_stop};
                    }
                } else if (task.child_ids && task.child_ids.length != 0) {
                    var tasks = [];
                    _.each(task.siblingTasks, function (sub_task) {
                        if (contains(task.child_ids, sub_task.id)) {
                            tasks.push(sub_task);
                        }
                    });
                    var task_infos = _.compact(_.map(tasks, function (sub_task) {
                        sub_task.siblingTasks = task.siblingTasks;
                        return generate_task_info(sub_task, level + 1);
                    }));

                    var task_start = time.auto_str_to_date(task[self.fields_view.arch.attrs.date_start]);
                    if (!task_start)
                        return;
                    var task_stop = time.auto_str_to_date(task[self.fields_view.arch.attrs.date_stop]);
                    if (!task_stop)
                        task_stop = task_start;
                    var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                    var group_name = task.__name;
                    var id = _.uniqueId("gantt_project_task_");
                    duration = (duration / 24) * 8;
                    var group = new GanttTaskInfo(id, group_name, task_start, duration || 1, percent, undefined, task_stop);
                    _.each(task_infos, function (e) {
                        group.addChildTask(e.task_info);
                    });
                    group.internal_task = task;
                    task_ids[id] = group;
                    return {task_info: group, task_start: task_start, task_stop: task_stop};
                } else {
                    var task_name = task.__name;
                    var task_start = time.auto_str_to_date(task[self.fields_view.arch.attrs.date_start]);
                    if (!task_start)
                        return;
                    var task_stop = time.auto_str_to_date(task[self.fields_view.arch.attrs.date_stop]);
                    if (!task_stop)
                        task_stop = task_start;
                    var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                    var id = _.uniqueId("gantt_task_");
                    duration = (duration / 24) * 8;
                    var task_info = new GanttTaskInfo(id, task_name, task_start, (duration) || 1, percent, undefined, task_stop);
                    task_info.internal_task = task;
                    task_ids[id] = task_info;
                    return {task_info: task_info, task_start: task_start, task_stop: task_stop};
                }
            }

            var gantt = new GanttChart();
            _.each(_.compact(_.map(groups, function (e) {
                return generate_task_info(e, 0);
            })), function (project) {
                gantt.addProject(project);
            });

            gantt.setEditable(false);
            gantt.setImagePath("/web_gantt/static/lib/dhtmlxGantt/codebase/imgs/");
            gantt.attachEvent("onTaskEndDrag", function (task) {
                self.on_task_changed(task);
            });
            gantt.attachEvent("onTaskEndResize", function (task) {
                self.on_task_changed(task);
            });

            gantt.create($(this.$el).get(0));
            // gantt.create(2);

            // bind event to display task when we click the item in the tree
            $(".taskNameItem", self.$el).click(function (event) {
                var task_info = task_ids[event.target.id];
                if (task_info) {
                    self.on_task_display(task_info.internal_task);
                }
            });


            if (this.is_action_enabled('create')) {
                // insertion of create button
                var td = $($("td", self.$el)[0]);
                var rendered = QWeb.render("GanttView-create-button");
                $(rendered).prependTo(td);
                $(".oe_gantt_button_create", this.$el).click(this.on_task_create);
            }
            // Fix for IE to display the content of gantt view.
            this.$el.find(".oe_gantt td:first > div, .oe_gantt td:eq(1) > div > div").css("overflow", "");
        },
    });

    var by = function (name, minor) {
        return function (o, p) {
            var a, b;
            if (o && p && typeof o === 'object' && typeof p === 'object') {
                a = o[name];
                b = p[name];
                if (a === b) {
                    return typeof minor === 'function' ? minor(o, p) : 0;
                }
                if (typeof a === typeof b) {
                    return a < b ? -1 : 1;
                }
                return typeof a < typeof b ? -1 : 1;
            } else {
                thro("error");
            }
        }
    }

    function contains(arr, obj) {
        var index = arr.length;
        while (index--) {
            if (arr[index] === obj) {
                return true;
            }
        }
        return false;
    }
});
