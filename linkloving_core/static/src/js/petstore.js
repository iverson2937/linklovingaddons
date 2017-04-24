openerp.oepetstore = function(instance, local) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    local.HomePage = instance.Widget.extend({
        template: "HomePage",
        events: {
            'click .level-top': 'zhankai',
        },
        zhankai : function (e) {
            // $el.removeClass("fa-caret-right")
           // $(this).addClass("jjjjj")
           // console.log("ppp")
           //  console.log($(this).html())

            var e = e||window.event;
            var target = e.target || e.srcElement;
            if(target.classList.contains("fa-caret-right")){
                console.log(target.className);
                target.classList.remove("fa-caret-right");
                target.classList.add("fa-caret-down");
                $(".ceshi").show()
            }else if(target.classList.contains("fa-caret-down")) {
                target.classList.remove("fa-caret-down");
                target.classList.add("fa-caret-right");
                 $(".ceshi").hide()
            }

        },
        start: function() {
             // return $.when(
                // new local.PetToysList(this).appendTo(this.$('.oe_petstore_homepage_left')),
                // new local.MessageOfTheDay(this).appendTo(this.$('.oe_petstore_homepage_right')),
                // new local.OpenTheTree(this).appendTo(this.$(".oe_petstore_homepage_right"))
            // );

            var self = this;
            return new instance.web.Model("oepetstore.message_of_the_day")
                .query(["message"])
                .order_by('-create_date', '-id')
                .limit(7)
                .all()
                .then(function(result) {
                    console.log(result)
                    // self.$(".oe_mywidget_message_of_the_day").text(result.message);
                    _(result).each(function (items) {
                         self.$(".bodys").append(QWeb.render('xx', {items: items}));
                    })
                });

        },
    });

    instance.web.client_actions.add('petstore.homepage', 'instance.oepetstore.HomePage');

    local.OpenTheTree = instance.Widget.extend({
         start:function () {
             var self = this;
             this.$el.append(QWeb.render("OpenTree"));
        },
    });


    local.MessageOfTheDay = instance.Widget.extend({
        template: "MessageOfTheDay",
        start: function() {
            var self = this;
            return new instance.web.Model("oepetstore.message_of_the_day")
                .query(["message"])
                .order_by('-create_date', '-id')
                .limit(5)
                .all()
                .then(function(result) {
                    console.log(result[0].message)
                    // self.$(".oe_mywidget_message_of_the_day").text(result.message);
                    _(result).each(function (items) {
                         self.$el.append(QWeb.render('xx', {items: items}));
                    })
                });

        },
    });

    local.PetToysList = instance.Widget.extend({
        template: 'PetToysList',
        events: {
            'click .oe_petstore_pettoy': 'selected_item',
        },

        start: function () {
            var self = this;
            return new instance.web.Model('product.product')
                .query(['name', 'image'])
                .filter([['categ_id.name', '=', "Pet Toys"]])
                .limit(5)
                .all()
                .then(function (results) {
                    _(results).each(function (item) {
                        self.$el.append(QWeb.render('PetToy', {item: item}));
                    });
                });
        },
        selected_item: function (event) {
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'product.product',
                res_id: $(event.currentTarget).data('id'),
                views: [[false, 'form']],
            });
        },
    });

    var MyClass = instance.web.Class.extend({
        init: function(name) {
            this.name = name;
        },
        say_hello: function() {
            // console.log("jsjsjs");
        },
    });
    var my_object = new MyClass("Bob");
    my_object.say_hello();

}
