odoo.define('linkloving_copy_default_code_subcompany.code_copy', function (require) {
    "use strict";
    var Model = require('web.Model');
    var planner = require('web.planner.common');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var _t = core._t;
    var Dialog = require('web.Dialog');
    var webclient = require('web.web_client');
    var PlannerDialog = planner.PlannerDialog;
    var ListView = require('web.ListView');
    var framework = require('web.framework');
    ListView.prototype.defaults.import_enabled = true;
    ListView.include({

        /**
         * Extend the render_buttons function of ListView by adding an event listener
         * on the import button.
         * @return {jQuery} the rendered buttons
         */
        render_buttons: function () {
            var self = this;
            var add_button = false;
            if (!this.$buttons) { // Ensures that this is only done once
                add_button = true;
            }
            this._super.apply(this, arguments); // Sets this.$buttons
            //var is_show_procuremnt_create_btn = this.options.action && this.options.action.context.is_show_procuremnt_create_btn
            if (add_button) {
                this.$buttons.on('click', '.o_button_copy_code', this.execute_copy_code_action.bind(this));
            }
            if (self.model == 'product.template') {
                self.session.user_has_group('linkloving_copy_default_code_subcompany.group_copy_code')
                    .then(function (has_group) {
                        if (has_group) {
                            $('.o_button_copy_code').show();
                        }
                        else {
                            $('.o_button_copy_code').hide();
                        }
                    });
            }

        },
        execute_copy_code_action: function (ev) {
            var self = this;
            console.log(ev);
            return (new Model('web.planner')).call('search_read', [[['planner_application', '=', 'planner_copy_code']]]).then(function (planner) {
                if (planner.length) {
                    self.planner = planner[0];
                    self.planner.data = $.parseJSON(planner[0].data) || {};
                    self.dialog = new CodeCopyPlannerDialog(self, self.planner);
                    self.dialog.appendTo(webclient.$el).then(function () {
                        self.dialog.$el.modal('show');
                    });
                }
            });
        }

    });
    var CodeCopyPlannerDialog = planner.PlannerDialog.extend({
        prepare_planner_event: function () {
            var self = this;
            this._super.apply(this, arguments);
            if (self.planner['planner_application'] == 'planner_copy_code') {
                self.$('input[name="optionsRadios"]').on('click', function (ev) {
                    console.log(ev);
                    var copyinfo = {
                        company: parseInt($(ev.target).val()),
                    };
                    self.copy_info = copyinfo;

                });
                self.$('input[name="product_type"]').on('click', function (ev) {
                    self.product_type = $(ev.target).val();
                })

                self.$('.btn_check_codes').on('click', function (ev) {
                    framework.blockUI();
                    self.$(".exist_code_table_area").html('');//
                    self.$(".invalid_code_table_area").html('');//
                    var exist_node = '<table id="exist_code_table"></table>';
                    var not_exist_node = '<table id="invalid_code_table"></table>';
                    self.$(".exist_code_table_area").html($(exist_node));
                    self.$(".invalid_code_table_area").html($(not_exist_node));
                    self.$('.btn_import').prop('disabled', false);
                    new Model("web.planner")
                        .call('check_codes', [self.planner.id, self.copy_info])
                        .then(function (res) {
                            framework.unblockUI();
                            if (!res.error_msg) {
                                self.init2Tables(res);
                            } else {
                                self.do_warn("警告", res.error_msg)
                            }
                        }).always(function () {
                        framework.unblockUI();
                    });
                });
                self.$('.btn_import').prop('disabled', true);
                self.$('.btn_import').on('click', function (ev) {
                    if (!self.validate_codes) {
                        self.do_warn("警告", "请先检查料号");
                        return;
                    }
                    framework.blockUI();
                    new Model("web.planner")
                        .call('import_codes', [self.planner.id, self.validate_codes, self.product_type])
                        .then(function (res) {
                            console.log(res);
                            framework.unblockUI();
                            self.$('#success_count').html(res[0].success_count);
                            //if(res[0].not_found_list && res[0].not_found_list.length > 0){
                            self.initCategNotFoundTable(res[0].not_found_list);
                            //}

                            var next_page_id = self.get_next_page_id();
                            if (next_page_id) {
                                self._display_page(next_page_id);
                            }

                        }).always(function () {
                        framework.unblockUI();
                    });
                });
            }
        },
        init: function (parent, planner) {
            this._super(parent, planner);
            this.planner = planner;
            this.cookie_name = this.planner.planner_application + '_last_page';
            this.pages = [];
            this.menu_items = [];
        },
        start: function () {
            var self = this;
            self.$res.find('.o_planner_page').andSelf().filter('.o_planner_page').each(function (index, dom_page) {
                var page = new Page(dom_page, index);
                self.pages.push(page);
            });

            var $menu = self.render_menu();  // wil use self.$res
            self.$('.o_planner_menu ul').html($menu);
            self.menu_items = self.$('.o_planner_menu li');

            self.pages.forEach(function (page) {
                page.menu_item = self._find_menu_item_by_page_id(page.id);
            });
            self.$el.find('.o_planner_content_wrapper').append(self.$res);

            // update the planner_data with the new inputs of the view
            var actual_vals = self._get_values();
            self.planner.data = _.defaults(self.planner.data, actual_vals);
            // set the default value
            self._set_values(self.planner.data);
            // show last opened page
            self._display_page(self.pages[0].id);

            self.prepare_planner_event();
        },
        rerender_page: function (index) {//根据下标来确定重新渲染哪个页面
            var self = this;
            var pages = self.$res.find('.o_planner_page').andSelf().filter('.o_planner_page');
            var page = new Page(pages[index], index);
            page.menu_item = self._find_menu_item_by_page_id(page.id);
            self.pages[index] = page;
        },
        init2Tables: function (data) {
            var self = this;
            var columns = [[{
                field: 'title',
                title: '有效的料号信息',
                halign: "center",
                align: "center",
                'class': "font_35_header",
                colspan: 7,
            }], [{
                field: 'seq',
                title: '序号',
                formatter: function (value, row, index) {
                    return index + 1;
                }
            }, {
                field: 'default_code',
                title: '料号',
            }, {
                field: 'name',
                title: '品名',
            }, {
                field: 'product_specs',
                title: '规格',
            }, {
                field: 'inner_code',
                title: '国内简称',
            }, {
                field: 'inner_spec',
                title: '国内型号',
            }, {
                field: 'category_name',
                title: '产品类别',
                formatter: function (value, row, index) {
                    console.log(value);
                    return value[0][1];
                }
            }]];

            var invalid_columns = [[{
                field: 'title',
                title: '无效的料号',
                colspan: 3,
                halign: "center",
                align: "center",
                'class': "font_35_header",
            }], [{
                field: 'seq',
                title: '序号',
                formatter: function (value, row, index) {
                    return index + 1;
                }
            },
                {
                    field: 'default_code',
                    title: '料号',
                },
                {
                    field: 'reason',
                    title: '原因',
                    //formatter: function (value, row, index) {
                    //    return index + 1;
                    //}
                },
            ]]
            self.validate_codes = data.exist_codes;
            var exist_options = self.options_init(columns, self.validate_codes);
            var invalid_codes_options = self.options_init(invalid_columns, data.error_codes);
            self.$('#exist_code_table').bootstrapTable(exist_options);
            self.$('#invalid_code_table').bootstrapTable(invalid_codes_options);


        },
        initCategNotFoundTable: function (data) {
            var self = this;
            var columns = [[{
                field: 'title',
                title: '找不到对应分类的料号信息',
                halign: "center",
                align: "center",
                'class': "font_35_header",
                colspan: 5,
            }], [{
                field: 'seq',
                title: '序号',
                formatter: function (value, row, index) {
                    return index + 1;
                }
            }, {
                field: 'default_code',
                title: '料号',
            }, {
                field: 'name',
                title: '品名',
            }, {
                field: 'product_specs',
                title: '规格',
            }, {
                field: 'category_name',
                title: '产品类别',
                formatter: function (value, row, index) {
                    console.log(value);
                    return value[0][1];
                }
            }]];
            var categ_not_found = self.options_init(columns, data);
            self.$('#categ_not_found_table').bootstrapTable(categ_not_found);
        },
        options_init: function (coloums, data) {
            return {
                cache: false,
                //sortable: true,
                //showToggle: true,
                //search: true,
                striped: true,
                //showColumns: true,
                //showExport: true,
                iconsPrefix: 'fa', // glyphicon of fa (font awesome)
                //exportTypes: ['excel'],
                //exportOptions: {
                //    excelstyles: ['background-color', 'color', 'font-weight', 'border-top', 'border-bottom', 'border-left', 'border-right'],
                //},
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
            }
        },
        change_to_next_page: function (ev) {
            console.log(this);
            var self = this;
            if (self.planner['planner_application'] == 'planner_copy_code') {
                if (!self.copy_info || !self.copy_info.company) {
                    self.do_warn("警告", "请选择子公司");
                    return;
                }
                //料号
                if (self.currently_shown_page.id == self.pages[1].id) {//
                    var codes = self.$("#default_codes").val();
                    var code_list = codes.trim().split("\n");
                    if (codes && code_list) {
                        self.copy_info = _.extend(self.copy_info, {
                            default_codes: code_list
                        })
                        console.log(self.copy_info);
                    } else {
                        self.do_warn("警告", "请输入料号");
                        return;
                    }
                    if (!self.product_type) {
                        self.do_warn("警告", "请选择产品类型");
                        return;
                    }

                }

            }
            var next_page_id = this.get_next_page_id();

            ev.preventDefault();

            if (next_page_id) {
                this._display_page(next_page_id);
            }
        },
        change_page: function (ev) {
            var self = this;
            ev.preventDefault();
            var page_id = $(ev.currentTarget).attr('href').replace('#', '');
            if (page_id == self.pages[0].id || page_id == self.pages[1].id) {
                self.rerender_page(2);
            }
            this._display_page(page_id);
            //ev.preventDefault();
        },
        _display_page: function (page_id) {
            this._super(page_id);
            if (page_id == this.pages[2].id) {
                var next_button = this.$('a.btn-next');
                next_button.hide();
            }
        }

    });
    var Page = core.Class.extend({
        init: function (dom, page_index) {
            var $dom = $(dom);
            this.dom = dom;
            this.hide_from_menu = $dom.attr('hide-from-menu');
            this.hide_mark_as_done = $dom.attr('hide-mark-as-done');
            this.done = false;
            this.menu_item = null;
            this.title = $dom.find('[data-menutitle]').data('menutitle');

            var page_id = this.title.replace(/\s/g, '') + page_index;
            this.set_page_id(page_id);
        },
        set_page_id: function (id) {
            this.id = id;
            $(this.dom).attr('id', id);
        },
        toggle_done: function () {
            this.done = !this.done;
        },
        get_category_name: function (category_selector) {
            var $page = $(this.dom);
            return $page.parents(category_selector).attr('menu-category-id');
        },
    });

    return {
        CodeCopyPlannerDialog: CodeCopyPlannerDialog
    }
});
