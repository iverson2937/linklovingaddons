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
            // console.log('yes')
        },
        start:function () {
            self.$(document).ajaxComplete(function (event, xhr, settings) {
                // console.log(settings)
                // var data = JSON.parse(settings.data)
                if(settings.url == '/web/dataset/search_read'){
                    $("tbody tr:first td").each(function (index) {
                        // $("thead tr:first th").eq(index).width($(this).width());
                        $("thead tr:first th").eq(index).css("width",index==0 ? $(this).width()/$("thead tr:first").width()*100+'%':$(this).width()+10);
                        console.log($(this).width())
                    })
                    if($("tbody tr:first").hasClass("add_empty_tr")){

                    }else {
                        $("tbody").prepend("<tr class='add_empty_tr'><td> </td></tr>");
                    }
                    $("tbody tr:first td").height($("thead tr th").height());

                   if($(".table-responsive>table").height()<$(".o_view_manager_content").height()){
                       $(".table-responsive thead").addClass("not_full_thead")
                   }
                }
            })
            $(window).resize(function () {
                $("tbody .add_empty_tr+tr td").each(function (index) {
                        // $("thead tr:first th").eq(index).width($(this).width());
                        $("thead tr:first th").eq(index).css("width",index==0 ? $(this).width()/$("thead tr:first").width()*100+'%':($(this).width()+10)/$("thead tr:first").width()*100+'%');
                        console.log($(this).width())
                    })
                    // if($("tbody tr:first").hasClass("add_empty_tr")){
                    //
                    // }else {
                    //     $("tbody").prepend("<tr class='add_empty_tr'><td> </td></tr>");
                    // }
                    $("tbody tr:first td").height($("thead tr th").height());

                   if($(".table-responsive>table").height()<$(".o_view_manager_content").height()){
                       $(".table-responsive thead").addClass("not_full_thead")
                   }
            })

        }
    })
    core.view_registry.add('oe_list', oe_ListView);
    return oe_ListView
})