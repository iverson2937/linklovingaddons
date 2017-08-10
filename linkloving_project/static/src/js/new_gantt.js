/**
 * Created by 123 on 2017/7/24.
 */
odoo.define('linkloving_project.new_gantt', function (require){
    "use strict";

    var core = require('web.core');
    var View = require('web.View');
    var Model = require('web.DataModel');
    var formats = require('web.formats');
    var time = require('web.time');
    var data = require('web.data');
    var QWeb = core.qweb;

    var New_Gantt = View.extend({
        template:'new_gantt',
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
            var fields = _.compact(_.map(["date_start", "date_stop", "progress"], function (key) {
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


             // var self = this;
            // $(".o_content").append("<div class='o_view_manager_content'></div>")
            // gantt.init("gantt_here_");
            // var para=document.createElement("div");
            // para.className="o_view_manager_content";
            // var div1 = $("<div class='o_view_manager_content'></div>");
            // $(div1).append($(".gantt_container"));
            // $(".o_content").append($(div1));
            // console.log($(".o_view_manager_content"));
            // gantt.create(2);

            var self = this;
            $(".o_content").append(self.$el[0]);
            console.log(self.$el);
            gantt.init(self.$el[0]);
            gantt.parse(demo_tasks)
            // gantt.create(2);

            // bind event to display task when we click the item in the tree
            // $(".taskNameItem", self.$el).click(function (event) {
            //     var task_info = task_ids[event.target.id];
            //     if (task_info) {
            //         self.on_task_display(task_info.internal_task);
            //     }
            // });

            // if (this.is_action_enabled('create')) {
            //     // insertion of create button
            //     var td = $($("td", self.$el)[0]);
            //     var rendered = QWeb.render("GanttView-create-button");
            //     $(rendered).prependTo(td);
            //     $(".oe_gantt_button_create", this.$el).click(this.on_task_create);
            // }
            // // Fix for IE to display the content of gantt view.
            // this.$el.find(".oe_gantt td:first > div, .oe_gantt td:eq(1) > div > div").css("overflow", "");
        },
        on_task_changed: function (task_obj) {
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
            var self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: self.model,
                res_id: task.id,
                views: [[false, 'form']],
                target: 'new'
            }, {
                on_close: function () {
                    self.reload();
                }
            });
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

    var demo_tasks = {
	"data":[
		{"id":11, "text":"Project #1", "start_date":"28-03-2013", "duration":"11", "progress": 0.6, "open": true},
		{"id":1, "text":"Project #2", "start_date":"01-04-2013", "duration":"18", "progress": 0.4, "open": true},

		{"id":2, "text":"Task #1", "start_date":"02-04-2013", "duration":"8", "parent":"1", "progress":0.5, "open": true},
		{"id":3, "text":"Task #2", "start_date":"11-04-2013", "duration":"8", "parent":"1", "progress": 0.6, "open": true},
		{"id":4, "text":"Task #3", "start_date":"13-04-2013", "duration":"6", "parent":"1", "progress": 0.5, "open": true},
		{"id":5, "text":"Task #1.1", "start_date":"02-04-2013", "duration":"7", "parent":"2", "progress": 0.6, "open": true},
		{"id":6, "text":"Task #1.2", "start_date":"03-04-2013", "duration":"7", "parent":"2", "progress": 0.6, "open": true},
		{"id":7, "text":"Task #2.1", "start_date":"11-04-2013", "duration":"8", "parent":"3", "progress": 0.6, "open": true},
		{"id":8, "text":"Task #3.1", "start_date":"14-04-2013", "duration":"5", "parent":"4", "progress": 0.5, "open": true},
		{"id":9, "text":"Task #3.2", "start_date":"14-04-2013", "duration":"4", "parent":"4", "progress": 0.5, "open": true},
		{"id":10, "text":"Task #3.3", "start_date":"14-04-2013", "duration":"3", "parent":"4", "progress": 0.5, "open": true},

		{"id":12, "text":"Task #1", "start_date":"03-04-2013", "duration":"5", "parent":"11", "progress": 1, "open": true},
		{"id":13, "text":"Task #2", "start_date":"02-04-2013", "duration":"7", "parent":"11", "progress": 0.5, "open": true},
		{"id":14, "text":"Task #3", "start_date":"02-04-2013", "duration":"6", "parent":"11", "progress": 0.8, "open": true},
		{"id":15, "text":"Task #4", "start_date":"02-04-2013", "duration":"5", "parent":"11", "progress": 0.2, "open": true},
		{"id":16, "text":"Task #5", "start_date":"02-04-2013", "duration":"7", "parent":"11", "progress": 0, "open": true},

		{"id":17, "text":"Task #2.1", "start_date":"03-04-2013", "duration":"2", "parent":"13", "progress": 1, "open": true},
		{"id":18, "text":"Task #2.2", "start_date":"06-04-2013", "duration":"3", "parent":"13", "progress": 0.8, "open": true},
		{"id":19, "text":"Task #2.3", "start_date":"10-04-2013", "duration":"4", "parent":"13", "progress": 0.2, "open": true},
		{"id":20, "text":"Task #2.4", "start_date":"10-04-2013", "duration":"4", "parent":"13", "progress": 0, "open": true},
		{"id":21, "text":"Task #4.1", "start_date":"03-04-2013", "duration":"4", "parent":"15", "progress": 0.5, "open": true},
		{"id":22, "text":"Task #4.2", "start_date":"03-04-2013", "duration":"4", "parent":"15", "progress": 0.1, "open": true},
		{"id":23, "text":"Task #4.3", "start_date":"03-04-2013", "duration":"5", "parent":"15", "progress": 0, "open": true}
	],
	"links":[
		{"id":"1","source":"1","target":"2","type":"1"},
		{"id":"2","source":"2","target":"3","type":"0"},
		{"id":"3","source":"3","target":"4","type":"0"},
		{"id":"4","source":"2","target":"5","type":"2"},
		{"id":"5","source":"2","target":"6","type":"2"},
		{"id":"6","source":"3","target":"7","type":"2"},
		{"id":"7","source":"4","target":"8","type":"2"},
		{"id":"8","source":"4","target":"9","type":"2"},
		{"id":"9","source":"4","target":"10","type":"2"},
		{"id":"10","source":"11","target":"12","type":"1"},
		{"id":"11","source":"11","target":"13","type":"1"},
		{"id":"12","source":"11","target":"14","type":"1"},
		{"id":"13","source":"11","target":"15","type":"1"},
		{"id":"14","source":"11","target":"16","type":"1"},
		{"id":"15","source":"13","target":"17","type":"1"},
		{"id":"16","source":"17","target":"18","type":"0"},
		{"id":"17","source":"18","target":"19","type":"0"},
		{"id":"18","source":"19","target":"20","type":"0"},
		{"id":"19","source":"15","target":"21","type":"2"},
		{"id":"20","source":"15","target":"22","type":"2"},
		{"id":"21","source":"15","target":"23","type":"2"}
	]
};

    core.view_registry.add('wangke', New_Gantt);
    return New_Gantt;
})