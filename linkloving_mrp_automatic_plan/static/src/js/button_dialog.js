odoo.define('linkloving_mrp_automatic_plan.button_dialog', function (require) {
    "use strict";

    var ControlPanel = require('web.ControlPanel');
    var core = require('web.core');
    var data = require('web.data');
    var Dialog = require('web.Dialog');
    var common = require('web.form_common');
    var ListView = require('web.ListView');
    require('web.ListEditor'); // one must be sure that the include of ListView are done (for eg: add start_edition methods)
    var Model = require('web.DataModel');
    var session = require('web.session');
    var utils = require('web.utils');
    var ViewManager = require('web.ViewManager');
    var View = require('web.View');
    var data_manager = require('web.data_manager');

    var _t = core._t;

    var ButtonDialog = View.include({
        do_execute_action: function (action_data, dataset, record_id, on_closed) {
            var self = this;
            if (action_data.type == 'formview_dialog') {
                var model_obj = new Model(dataset.model);
                model_obj.call(action_data.name, [record_id]).then(function (view) {
                    console.log(view)
                    view['context'] = action_data.context;
                    var pop = new NewFormViewDialog(self, view).open();
                    pop.on("record_saved", self, function () {
                        self.reload();
                        console.log("reload");
                    })
                });
                return dataset.exec_workflow(record_id, action_data.name);
            }

            return this._super(action_data, dataset, record_id, on_closed);
        }
    });

    var NewFormViewDialog = common.ViewDialog.extend({
        init: function (parent, options) {
            var self = this;

            var multi_select = !_.isNumber(options.res_id) && !options.disable_multiple_selection;
            var readonly = _.isNumber(options.res_id) && options.readonly;

            if (!options || !options.buttons) {
                options = options || {};
                options.buttons = [
                    {
                        text: (readonly ? "取消" : "取消"),
                        classes: "btn-default o_form_button_cancel",
                        close: true,
                        click: function () {
                            self.view_form.trigger('on_button_cancel');
                        }
                    }
                ];

                if (true) {
                    options.buttons.splice(0, 0, {
                        text: "确定" + ((multi_select) ? " " + _t(" & Close") : ""),
                        classes: "btn-primary",
                        click: function () {
                            self.view_form.onchanges_mutex.def.then(function () {
                                if (!self.view_form.warning_displayed) {
                                    $.when(self.view_form.save()).done(function () {
                                        self.view_form.reload_mutex.exec(function () {
                                            self.trigger('record_saved');
                                            self.close();
                                        });
                                    }).fail(function () {
                                        setTimeout(function () {
                                            self.$footer.children().prop("disabled", false);
                                        }, 1000);
                                    });
                                }
                            });
                        }
                    });

                    if (false) {
                        options.buttons.splice(1, 0, {
                            text: _t("Save & New"), classes: "btn-primary", click: function () {
                                $.when(self.view_form.save()).done(function () {
                                    self.view_form.reload_mutex.exec(function () {
                                        self.view_form.on_button_new();
                                    });
                                });
                            }
                        });
                    }
                }
            }

            this._super(parent, options);
        },

        open: function () {
            var self = this;
            var _super = this._super.bind(this);
            this.init_dataset();

            if (this.res_id) {
                this.dataset.ids = [this.res_id];
                this.dataset.index = 0;
            } else {
                this.dataset.index = null;
            }
            var options = _.clone(this.options.form_view_options) || {};
            if (this.res_id !== null) {
                options.initial_mode = this.options.readonly ? "view" : "edit";
            }
            _.extend(options, {
                $buttons: this.$buttons,
            });
            var FormView = core.view_registry.get('form');
            var fields_view_def;
            if (this.options.alternative_form_view) {
                fields_view_def = $.when(this.options.alternative_form_view);
            } else {
                fields_view_def = data_manager.load_fields_view(this.dataset, this.options.view_id, 'form', false);
            }
            fields_view_def.then(function (fields_view) {
                self.view_form = new FormView(self, self.dataset, fields_view, options);
                var fragment = document.createDocumentFragment();
                self.view_form.appendTo(fragment).then(function () {
                    self.view_form.do_show().then(function () {
                        _super().$el.append(fragment);
                        self.view_form.autofocus();
                    });
                });
            });

            return this;
        },
    });
    var MyDialog = Dialog.include({

        set_buttons: function (buttons) {
            var self = this;
            var res = this._super(buttons);

            _.each(self.$footer.children(), function (b) {
                $(b).on('click', function (e) {
                    $(b).prop('disabled', true);
                });
                self.$footer.append($(b));
            });
            return res;
        },
    });
    //disable_button: function () {
    //    console.log("eeeeeeee")
    //    this.$('.oe_form_buttons').add(this.$buttons).find('button').addClass('o_disabled').prop('disabled', true);
    //    this.is_disabled = true;
    //},

    return {
        ButtonDialog: ButtonDialog,
        NewFormViewDialog: NewFormViewDialog,
        MyDialog: MyDialog,
    };

});
