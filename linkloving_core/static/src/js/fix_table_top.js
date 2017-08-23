/**
 * Created by 123 on 2017/6/15.
 */
odoo.define('linkloving_core.TreeView', function (require) {
    "use strict";

    var core = require('web.core');
    var Model = require('web.Model');
    var Widget = require('web.Widget');
    var View = require('web.View');

    var QWeb = core.qweb;
    var _t = core._t;

    var oe_ListView = View.include({
        init: function () {
            var self = this;
            this._super.apply(this, arguments);
        },
        start:function () {
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                // numberChange("o_form_field_number");
                // numberChange("o_list_number");
                if(settings.url == '/web/dataset/search_read'){
                        if($(".modal-content").length>=1 || $(".o_treeview_table").length>=1){
                            return;
                        }

                        var w = $(".o_sub_menu").width()+18
                        $(".table-responsive table").addClass("fix_table");
                        $(".table-responsive thead").addClass("fix_table_thead");
                        $(".table-responsive thead").css("width","calc(100% - "+ w +"px)")

                        $(".table-responsive thead tr").addClass("fix_table_thead_tr");
                        $(".table-responsive thead tr th").addClass("fix_table_thead_tr_th");


                        $("tbody tr:first td").each(function (index) {
                            $("thead tr:first th").eq(index).css("width", index == 0 ? $(this).width() / $("thead tr:first").width() * 100 + '%' : $(this).width() + 10);
                        })
                        if ($("tbody tr:first").hasClass("add_empty_tr")) {

                        } else {
                            $("tbody").prepend("<tr class='add_empty_tr'><td> </td></tr>");
                        }
                        $("tbody tr:first td").height($("thead tr th").height());

                        if ($(".table-responsive>table").height() < $(".o_view_manager_content").height()) {
                            $(".table-responsive thead").addClass("not_full_thead");
                        }else {
                             $(".table-responsive thead").removeClass("not_full_thead");
                        }
                }
                // numberChange("o_list_number");
            })
            $(window).resize(function () {
                $("tbody .add_empty_tr+tr td").each(function (index) {
                    $("thead tr:first th").eq(index).css("width",index==0 ? $(this).width()/$("thead tr:first").width()*100+'%':($(this).width()+10)/$("thead tr:first").width()*100+'%');
                })
                $("tbody tr:first td").height($("thead tr th").height());
            })

            //小数和整数部分区分展示
            function numberChange(className) {
                if($("."+ className +"")){
                    $("."+ className +"").each(function () {
                        var s = $(this).text().toString();
                        for (var i=0;i<s.length;i++){
                            if(s[i] == '.'){
                                var k=i;
                                $(this).html("");
                                var zs=[],xs=[];
                                for(var j=0;j<s.length;j++){
                                    if(j<k){
                                        zs.push(s[j]);
                                    }
                                    if(j>k){
                                        xs.push(s[j]);
                                    }
                                }
                                $(this).append('<span class="zs">'+ zs.join("") +'.</span>');
                                $(this).append('<span class="xs">'+ xs.join("") +'</span>');
                                break;
                            }
                        }
                    })
                }
            }
        }
    })
    core.view_registry.add('oe_list', oe_ListView);
    return oe_ListView
})