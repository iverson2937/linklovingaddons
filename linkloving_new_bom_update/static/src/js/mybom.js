/**
 * Created by 123 on 2017/7/10.
 */
odoo.define('linkloving_new_bom_update.new_bom_update', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var View = require('web.View');
    var Dialog = require('web.Dialog');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var SearchView = require('web.SearchView');
    var data = require('web.data');
    var _t = core._t;
    var del_ids = [];


    var NewBomUpdate = Widget.extend({
        template: 'my_bom_container',
        events: {
            'click .add_bom_data': 'add_bom_data_fn',
            'click .product_name': 'product_name_fn',
            'click .new_bom_modify_submit': 'new_bom_modify_submit_fn',
            'click .new_bom_modify_direct': 'new_bom_modify_submit_fn',
            'click .new_product_edit': 'edit_bom_line_fn',
            'click .new_product_delete': 'delete_bom_line_fn',
            'click .submit_to_approval': 'submit_to_approval_fn'
        },


        update_cp: function () {
            this.update_control_panel({
                breadcrumbs: this.action_manager.get_breadcrumbs(),
                cp_content: {
                    $buttons: this.$buttons,
                    $searchview: this.searchview.$el,
                    $searchview_buttons: this.$searchview_buttons,
                },
                searchview: this.searchview,
            });
        },

        submit_to_approval_fn: function (e) {
            var tar = this;
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var bom_id = $("#treeMenu").data("bom-id");
            var is_show_action_deny = $(target).data("action-deny");

            var is_final_one = false;

            if (parseInt(bom_id))
                is_final_one = true;
            else
                is_final_one = false;

            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'review.process.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {
                    'default_bom_id': parseInt(bom_id),
                    'is_show_action_deny': 'false',
                    'review_type': 'bom_review',
                    'is_final_one': is_final_one
                },
                'target': "new",
            };
            this.do_action(action);
        },

        //另存为的动作
        new_bom_modify_submit_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;

            var self = this;
            self.changes_back = [];
            self.xNodes.forEach(function (v, i) {
                if (self.xNodes[i].modify_type) {
                    if (self.xNodes[i].modify_type == 'delete') {
                        if ($.inArray(self.xNodes[i].id, del_ids) != -1) {
                            self.changes_back.push(self.xNodes[i]);
                        }
                    } else {
                        self.changes_back.push(self.xNodes[i]);
                    }

                }
            })
            console.log(self.changes_back);
            del_ids = [];
            if (self.changes_back.length == 0) {
                var message = ("您没有做任何操作");
                var def = $.Deferred();
                var options = {
                    title: _t("Warning"),
                    //确认删除的操作
                    confirm_callback: function () {
                        self.$el.removeClass('oe_form_dirty');
                        this.on('closed', null, function () { // 'this' is the dialog widget
                            def.resolve();
                        });
                    },
                    cancel_callback: function () {
                        def.reject();
                    },
                };
                var dialog = Dialog.confirm(this, message, options);
                dialog.$modal.on('hidden.bs.modal', function () {
                    def.reject();
                });
                return def;
            }


            if ($(target).hasClass("new_bom_modify_direct")) {
                var btn_update = true;
            } else {
                var btn_update = false;
            }
            var top_bom_id = $("#treeMenu").data("bom-id");


            if (!btn_update) {
                $(".o_content").html("");
                var action = {
                    name: "BOM",
                    type: 'ir.actions.act_window',
                    res_model: 'bom.update.wizard',
                    view_type: 'form',
                    view_mode: 'tree,form',
                    context: {'back_datas': this.changes_back, "bom_id": top_bom_id, "update": btn_update},
                    views: [[false, 'form']],
                    // res_id: act_id,
                    target: "new"
                };
                this.do_action(action);
            } else {
                new Model("bom.update.wizard").call("bom_line_save", [this.changes_back, top_bom_id]).then(function (result) {
                    window.location.reload(true);
                })
            }

        },


        //获得子孙
        getchildren: function (x, i) {
            var self = this;
            self.childrenid.push(parseInt(x));
            for (i; i < self.xNodes.length; i++) {
                if (self.xNodes[i].pId == x) {
                    self.getchildren(self.xNodes[i].id, i);
                }
            }
        },

        //删除的动作
        delete_bom_line_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var del_id = $(target).parents("tr").attr("data-tt-id");
            del_ids.push(parseInt(del_id))
            var self = this;

            self.parentsid = [];
            var message = ("确定删除这条记录？");
            var def = $.Deferred();
            var options = {
                title: _t("Warning"),
                //确认删除的操作
                confirm_callback: function () {
                    self.childrenid = [];
                    self.getchildren(del_id, 0);

                    self.xNodes.forEach(function (v, i) {
                        self.childrenid.forEach(function (ele, j) {
                            if (self.xNodes[i].id == self.childrenid[j]) {
                                self.xNodes[i].modify_type = 'delete';
                                self.parentsid = [];
                                self.getParents($("#treeMenu tr[data-tt-id=" + self.xNodes[i].id + "]"));
                                self.parentsid.shift();
                                self.xNodes[i].parents = self.parentsid;
                            }
                        })
                    });
                    $("#treeMenu").html("");
                    var heads = ["名字", "规格", "数量", "工序", "添加", "编辑", "删除"];
                    $.TreeTable("treeMenu", heads, self.xNodes);
                    $("#treeMenu").treetable("node", $("#treeMenu").attr("data-bom-id")).toggle();


                    self.$el.removeClass('oe_form_dirty');
                    this.on('closed', null, function () { // 'this' is the dialog widget
                        def.resolve();
                    });
                },
                cancel_callback: function () {
                    def.reject();
                },
            };
            var dialog = Dialog.confirm(this, message, options);
            dialog.$modal.on('hidden.bs.modal', function () {
                def.reject();
            });

            return def;
        },

        //点击产品名弹出相应的产品页面
        product_name_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var action = {
                name: "产品",
                type: 'ir.actions.act_window',
                res_model: 'product.template',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: parseInt($(target).attr("data-pt-id")),
                target: "new"
            };
            this.do_action(action);
        },
        //编辑按钮的点击事件
        edit_bom_line_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var product_id = $(target).parents("tr").attr("data-product-id");
            var pId = $(target).parents("tr").attr("data-tt-id");
            var qty = parseFloat($(target).parents("tr").data("qty"));
            var to_add = $(target).parents("tr").data("to-add");
            var isTrueSet = (to_add == true);
            var product_specs = $(target).parents("tr").data("product-specs");
            var name = $(target).parents("tr").data("name");
            var product_spec = $(target).parents("tr").data("product_spec");
            var default_name = $(target).parents("tr").find(".product_name").html();
            var process_id = $(target).parents("tr").data("process-id");
            var product_type = $(target).parents("tr").data("product-type")
            if (typeof(process_id) == "undefined") {
                process_id = false
            }


            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'add.bom.line.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                context: {
                    'default_product_id': parseInt(product_id),
                    'default_qty': qty,
                    'edit': true,
                    'default_to_add': isTrueSet,
                    'default_product_specs': product_specs,
                    'pid': pId,
                    'default_name': default_name,
                    // 'default_process_id': process_id,
                    'default_product_type': product_type
                },
                target: "new"
            };
            this.do_action(action);
            var my = this;
            my.flag = true;
            my.parentsid = [];
            my.getParents($(target).parents("tr"));
            //删除第一个
            my.parentsid.shift();

            $(document).ajaxComplete(function (event, xhr, settings) {
                var data = null;
                if (settings.data) {
                    var data = JSON.parse(settings.data);
                }
                if (data.params && data.params.model == 'add.bom.line.wizard') {
                    if (data.params.method == 'action_edit' && my.flag == true) {
                        my.flag = false;
                        for (var i = 0; i < my.xNodes.length; i++) {
                            if (my.xNodes[i].id == xhr.responseJSON.result.pid) {
                                var a_r = xhr.responseJSON.result;
                                //table树重新渲染
                                my.xNodes[i].name = a_r.new_name;
                                my.xNodes[i].id = a_r.id;
                                my.xNodes[i].add = 2;
                                if (my.xNodes[i].modify_type) {
                                    if (my.xNodes[i].modify_type == 'add') {
                                        my.xNodes[i].modify_type = 'add';
                                    } else {
                                        my.xNodes[i].modify_type = 'edit';
                                    }
                                } else {
                                    my.xNodes[i].modify_type = 'edit';
                                }
                                my.xNodes[i].parents = my.parentsid;
                                my.xNodes[i].input_changed_value = a_r.to_add;
                                my.xNodes[i].productid = a_r.name[0][0];
                                my.xNodes[i].qty = a_r.qty;
                                my.xNodes[i].name = a_r.new_name;
                                my.xNodes[i].name = a_r.new_name;
                                my.xNodes[i].product_specs = a_r.product_specs;
                                my.xNodes[i].to_add = a_r.to_add;
                                my.xNodes[i].process_id = a_r.process_id[0];
                                my.xNodes[i].td = [a_r.product_specs, a_r.qty, a_r.process_id[1],
                                    a_r.product_type == 'raw material' ? "" : "<span class='fa fa-plus-square-o add_bom_data'></span>",
                                    "<span class='fa fa-edit new_product_edit'></span>",
                                    "<span class='fa fa-trash-o new_product_delete'></span>"];
                                $("#treeMenu").html("");
                                var heads = ["名字", "规格", "数量", "工序", "添加", "编辑", "删除"];
                                $.TreeTable("treeMenu", heads, my.xNodes);
                                $("#treeMenu").treetable("node", $("#treeMenu").attr("data-bom-id")).toggle();

                                //传给后台的数据
                                // var c = {
                                //     modify_type: "edit",
                                //     qty: xhr.responseJSON.result.qty,
                                //     product_id: xhr.responseJSON.result.name[0][0],
                                //     input_changed_value: xhr.responseJSON.result.to_add,
                                //     parents: my.parentsid,
                                //     product_specs: xhr.responseJSON.result.product_specs
                                // }
                                // my.changes_back.push(c);
                                break;
                            }
                        }
                    }
                }
            })

        },
        //添加按钮的点击事件
        add_bom_data_fn: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var pId = $(target).parents("tr").attr("data-tt-id");
            var my = this;
            my.flag = true;
            var action = {
                name: "详细",
                type: 'ir.actions.act_window',
                res_model: 'add.bom.line.wizard',
                view_type: 'form',
                view_mode: 'tree,form',
                context: {'pid': pId, 'add': true},
                views: [[false, 'form']],
                target: "new"
            };
            this.do_action(action);

            //清空之前的数组，再执行查找父级id的函数
            my.parentsid = [];
            my.getParents($(target).parents("tr"));

            self.$(document).ajaxComplete(function (event, xhr, settings) {
                var data = JSON.parse(settings.data);
                if (data.params.model == 'add.bom.line.wizard') {
                    if (data.params.method == 'action_add' && my.flag == true) {
                        my.flag = false;
                        var a_r = xhr.responseJSON.result;
                        //table树重新渲染
                        var s = {
                            id: a_r.id,
                            pId: a_r.pid,
                            add: 1,
                            modify_type: "add",
                            qty: a_r.qty,
                            productid: a_r.name[0][0],
                            input_changed_value: a_r.to_add,
                            parents: my.parentsid,
                            ptid: a_r.product_tmpl_id,
                            name: a_r.new_name,
                            process_id: a_r.process_id[0],
                            product_type: a_r.product_type,
                            td: [a_r.product_specs, a_r.qty, a_r.process_id[1],
                                a_r.product_type == 'raw material' ? "" : "<span class='fa fa-plus-square-o add_bom_data'></span>", "<span class='fa fa-edit new_product_edit'></span>",
                                "<span class='fa fa-trash-o new_product_delete'></span>"]
                        };
                        my.xNodes.push(s);
                        $("#treeMenu").html("");
                        var heads = ["名字", "规格", "数量", "工序", "添加", "编辑", "删除"];
                        $.TreeTable("treeMenu", heads, my.xNodes);
                        $("#treeMenu").treetable("node", $("#treeMenu").attr("data-bom-id")).toggle();

                        // var c = {
                        //     modify_type: "add",
                        //     qty: xhr.responseJSON.result.qty,
                        //     product_id: xhr.responseJSON.result.name[0][0],
                        //     input_changed_value: xhr.responseJSON.result.to_add,
                        //     parents: my.parentsid
                        // }
                        // my.changes_back.push(c);
                    }
                }
            })

        },


        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.bom_id = action.bom_id;
            this.dataset = new data.DataSetSearch(this, 'mail.message');
            this.domain = [];
            this.is_show = action.is_show;
            if (action.bom_id) {
                this.bom_id = action.bom_id;
            } else {
                this.bom_id = action.params.active_id;
            }
            var self = this;
            self.xNodes = [];
            self.flag = true;
            //返回给后台的数组
            self.changes_back = [];
            //存储父级id的数组
            self.parentsid = [];
            self.childrenid = [];
            // $(".o_content").css("background", "white")
        },

        //查找父级的递归函数
        getParents: function ($obj) {
            var self = this;
            self.parentsid.push($obj.attr("data-tt-id"));
            if ($obj.attr("data-tt-parent-id")) {
                var p = $obj.attr("data-tt-parent-id");
                $obj = $obj.prevAll("tr[data-tt-id=" + p + "]");
                self.getParents($obj);
            } else {
                return;
            }
        },
        on_search: function () {

        },
        start: function () {
            var self = this;
            if (this.is_show === false) {
                this.$el.find('.new_bom_modify_submit').hide();
                this.$el.find('.new_bom_modify_direct').hide();
            }
            var options = {
                $buttons: $("<div>"),
                action: this.action,
                disable_groupby: true,
            };

            this.searchview = new SearchView(this, this.dataset, this.fields_view, options);
            this.searchview.on('search_data', this, this.on_search);

            if (this.bom_id) {
                return new Model("mrp.bom")
                    .call("get_bom", [this.bom_id])
                    .then(function (result) {
                        console.log(result)
                        var tNodes = [];
                        //获取数据存入数组

                        function get_datas(obj) {
                            for (var i = 0; i < obj.length; i++) {
                                if (self.is_show === false) {
                                    var td1 = [obj[i].product_specs, obj[i].qty, obj[i].process_id[1]];

                                } else {
                                    var td1 = [obj[i].product_specs, obj[i].qty, obj[i].process_id[1], obj[i].product_type == 'raw material' ? "" : "<span class='fa fa-plus-square-o add_bom_data'></span>",
                                        "<span class='fa fa-edit new_product_edit'></span>", "<span class='fa fa-trash-o new_product_delete'></span>"];
                                }
                                var s = {
                                    id: obj[i].id,
                                    pId: obj[i].parent_id,
                                    ptid: obj[i].product_tmpl_id,
                                    productid: obj[i].product_id,
                                    qty: obj[i].qty,
                                    is_highlight: obj[i].is_highlight,
                                    name: obj[i].name,
                                    product_type: obj[i].product_type,
                                    process_id: obj[i].process_id[0],
                                    td: td1,
                                    index: i + 1
                                };
                                tNodes.push(s);
                                if (obj[i].bom_ids.length > 0) {
                                    get_datas(obj[i].bom_ids);
                                }
                            }
                        }

                        if (self.is_show === false) {
                            var td2 = [result.product_specs, '', result.process_id[1]]
                        } else {
                            var td2 = [result.product_specs, '', result.process_id[1], "<span class='fa fa-plus-square-o add_bom_data'></span>", "", ""]
                        }

                        get_datas(result.bom_ids);
                        tNodes.push({
                            id: result.bom_id,
                            pId: 0,
                            qty: result.qty,
                            product_specs: result.product_specs,
                            to_add: result.to_add,
                            ptid: result.product_tmpl_id,
                            productid: result.product_id,
                            name: result.name,
                            product_type: result.product_type,
                            process_id: result.process_id[0],
                            td: td2,
                            index: ''
                        });
                        self.xNodes = tNodes;
                        var heads = ["名字", "规格", "数量", "工序", "添加", "编辑", "删除"];

                        setTimeout(function () {
                            $("#treeMenu").attr("data-bom-id", result.bom_id);
                            $.TreeTable("treeMenu", heads, tNodes);
                            $("#treeMenu").treetable("node", result.bom_id).toggle();
                            if (result.state == 'new' || result.state == 'draft' || result.state == 'updated'||result.state=='deny') {
                                if (!this.is_show) {
                                    $(".new_bom_btns_wrap").append('<button class="btn btn-primary btn-sm submit_to_approval">提交审核</button>')
                                }

                            }
                        }, 200)
                    })
            }
            ;

        }
    });
    core.action_registry.add('new_bom_update', NewBomUpdate);

    return NewBomUpdate;
});
$(document).ajaxComplete(function (event, xhr, settings) {

});