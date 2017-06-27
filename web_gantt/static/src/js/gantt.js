odoo.define('web_gantt.GanttView', function (require) {
    "use strict";

    var core = require('web.core');
    var View = require('web.View');
    var Model = require('web.DataModel');
    var formats = require('web.formats');
    var time = require('web.time');
    var data = require('web.data')

    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;

    /*---------------------------------------------------------
     * OpenERP web_gantt
     *---------------------------------------------------------*/

    var GanttView = View.extend({
        display_name: _lt('Gantt'),
        template: "GanttView",
        view_type: "gantt",
        init: function () {
            var self = this;
            this._super.apply(this, arguments);
            this.has_been_loaded = $.Deferred();
            this.chart_id = _.uniqueId();
        },
        start: function () {
            return this.load_view();
        },
        load_view: function (context) {
            var self = this;
            var view_loaded_def;
            if (this.embedded_view) {
                view_loaded_def = $.Deferred();
                $.async_when().done(function () {
                    view_loaded_def.resolve(self.embedded_view);
                });
            } else {
                if (!this.view_type)
                    console.warn("view_type is not defined", this);
                view_loaded_def = fields_view_get({
                    "model": this.dataset._model,
                    "view_id": this.view_id,
                    "view_type": this.view_type,
                    "toolbar": !!this.options.$sidebar,
                    "context": this.dataset.get_context(),
                });
            }
            return this.alive(view_loaded_def).then(function (r) {
                self.fields_view = r;
                // add css classes that reflect the (absence of) access rights
                // self.$el.addClass('oe_view')
                //     .toggleClass('oe_cannot_create', !self.is_action_enabled('create'))
                //     .toggleClass('oe_cannot_edit', !self.is_action_enabled('edit'))
                //     .toggleClass('oe_cannot_delete', !self.is_action_enabled('delete'));
                return $.when(self.view_loading(r)).then(function () {
                    self.trigger('view_loaded', r);
                });
            });
        },
        view_loading: function (r) {
            return this.load_gantt(r);
        },
        load_gantt: function (fields_view_get, fields_get) {
            var self = this;
            this.fields_view = fields_view_get;
            this.$el.addClass(this.fields_view.arch.attrs['class']);
            return self.alive(new Model(this.dataset.model)
                .call('fields_get')).then(function (fields) {
                self.fields = fields;
                self.has_been_loaded.resolve();
            });
        },
        do_search: function (domains, contexts, group_bys) {
            var self = this;
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
            var fields = _.compact(_.map(["date_start", "date_delay", "date_stop", "progress"], function (key) {
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
        reload: function () {
            if (this.last_domains !== undefined)
                return this.do_search(this.last_domains, this.last_contexts, this.last_group_bys);
        },
        on_data_loaded: function (tasks, group_bys) {
            var self = this;
            var ids = _.pluck(tasks, "id");
            return this.dataset.name_get(ids).then(function (names) {
                var ntasks = _.map(tasks, function (task) {
                    return _.extend({
                        __name: _.detect(names, function (name) {
                            return name[0] == task.id;
                        })[1]
                    }, task);
                });
                return self.on_data_loaded_2(ntasks, group_bys);
            });
        },
        on_data_loaded_2: function (tasks, group_bys) {
            var self = this;
            //prevent more that 1 group by
            if (group_bys.length > 0) {
                group_bys = [group_bys[0]];
            }
            // if there is no group by, simulate it
            if (group_bys.length == 0) {
                group_bys = ["_pseudo_group_by"];
                _.each(tasks, function (el) {
                    el._pseudo_group_by = "Gantt View";
                });
                this.fields._pseudo_group_by = {type: "string"};
            }
            // get the groups
            var split_groups = function (tasks, group_bys) {
                if (group_bys.length === 0)
                    return tasks;
                var groups = [];
                _.each(tasks, function (task) {
                    var group_name = task[_.first(group_bys)];
                    var group = _.find(groups, function (group) {
                        return _.isEqual(group.name, group_name);
                    });
                    if (group === undefined) {
                        group = {name: group_name, tasks: [], __is_group: true};
                        groups.push(group);
                    }
                    group.tasks.push(task);
                });
                _.each(groups, function (group) {
                    group.tasks = split_groups(group.tasks, _.rest(group_bys));
                });
                return groups;
            }
            var groups = split_groups(tasks, group_bys);

            // track ids of task items for context menu
            var task_ids = {};
            // creation of the chart
            var generate_task_info = function (task, plevel) {
                if (_.isNumber(task[self.fields_view.arch.attrs.progress])) {
                    var percent = task[self.fields_view.arch.attrs.progress] || 0;
                } else {
                    var percent = 100;
                }
                var level = plevel || 0;
                if (task.__is_group) {
                    var task_infos = _.compact(_.map(task.tasks, function (sub_task) {
                        return generate_task_info(sub_task, level + 1);
                    }));
                    if (task_infos.length == 0)
                        return;
                    var task_start = _.reduce(_.pluck(task_infos, "task_start"), function (date, memo) {
                        return memo === undefined || date < memo ? date : memo;
                    }, undefined);
                    var task_stop = _.reduce(_.pluck(task_infos, "task_stop"), function (date, memo) {
                        return memo === undefined || date > memo ? date : memo;
                    }, undefined);
                    var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                    var group_name = task.name ? formats.format_value(task.name, self.fields[group_bys[level]]) : "-";
                    if (level == 0) {
                        var group = new GanttProjectInfo(_.uniqueId("gantt_project_"), group_name, task_start);
                        _.each(task_infos, function (el) {
                            group.addTask(el.task_info);
                        });
                        return group;
                    } else {
                        var group = new GanttTaskInfo(_.uniqueId("gantt_project_task_"), group_name, task_start, duration || 1, percent);
                        _.each(task_infos, function (el) {
                            group.addChildTask(el.task_info);
                        });
                        return {task_info: group, task_start: task_start, task_stop: task_stop};
                    }
                } else {
                    var task_name = task.__name;
                    var duration_in_business_hours = false;
                    var task_start = time.auto_str_to_date(task[self.fields_view.arch.attrs.date_start]);
                    if (!task_start)
                        return;
                    var task_stop;
                    if (self.fields_view.arch.attrs.date_stop) {
                        task_stop = time.auto_str_to_date(task[self.fields_view.arch.attrs.date_stop]);
                        if (!task_stop)
                            task_stop = task_start;
                    } else { // we assume date_duration is defined
                        var tmp = formats.format_value(task[self.fields_view.arch.attrs.date_delay],
                            self.fields[self.fields_view.arch.attrs.date_delay]);
                        if (!tmp)
                            return;
                        task_stop = task_start.clone().addMilliseconds(formats.parse_value(tmp, {type: "float"}) * 60 * 60 * 1000);
                        duration_in_business_hours = true;
                    }
                    var duration = (task_stop.getTime() - task_start.getTime()) / (1000 * 60 * 60);
                    var id = _.uniqueId("gantt_task_");
                    if (!duration_in_business_hours) {
                        duration = (duration / 24) * 8;
                    }
                    var task_info = new GanttTaskInfo(id, task_name, task_start, (duration) || 1, percent);
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
        on_task_changed: function (task_obj) {
            alert("on_task_changed");
            var self = this;
            var itask = task_obj.TaskInfo.internal_task;
            var start = task_obj.getEST();
            var duration = task_obj.getDuration();
            var duration_in_business_hours = !!self.fields_view.arch.attrs.date_delay;
            if (!duration_in_business_hours) {
                duration = (duration / 8 ) * 24;
            }
            var end = start.clone().addMilliseconds(duration * 60 * 60 * 1000);
            var data = {};
            data[self.fields_view.arch.attrs.date_start] =
                time.auto_date_to_str(start, self.fields[self.fields_view.arch.attrs.date_start].type);
            if (self.fields_view.arch.attrs.date_stop) {
                data[self.fields_view.arch.attrs.date_stop] =
                    time.auto_date_to_str(end, self.fields[self.fields_view.arch.attrs.date_stop].type);
            } else { // we assume date_duration is defined
                data[self.fields_view.arch.attrs.date_delay] = duration;
            }
            this.dataset.write(itask.id, data);
        },
        on_task_display: function (task) {
            alert("on_task_display");
            var self = this;
            var pop = new data.FormOpenPopup(self);
            pop.on('write_completed', self, self.reload);
            pop.show_element(
                self.dataset.model,
                task.id,
                null,
                {}
            );
        },
        on_task_create: function () {
            alert("on_task_create");
            var self = this;
            var pop = new data.SelectCreatePopup(this);
            pop.on("elements_selected", self, function () {
                self.reload();
            });
            pop.select_element(
                self.dataset.model,
                {
                    initial_view: "form",
                }
            );
        },
    });


    var fields_view_get = function (args) {
        function postprocess(fvg) {
            var doc = $.parseXML(fvg.arch).documentElement;
            fvg.arch = xml_to_json(doc, (doc.nodeName.toLowerCase() !== 'kanban'));
            if ('id' in fvg.fields) {
                // Special case for id's
                var id_field = fvg.fields['id'];
                id_field.original_type = id_field.type;
                id_field.type = 'id';
            }
            _.each(fvg.fields, function (field) {
                _.each(field.views || {}, function (view) {
                    postprocess(view);
                });
            });
            return fvg;
        }

        args = _.defaults(args, {
            toolbar: false,
        });
        var model = args.model;
        if (typeof model === 'string') {
            model = new Model(args.model, args.context);
        }
        return args.model.call('fields_view_get', {
            view_id: args.view_id,
            view_type: args.view_type,
            context: args.context,
            toolbar: args.toolbar
        }).then(function (fvg) {
            return postprocess(fvg);
        });
    };

    var xml_to_json = function (node, strip_whitespace) {
        switch (node.nodeType) {
            case 9:
                return xml_to_json(node.documentElement, strip_whitespace);
            case 3:
            case 4:
                return (strip_whitespace && node.data.trim() === '') ? undefined : node.data;
            case 1:
                var attrs = $(node).getAttributes();
                _.each(['domain', 'filter_domain', 'context', 'default_get'], function (key) {
                    if (attrs[key]) {
                        try {
                            attrs[key] = JSON.parse(attrs[key]);
                        } catch (e) {
                        }
                    }
                });
                return {
                    tag: node.tagName.toLowerCase(),
                    attrs: attrs,
                    children: _.compact(_.map(node.childNodes, function (node) {
                        return xml_to_json(node, strip_whitespace);
                    })),
                };
        }
    };


    core.view_registry.add('gantt', GanttView);
    return GanttView;
});
