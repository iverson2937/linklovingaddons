odoo.define('linkloving_crm.crm_tree_list_js', function (require) {

    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');


    var QWeb = core.qweb;
    var _t = core._t;

    var TreeList = Widget.extend({
        template: "TreeListView",
        events: {
            'click span.lead_update_submit': 'update_lead',
            'click span.lead_back_click': 'lead_back_fn',
            'click .show_time_begin': 'show_time_view',
            'click input.brand_check': 'on_click_version',


            // 'click .tree': 'init_show_time',
        },

        init: function (parent, action) {
            this._super.apply(this, arguments);
            var self = this;

            this.version_lists = new Set();
            this.data_view = action.products_data;
            this.leads_id = action.leads_id;
            this.models_view = action.model_lead_partner;
            this.LeadModel = new Model('crm.lead');


            // $(document).ready(function () {
            //     alert("第一种方法。");
            //
            //     if ($('.show_time_begin').length > 0) {
            //         alert(111);
            //     }
            //
            // });


        },
        start: function () {
            var self = this;
        },

        show_time_view: function () {
            var self = this;
            this.tree_view_jq(this.data_view);
            this.init_show_time();
            $('.show_time_begin').hide();

        },

        init_show_time: function () {
            $('.tree li:has(ul)').addClass('parent_li').find(' > span').attr('title', '展开');

            $('.tree ul li ul li').hide('fast');


            $('.tree li.parent_li > span').on('click', function (e) {
                var children = $(this).parent('li.parent_li').find(' > ul > li');
                if (children.is(":visible")) {
                    children.hide('fast');
                    $(this).attr('title', '展开').find(' > i').addClass('icon-plus-sign').removeClass('icon-minus-sign');
                } else {
                    children.show('fast');
                    $(this).attr('title', '关闭').find(' > i').addClass('icon-minus-sign').removeClass('icon-plus-sign');
                }
                e.stopPropagation();
            });
        },

        tree_view_jq: function (data) {


            for (var i = 0; i < data.length; i++) {
                var data2 = data[i];
                if (data[i].icon == "icon-th") {
                    $("#rootUL").append("<li data-name='" + data[i].code + "'><input type='checkbox' id='" + data[i].code + "' class='brand_check  " + data[i].type + "'/>&nbsp;&nbsp;<span><i class='" + data[i].icon + "'></i> " + data[i].name + "</span></li>");
                } else {
                    var children = $("li[data-name='" + data[i].parentCode + "']").children("ul");
                    if (children.length == 0) {
                        $("li[data-name='" + data[i].parentCode + "']").append("<ul></ul>")
                    }
                    $("li[data-name='" + data[i].parentCode + "'] > ul").append(
                        "<li data-name='" + data[i].code + "'>" +
                        "<input type='checkbox' id='" + data[i].code + "' class='brand_check  " + data[i].type + "'/>" +
                        "&nbsp;&nbsp;" +
                        "<span>" +
                        "<i class='" + data[i].icon + "'></i> " +
                        data[i].name +
                        "</span>" +
                        "</li>")
                }
                for (var j = 0; j < data[i].child.length; j++) {
                    var child = data[i].child[j];
                    var children = $("li[data-name='" + child.parentCode + "']").children("ul");
                    if (children.length == 0) {
                        $("li[data-name='" + child.parentCode + "']").append("<ul></ul>")
                    }
                    $("li[data-name='" + child.parentCode + "'] > ul").append(
                        "<li data-name='" + child.code + "'>" +
                        "<input type='checkbox' id='" + child.code + "' class='brand_check  " + child.type + "'/>" +
                        "&nbsp;&nbsp;" +
                        "<span>" +
                        "<i class='" + child.icon + "'></i> " +
                        child.name +
                        "</span>" +
                        "</li>")
                    var child2 = data[i].child[j].child;
                    // tree(child2)
                    this.tree_view_jq(child2)
                }
                // tree(data[i]);
                this.tree_view_jq(data[i]);
            }

        },
        delete_node: function (data) {
            var self = this;
            if (data.tagName == 'LI') {

                if (data.firstChild.checked) {

                    if (data.parentNode.parentNode.tagName == 'LI') {
                        // console.log('处理三层情况')

                        var series_boxes_three = data.parentNode.parentNode.getElementsByClassName('series');
                        for (var i = 0; i < series_boxes_three.length; i++) {
                            if (series_boxes_three[i].checked)
                                self.version_lists.add(series_boxes_three[i].id);
                        }
                        self.version_lists.delete(data.parentNode.parentNode.firstChild.id);
                        data.parentNode.parentNode.firstChild.checked = false;
                    }
                    // console.log('处理两层 上层选中')
                    var input_class = ''
                    if (data.firstChild.className == 'brand_check  series') {
                        // console.log('删除系列 保存除此之外的所有型号')
                        input_class = 'version';
                    }
                    if (data.firstChild.className == 'brand_check  brand') {
                        // console.log('删除品牌 保存系列 除此系列')
                        input_class = 'series';
                    }
                    var series_boxes = data.getElementsByClassName(input_class)
                    for (var i = 0; i < series_boxes.length; i++) {
                        if (series_boxes[i].checked)
                            self.version_lists.add(series_boxes[i].id);
                    }
                    self.version_lists.delete(data.firstChild.id);
                    data.firstChild.checked = false;
                } else {
                    // console.log('上层没选')
                }
            }
        },

        on_click_version: function (e) {
            var self = this;

            if (e.target.nextElementSibling.nextElementSibling != null) {
                // console.log('选择系列下面所有')
                var boxes = e.target.nextElementSibling.nextElementSibling.getElementsByClassName('brand_check')
                if (e.target.checked) {
                    self.version_lists.add(e.target.id);
                }
                else {
                    self.delete_node(e.target.parentNode.parentNode.parentNode);
                    self.version_lists.delete(e.target.id);
                }
                for (var i = 0; i < boxes.length; i++) {
                    self.version_lists.delete(boxes[i].id);
                    boxes[i].checked = e.target.checked ? true : false;
                }
            } else {
                // console.log('单个添加型号')
                if (e.target.checked) {
                    // console.log('单一添加')
                    self.version_lists.add(e.target.id);
                } else {
                    // console.log('单一删除')
                    self.delete_node(e.target.parentNode.parentNode.parentNode);
                    self.version_lists.delete(e.target.id);
                }
            }
            var data_list1 = new Array();
            self.version_lists.forEach(function (item) {
                data_list1.splice(0, 0, item)
            });
            console.log('此刻已选型号为：' + data_list1)
        },


        update_lead: function () {
            var self = this;
            var lead_data_list = new Array();
            self.version_lists.forEach(function (item) {
                lead_data_list.splice(0, 0, parseInt(item))
            });
            self.LeadModel.call('add_partner_to_lead', [], {
                id_one: self.leads_id,
                version_list: lead_data_list,
                models_view: self.models_view,
            }).then(function (msgs) {
                if (msgs == 'ok') window.history.go(-1);
            });

        },

        lead_back_fn: function () {
            window.history.go(-1);
        },
        mention_fetch_throttleds: function (model, method, kwargs) {
            // Delays the execution of the RPC to prevent unnecessary RPCs when the user is still typing
            var def = $.Deferred();
            clearTimeout(this.mention_fetch_timer);
            this.mention_fetch_timer = setTimeout(function () {
                return model.call(method, kwargs).then(function (results) {
                    def.resolve(results);
                });
            }, 200);
            return def;
        },

    });

    core.action_registry.add('crm_tree_list_js', TreeList);

    return TreeList;

});