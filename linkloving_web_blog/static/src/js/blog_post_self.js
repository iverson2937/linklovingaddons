$(function () {

    $('.o_menu_systray').hide();

    var blog_checkbox = new Array();


    if (document.getElementById("hot_faq"))
        ajax_search_body(document.getElementById("hot_faq"));


    $(".show_dl").click(function (e) {
        var e = e || window.event;
        var target = e.target || e.srcElement;
        // console.log(target)

        if ($(target.nextElementSibling).context.children.length > 0)
            $(target.nextElementSibling).toggle();
    });

    $(".save_self_blog").click(function (e) {
        if (!$.trim($('#name').val())) {
            $('.name-span').html('主题不能为空!');
            $('#name').html('');
            return false;
        }

        if ($('#summernote').summernote('isEmpty')) {
            $('.content-span').html('博文主题不能为空!');
            return false;
        }

    });

    $('#name').change(function (e) {
        if ($('#name').val()) $('.name-span').html('');
        else $('.name-span').html('主题不能为空!');
    });

    $('#kf_search_index_key').on('keypress', function (event) {
        if (event.keyCode === 13) {
            $('.search-type').trigger('click');
        }
    });


    $(".change_tab_blog_view_div dl").on("click", "a", function (e) {

        $('.change_tab_blog_view').hide();
        $('.iframe_view_post').show();

        $(".div_show_go_back").show();

        var e = e || window.event;
        var target = e.target || e.srcElement;
        // console.log(target);

    });


    $(".div_show_go_back").on("click", "a", function (e) {

        $('.change_tab_blog_view').show();
        $('.iframe_view_post').hide();
        $(".div_show_go_back").hide();

    });

    // $(".a_show_go_back").click(function (e) {
    //
    //     alert(111)
    //
    // });


    $(".btn-default").click(function (e) {

        var html = $('#summernote').summernote('code');
        $('#content').html(html);
        return true;

    });


    $(".blog-type").click(function (e) {

        var e = e || window.event;
        var target = e.target || e.srcElement;
        console.log(target.id);


        $('a.blog-type').removeClass('current');
        $(target).addClass("current");


        if ($(target).hasClass("general-type")) {

            if (!$(target.nextElementSibling).context.children.length)
                $("ul li dl").css("display", "none");

            if ($(target.nextElementSibling).css('display') != 'none') {
                $("ul li dl").css("display", "none");

                if ($(target.nextElementSibling).context.children.length > 0)
                    $(target.nextElementSibling).css("display", "block");

            }
        }

        ajax_search_body(target);

        $(".div_show_go_back").hide();

    });


    function ajax_search_body(target) {
        //is_Parent true 为子分类
        var is_Parent;

        if ($(target).hasClass("general-type")) is_Parent = false;
        else if ($(target).hasClass("detailed-type")) is_Parent = true;

        var is_search;
        if ($(target).hasClass("search-type") || $(target).hasClass("glyphicon-search")) {
            is_search = true;
        }

        var is_hot;
        if ($(target).hasClass("hot-type")) {
            is_hot = true;
            $("ul li dl").css("display", "none");
        }


        $.ajax({
            type: "POST",
            dataType: 'json',
            url: '/blog/get_blog_data_lists',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({
                "params": {
                    'blog_blog_id': target.id,
                    'blog_type_id': target.id,
                    'is_Parent': is_Parent,
                    'is_search': is_search,
                    'search_body': $('#kf_search_index_key').val(),
                    'is_hot': is_hot,
                }
            }),

            // data: JSON.stringify({'blog_type_id': target.id, 'is_Parent': is_Parent, 'is_search': is_search}),
            success: function (res) {
                console.log(res.result.data);
                var data_list = res.result.data;
                var html_val = "";
                $('.change_tab_blog_view').html("");


                for (var data_one in data_list) {
                    html_val += "<dd> <div class='row'> <div class='col-md-10'> <a target='main_my' class='view_post_js' href='/blog/" + data_list[data_one].blog_id + "/post1/" + data_list[data_one].blog_post_id + "'>" + data_list[data_one].name + "</a></div> <div class='col-md-2'>" + data_list[data_one].blog_post_name + "</div> </div></dd>";

                    // html_val += "<dd><a class='view_post' href='/blog/" + data_list[data_one].blog_id + "/post/" + data_list[data_one].blog_post_id + ">" + data_list[data_one].name + "</a></dd>"
                }
                if (!html_val) {
                    html_val = "<dd>没有找到文章</dd>";
                }

                $('.change_tab_blog_view').html(html_val);

                $('.change_tab_blog_view').show();
                $('.iframe_view_post').hide();
            },
            error: function (data) {
                console.log("ERROR ", data);
            }
        });

    };

    $('#blog_type_general').change(function (e) {
        // detailed_list

        var e = e || window.event;
        var target = e.target || e.srcElement;
        console.log($(target).find("option:selected").text());

        ajax_get_general($(target).find("option:selected").text());

    });

    function ajax_get_general(target_name) {

        $.ajax({
            type: "POST",
            dataType: 'json',
            url: '/blog/get_blog_detailed_type_list',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({
                'jsonrpc': "2.0",
                'method': "call",
                "params": {
                    'blog_type_general_id': target_name,
                }
            }),

            // data: JSON.stringify({'blog_type_id': target.id, 'is_Parent': is_Parent, 'is_search': is_search}),
            success: function (res) {
                // console.log(res.result.data);
                var data_list = res.result.data;
                $("#blog_type_detailed").empty();
                // 实际的应用中，这里的option一般都是用循环生成多个了
                for (var data_one in data_list) {
                    // html_val += "<dd><a href='/blog/'+data_list[data_one].blog_post_id>data_list[data_one].name</a></dd>"

                    var option = $("<option>").val(data_list[data_one]).text(data_list[data_one]);
                    $("#blog_type_detailed").append(option);
                }


                // $('.change_tab_blog_view').html(html_val);
            },
            error: function (data) {
                console.log("ERROR ", data);
            }
        });

    };

    $('#blog_type_detailed').find('option:eq(0)').select(function (e) {
        ajax_get_general($('#blog_type_general').find("option:selected").text());
    });
    $('#blog_type_detailed').find('option:eq(0)').trigger('select');


    $('.btn-blog-delect').click(function (e) {
        var choice = confirm("您确认要删除吗？", function () {
        }, null);
        if (choice) {


            var self_blog_checkbox = blog_checkbox;

            for (var i = 0; i < self_blog_checkbox.length; i++) {
                self_blog_checkbox[i] = parseInt(self_blog_checkbox[i])
            }

            console.log(self_blog_checkbox)

            $.ajax({
                type: "POST",
                dataType: 'json',
                url: '/web/dataset/call_kw',
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify(
                    {
                        'jsonrpc': "2.0",
                        'method': "unlink",
                        "params": {
                            'model': 'blog.post',
                            'method': "unlink",
                            'args': [self_blog_checkbox],
                            'kwargs': {},
                            'path': '',
                        }
                    }
                ),
                success: function (res) {
                    window.location.reload();
                },
                error: function (data) {
                    console.log("ERROR ", data);
                }
            });
        }
    });


    $('.o_chat_header_blog').click(function (e) {

        var e = e || window.event;
        var target = e.target || e.srcElement;

        click_checkbox(target);

        if (blog_checkbox.length > 0)
            $('.btn-blog-delect').show();
        else
            $('.btn-blog-delect').hide();
    });


    function click_checkbox(target) {

        console.log($(target));
        var is_hava = true;


        if ($(target).prop("checked")) {
            if ($.inArray(target.name, blog_checkbox) < 0)
                blog_checkbox.splice(0, 0, target.name);
        } else {

            while (is_hava) {
                if ($.inArray(target.name, blog_checkbox) >= 0)
                    blog_checkbox.splice($.inArray(target.name, blog_checkbox), 1);
                else
                    break;
            }
        }
        console.log(blog_checkbox)

    };


    $('.btn-publish').click(function (e) {
        var self = this;

        var e = e || window.event;
        var target = e.target || e.srcElement;
        console.log($(target));

        var blog_publish = 0;

        if ($(target).hasClass("btn-primary")) {
            blog_publish = 1;
        }
        else if ($(target).hasClass("btn-danger")) {
            blog_publish = 2;
        }


        $.ajax({
            type: "POST",
            dataType: 'json',
            url: '/blog/blog_all_publish',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({
                'jsonrpc': "2.0",
                'method': "call",
                "params": {
                    'blog_checkbox_list': blog_checkbox,
                    'blog_publish': blog_publish,
                }
            }),
            success: function (res) {

                window.location.reload();
                console.log(res);
            },
            error: function (data) {
                console.log("ERROR ", data);
            }
        });


    });

    $('.document_all_checkbox_blog').click(function (e) {

        var e = e || window.event;
        var target = e.target || e.srcElement;


        var approval_type = $("#document_tab").attr("data-now-tab");
        $("#main_column input[type='checkbox']").each(function () {
            $(this).prop('checked', $(target).prop('checked') || false);
            click_checkbox(this);
        });

        if (blog_checkbox.length > 0)
            $('.btn-blog-delect').show();
        else
            $('.btn-blog-delect').hide();


    });


});


function UploadFiles(files, content, func) {
    //这里files是因为我设置了可上传多张图片，所以需要依次添加到formData中
    var formData = new FormData();
    // for (var f in files) {
    //     formData.append("file", files[f]);
    // }

    var name_list = files.split("\\");
    files = name_list[name_list.length - 1];

    formData.append("file", files);
    formData.append("content", content);

    console.log(formData);

    $.ajax({
        data: formData,
        type: "POST",
        url: "/blog/create_attachment",
        // url: "#",
        cache: false,
        contentType: false,
        processData: false,
        success: function (imageUrl) {
            func("/web/content?id=" + imageUrl + "&download=true");
        },
        error: function () {
            console.log("uploadError");
        }
    })
};


function setIframeHeight(iframe) {
    if (iframe) {
        var iframeWin = iframe.contentWindow || iframe.contentDocument.parentWindow;
        if (iframeWin.document.body) {
            iframe.height = iframeWin.document.documentElement.scrollHeight ||
                iframeWin.document.body.scrollHeight;
        }
    }
};