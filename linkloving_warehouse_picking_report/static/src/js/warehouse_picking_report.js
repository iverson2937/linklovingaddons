/**
 * Created by allen on 2017/11/22.
 */
odoo.define('linkloving_warehouse_picking_report.warehouse_picking_report', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var PickingReport = Widget.extend(ControlPanelMixin, {
        template: "WarehousePickingReport",
        events: {},
        init: function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
            console.log("aAAAAAAAAAAAAAAAAAAAAAAAA");
            if (parent && parent.action_stack.length > 0) {
                this.action_manager = parent.action_stack[0].widget.action_manager
            }
            if (action && action.context && action.context["sub_company_order_track"]) {
                this.sub_company_order_track = true;
                this.so_id = action.context["so_id"];
            }
            if (action && action.params) {
                this.so_id = action.params["active_id"];
                this.sub_company_order_track = true;
            }
            this.action = action;
        },

        start: function () {
            var self = this;
            var cp_status = {
                breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
                // cp_content: _.extend({}, self.searchview_elements, {}),
            };
            self.update_control_panel(cp_status);

            if (self.action && self.action.context) {
                self.get_field_info("stock.picking", ['state']).done(function () {
                    self.get_delivery_data();
                    self.initTable(self.action.context.vals);
                })
            }

            //if (self.sub_company_order_track) {
            //    new Model("sub.company.report")
            //        .call("get_sub_company_report", [], {so_id: self.so_id})
            //        .then(function (res) {
            //            self.initTableSubCompany(res);
            //        })
            //} else {
            //    new Model("sub.company.report")
            //    .call("get_report")
            //    .then(function (res) {
            //        var data = res;
            //        self.initTable(data);
            //    });
            //}


        },
        initTable: function (data) {
            var self = this;
            var formatter_func = function (value, row, index) {
                if (value) {
                    if (value["sub_ip"]) {
                        var url = value["sub_ip"] + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                    }
                    else {
                        var url = 'http://' + location.host + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                    }
                    return '<a href="' + url + '" target="_blank">' + value.name + '</a>';
                }
                else {
                    return '';
                }
            };
            var sorter = function (a, b) {
                console.log(a);
                var aname = '';
                var bname = '';
                if (a) {
                    aname = a;
                }
                if (b) {
                    bname = b;
                }
                if (aname > bname) return 1;
                if (aname < bname) return -1;
                return 0;
            }
            var coloums = [{
                field: 'seq',
                title: '序号',
                formatter: function (value, row, index) {
                    return index + 1;
                }
            }, {
                field: 'name',
                title: '销售单号',
                sortable: true,
                formatter: function (value, row, index) {
                    var url = 'http://' + location.host + '/web?#view_type=form&model=' + row.model + '&id=' + row.id;
                    return '<a href="' + url + '" target="_blank">' + row.name + '</a>';
                },
                sorter: sorter,
            }, {
                field: 'partner_name',
                title: '客户',
                //formatter: function (value, row, index) {
                //    this.colspan = row.pickings.length;
                //    return value;
                //},
                sortable: true,
            },
            ];
            var options = self.options_init('江苏若态订单汇总' + new Date().Format("yyyy-MM-dd"),
                [
                    [{
                        field: 'title',
                        title: self.action.name,
                        halign: "center",
                        align: "center",
                        colspan: coloums.length,
                        'class': "font_35_header",
                    }],
                    coloums
                ], data, false);
            self.$('#picking_report_table').bootstrapTable(options);
        },
        options_init: function (filename, coloums, data, is_sub) {
            var self = this;
            return {
                cache: false,
                sortable: true,
                showToggle: is_sub ? false : true,
                search: is_sub ? false : true,
                //striped: true,
                showColumns: is_sub ? false : true,
                showExport: is_sub ? false : true,
                detailView: is_sub ? false : true,
                editable: true,

                iconsPrefix: 'fa', // glyphicon of fa (font awesome)
                exportTypes: ['excel', 'png'],
                exportOptions: {
                    fileName: filename,//'生产跟踪单' + data.so_name,
                    excelstyles: ['background-color', 'color', 'font-weight', 'border', 'border-top', 'border-bottom', 'border-left', 'border-right', 'font-size', 'width', 'height'],
                },
                icons: {
                    paginationSwitchDown: 'glyphicon-collapse-down icon-chevron-down',
                    paginationSwitchUp: 'glyphicon-collapse-up icon-chevron-up',
                    refresh: 'glyphicon-refresh icon-refresh',
                    toggle: 'fa-lg fa-list-ul',
                    columns: 'fa-th',
                    detailOpen: 'glyphicon-plus icon-plus',
                    detailClose: 'glyphicon-minus icon-minus',
                    export: 'fa-upload',
                },
                columns: coloums,
                data: data,//data.order_line,
                rowStyle: function (row, index) {
                    //这里有5个取值代表5中颜色['active', 'success', 'info', 'warning', 'danger'];
                    var strclass = "";
                    if (is_sub) {
                        if (row.state == "done") {
                            strclass = 'success';//还有一个active
                        }
                        else {
                            return {}
                        }

                    }
                    else {
                        if (row.is_done) {
                            strclass = 'success';//还有一个active
                        }
                        else {
                            return {}
                        }
                    }
                    return {classes: strclass}
                },
                onExpandRow: function (index, row, $detail) {
                    self.initTableSubCompany(row.pickings, $detail);
                },
                onEditableShown: function (field, row, $el, editable) {
                    if (field === 'carrier_id_select') {
                        if (!self.origin_delivery_data || self.origin_delivery_data.length == 0) {
                            self.do_warn("警告", "暂无可选择的物流公司,请先设置");
                        }
                    }
                    return false;
                },
                onEditableSave: function (field, row, oldValue, $el) {
                    console.log("save savesavesavesavesavesavesave")
                    var field_name = field;
                    if (field_name === 'carrier_id_select') {
                        var new_carrier_id = row.carrier_id_select;

                        new Model(row.model).call("write", [row.id, {carrier_id: new_carrier_id}]).then(function (res) {
                            if (res) {
                                self.do_notify("消息", "设置成功");
                                $.each(self.origin_delivery_data, function (key, value) {
                                    if (new_carrier_id == value.id) {
                                        row.carrier_id = {
                                            id: value.id,
                                            name: value.name,
                                            model: 'delivery.carrier',
                                        }
                                        return;
                                    }
                                });
                            }
                        })
                    }
                    else {
                        var params = {};
                        params[field_name] = row[field_name];
                        new Model(row.model).call("write", [row.id, params]).then(function (res) {
                            if (res) {
                                self.do_notify("消息", "设置成功");
                            }
                        })
                    }
                    return false;
                }
            }
        },
        initTableSubCompany: function (data, $detail) {
            var self = this;
            var cur_table = $detail.html('<table></table>').find('table');
            if (!data) {
                return;
            }
            var colomns = self.initSubColumns(data);
            var options = self.options_init('', colomns, data, true);
            self.$(cur_table).bootstrapTable(options);
        },
        get_field_info: function (model, fields) {
            var self = this;
            return new Model(model).call("fields_get", [fields]).then(function (res) {
                self.fields = res;
            })
        },
        get_delivery_data: function () {
            var self = this;
            var result = [];
            console.log("AAAAAAAAAAA");
            //new Model("delivery.carrier").query(['id', 'name']).all().then(function (res) {
            //    $.each(res, function (key, value) {
            //        result.push({ value: value.id, text: value.name });
            //    });
            //    self.result = result;
            //});
            new Model("delivery.carrier").query(['id', 'name']).all().then(function (res) {
                $.each(res, function (key, value) {
                    result.push({value: value.id, text: value.name});
                });
                self.delivery_data = result;
                self.origin_delivery_data = res;
            });

        },
        concactEditTag: function (result, field) {
            return ['<a href="javascript:void(0)"',
                ' data-name="' + field + '"',
                ' data-pk="' + '"',
                ' data-value="' + result + '"',
                '>' + result + '<i class="icon-margin fa fa-pencil"></i>' + '</a>'
            ].join('');
        },
        initSubColumns: function (data) {
            var self = this;
            var formatter_func = function (value, row, index) {
                if (value) {
                    if (value["sub_ip"]) {
                        var url = value["sub_ip"] + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                    }
                    else {
                        if (value.model && value.id) {
                            var url = 'http://' + location.host + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                        }
                        else {
                            return '';
                        }
                    }
                    return '<a href=\"' + url + '\" target=\"_blank\">' + value.name + '</a>';
                }
                else {
                    return '';
                }
            };
            var sorter = function (a, b) {
                console.log(a);
                var aname = '';
                var bname = '';
                if (a) {
                    aname = a.name;
                }
                if (b) {
                    bname = b.name;
                }
                if (aname > bname) return 1;
                if (aname < bname) return -1;
                return 0;
            }
            var row1 = [{
                field: 'name',
                title: '出货单',
                formatter: function (value, row, index) {
                    if (value) {
                        var url = 'http://' + location.host + '/web?#view_type=form&model=' + row.model + '&id=' + row.id;
                        return '<a href="' + url + '" target="_blank">' + row.name + '</a>';
                    }
                    else {
                        return '';
                    }
                },
                sortable: true,
            }, {
                field: 'state',
                title: '出货单状态',
                sortable: true,
                formatter: function (value, row, index) {
                    //fields.state
                    var state_str = "";
                    $.each(self.fields.state.selection, function (key, val) {
                        if (val[0] === value) {
                            state_str = val[1];
                        }
                    })
                    return state_str;
                }
            }, {
                field: 'carrier_id_select',
                title: '物流',
                formatter: function (value, row, index) {
                    return (row.carrier_id.name || '');
                },
                //formatter:formatter_func,
                sortable: true,
                editable: {
                    type: 'select',
                    title: '选择物流公司',
                    emptytext: '暂未选择物流<i class="icon-margin fa fa-pencil"></i>',
                    source: self.delivery_data,
                    noeditFormatter: function (value, row, index) {
                        var result = (row.carrier_id.name || '');

                        return self.concactEditTag(result, 'carrier_id_select')
                    }
                },
            }, {
                field: 'number_of_packages',
                title: '件数',
                sortable: true,
                editable: {
                    type: 'text',
                    title: '请输入件数<i class="icon-margin fa fa-pencil"></i>',
                    emptytext: '0',
                    validate: function (value) {
                        if (isNaN(value)) return '请输入数字';
                        var number = parseFloat(value);
                        if (number % 1 !== 0) return '请输入整数';
                        if (number <= 0) return '请输入正确的件数';
                    },
                    noeditFormatter: function (value, row, index) {
                        //var result = (row.carrier_id.name || '');

                        return self.concactEditTag(value, 'number_of_packages')
                    }
                }
            }, {
                field: 'back_order_id',
                title: '欠货单',
                sortable: true,
                formatter: formatter_func,
                sorter: sorter,
            },
                {
                    field: 'report_remark',
                    title: '备注',
                    editable: {
                        type: 'textarea',
                        emptytext: '暂无备注<i class="icon-margin fa fa-pencil"></i>',
                        noeditFormatter: function (value, row, index) {
                            //var result = (row.carrier_id.name || '');

                            return self.concactEditTag(value, 'report_remark')
                        }
                    }
                }]
            return [row1];
        }
    });

    core.action_registry.add('warehouse_picking_report', PickingReport);

    return PickingReport;


});
