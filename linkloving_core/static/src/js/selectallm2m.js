/**
 * Created by 123 on 2017/6/23.
 */
odoo.define('linkloving_core.selectallm2m', function (require){
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

    var listview = require('web.ListView');

    var Class = core.Class;
    var _t = core._t;
    var _lt = core._lt;
    var QWeb = core.qweb;
    var list_widget_registry = core.list_widget_registry;

    var addcheckbox = listview.Groups.include({
        render_groups: function (datagroups) {
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

                var $row = child.$row = $('<tr class="o_group_header">');
                //解决点击复选框时的问题
                if (group.openable && group.length) {
                    $row.click(function (e) {
                        var e = e||window.event;
                        var target = e.target || e.srcElement;
                        if($(target).hasClass('m2mcheckbox')){
                            return
                        }

                        if (!$row.data('open')) {
                            $row.data('open', true)
                                .find('span.fa')
                                    .removeClass('fa-caret-right')
                                    .addClass('fa-caret-down');
                            child.open(self.point_insertion(e.currentTarget));
                        } else {
                            $row.removeData('open')
                                .find('span.fa')
                                    .removeClass('fa-caret-down')
                                    .addClass('fa-caret-right');
                            child.close();
                            // force recompute the selection as closing group reset properties
                            var selection = self.get_selection();
                            $(self).trigger('selected', [selection.ids, this.records]);
                        }
                    });
                }
                placeholder.appendChild($row[0]);

                var $group_column = $('<th class="o_group_name">').appendTo($row);
                // Don't fill this if group_by_no_leaf but no group_by
                if (group.grouped_on) {
                    var row_data = {};
                    //获取id
                    var categ_id;
                    if (group.value){
                        var categ_raw_id=group.value;
                       categ_id=categ_raw_id[0]
                    }

                    row_data[group.grouped_on] = group;
                    var group_label = _t("Undefined");
                    var group_column = _(self.columns).detect(function (column) {
                        return column.id === group.grouped_on; });
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
                            group_label = _.find(grouped_on_field.selection, function(selection) {
                                return selection[0] === group.value;
                            });
                        }
                        if (group_label instanceof Array) {
                            group_label = group_label[1];
                        }
                        if (group_label === false) {
                            group_label = _t('Undefined');
                        }
                        console.log(group_label)
                        group_label = _.str.escapeHTML(group_label);
                    }

                    // group_label is html-clean (through format or explicit
                    // escaping if format failed), can inject straight into HTML

                    $group_column.html(_.str.sprintf("%s (%d)",
                        group_label, group.length));

                    $group_column.attr('data-id',categ_id);

                    if (group.length && group.openable) {
                        // Make openable if not terminal group & group_by_no_leaf
                        //添加了checkbox复选框
                        $group_column.prepend('<input class="m2mcheckbox" type="checkbox"/><span class="fa fa-caret-right" style="padding-right: 5px;">');
                    } else {
                        $group_column.prepend('<span class="fa">');
                    }
                }
                self.indent($group_column, group.level);

                if (self.options.selectable) {
                    $row.append('<td>');
                }
                _(self.columns).chain()
                    .filter(function (column) { return column.invisible !== '1'; })
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
    });

    var selectall = listview.include({
       get_selection:function () {
            var result = {ids: [], records: [], category_ids:[]};
            if (!this.options.selectable) {
                return result;
            }
            var records = this.records;
            this.$current.find('td.o_list_record_selector input:checked')
                    .closest('tr').each(function () {
                var record = records.get($(this).data('id'));
                result.ids.push(record.get('id'));
                result.records.push(record.attributes);
            });

           //添加(全选)
           this.$current.find('th.o_group_name input:m2mcheckbox').closest('th').each(function () {
               var r = records.get($(this).data('id'));
               result.category_ids.push(r.get('id'));
               result.records.push(r.attributes);
           })
            return result;
       },
       load_list: function() {
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
            //全选功能
            this.$('thead .o_list_record_selector input').click(function() {
                self.$('tbody .o_list_record_selector input').prop('checked', $(this).prop('checked') || false);
                self.$('tbody .m2mcheckbox').prop('checked', $(this).prop('checked') || false);
                var selection = self.groups.get_selection();
                $(self.groups).trigger('selected', [selection.ids, selection.records, selection.category_ids]);
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

    // core.action_registry.add('selectallm2m', addcheckbox);
    // core.action_registry.add('selectallm2m', selectall);

    // return addcheckbox
})