/**
 * Created by 123 on 2017/7/24.
 */
odoo.define('linkloving_project.new_gantt', function (require) {
    "use strict";

    var core = require('web.core');
    var View = require('web.View');
    var Model = require('web.DataModel');
    var formats = require('web.formats');
    var time = require('web.time');
    var data = require('web.data');
    var Dialog = require('web.Dialog');
    var QWeb = core.qweb;
    var _t = core._t;

    Date.prototype.Format = function (fmt) { //author: meizz
        var o = {
            "M+": this.getMonth() + 1,                 //月份
            "d+": this.getDate(),                    //日
            "h+": this.getHours(),                   //小时
            "m+": this.getMinutes(),                 //分
            "s+": this.getSeconds(),                 //秒
            "q+": Math.floor((this.getMonth() + 3) / 3), //季度
            "S": this.getMilliseconds()             //毫秒
        };
        if (/(y+)/.test(fmt))
            fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
        for (var k in o)
            if (new RegExp("(" + k + ")").test(fmt))
                fmt = fmt.replace(RegExp.$1, (RegExp.$1.length == 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
        return fmt;
    }

    var New_Gantt = View.extend({
        template: 'new_gantt',
        view_type: "wangke",
        init: function (parent, options) {
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
            var fields = _.compact(_.map(["date_start", "date_stop", "progress", "child_ids", "parent_ids", "stage_id", "top_task_id", "after_task_id"], function (key) {
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
            var data_tasks = [];
            var data_links = [];
            _.each(tasks, function (task, i) {
                var t;
                if (task.top_task_id && task.top_task_id[0] != task.id) {
                    t = {
                        "id": task.id,
                        "text": task.__name,
                        "start_date": new Date(task.date_start).Format("dd-MM-yyyy"),
                        "duration": (new Date(task.date_end).getTime() - new Date(task.date_start).getTime()) / (1000 * 60 * 60) / 24,
                        "parent": task.parent_ids ? task.parent_ids[0] : task.top_task_id[0],
                        "progress": task.task_progress / 100,
                        "open": false
                    };
                } else {
                    t = {
                        "id": task.id,
                        "text": task.__name + ' - ' + task.stage_id[1],
                        "start_date": new Date(task.date_start).Format("dd-MM-yyyy"),
                        "duration": (new Date(task.date_end).getTime() - new Date(task.date_start).getTime()) / (1000 * 60 * 60) / 24,
                        "progress": task.task_progress / 100,
                        "open": true
                    };
                }
                data_tasks.push(t);
                if (task.after_task_id) {
                    var l = {"id": i + 1, "source": task.id, "target": task.after_task_id[0], "type": "0"}
                    data_links.push(l);
                }
            })
            var data = {
                "data": data_tasks,
                "links": data_links
            }
            var self = this;
            $(".o_content").append(self.$el[0]);
            gantt.init(self.$el[0]);
            gantt.clearAll();
            gantt.parse(data);

            gantt.attachEvent("onBeforeLinkAdd", function (link) {
                return self.on_link_add(link);
            });

            gantt.attachEvent("onTaskChanged", function (task) {
                return self.on_task_changed(task);
            });

            gantt.attachEvent("onBeforeLinkDelete", function (link) {
                return self.on_delete_link(link);
            });

            gantt.attachEvent("onTaskAdd", function (id) {
                return self.on_task_create(id);
            });

            gantt.attachEvent("onTaskDisplay", function (id) {
                return self.on_task_display(id);
            });


        },
        on_link_add: function (link) {
            if (link.type != 0){
                this.do_notify("Tip", "关系设定必须又前置任务尾部连至后置任务头部.")
                return false;
            }
            new Model("project.task")
                .call("on_link_task", [parseInt(link.source), parseInt(link.target)])

                .then(function (result) {
                    if (result || result.length > 0) {
                        gantt._lpull[link.id] = link;
                        gantt._sync_links();
                        gantt._render_link(link.id);

                        _.each(result, function (task) {
                            var old_t = gantt.getTask(task.id)
                            old_t.start_date = new Date(task.start_date.replace(/-/g, "/"));
                            old_t.end_date = task.end_date ? new Date(task.end_date.replace(/-/g, "/")) : new Date(task.start_date.replace(/-/g, "/"));
                            gantt.updateTask(task.id, old_t);
                        });
                        gantt.refreshData();
                    }
                })
        },
        on_task_changed: function (task_obj) {
            var data = {};
            data["date_start"] = (task_obj.start_date).Format("yyyy-MM-dd");
            data["date_end"] = (task_obj.end_date).Format("yyyy-MM-dd");
            data["task_progress"] = task_obj.progress * 100;

            new Model("project.task")
                .call("on_task_change", [parseInt(task_obj.id), data])

                .then(function (result) {
                    if (result || result.length > 0) {
                        _.each(result, function (task) {
                            var old_t = gantt.getTask(task.id)
                            old_t.start_date = new Date(task.start_date.replace(/-/g, "/"));
                            old_t.end_date = task.end_date ? new Date(task.end_date.replace(/-/g, "/")) : new Date(task.start_date.replace(/-/g, "/"));
                            gantt.updateTask(task.id, old_t);
                        });
                    }
                })
        },

        on_delete_link: function (link) {
            return new Model("project.task")
                .call("on_task_relation_delete", [parseInt(link.source), parseInt(link.target)])
                .then(function (result) {
                    return result
                })
        },
        on_task_display: function (id) {
            var self = this;
            var task_id = parseInt(id);
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: self.model,
                res_id: task_id,
                views: [[false, 'form']],
                target: 'new'
            }, {
                on_close: function () {
                    new Model("project.task")
                        .call("on_refresh_task", [task_id])
                        .then(function (task_obj) {
                            if (task_obj && task_id == task_obj.id) {
                                var old_t = gantt.getTask(task_id)
                                old_t.start_date = new Date(task_obj.start_date.replace(/-/g, "/"));
                                old_t.end_date = task_obj.end_date ? new Date(task_obj.end_date.replace(/-/g, "/")) : new Date(task_obj.start_date.replace(/-/g, "/"));
                                old_t.progress = task_obj.progress / 100;
                                old_t.text = task_obj.text;
                                gantt.updateTask(task_obj.id, old_t);
                            }
                        })
                }
            });
        },
        on_task_create: function (id) {
            this.do_notify("Tip", "该功能正在实现中.")
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

    var demo_tasks = {
        "data": [
            {
                "id": 11,
                "text": "Project #1",
                "start_date": "28-03-2013",
                "duration": "11",
                "progress": 0.6,
                "open": true
            },
            {
                "id": 1,
                "text": "Project #2",
                "start_date": "01-04-2013",
                "duration": "18",
                "progress": 0.4,
                "open": true
            },

            {
                "id": 2,
                "text": "Task #1",
                "start_date": "02-04-2013",
                "duration": "8",
                "parent": "1",
                "progress": 0.5,
                "open": true
            },
            {
                "id": 3,
                "text": "Task #2",
                "start_date": "11-04-2013",
                "duration": "8",
                "parent": "1",
                "progress": 0.6,
                "open": true
            },
            {
                "id": 4,
                "text": "Task #3",
                "start_date": "13-04-2013",
                "duration": "6",
                "parent": "1",
                "progress": 0.5,
                "open": true
            },
            {
                "id": 5,
                "text": "Task #1.1",
                "start_date": "02-04-2013",
                "duration": "7",
                "parent": "2",
                "progress": 0.6,
                "open": true
            },
            {
                "id": 6,
                "text": "Task #1.2",
                "start_date": "03-04-2013",
                "duration": "7",
                "parent": "2",
                "progress": 0.6,
                "open": true
            },
            {
                "id": 7,
                "text": "Task #2.1",
                "start_date": "11-04-2013",
                "duration": "8",
                "parent": "3",
                "progress": 0.6,
                "open": true
            },
            {
                "id": 8,
                "text": "Task #3.1",
                "start_date": "14-04-2013",
                "duration": "5",
                "parent": "4",
                "progress": 0.5,
                "open": true
            },
            {
                "id": 9,
                "text": "Task #3.2",
                "start_date": "14-04-2013",
                "duration": "4",
                "parent": "4",
                "progress": 0.5,
                "open": true
            },
            {
                "id": 10,
                "text": "Task #3.3",
                "start_date": "14-04-2013",
                "duration": "3",
                "parent": "4",
                "progress": 0.5,
                "open": true
            },

            {
                "id": 12,
                "text": "Task #1",
                "start_date": "03-04-2013",
                "duration": "5",
                "parent": "11",
                "progress": 1,
                "open": true
            },
            {
                "id": 13,
                "text": "Task #2",
                "start_date": "02-04-2013",
                "duration": "7",
                "parent": "11",
                "progress": 0.5,
                "open": true
            },
            {
                "id": 14,
                "text": "Task #3",
                "start_date": "02-04-2013",
                "duration": "6",
                "parent": "11",
                "progress": 0.8,
                "open": true
            },
            {
                "id": 15,
                "text": "Task #4",
                "start_date": "02-04-2013",
                "duration": "5",
                "parent": "11",
                "progress": 0.2,
                "open": true
            },
            {
                "id": 16,
                "text": "Task #5",
                "start_date": "02-04-2013",
                "duration": "7",
                "parent": "11",
                "progress": 0,
                "open": true
            },

            {
                "id": 17,
                "text": "Task #2.1",
                "start_date": "03-04-2013",
                "duration": "2",
                "parent": "13",
                "progress": 1,
                "open": true
            },
            {
                "id": 18,
                "text": "Task #2.2",
                "start_date": "06-04-2013",
                "duration": "3",
                "parent": "13",
                "progress": 0.8,
                "open": true
            },
            {
                "id": 19,
                "text": "Task #2.3",
                "start_date": "10-04-2013",
                "duration": "4",
                "parent": "13",
                "progress": 0.2,
                "open": true
            },
            {
                "id": 20,
                "text": "Task #2.4",
                "start_date": "10-04-2013",
                "duration": "4",
                "parent": "13",
                "progress": 0,
                "open": true
            },
            {
                "id": 21,
                "text": "Task #4.1",
                "start_date": "03-04-2013",
                "duration": "4",
                "parent": "15",
                "progress": 0.5,
                "open": true
            },
            {
                "id": 22,
                "text": "Task #4.2",
                "start_date": "03-04-2013",
                "duration": "4",
                "parent": "15",
                "progress": 0.1,
                "open": true
            },
            {
                "id": 23,
                "text": "Task #4.3",
                "start_date": "03-04-2013",
                "duration": "5",
                "parent": "15",
                "progress": 0,
                "open": true
            }
        ],
        "links": [
            {"id": "1", "source": "1", "target": "2", "type": "0"},
            {"id": "2", "source": "2", "target": "3", "type": "0"},
            {"id": "3", "source": "3", "target": "4", "type": "0"},
            {"id": "4", "source": "2", "target": "5", "type": "0"},
            {"id": "5", "source": "2", "target": "6", "type": "0"},
            {"id": "6", "source": "3", "target": "7", "type": "0"},
            {"id": "7", "source": "4", "target": "8", "type": "0"},
            {"id": "8", "source": "4", "target": "9", "type": "0"},
            {"id": "9", "source": "4", "target": "10", "type": "0"},
            {"id": "10", "source": "11", "target": "12", "type": "0"},
            {"id": "11", "source": "11", "target": "13", "type": "0"},
            {"id": "12", "source": "11", "target": "14", "type": "0"},
            {"id": "13", "source": "11", "target": "15", "type": "0"},
            {"id": "14", "source": "11", "target": "16", "type": "0"},
            {"id": "15", "source": "13", "target": "17", "type": "0"},
            {"id": "16", "source": "17", "target": "18", "type": "0"},
            {"id": "17", "source": "18", "target": "19", "type": "0"},
            {"id": "18", "source": "19", "target": "20", "type": "0"},
            {"id": "19", "source": "15", "target": "21", "type": "0"},
            {"id": "20", "source": "15", "target": "22", "type": "0"},
            {"id": "21", "source": "15", "target": "23", "type": "0"}
        ]
    };

    core.view_registry.add('wangke', New_Gantt);
    return New_Gantt;
})