/**
 * Created by 123 on 2017/8/31.
 */
odoo.define('linkloving_mrp_automatic_plan.arrange_production', function (require) {
    "use strict";
    var core = require('web.core');
    var Model = require('web.Model');
    var data_manager = require('web.data_manager');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var ControlPanel = require('web.ControlPanel');
    var Widget = require('web.Widget');
    var data = require('web.data');
    var ListView = require('web.ListView');
    var common = require('web.form_common');
    var Pager = require('web.Pager');
    var datepicker = require('web.datepicker');
    var Dialog = require('web.Dialog');
    var framework = require('web.framework');
    var SearchView = require('web.SearchView');
    var pyeval = require('web.pyeval');
    var QWeb = core.qweb;
    var _t = core._t;
    var myself;
    var move_id;

    var Arrange_Production = Widget.extend(ControlPanelMixin,{
        template: 'arrange_production_tmp',
        events:{
            'click .a_p_showorhide': 'production_lists_wrap_toggle',
            'click .to_bom': 'to_bom_func',
            'click .to_relevant_struc': 'to_relevant_struc_func',
            'click .a_p_mo_name':'to_mo_func',
            'click .so_report_btn': 'so_report',
            'click .order_by_material': 'order_by_material_1',
            'click .order_by_default': 'order_by_material_1',
            'click .un_a_p_showorhide':'un_a_p_showorhide_toggle',   //未排产的
        },
        order_by_material_1: function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            console.log(target);
            if ($(target).hasClass("order_by_material")) {//物料排序
                myself.order_by_material = true;
                $(target).hide();
                $(".order_by_default").show();
            }
            else {//时间排序
                myself.order_by_material = false;
                $(target).hide();
                $(".order_by_material").show();
            }
            myself.arrangeed_searched();

        },


        to_mo_func:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            new Model("mrp.production").call("show_paichan_form_view", [parseInt($(target).parents('.ap_item_wrap').attr("data-mo-id"))]).then(function (res) {
                var action = {
                    type: 'ir.actions.act_window',
                    res_model: 'mrp.production',
                    view_mode: 'form',
                    views: [[res, 'form']],
                    view_type: 'form',
                    view_id: res,
                    res_id: parseInt($(target).parents('.ap_item_wrap').attr("data-mo-id")),
                    readonly: true,
                    target: "new"
                };
                console.log("332")
                self.do_action(action);
            })

        },
        to_relevant_struc_func:function (e) {
             var e = e || window.event;
             var target = e.target || e.srcElement;
             var action = {
               'type': 'ir.actions.client',
                'tag': 'product_detail',
                'product_id': parseInt($(target).parents('.ap_item_wrap').attr("data-product-id")),
                'is_show': false,
                'target':'new'
            };
            this.do_action(action);
        },
        to_bom_func:function (e) {
             var e = e || window.event;
             var target = e.target || e.srcElement;
             var action = {
               'type': 'ir.actions.client',
                'tag': 'new_bom_update',
                'bom_id': parseInt($(target).parents('.ap_item_wrap').attr("data-bom-id")),
                'is_show': false,
                'target':'new'
            };
            this.do_action(action);
        },
        //未排产的toggle
        un_a_p_showorhide_toggle:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            $(target).parents('.production_line').next('.production_lists_wrap').slideToggle("fast");
            var self = this;
            // self.un_arrange_production(myself.process_id,10,1,myself);
            if($(target).hasClass('fa-chevron-down')){
                $(target).removeClass('fa-chevron-down');
                $(target).addClass('fa-chevron-up');
            }else {
                $(target).removeClass('fa-chevron-up');
                $(target).addClass('fa-chevron-down');
            }
        },
        //已经排产的产线的toggle
        production_lists_wrap_toggle:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var own = this;

            //开一个产线  关掉其他展开的产线
            $('.fa-chevron-up').each(function () {
                if($(target).hasClass('fa-chevron-up')){
                    return
                }
                $(this).addClass('fa-chevron-down').removeClass('fa-chevron-up');
                $(this).parents('.production_line').next('.production_lists_wrap').slideToggle("fast");
            });

            $(target).parents('.production_line').next('.production_lists_wrap').slideToggle("fast");
            if($(target).hasClass('fa-chevron-down')){
                $(target).removeClass('fa-chevron-down');
                $(target).addClass('fa-chevron-up');
                var index = $(target).parents('.production_line').attr("data-index");
                myself.index = index;

                framework.blockUI();
                new Model("mrp.production.line")
                    .call("get_mo_by_productin_line", [[]], {
                        process_id: myself.process_id,
                        production_line_id: myself.mydataset.product_line[index].id,
                        limit: 10,
                        offset: 0,
                        planned_date: myself.chose_date,
                        domains: myself.left_domain,
                        order_by_material: myself.order_by_material,
                    })
                    .then(function (result) {
                        console.log(result);
                        // myself.mydataset = result;
                        $(target).parents('.production_line').next('.production_lists_wrap').html("");
                        $(target).parents('.production_line').next('.un_group_list_wrap').append("<div class='un_group'></div>")
                        $(target).parents('.production_line').next('.production_lists_wrap').removeClass('production_lists_no_item');
                        $(target).parents('.production_line').next('.production_lists_wrap').append(QWeb.render('a_p_render_right_tmpl',{result: result,
                            show_more:true,
                            selection:myself.states.state.selection,
                            new_selection:myself.states.product_order_type.selection,
                            material_selection: myself.states.availability.selection
                        }));
                        if($(target).parents('.production_line').next('.production_lists_wrap').children('.ap_item_wrap').length == 0){
                            $(target).parents('.production_line').next('.production_lists_wrap').addClass('production_lists_no_item');
                        }
                        own.render_pager2();
                    }).always(function () {
                    framework.unblockUI();
                })

            }else {
                $(target).removeClass('fa-chevron-up');
                $(target).addClass('fa-chevron-down');
            }
        },
        render_one_production_line: function (target, result) {

            $(target).removeClass('fa-chevron-down');
            $(target).addClass('fa-chevron-up');
            $(target).parents('.production_line').next('.production_lists_wrap').html("");
            $(target).parents('.production_line').next('.production_lists_wrap').removeClass('production_lists_no_item');
            if($(target).hasClass('un_a_p_showorhide')){
                $(target).parents('.production_line').next('.production_lists_wrap').append(QWeb.render('un_a_p_render_right_tmpl', {
                result: result,
                show_more: true,
                selection: myself.states.state.selection,
                new_selection: myself.states.product_order_type.selection,
                material_selection: myself.states.availability.selection
            }));
            }
            else {
                $(target).parents('.production_line').next('.production_lists_wrap').append(QWeb.render('a_p_render_right_tmpl', {
                result: result,
                show_more: true,
                selection: myself.states.state.selection,
                new_selection: myself.states.product_order_type.selection,
                material_selection: myself.states.availability.selection
            }));
            }
            if ($(target).parents('.production_line').next('.production_lists_wrap').children('.ap_item_wrap').length == 0) {
                $(target).parents('.production_line').next('.production_lists_wrap').slideUp(0);
                $(target).parents('.production_line').next('.production_lists_wrap').addClass('production_lists_no_item');
            }
            else {
                if ($(target).parents('.production_line').next('.production_lists_wrap').is(':hidden')) {
                    $(target).parents('.production_line').next('.production_lists_wrap').slideToggle("fast");
                }
            }
        },

        build_widget: function() {
            return new datepicker.DateTimeWidget(this);
        },
        init_date_widget:function (node) {
             var self = this;
            this.datewidget = this.build_widget();
            this.datewidget.on('datetime_changed', this, function() {
                myself.chose_date = self.datewidget.get_value();
                // $(".bootstrap-datetimepicker-widget").attr('id','a_p_date');
                if(node[0].className == 'a_p_latest_time'){
                    new Model("mrp.production")
                        .call("change_backup_time", [[parseInt($(node).parents('.ap_item_wrap').attr('data-mo-id'))]], {'planned_start_backup': myself.chose_date})
                    .then(function (result) {

                        self.render_one_production_line($(node).parents('.production_lists_wrap').prev(".production_line").find(".a_p_showorhide"), result.mos)
                    })

                    return
                }
                $(".a_p_showorhide").each(function () {
                    if($(this).hasClass('fa-chevron-up')){
                        $(this).parents('.production_line').next('.production_lists_wrap').slideToggle("fast");
                        $(this).removeClass('fa-chevron-up');
                        $(this).addClass('fa-chevron-down');
                    }
                })
            });
            this.datewidget.appendTo(node).done(function() {
                console.log(self.datewidget.$el);
                // self.datewidget.$el.addClass(self.$el.attr('class'));
                // self.replaceElement(self.datewidget.$el);
                // self.datewidget.$input.addClass('o_form_input');


                self.setupFocus(self.datewidget.$input);
                // self.datewidget.set_datetime_default();

                if(node[0].className == 'a_p_latest_time' && self.current_time){
                    self.datewidget.set_value(self.current_time);
                }else if(node[0].className == 'a_p_latest_time' && self.current_time==''){

                }else {
                    self.datewidget.set_datetime_default();
                }

                //self.datewidget.commit_value();
            });
        },
        init: function (parent, action) {
            this._super(parent);
            this._super.apply(this, arguments);
            if (parent && parent.action_stack.length > 0){
                this.action_manager = parent.action_stack[0].widget.action_manager
            }
            if (action.process_id) {
                this.process_id = action.process_id;
            } else {
                this.process_id = action.params.active_id;
            }
            var self = this;
            self.limit = 10;
            self.offset=1;
            self.length = 10;

            self.limit_un_group = 10;
            self.offset_un_group = 1;
            self.length_un_group = 10;
        },
        setup_search_view: function () {
            var self = this;
            if (this.searchview) {
                this.searchview.destroy();
            }
            var search_defaults = {};
            var options = {
                hidden: true,
                disable_custom_filters: true,
                $buttons: $("<div>"),
                action: this.action,
                search_defaults: search_defaults,
            };
            self.dataset = new data.DataSetSearch(this, "mrp.production", {}, false);
            $.when(self.load_views()).done(function () {
                // Instantiate the SearchView, but do not append it nor its buttons to the DOM as this will
                // be done later, simultaneously to all other ControlPanel elements
                self.searchview = new SearchView(self, self.dataset, self.search_fields_view, options);
                var $node1 = $('<div/>').addClass('no_arrange_product_searchview')
                // $(".a_p_right_head").prepend($node1);
                self.searchview.on('search_data', self, self.search.bind(self));
                $.when(self.searchview.appendTo($node1)).done(function () {
                    self.searchview_elements = {};
                    self.searchview_elements.$searchview = self.searchview.$el;
                    self.searchview_elements.$searchview_buttons = self.searchview.$buttons.contents();
                    self.searchview.do_show();
                });
            });

        },
        //搜索部分
        setup_left_search_view: function () {
            var self = this;
            if (this.left_searchview) {
                this.left_searchview.destroy();
            }
            var search_defaults = {};
            var options = {
                hidden: true,
                disable_custom_filters: true,
                $buttons: $("<div>"),
                action: this.action,
                search_defaults: search_defaults,
            };
            self.left_dataset = new data.DataSetSearch(this, "mrp.production", {}, false);
            $.when(self.load_views()).done(function () {
                // Instantiate the SearchView, but do not append it nor its buttons to the DOM as this will
                // be done later, simultaneously to all other ControlPanel elements
                self.left_searchview = new SearchView(self, self.dataset, self.search_fields_view, options);
                var $node1 = $('<div/>').addClass('arranged_product_searchview')
                $(".a_p_time_end").prepend($node1);
                self.left_searchview.on('search_data', self, self.left_search.bind(self));
                $.when(self.left_searchview.appendTo($node1)).done(function () {
                    self.left_searchview_elements = {};
                    self.left_searchview_elements.$searchview = self.left_searchview.$el;
                    self.left_searchview_elements.$searchview_buttons = self.left_searchview.$buttons.contents();
                    self.left_searchview.do_show();
                });
            });

        },
        load_views: function (load_fields) {
            var self = this;
            var views = [];
            _.each(this.views, function (view) {
                if (!view.fields_view) {
                    views.push([view.view_id, view.type]);
                }
            });
            var options = {
                load_fields: load_fields,
            };
            if (!this.search_fields_view) {
                options.load_filters = true;
                views.push([false, 'search']);
            }
            return data_manager.load_views(this.dataset, views, options).then(function (fields_views) {
                _.each(fields_views, function (fields_view, view_type) {
                    if (view_type === 'search') {
                        self.search_fields_view = fields_view;
                    } else {
                        self.views[view_type].fields_view = fields_view;
                    }
                });
            });
        },
        search: function (domains, contexts, groupbys) {
            var own = this;
            pyeval.eval_domains_and_contexts({
                domains: [[]].concat(domains || []),
                contexts: [].concat(contexts || []),
                group_by_seq: groupbys || []
            }).done(function (results) {
                own.offset = 1;
                own.domain = results.domain;
                own.un_arrange_production(own.process_id,10,own.offset,own)
            })
        },
        left_search: function (domains, contexts, groupbys) {
            var own = this;
            console.log("1111111");
            pyeval.eval_domains_and_contexts({
                domains: [[]].concat(domains || []),
                contexts: [].concat(contexts || []),
                group_by_seq: groupbys || []
            }).done(function (results) {
                own.offset = 1;
                own.left_domain = results.domain;
                own.arrangeed_searched();
                own.un_arrange_searched();
            })
        },
        un_arrange_searched:function () {
            var self = this;
            framework.blockUI();
            new Model("mrp.production")
                    .call("get_unplanned_mo_by_search", [[]], {
                        process_id: self.process_id,
                        domains: self.left_domain,
                    group_by: self.group_by,
                    order_by_material: myself.order_by_material,
                    })
                    .then(function (result) {
                        framework.unblockUI();
                        console.log(result)
                        console.log(self.states)
                        var showorhides = $(".un_a_p_showorhide");


                        // showorhides.each(function (i) {
                        //     if (result[line_id]) {
                                var mos = result["result"];
                                myself.render_one_production_line($('.un_a_p_showorhide'), mos)
                        //     }
                        //     else {
                        //         myself.render_one_production_line(this, {})
                        //     }
                        // })
                        framework.unblockUI();
                    })
        },
        render_pager: function () {
            if ($(".approval_pagination")) {
                $(".approval_pagination").remove()
            }
            var $node = $('<div/>').addClass('approval_pagination').prependTo($(".a_p_right_head"));
            this.pager = new Pager(this, this.length, this.offset, this.limit);
            this.pager.appendTo($node);

            this.pager.on('pager_changed', this, function (new_state) {
                var self = this;
                var limit_changed = (this._limit !== new_state.limit);
                this._limit = new_state.limit;
                this.current_min = new_state.current_min;
                self.reload_content(this).then(function () {
                    self.$el.animate({"scrollTop": "0px"}, 100);
                });
            });
        },
        render_pager2: function () {
            if ($(".approval_pagination")) {
                $(".approval_pagination").remove()
            }
            var $node = $('<div/>').addClass('approval_pagination').prependTo($(".un_group"));
            this.pager = new Pager(this, this.length_un_group, this.offset_un_group, this.limit_un_group);
            this.pager.appendTo($node);

            this.pager.on('pager_changed', this, function (new_state) {
                var self = this;
                var limit_changed = (this._limit !== new_state.limit);
                this._limit = new_state.limit_un_group;
                this.current_min = new_state.current_min;
                self.reload_content2(this).then(function () {
                    self.$el.animate({"scrollTop": "0px"}, 100);
                });
            });
        },
        reload_content: function (own) {
            var reloaded = $.Deferred();
            own.offset = own.current_min;
            own.limit = own._limit;
            own.un_arrange_production(own.process_id,own.limit,own.offset,own);
            reloaded.resolve();
            return reloaded.promise();
        },
        reload_content2: function (own) {
            var reloaded = $.Deferred();
            own.offset_un_group = own.current_min;
            own.limit_un_group = own._limit;

            new Model("mrp.production.line")
                    .call("get_mo_by_productin_line", [[]], {
                        process_id: myself.process_id,
                        production_line_id: -1,
                        limit: 10,
                        offset: myself.offset_un_group,
                        planned_date: myself.chose_date,
                        domains: myself.left_domain,
                        order_by_material: myself.order_by_material,
                    })
                    .then(function (result) {
                        console.log(result);
                        // myself.mydataset = result;
                        $(".production_line[data-index="+ myself.index +"]").nextAll('.production_lists_wrap').children('.un_group').nextAll().remove();
                        $(".production_line[data-index="+ myself.index +"]").nextAll('.production_lists_wrap').append(QWeb.render('a_p_render_right_tmpl', {
                            result: result,
                            show_more: true,
                            selection: myself.states.state.selection,
                            new_selection: myself.states.product_order_type.selection,
                            material_selection: myself.states.availability.selection
                        }))
                        // if($(target).parents('.production_line').next('.production_lists_wrap').children('.ap_item_wrap').length == 0){
                        //     $(target).parents('.production_line').next('.production_lists_wrap').addClass('production_lists_no_item');
                        // }
                        // own.render_pager2();
                    }).always(function () {
                    framework.unblockUI();
                })
            reloaded.resolve();
            return reloaded.promise();
        },
        set_scrollTop: function (scrollTop) {
            this.scrollTop = scrollTop;
        },

        arrangeed_searched: function () {
            var self = this;
            framework.blockUI();

            // console.log(own.states.product_order_type.selection)
            new Model("mrp.production")
                .call("get_planned_mo_by_search", [[]], {
                        process_id: self.process_id,
                        domains: self.left_domain,
                    group_by: self.group_by,
                    order_by_material: myself.order_by_material,
                    }
                )
                .then(function (result) {
                    framework.unblockUI();
                    console.log(result)
                    console.log(self.states)
                    var showorhides = $(".a_p_showorhide")
                    showorhides.each(function (i) {
                        var index = parseInt($(this).parents('.production_line').attr("data-index"));
                        var line_id = myself.mydataset.product_line[index].id;
                        if (result[line_id]) {
                            var mos = result[line_id].mos;
                            myself.render_one_production_line(this, mos)
                        }
                        else {
                            myself.render_one_production_line(this, {})
                        }
                    })
                    })
        },
        setupFocus: function ($e) {
            var self = this;
            $e.on({
                focus: function () {
                    self.trigger('focused');
                },
                blur: function () { self.trigger('blurred'); }
            });
        },

        //未排产
        un_arrange_production:function (process_id,limit,offset,own) {
            framework.blockUI();
            new Model("mrp.production")
                    .call("get_unplanned_mo", [[]], {process_id:process_id,limit:limit,offset:offset-1,domains:own.domain})
                    .then(function (result) {
                        console.log(result);
                        if($('.un_production_line').length>0){
                            $('.un_a_p_lists_wrap .a_p_right_head').nextAll().remove();
                            framework.unblockUI();
                            $(".un_a_p_lists_wrap").append(QWeb.render('un_a_p_render_right_tmpl',{result: result.result,
                                show_more:false,
                                selection:own.states.state.selection,
                                new_selection:own.states.product_order_type.selection,
                                material_selection: own.states.availability.selection
                            }));
                            return
                        }
                        myself.mydataset.mo = result.result;
                        $("#a_p_left").append(QWeb.render('un_a_p_tmpl',{result: result.result,length:result.length,
                            show_more:false,
                            selection:own.states.state.selection,
                            new_selection:own.states.product_order_type.selection,
                            material_selection: own.states.availability.selection
                        }));
                        framework.unblockUI();
                        own.length = result.length;
                        own.render_pager();
                        if(!own.domain){
                            own.setup_search_view();
                            own.setup_left_search_view();
                        }
                    })
        },
        start: function () {
            var self = this;
            var cp_status = {
                breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
                // cp_content: _.extend({}, self.searchview_elements, {}),
            };
            self.update_control_panel(cp_status);

            myself = this;
            myself.group_by = ["production_line_id"]
            myself.mydataset = {};
            framework.blockUI();

            new Model("mrp.production").call("fields_get",[],{allfields: ['state', 'product_order_type','availability']}).then(function (result) {
                console.log(result);
                myself.states = result;
            });

            var model_ = new Model("mrp.production.line")

            model_.call("get_production_line_list", [[]], {process_id:this.process_id})
            .then(function (result) {
                console.log(result);
                model_.call('get_process_info',[[]], {process_id:myself.process_id}).then(function (process_info) {
                    console.log(process_info)
                    myself.length_un_group = result[result.length-1].amount_of_planned_mo;
                    myself.mydataset.product_line = result;
                    self.$el.eq(0).append(QWeb.render('a_p_render_tmpl', {result: result,process_info:process_info}));
                    self.init_date_widget($(".a_p_time_start"));
                    framework.unblockUI();
                });
            });

            self.un_arrange_production(myself.process_id,10,1,myself);
        }

    })

    core.action_registry.add('arrange_production', Arrange_Production);

    return Arrange_Production;
})
