/**
 * Created by allen on 2017/11/22.
 */
odoo.define('linkloving_mo_planned_report.mo_planned_report', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var pyeval = require('web.pyeval');
    var MoPlannedReport = Widget.extend(ControlPanelMixin, {
        template: "MoPlannedReport",
        events: {},
        init: function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
            if (parent && parent.action_stack.length > 0) {
                this.action_manager = parent.action_stack[0].widget.action_manager
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
            self.get_field_info("stock.picking", ['state']).done(function () {
                self.initTable(self.action.context.vals);
            });
        },
        get_field_info: function (model, fields) {
            var self = this;
            return new Model(model).call("fields_get", [fields]).then(function (res) {
                self.fields = res;
            })
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
                    aname = a.name;
                }
                if (b) {
                    bname = b.name;
                }
                if (aname > bname) return 1;
                if (aname < bname) return -1;
                return 0;
            }
            var coloums = [
                {
                    field: 'name',
                    title: 'SO单号',
                }, {
                    field: 'partner_name',
                    title: '客户/公司名称',
                },
                {
                    field: 'validity_date',
                    title: '交货日期',
                    formatter: function (value, row, index) {
                        if (value) {
                            return new Date(value.replace(/-/g, "/")).Format("yyyy-MM-dd");
                        } else {
                            return '暂无时间'
                        }
                    },
                },
                {
                    field: 'pi_number',
                    title: 'PI号码',
                }, {
                    field: 'product_name',
                    title: '产品',
                    sortable: true,
                },

                {
                    field: 'order_qty',
                    title: '订单数量',
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
                ]
                , data, true);
            //options = $.extend(options, {
            //    //url: '/linkloving_web/get_report',
            //    query: {},
            //})
            self.$('#mo_planned_table').bootstrapTable(options);
            self.$('#btn-expand-all').click(function () {
                self.$('#mo_planned_table').bootstrapTable('expandAllRows');
            });
            self.$('#btn-collapse-all').click(function () {
                self.$('#mo_planned_table').bootstrapTable('collapseAllRows');
            });

        },
        options_init: function (filename, coloums, data, detail_view) {
            var self = this;
            return {
                contentType: 'application/json',
                method: 'post',
                //toolbar: '.toolbar',
                //pagination: true,
                //paginationLoop: true,
                //sidePagination: 'client',
                showToggle: !detail_view ? false : true,
                search: !detail_view ? false : true,
                //striped: true,
                showColumns: !detail_view ? false : true,
                showExport: !detail_view ? false : true,
                detailView: !detail_view ? false : true,
                cache: false,
                sortable: true,
                expandAllRows: true,
                striped: true,
                //showRefresh: is_sub ? false : true,
                editable: true,
                iconsPrefix: 'fa', // glyphicon of fa (font awesome)
                exportTypes: ['excel', 'png'],
                exportOptions: {
                    fileName: filename,//'生产跟踪单' + data.so_name,
                    excelstyles: ['background-color', 'color', 'font-weight', 'border', 'border-top', 'border-bottom', 'border-left', 'border-right', 'font-size', 'width', 'height'],
                },
                exportDataType: "all",
                icons: {
                    paginationSwitchDown: 'glyphicon-collapse-down icon-chevron-down',
                    paginationSwitchUp: 'glyphicon-collapse-up icon-chevron-up',
                    refresh: 'fa fa-refresh',
                    toggle: 'fa-lg fa-list-ul',
                    columns: 'fa-th',
                    detailOpen: 'fa fa-caret-right',
                    detailClose: 'fa fa-caret-down',
                    export: 'fa-upload',
                },
                columns: coloums,
                data: data,//data.order_line,
                onExpandRow: function (index, row, $detail) {
                    console.log("12312312312312");
                    self.initTableMosByProcess(row.orders, $detail);
                },
            }
        },
        initTableMosByProcess: function (data, $detail) {
            var self = this;
            var cur_table = $detail.html('<table></table>').find('table');
            if (!data) {
                return;
            }
            var colomns = self.initSubColumns(data);
            var options = $.extend(self.options_init('', colomns, data, true), {
                onExpandRow: function (index, row, $detail) {
                    self.initTablePos(row.orders, $detail);
                },
                rowStyle: function (row, index) {
                    //这里有5个取值代表5中颜色['active', 'success', 'info', 'warning', 'danger'];
                    var strclass = "";
                    if (row.virtual_available <= 0) {
                        strclass = 'danger';//还有一个active
                    }
                    else {
                        return {}
                    }

                    return {classes: strclass}
                },
            });
            self.$(cur_table).bootstrapTable(options);
        },
        initTablePos: function (data, $detail) {
            var self = this;
            var cur_table = $detail.html('<table></table>').find('table');
            if (!data) {
                return;
            }
            var colomns = self.init2SubColumns(data);
            var options = $.extend(self.options_init('', colomns, data, false), {
                onEditableSave: function (field, row, oldValue, $el) {
                    console.log(row)
                    if (field == 'handle_date')
                        return new Model("purchase.order")
                            .call("change_handle_date", [row.id, {handle_date: row.handle_date}])
                            .then(function (result) {
                                self.do_notify("消息", "设置成功");
                            })
                },
            })
            self.$(cur_table).bootstrapTable(options);
        },
        initSubColumns: function (data) {
            var self = this;
            var formatter_func = function (value, row, index) {

                //if (value) {
                //    if (value["sub_ip"]) {
                //        var url = value["sub_ip"] + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                //    }
                //    else {
                //        if (value.model && value.id) {
                //            var url = 'http://' + location.host + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                //        }
                //        else {
                //            return '';
                //        }
                //    }
                //    return '<a href=\"' + url + '\" target=\"_blank\">' + value.name + '</a>';
                //}
                //else {
                //    return '';
                //}
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
                title: '产品',
                sortable: true,
            }, {
                field: 'qty_available',
                title: '库存',
                sortable: true,
            }, {
                field: 'virtual_available',
                title: '预测数量',
                sortable: true,
            }, {
                field: 'incoming_qty',
                title: '在产数量',
                sortable: true,
            },
            ]
            return [row1];
        },
        init2SubColumns: function (data) {
            var self = this;
            var formatter_func = function (value, row, index) {

                //if (value) {
                //    if (value["sub_ip"]) {
                //        var url = value["sub_ip"] + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                //    }
                //    else {
                //        if (value.model && value.id) {
                //            var url = 'http://' + location.host + '/web?#view_type=form&model=' + value.model + '&id=' + value.id;
                //        }
                //        else {
                //            return '';
                //        }
                //    }
                //    return '<a href=\"' + url + '\" target=\"_blank\">' + value.name + '</a>';
                //}
                //else {
                //    return '';
                //}
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
                title: '单号',
                sortable: true,
            }, {
                field: 'state',
                title: '状态',
                sortable: true,
            }, {
                field: 'product_name',
                title: '产品',
                sortable: true,
            }, {
                field: 'product_qty',
                title: '订单数量',
                sortable: true,
            },
                {
                    field: 'qty_received',
                    title: '已收货数量',
                    sortable: true,
                },
                {
                    field: 'handle_date',
                    title: 'PO交期',
                    sortable: true,
                    formatter: function (value, row, index) {
                        if (value) {
                            return new Date(value.replace(/-/g, "/")).Format("yyyy-MM-dd");
                        } else {
                            return '暂无时间'
                        }
                    },
                    editable: {
                        type: 'date',
                        title: '选择交期',
                        emptytext: '暂未设置交期',
                        //noeditFormatter: function (value, row, index) {
                        //    var result = (row.carrier_id.name || '');
                        //
                        //    return self.concactEditTag(result, 'carrier_id_select')
                        //}
                    },
                },
            ]
            return [row1];
        }


    });

    core.action_registry.add('mo_planned_report', MoPlannedReport);

    return MoPlannedReport;


});
