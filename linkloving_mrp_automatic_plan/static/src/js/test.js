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
            'mouseenter .a_p_move_point':'change_drag_true',
            'mouseleave .a_p_move_point':'change_drag_false',
            'dragover #a_p_left':'prevent_default',
            'drop #a_p_left':'move_over_left',
            'dragover #a_p_right':'prevent_default',
            'drop #a_p_right':'move_over_right',
            'dragstart .ap_item_wrap': 'move_start',
            'click .to_bom': 'to_bom_func',
            'click .to_relevant_struc': 'to_relevant_struc_func',
            'click .a_p_mo_name':'to_mo_func',
            'click .a_p_create_alia': 'show_create_alia',
            'click .alia_cancel': 'close_create_alia',
            'click .alia_confirm': 'confirm_alia_fun',
            'click .may_choose_a_time':'change_late_time',
            'click .unarrangeed_refresh':'refresh_right',
            'click .a_p_bars': 'show_bars_buttons',
            'click .show_edit_wrap': 'show_edit_ui',
            'click .edit_prodiction_confirm': 'confirm_edit_operation',
            'click .to_schedule_report_btn': 'to_schedule_report',
        },
        to_schedule_report: function () {
            var action = {
                type: 'ir.actions.client',
                name: 'Rport',
                tag: 'schedule_production_report',
                process_id: myself.process_id,
            };
            this.do_action(action);
        },
        confirm_edit_operation:function () {
            var myself = this;
            var ele = $('.arrange_production_container').find(".ap_item_wrap[data-mo-id="+ myself.alia_mo +"]");
            if($(ele).parents('#a_p_left').length>=1){
                var edit_show_more = true
            } else {
                var edit_show_more = false
            }
            var edit_qty = $(".product_qty").val();
            new Model("mrp.production")
                    .call("change_prod_qty", [[parseInt(this.alia_mo)], {'product_qty':  edit_qty}])
                    .then(function (result) {
                        console.log(result)
                        var replace_item = QWeb.render('a_p_render_right_tmpl', {result: result,
                            show_more:edit_show_more,
                            selection:myself.states.state.selection,
                            new_selection: myself.states.product_order_type.selection,
                            material_selection: myself.states.availability.selection
                        })
                        $(ele).replaceWith(replace_item);
                        $(".item_edit_container").hide();
                    });
        },
        show_edit_ui:function () {
            $(".item_edit_container").show();
            $('.a_p_bars_buttons_wrap').hide();
            $(".product_qty").val('');
        },
        show_bars_buttons:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            this.alia_mo = $(target).parents('.ap_item_wrap').attr('data-mo-id');
            $(target).parents('.ap_item_wrap').find('.a_p_bars_buttons_wrap').toggle();
        },
        refresh_right:function () {
            this.un_arrange_production(this.process_id,10,1,this);
        },
        change_late_time:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            var select_time_wrap = $(target).parents('.a_p_latest_time');
            $(target).remove();
            self.init_date_widget($(select_time_wrap));
        },
        confirm_alia_fun:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var self = this;
            if($('.alia_input').val().length>=16){
                Dialog.alert(target, "字符数不能超过16个");
                return;
            }
            new Model("mrp.production")
                    .call("write", [[parseInt(this.alia_mo)], {'alia_name':  $('.alia_input').val()}])
                    .then(function (result) {
                        console.log(result);
                        $('.create_alia_container').hide();
                        var alia_val = $('.alia_input').val().replace(/\s+/g, "");
                        if(alia_val != ''){
                            $(self.a_p_create_alia).html($('.alia_input').val());
                        }
                    })
        },
        close_create_alia:function () {
            $('.close_this_container').hide();
        },
        show_create_alia:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            $('.alia_input').val('');
            $('.create_alia_container').show();
            this.alia_mo = $(target).parents('.ap_item_wrap').attr('data-mo-id');
            this.a_p_create_alia = $(target);
        },
        to_mo_func:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            var action = {
                type: 'ir.actions.act_window',
                res_model:'mrp.production',
                view_type: 'form',
                view_mode: 'tree,form',
                views: [[false, 'form']],
                res_id: parseInt($(target).parents('.ap_item_wrap').attr("data-mo-id")),
                target:"new"
            };
            this.do_action(action);
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
        production_lists_wrap_toggle:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            $(target).parents('.production_line').next('.production_lists_wrap').slideToggle("fast");
            if($(target).hasClass('fa-chevron-down')){
                $(target).removeClass('fa-chevron-down');
                $(target).addClass('fa-chevron-up');
                var index = $(target).parents('.production_line').attr("data-index");

                new Model("mrp.production.line")
                    .call("get_mo_by_productin_line", [[]], {production_line_id: myself.mydataset.product_line[index].id,limit:10,offset:0, planned_date:myself.chose_date})
                    .then(function (result) {
                        console.log(result);
                        // myself.mydataset = result;
                        $(target).parents('.production_line').next('.production_lists_wrap').html("");
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
                    })

            }else {
                $(target).removeClass('fa-chevron-up');
                $(target).addClass('fa-chevron-down');
            }
        },
        move_start:function (ev) {
            var ev = ev || window.event;
            var target = ev.target || ev.srcElement;
            move_id = target.id;
        },
        //移到左边
        move_over_left:function (ev) {
            ev.preventDefault();
            var elem = document.getElementById(move_id); //当前拖动的元素
            var toElem = ev.target;  //松开鼠标释放节点时光标所在元素
            //判断是否拖动后还在一个产线  若是 则不做操作
            if($(elem).parents('.production_lists_wrap').length>=1){
                var elem_line_index = $(elem).parents('.production_lists_wrap').prev('.production_line').attr('data-index');  //若拖动的节点在左边  取到他所在产线的序号
                if($(toElem).hasClass('production_lists_wrap')){
                    if($(toElem).prev('.production_line').attr('data-index') == elem_line_index){
                        return
                    }
                }else if ($(toElem).parents('.production_lists_wrap').prev('.production_line').attr('data-index') == elem_line_index){
                    return
                }
            }

            if(toElem.className == 'ap_item_wrap'){
                // $(elem).insertBefore($(toElem));
                var mo_id = $(elem).attr("data-mo-id");
                var pt_line_index = $(toElem).parents('.production_lists_wrap').prev('.production_line').attr('data-index');
                myself.no_ap_to_ag(parseInt(mo_id), myself.mydataset.product_line[pt_line_index].id,toElem,elem, function () {
                    $(elem).insertBefore($(toElem).parents('.ap_item_wrap'));
                });
            }else if($(toElem).parents('.ap_item_wrap').length>=1){
                // $(elem).insertBefore($(toElem).parents('.ap_item_wrap'));
                var mo_id = $(elem).attr("data-mo-id");
                var pt_line_index = $(toElem).parents('.production_lists_wrap').prev('.production_line').attr('data-index');
                myself.no_ap_to_ag(parseInt(mo_id), myself.mydataset.product_line[pt_line_index].id,toElem,elem, function () {
                    $(elem).insertBefore($(toElem).parents('.ap_item_wrap'));
                });
            }
            else if($(toElem).hasClass('production_lists_wrap')){
                // $(toElem).prepend($(elem));
                var mo_id = $(elem).attr("data-mo-id");
                var pt_line_index = $(toElem).prev('.production_line').attr('data-index');
                if($(toElem).hasClass('production_lists_no_item')){
                    $(toElem).removeClass('production_lists_no_item')
                }
                myself.no_ap_to_ag(parseInt(mo_id), myself.mydataset.product_line[pt_line_index].id,toElem,elem, function () {
                    $(toElem).prepend($(elem));
                });
            }
        },
        //移到右边
        move_over_right:function (ev) {
            ev.preventDefault();
            var elem = document.getElementById(move_id); //当前拖动的元素
            var toElem = ev.target;
            if($(elem).parents('#a_p_right').length>=1){
                return;
            }
            if(toElem.className == 'ap_item_wrap'){
                var mo_id = $(elem).attr("data-mo-id");
                myself.no_ap_to_ag(parseInt(mo_id),false,toElem,elem, function () {
                    $(elem).insertBefore($(toElem).parents('.ap_item_wrap'));
                });
            }else if($(toElem).parents('.ap_item_wrap').length>=1){
                var mo_id = $(elem).attr("data-mo-id");
                myself.no_ap_to_ag(parseInt(mo_id),false,toElem,elem, function () {
                    $(elem).insertBefore($(toElem).parents('.ap_item_wrap'));
                });
            }else if($(toElem).attr('id') == 'a_p_right'){
                var mo_id = $(elem).attr("data-mo-id");
                myself.no_ap_to_ag(parseInt(mo_id),false,toElem,elem, function () {
                    $(elem).insertAfter($('.a_p_right_head'));
                });
            }
        },
        change_drag_true:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            $(target).parents('.ap_item_wrap').attr('draggable','true');
        },
        change_drag_false:function (e) {
            var e = e || window.event;
            var target = e.target || e.srcElement;
            $(target).parents('.ap_item_wrap').attr('draggable','false');
        },
        prevent_default:function (ev) {
            ev.preventDefault(); //阻止向上冒泡
        },

        //拖动的接口
        no_ap_to_ag: function (mo_id,production_line_id,toElem,ele, success_cb) {
              framework.blockUI();
              new Model("mrp.production")
                    .call("settle_mo", [mo_id], {production_line_id:production_line_id,settle_date:myself.chose_date})
                    .then(function (result) {
                        console.log(result);
                        var origin_wrap_bkup = $(ele).parents('.production_lists_wrap');//左边
                        success_cb();
                        if (production_line_id != false) {//从右到左
                            var show_more = true;//显示更多
                            if($(toElem)[0].className != 'production_lists_wrap'){
                                var elem_wrap = $(toElem).parents('.production_lists_wrap');
                            }else {
                                var elem_wrap = $(toElem);
                            }//获取目的位置

                            if ($(origin_wrap_bkup).length >= 1) {//左边到左边  from位置
                                $(origin_wrap_bkup).html('');
                                var new_items = QWeb.render('a_p_render_right_tmpl', {result: result.origin_pl_mos,
                                    show_more:true,
                                    selection:myself.states.state.selection,
                                    new_selection:myself.states.product_order_type.selection,
                                    material_selection: myself.states.availability.selection
                                })
                                $(origin_wrap_bkup).append(new_items);
                            }
                            //重新渲染拖动的MO所在的产线
                            $(elem_wrap).html('');
                            var new_ite = QWeb.render('a_p_render_right_tmpl', {
                                result: result.mos,
                                show_more: true,
                                selection: myself.states.state.selection,
                                new_selection: myself.states.product_order_type.selection,
                                material_selection: myself.states.availability.selection
                            })
                            $(elem_wrap).append(new_ite);
                        } else {//从左到右
                            var show_more = false;
                            //这是从已排产拖到未排产的情况,要重新渲染已排产的数据
                            var origin_wrap = origin_wrap_bkup;//左边
                            $(origin_wrap).html('');
                            var new_items = QWeb.render('a_p_render_right_tmpl', {
                                result: result.origin_pl_mos,
                                show_more: true,
                                selection: myself.states.state.selection,
                                new_selection: myself.states.product_order_type.selection,
                                material_selection: myself.states.availability.selection
                            })
                            $(origin_wrap).append(new_items);
                        }

                        //从新渲染拖动的MO单
                        var replace_item = QWeb.render('a_p_render_right_tmpl', {result: result.operate_mo,
                            show_more:show_more,
                            selection:myself.states.state.selection,
                            new_selection: myself.states.product_order_type.selection,
                            material_selection: myself.states.availability.selection
                        })
                        $(ele).replaceWith(replace_item);

                    }).always(function (result) {
                        console.log(result);
                        framework.unblockUI();
                        if(result && result.code == '200'){
                            return 'error';
                        }
                    })
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
                    .call("write", [[parseInt($(node).parents('.ap_item_wrap').attr('data-mo-id'))], {'planned_start_backup':  myself.chose_date}])
                    .then(function (result) {
                        console.log(result)
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
                self.datewidget.set_datetime_default();
                self.datewidget.commit_value();
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
        },
        //搜索部分
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
                $(".a_p_right_head").prepend($node1);
                self.searchview.on('search_data', self, self.search.bind(self));
                $.when(self.searchview.appendTo($node1)).done(function () {
                    self.searchview_elements = {};
                    self.searchview_elements.$searchview = self.searchview.$el;
                    self.searchview_elements.$searchview_buttons = self.searchview.$buttons.contents();
                    self.searchview.do_show();
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
        reload_content: function (own) {
            var reloaded = $.Deferred();
            own.offset = own.current_min;
            own.limit = own._limit;
            own.un_arrange_production(own.process_id,own.limit,own.offset,own);
            reloaded.resolve();
            return reloaded.promise();
        },
        set_scrollTop: function (scrollTop) {
            this.scrollTop = scrollTop;
        },


        //右边未排产的接口
        un_arrange_production:function (process_id,limit,offset,own) {
            framework.blockUI();
            // console.log(own.states.product_order_type.selection)
            new Model("mrp.production")
                    .call("get_unplanned_mo", [[]], {process_id:process_id,limit:limit,offset:offset-1,domains:own.domain})
                    .then(function (result) {
                        console.log(result)
                        console.log(own.states)
                        myself.mydataset.mo = result.result;
                        $("#a_p_right .a_p_right_head").nextAll().remove();
                        $("#a_p_right").append(QWeb.render('a_p_render_right_tmpl',{result: result.result,
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
                        }
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
        start: function () {
            var self = this;
            var cp_status = {
                breadcrumbs: self.action_manager && self.action_manager.get_breadcrumbs(),
                // cp_content: _.extend({}, self.searchview_elements, {}),
            };
            self.update_control_panel(cp_status);

            myself = this;

            myself.mydataset = {};
            framework.blockUI();

            new Model("mrp.production").call("fields_get",[],{allfields: ['state', 'product_order_type','availability']}).then(function (result) {
                console.log(result);
                myself.states = result;
                //未排产
                self.un_arrange_production(myself.process_id,10,1,myself);
            })


            new Model("mrp.production.line")
                    .call("get_production_line_list", [[]], {process_id:this.process_id})
                    .then(function (result) {
                        console.log(result);
                        myself.mydataset.product_line = result;
                        self.$el.eq(0).append(QWeb.render('a_p_render_tmpl', {result: result}));
                        self.init_date_widget($(".a_p_time_start"));
                        framework.unblockUI();
                    })
        }

    })

    core.action_registry.add('arrange_production', Arrange_Production);

    return Arrange_Production;
})
