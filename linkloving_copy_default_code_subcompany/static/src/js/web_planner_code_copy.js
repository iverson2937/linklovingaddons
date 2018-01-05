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
                self.$(':radio').on('click', function (ev) {
                    console.log(ev);
                    var copyinfo = {
                        company: parseInt($(ev.target).val()),
                    };
                    self.copy_info = copyinfo;

                });
                self.$('.btn_check_codes').on('click', function (ev) {
                    new Model("web.planner")
                        .call('check_codes', [self.planner.id, self.copy_info])
                        .then(function (res) {
                            if (!res.error_msg) {
                                self.init2Tables(res);
                            } else {
                                self.do_warn("警告", res.error_msg);
                            }
                        });
                })
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
        init2Tables: function (data) {
            var self = this;
            var columns = [[{
                field: 'title',
                title: '子系统的料号信息',
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
                field: 'categ_id',
                title: '产品类别',
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

            var exist_options = self.options_init(columns, data.exist_codes);
            var invalid_codes_options = self.options_init(invalid_columns, data.error_codes);
            self.$('#exist_code_table').bootstrapTable(exist_options);
            self.$('#invalid_code_table').bootstrapTable(invalid_codes_options);


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
                if (self.currently_shown_page.id == self.pages[1].id) {
                    var codes = self.$("#default_codes").val();
                    var code_list = codes.trim().split("\n");
                    if (code_list) {
                        self.copy_info = _.extend(self.copy_info, {
                            default_codes: code_list
                        })
                        console.log(self.copy_info);
                    } else {
                        self.do_warn("警告", "请输入料号");
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
            //ev.preventDefault();
            //var page_id = $(ev.currentTarget).attr('href').replace('#', '');
            //this._display_page(page_id);
        },
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
