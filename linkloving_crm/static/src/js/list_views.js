/**
 * Created by Administrator on 2017/6/30.
 */
odoo.define('linkloving_crm.list_views', function (require) {
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


    var Class = core.Class;
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;
    var list_widget_registry = core.list_widget_registry;

    var data_list = new Set();
    var data_list_temporary = new Set();

// Allowed decoration on the list's rows: bold, italic and bootstrap semantics classes
    var row_decoration = [
        'decoration-bf',
        'decoration-it',
        'decoration-danger',
        'decoration-info',
        'decoration-muted',
        'decoration-primary',
        'decoration-success',
        'decoration-warning'
    ];


    var List_View_New = ListView.extend({
        init: function () {

            var self = this;
            this._super.apply(this, arguments);
            this.options = _.defaults(this.options, {
                GroupsType: ListView.Groups,
                ListType: ListView.List,
            });

            data_list = new Set();
            data_list_temporary = new Set();

            this.previous_colspan = null;
            this.decoration = null;

            this.columns = [];

            this.records = new common.Collection();

            this.set_groups(new (this.options.GroupsType)(this));

            if (this.dataset instanceof data.DataSetStatic) {
                this.groups.datagroup = new StaticDataGroup(this.dataset);
            } else {
                this.groups.datagroup = new DataGroup(
                    this, this.model,
                    this.dataset.get_domain(),
                    this.dataset.get_context());
                this.groups.datagroup.sort = this.dataset._sort;
            }

            this.records.bind('change', function (event, record, key) {
                if (!_(self.aggregate_columns).chain()
                        .pluck('name').contains(key).value()) {
                    return;
                }
                self.compute_aggregates();
            });

            this.no_leaf = false;
            this.grouped = false;

            if (!this.options.$pager || !this.options.$pager.length) {
                this.options.$pager = false;
            }

            this.options.deletable = this.options.deletable && this.is_action_enabled('delete');
            this.name = "" + this.fields_view.arch.attrs.string;

            // the view's number of records per page (|| section)
            this._limit = (this.options.limit ||
            this.defaults.limit ||
            (this.getParent().action || {}).limit ||
            parseInt(this.fields_view.arch.attrs.limit, 10) ||
            80);
            // the index of the first displayed record (starting from 1)
            this.current_min = 1;

            // Sort
            var default_order = this.fields_view.arch.attrs.default_order;
            var unsorted = !this.dataset._sort.length;
            if (unsorted && default_order && !this.grouped) {
                this.dataset.set_sort(default_order.split(','));
            }
        },
        unique_list: function (arr) {
            var list = new Array();
            for (var i = 0; i < arr.length; i++) {
                if (list.indexOf(arr[i]) == -1) {
                    list.push(arr[i]);
                }
            }
            return list;
        },
        load_list: function () {
            var self = this;

            // Render the table and append its content
            this.$el.html(QWeb.render(this._template, this));
            this.$el.addClass(this.fields_view.arch.attrs['class']);
            if (this.grouped) {
                this.$('.o_list_view').addClass('o_list_view_grouped');
            }
            this.$('.o_list_view').append(this.groups.elements);

            // Compute the aggregates and display them in the list's footer
            this.compute_aggregates();

            // Head hook
            // Selecting records
            this.$('thead .o_list_record_selector input').click(function () {


                // console.log("LLLLLLLLLLLLLLLLLLL")
                self.$('tbody .o_list_record_selector input').prop('checked', $(this).prop('checked') || false);
                var data_list1 = new Array();
                var selection = self.groups.get_selection();

                data_list.forEach(function (item) {
                    data_list1.splice(0, 0, item)
                });

                data_list1 = self.unique_list(data_list1.concat(selection.ids))
                // 删除重复
                $(self.groups).trigger('selected', [data_list1, selection.records]);
            });


            this.$('tbody .o_list_record_selectorss input').click(function (e) {
                if ($(this).context.parentElement.parentElement.nextElementSibling == null) {
                    //系列下面 展开了
                    // console.log("选择实现方法")
                    var class_name_select = $(this).context.parentElement.parentElement.parentNode.nextElementSibling.className;
                    if (class_name_select.length > 0) {
                        var arr = class_name_select.split(' ');
                        self.$('.' + arr[0] + ' input').prop('checked', $(this).prop('checked') || false);
                        var data_list1 = new Array();
                        var selection = self.groups.get_selection();

                        data_list.forEach(function (item) {
                            data_list1.splice(0, 0, item)
                        });
                        data_list1 = self.unique_list(data_list1.concat(selection.ids))
                        // 删除重复
                        $(self.groups).trigger('selected', [data_list1, selection.records]);
                    }
                }
                // else {
                //     if (e.target.checked) {
                //         console.log("在点击未展开方块后 执行操作")
                //
                //         console.log(selection, 12)
                //         // new Model('ir.attachment').query()
                //         //     .filter([['res_model', '=', 'project.task'], ['res_id', '=', this.id], ['mimetype', 'ilike', 'image']])
                //         //     .all().then(function (result) {
                //         // });
                //         $(self.groups).trigger('selected', [[46634, 62500, 47465, 69710, 47460, 55279, 53327]]);
                //
                //     } else {
                //         console.log("未展开 取消选中 执行操作")
                //     }
                //
                // }


            });

            // Sort
            if (this.dataset._sort.length) {
                if (this.dataset._sort[0].indexOf('-') === -1) {
                    this.$('th[data-id=' + this.dataset._sort[0] + ']').addClass("o-sort-down");
                } else {
                    this.$('th[data-id=' + this.dataset._sort[0].split('-')[1] + ']').addClass("o-sort-up");
                }
            }

            this.trigger('list_view_loaded', data, this.grouped);
            return $.when();
        },
    });


    // core.view_registry.add('list', ListView);


    ListView.Groups.include({
        open: function (point_insertion) {
            //  point_insertion 当前tbody
            // console.log("open")

            if (this.$to_be_removed) {
                // this.$to_be_removed.css("display", "inline");
                $(point_insertion).next().show();
            } else {
                this.render();
                // $(this.elements).addClass(Date.parse(new Date()))
                $(this.elements).insertAfter(point_insertion);
                var no_subgroups = _(this.datagroup.group_by).isEmpty(),
                    records_terminated = !this.datagroup.context['group_by_no_leaf'];
                if (no_subgroups && records_terminated) {
                    this.render_group_pager();
                }
            }
        },
        close: function () {
            if (this.pager) {
                this.pager.destroy();
            }
            // this.records.reset();

            this.$to_be_removed = $(this.elements);
            _.each(this.children, function (child) {
                this.$to_be_removed = this.$to_be_removed.add(child.$to_be_removed);
            }.bind(this));


            this.$to_be_removed.css("display", "none");

            // this.$to_be_removed.remove();
        },
        render_groups: function (datagroups) {
            // console.log("FFFFFFFFFFFFFFFFFF")
            var self = this;
            var placeholder = this.make_fragment();
            _(datagroups).each(function (group) {
                if (self.children[group.value]) {
                    self.records.proxy(group.value).reset();
                    delete self.children[group.value];
                }
                var child = self.children[group.value] = new (self.view.options.GroupsType)(self.view, {
                    records: self.records.proxy(group.value),
                    options: self.options,
                    columns: self.columns
                });
                self.bind_child_events(child);
                child.datagroup = group;
                var html_val = ''
                if (!(self.view.model == "product.template" && self.view.name == "产品")) {
                    html_val = ' style="display:none" '
                }
                var $row = child.$row = $('<tr class="o_group_header"><th class="o_list_record_selectorss"><input type="checkbox"' + html_val + '/></th>');
                if (group.openable && group.length) {
                    $row.click(function (e) {

                        if (!$row.data('open')) {
                            // alert("dakai")

                            if (e.originalEvent.target.localName != "input") {
                                $row.data('open', true)
                                    .find('span.fa')
                                    .removeClass('fa-caret-right')
                                    .addClass('fa-caret-down');

                                child.open(self.point_insertion(e.currentTarget));

                                // 系列一经选中 展开式全选下面子项
                                if (e.currentTarget.childNodes[0].firstChild.checked) {
                                    // console.log("已经选中 但未展开 展开选择全部 删除本组在 data_list")


                                    e.currentTarget.childNodes[0].firstChild.checked = false;
                                    new Model('product.template').query().filter(child.datagroup.domain).all().then(function (result) {
                                        for (var res in result) {
                                            data_list.delete(result[res].id);
                                        }

                                        var data_list1 = new Array();
                                        var selection = self.get_selection();

                                        data_list.forEach(function (item) {
                                            data_list1.splice(0, 0, item)
                                        });

                                        data_list1 = self.unique_list1(data_list1.concat(selection.ids))

                                        // 删除重复

                                        console.log(data_list1, "已选的项")

                                        $(self).trigger('selected', [data_list1]);


                                    });


                                    // e.currentTarget.childNodes[0].firstChild.attr("width", '100px');
                                    // attr('checked', false);

                                    // 解注
                                    // console.log(e.currentTarget)
                                    // console.log(self.point_insertion(e.currentTarget))
                                }
                            }
                            else {
                                // 未展开点击系列 添加系列到 选择
                                // console.log("未展开点击系列 添加系列到 选择");
                                // 保存数据库 绑定每次选中的值

                                new Model('product.template').query().filter(child.datagroup.domain).all().then(function (result) {
                                    for (var res in result) {
                                        if (e.currentTarget.childNodes[0].firstChild.checked) {
                                            data_list.add(result[res].id);
                                        } else {
                                            data_list.delete(result[res].id)
                                        }
                                    }
                                    var data_list1 = new Array();
                                    var selection = self.get_selection();

                                    data_list.forEach(function (item) {
                                        data_list1.splice(0, 0, item)
                                    });

                                    data_list1 = self.unique_list1(data_list1.concat(selection.ids))
                                    // 删除重复
                                    // console.log(data_list1, 555)
                                    $(self).trigger('selected', [data_list1]);
                                });
                            }


                        } else {
                            if (e.originalEvent.target.localName != "input") {
                                // alert("关闭")
                                $row.removeData('open')
                                    .find('span.fa')
                                    .removeClass('fa-caret-down')
                                    .addClass('fa-caret-right');
                                child.close();
                            }
                        }

                    });
                }
                placeholder.appendChild($row[0]);

                var $group_column = $('<th class="o_group_name">').appendTo($row);
                // Don't fill this if group_by_no_leaf but no group_by
                if (group.grouped_on) {
                    var row_data = {};
                    row_data[group.grouped_on] = group;
                    var group_label = _t("Undefined");
                    var group_column = _(self.columns).detect(function (column) {
                        return column.id === group.grouped_on;
                    });
                    if (group_column) {
                        try {
                            group_label = group_column.format(row_data, {
                                value_if_empty: _t("Undefined"),
                                process_modifiers: false
                            });
                        } catch (e) {
                            group_label = _.str.escapeHTML(row_data[group_column.id].value);
                        }
                    } else {
                        group_label = group.value;
                        var grouped_on_field = self.view.fields_get[group.grouped_on];
                        if (grouped_on_field && grouped_on_field.type === 'selection') {
                            group_label = _.find(grouped_on_field.selection, function (selection) {
                                return selection[0] === group.value;
                            });
                        }
                        if (group_label instanceof Array) {
                            group_label = group_label[1];
                        }
                        if (group_label === false) {
                            group_label = _t('Undefined');
                        }
                        group_label = _.str.escapeHTML(group_label);
                    }

                    // group_label is html-clean (through format or explicit
                    // escaping if format failed), can inject straight into HTML
                    $group_column.html(_.str.sprintf("%s (%d)",
                        group_label, group.length));

                    if (group.length && group.openable) {
                        // Make openable if not terminal group & group_by_no_leaf
                        $group_column.prepend('<span class="fa fa-caret-right" style="padding-right: 5px;">');
                    } else {
                        $group_column.prepend('<span class="fa">');
                    }
                }
                self.indent($group_column, group.level);

                if (self.options.selectable) {
                    $row.append('<td>');
                }
                _(self.columns).chain()
                    .filter(function (column) {
                        return column.invisible !== '1';
                    })
                    .each(function (column) {
                        if (column.meta) {
                            // do not do anything
                        } else if (column.id in group.aggregates) {
                            var r = {};
                            r[column.id] = {value: group.aggregates[column.id]};
                            $('<td class="oe_number">')
                                .html(column.format(r, {process_modifiers: false}))
                                .appendTo($row);
                        } else {
                            $row.append('<td>');
                        }
                    });
                if (self.options.deletable) {
                    $row.append('<td class="oe_list_group_pagination">');
                }
            });
            return placeholder;
        },
        unique_list1: function (arr) {
            var list = new Array();
            for (var i = 0; i < arr.length; i++) {
                if (list.indexOf(arr[i]) == -1) {
                    list.push(arr[i]);
                }
            }
            return list;
        },
        bind_child_events: function (child) {
            var $this = $(this),
                self = this;
            // console.log("找不到的哪一个")
            $(child).bind('selected', function (e, _0, _1, deselected) {
                var data_list1 = new Array();
                var selection = self.get_selection();

                data_list.forEach(function (item) {
                    data_list1.splice(0, 0, item)
                });

                data_list1 = self.unique_list1(data_list1.concat(selection.ids))
                // 删除重复
                $this.trigger(e, [data_list1, selection.records, deselected]);
            }).bind(this.passthrough_events, function (e) {
                // additional positional parameters are provided to trigger as an
                // Array, following the event type or event object, but are
                // provided to the .bind event handler as *args.
                // Convert our *args back into an Array in order to trigger them
                // on the group itself, so it can ultimately be forwarded wherever
                // it's supposed to go.
                var args = Array.prototype.slice.call(arguments, 1);
                $this.trigger.call($this, e, args);
            });
        },
        setup_resequence_rows: function (list, dataset) {

            if (this.datagroup.value)list.$current.addClass((this.datagroup.value[0]).toString());

            var sequence_field = _(this.columns).findWhere({'widget': 'handle'});
            var seqname = sequence_field ? sequence_field.name : 'sequence';

            // drag and drop enabled if list is not sorted (unless it is sorted by
            // its sequence field (ASC)), and there is a visible column with
            // @widget=handle or "sequence" column in the view.
            if ((dataset.sort && [seqname, seqname + ' ASC', ''].indexOf(dataset.sort()) === -1)
                || !_(this.columns).findWhere({'name': seqname})) {
                return;
            }

            // ondrop, move relevant record & fix sequences
            list.$current.sortable({
                axis: 'y',
                items: '> tr[data-id]',
                helper: 'clone'
            });
            if (sequence_field) {
                list.$current.sortable('option', 'handle', '.o_row_handle');
            }
            list.$current.sortable('option', {
                start: function (e, ui) {
                    ui.placeholder.height(ui.item.height());
                },
                stop: function (event, ui) {
                    var to_move = list.records.get(ui.item.data('id')),
                        target_id = ui.item.prev().data('id'),
                        from_index = list.records.indexOf(to_move),
                        target = list.records.get(target_id);
                    if (list.records.at(from_index - 1) == target) {
                        return;
                    }

                    list.records.remove(to_move, {silent: true});
                    var to = target_id ? list.records.indexOf(target) + 1 : 0;
                    list.records.add(to_move, {at: to, silent: true});

                    // resequencing time!
                    var record, index = to,
                        // if drag to 1st row (to = 0), start sequencing from 0
                        // (exclusive lower bound)
                        seq = to ? list.records.at(to - 1).get(seqname) : 0;
                    var defs = [];
                    var fct = function (dataset, id, seq) {
                        defs.push(utils.async_when().then(function () {
                            var attrs = {};
                            attrs[seqname] = seq;
                            return dataset.write(id, attrs, {internal_dataset_changed: true});
                        }));
                    };
                    while (++seq, (record = list.records.at(index++))) {
                        // write are independent from one another, so we can just
                        // launch them all at the same time and we don't really
                        // give a fig about when they're done
                        fct(dataset, record.get('id'), seq);
                        record.set(seqname, seq);
                    }
                    $.when.apply($, defs).then(function () {
                        // use internal_dataset_changed and trigger one onchange after all writes
                        dataset.trigger("dataset_changed");
                    });
                }
            });
        },
    });


    var DataGroup = Class.extend({
        init: function (parent, model, domain, context, group_by, level) {
            this.model = new Model(model, context, domain);
            this.group_by = group_by;
            this.context = context;
            this.domain = domain;

            this.level = level || 0;
        },
        list: function (fields, ifGroups, ifRecords) {
            var self = this;
            if (!_.isEmpty(this.group_by)) {
                // ensure group_by fields are read.
                fields = _.unique((fields || []).concat(this.group_by));
            }
            var query = this.model.query(fields).order_by(this.sort).group_by(this.group_by);
            return $.when(query).then(function (querygroups) {
                // leaf node
                if (!querygroups) {
                    var ds = new data.DataSetSearch(self, self.model.name, self.model.context(), self.model.domain());
                    ds._sort = self.sort;
                    return ifRecords(ds);
                }
                // internal node
                var child_datagroups = _(querygroups).map(function (group) {
                    var child_context = _.extend(
                        {}, self.model.context(), group.model.context());
                    var child_dg = new DataGroup(
                        self, self.model.name, group.model.domain(),
                        child_context, group.model._context.group_by,
                        self.level + 1);
                    child_dg.sort = self.sort;
                    // copy querygroup properties
                    child_dg.__context = child_context;
                    child_dg.__domain = group.model.domain();
                    child_dg.folded = group.get('folded');
                    child_dg.grouped_on = group.get('grouped_on');
                    child_dg.length = group.get('length');
                    child_dg.value = group.get('value');
                    child_dg.openable = group.get('has_children');
                    child_dg.aggregates = group.get('aggregates');
                    return child_dg;
                });
                ifGroups(child_datagroups);
            });
        }
    });

    var StaticDataGroup = DataGroup.extend({
        init: function (dataset) {
            this.dataset = dataset;
        },
        list: function (fields, ifGroups, ifRecords) {
            return ifRecords(this.dataset);
        }
    });


    var FieldPriority = common.AbstractField.extend({
        events: {
            'mouseup': function (e) {
                e.stopPropagation();
            },
        },
        start: function () {
            this.priority = new Priority(this, {
                readonly: this.get('readonly'),
                value: this.get('value'),
                values: this.field.selection || [],
            });

            this.priority.on('update', this, function (update) {
                /* setting the value: in view mode, perform an asynchronous call and reload
                 the form view; in edit mode, use set_value to save the new value that will
                 be written when saving the record. */
                var view = this.view;
                if (view.get('actual_mode') === 'view') {
                    var write_values = {};
                    write_values[this.name] = update.value;
                    view.dataset._model.call('write', [
                        [view.datarecord.id],
                        write_values,
                        view.dataset.get_context()
                    ]).done(function () {
                        view.reload();
                    });
                } else {
                    this.set_value(update.value);
                }
            });

            this.on('change:readonly', this, function () {
                this.priority.readonly = this.get('readonly');
                var $div = $('<div/>').insertAfter(this.$el);
                this.priority.replace($div);
                this.setElement(this.priority.$el);
            });

            var self = this;
            return $.when(this._super(), this.priority.appendTo('<div>').then(function () {
                self.priority.$el.addClass(self.$el.attr('class'));
                self.replaceElement(self.priority.$el);
            }));
        },
        render_value: function () {
            this.priority.set_value(this.get('value'));
        },
    });


    list_widget_registry.add('field.priorityw', FieldPriority);
    list_widget_registry.add('field.list_new_view', List_View_New);

})