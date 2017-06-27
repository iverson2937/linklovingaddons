odoo.define('linkloving_core.multi_selection', function (require) {
    "use strict";


    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var ListView = require('web.ListView');
    var ajax = require('web.ajax');
    var crash_manager = require('web.crash_manager');
    var data = require('web.data');
    var datepicker = require('web.datepicker');
    var dom_utils = require('web.dom_utils');
    var Priority = require('web.Priority');
    var ProgressBar = require('web.ProgressBar');
    var Dialog = require('web.Dialog');
    var common = require('web.form_common');
    var formats = require('web.formats');
    var framework = require('web.framework');
    var pyeval = require('web.pyeval');
    var session = require('web.session');
    var utils = require('web.utils');
    var form_relational = require('web.form_relational');

    var QWeb = core.qweb;
    var _t = core._t;

    ListView.Groups.include({
        render: function (post_render) {
            var self = this;
            var $el = $('<tbody>');
            this.elements = [$el[0]];
            console.log(this.view.visible_columns);


            return this.datagroup.list(
                _(this.view.visible_columns).chain()
                    .filter(function (column) {
                        return column.tag === 'field';
                    })
                    .pluck('name').value(),
                function (groups) {
                    console.log(groups)

                    $el[0].appendChild(
                        self.render_groups(groups));
                    if (post_render) {
                        post_render();
                    }
                }, function (dataset) {
                    return self.render_dataset(dataset).then(function (list) {
                        self.children[null] = list;
                        self.elements =
                            [list.$current.replaceAll($el)[0]];
                        self.setup_resequence_rows(list, dataset);
                    }).always(function () {
                        if (post_render) {
                            post_render();
                        }
                        self.view.trigger('view_list_rendered');
                    });
                });
        },

    });

    var X2ManyList = ListView.List.extend({
        pad_table_to: function (count) {
            if (!this.view.is_action_enabled('create') || this.view.x2m.get('effective_readonly')) {
                this._super(count);
                return;
            }

            this._super(count > 0 ? count - 1 : 0);

            var self = this;
            var columns = _(this.columns).filter(function (column) {
                return column.invisible !== '1';
            }).length;
            if (this.options.selectable) {
                columns++;
            }
            if (this.options.deletable) {
                columns++;
            }


            var $cell = $('<td>', {
                colspan: columns,
                'class': 'o_form_field_x2many_list_row_add'
            }).append(
                $('<a>', {href: '#'}).text(_t("add products"))
                    .click(function (e) {
                        e.preventDefault();
                        e.stopPropagation();
                        var def;
                        if (self.view.editable()) {
                            // FIXME: there should also be an API for that one
                            if (self.view.editor.form.__blur_timeout) {
                                clearTimeout(self.view.editor.form.__blur_timeout);
                                self.view.editor.form.__blur_timeout = false;
                            }
                            def = self.view.save_edition();
                        }
                        $.when(def).done(self.view.do_add_record.bind(self));
                    }));

            var $padding = this.$current.find('tr:not([data-id]):first');
            var $newrow = $('<tr>').append($cell);
            if ($padding.length) {
                $padding.before($newrow);
            } else {
                this.$current.append($newrow);
            }
        },
    });


    var OLMany2ManyListView = ListView.extend({

        init: function () {
            this.ol = true;
            this._super.apply(this, arguments);
            this.options = _.extend(this.options, {
                ListType: X2ManyList,
            });
            this.on('edit:after', this, this.proxy('_after_edit'));
            this.on('save:before cancel:before', this, this.proxy('_before_unedit'));
        },
        do_add_record: function () {
            var self = this;

            new common.SelectCreateDialog(this, {
                res_model: this.model,
                domain: new data.CompoundDomain(this.x2m.build_domain(), ["!", ["id", "in", this.x2m.dataset.ids]]),
                context: this.x2m.build_context(),
                title: _t("Add: ") + this.x2m.string,
                alternative_form_view: this.x2m.field.views ? this.x2m.field.views.form : undefined,
                no_create: this.x2m.options.no_create || !this.is_action_enabled('create'),
                on_selected: function (element_ids) {
                    return self.x2m.data_link_multi(element_ids).then(function () {
                        self.x2m.reload_current_view();
                    });
                }
            }).open();
        },
        do_activate_record: function (index, id) {
            var self = this;
            var pop = new common.FormViewDialog(this, {
                res_model: this.model,
                res_id: id,
                context: this.x2m.build_context(),
                title: _t("Open: ") + this.x2m.string,
                alternative_form_view: this.x2m.field.views ? this.x2m.field.views.form : undefined,
                readonly: !this.is_action_enabled('edit') || self.x2m.get("effective_readonly"),
            }).open();
            pop.on('write_completed', self, function () {
                self.dataset.evict_record(id);
                self.reload_content();
            });
        },
        do_button_action: function (name, id, callback) {
            var self = this;
            var _sup = _.bind(this._super, this);
            if (!this.x2m.options.reload_on_button) {
                return _sup(name, id, callback);
            } else {
                return this.x2m.view.save().then(function () {
                    return _sup(name, id, function () {
                        self.x2m.view.reload();
                    });
                });
            }
        },
        _after_edit: function () {
            this.editor.form.on('blurred', this, this._on_blur_many2many);
        },
        _before_unedit: function () {
            this.editor.form.off('blurred', this, this._on_blur_many2many);
        },
        _on_blur_many2many: function () {
            return this.save_edition().done(function () {
                if (self._dataset_changed) {
                    self.dataset.trigger('dataset_changed');
                }
            });
        },
        is_valid: function () {
            if (!this.fields_view || !this.editable()) {
                return true;
            }
            if (_.isEmpty(this.records.records)) {
                return true;
            }
            var fields = this.editor.form.fields;
            var current_values = {};
            _.each(fields, function (field) {
                field._inhibit_on_change_flag = true;
                field.__no_rerender = field.no_rerender;
                field.no_rerender = true;
                current_values[field.name] = field.get('value');
            });
            var cached_records = _.filter(this.dataset.cache, function (item) {
                return !_.isEmpty(item.values) && !item.to_delete;
            });
            var valid = _.every(cached_records, function (record) {
                _.each(fields, function (field) {
                    var value = record.values[field.name];
                    field._inhibit_on_change_flag = true;
                    field.no_rerender = true;
                    field.set_value(_.isArray(value) && _.isArray(value[0]) ? [COMMANDS.delete_all()].concat(value) : value);
                });
                return _.every(fields, function (field) {
                    field.process_modifiers();
                    field._check_css_flags();
                    return field.is_valid();
                });
            });
            _.each(fields, function (field) {
                field.set('value', current_values[field.name], {silent: true});
                field._inhibit_on_change_flag = false;
                field.no_rerender = field.__no_rerender;
            });
            return valid;
        },
        render_pager: function ($node, options) {
            console.log('ddd');
            options = _.extend(options || {}, {
                single_page_hidden: true,
            });
            this._super($node, options);
        },
        display_nocontent_helper: function () {
            return false;
        },

    });

    var FieldMany2Many = core.form_widget_registry.get('many2many');


    var OLTreeView = FieldMany2Many.extend({

        init: function () {
            console.log('sssssssssss');
            this._super.apply(this, arguments);
            this.x2many_views = {
                list: OLMany2ManyListView,
                kanban: core.view_registry.get('many2many_kanban'),
            };
        },

    });
    core.form_widget_registry.add('ol_tree_view', OLTreeView);

    return OLTreeView;

});