/**
 * Created by 123 on 2017/7/6.
 */



console.log("demo %%%%%%%%");

// console.log($('.o_cp_left'));
//
// alert($('.o_cp_left'))
//
// $('.o_cp_left').hide();


// $("div.this_my_product_type.o_form_field_many2manytags").bind('DOMNodeInserted', function (e) {
//     alert('11111: ' + $(e.target).html());
// });


// $(".my_load_file_view").on('change', function () {
//     var value = $(this).val();
//     value = value.split("\\")[2];
//     console.log(value)
// })


// $("#file_click_me").click(function (e) {
//     var e = e || window.event;
//     var target = e.target || e.srcElement;
//     var product_id_list = "";
//     var product_code_str = "";
//     $(".badge.dropdown").each(function () {
//         product_id_list += $(this).attr("data-id");
//         product_code_str += this.innerText;
//     });
//     var r = /\[(.+?)\]/g;
//     var product_code_list = product_code_str.match(r);
//     product_code_str = "";
//     for (var index in product_code_list)
//         product_code_str += product_code_list[index];
//     product_code_str1 = product_code_str.replace(/\[/g, ' ').replace(/]/g, '');
//
//     product_code_str = product_code_str.replace(/]/g, '');
//
//     $.ajax({
//         type: "GET",
//         url: "http://localhost:8088",
//         // dataType: 'json/html',
//         success: function (data) {
//             if (data.result == '1') {
//                 var cur_type = $("input.this_my_type_file").val();
//                 cur_type = cur_type.replace(/"/g, '');
//
//
//                 $.ajax({
//                     type: "POST",
//                     dataType: 'json',
//                     url: '/get_default_version',
//                     contentType: "application/json; charset=utf-8",
//                     data: JSON.stringify({
//                         'jsonrpc': "2.0",
//                         'method': "call",
//                         "params": {
//                             'id': product_id_list,
//                             'type': cur_type,
//                         }
//                     }),
//                     success: function (res) {
//                         console.log(res.result.data);
//
//                         var remote_file = cur_type.toUpperCase() + '/' + cur_type.toUpperCase() + '_' + product_code_str.replace(/\./g, '_') + '_v';
//
//                         var remote_file1 = cur_type.toUpperCase() + '/' + product_code_str1.trim().split('.').join('/') + '/v' + res.result.data +
//                             '/' + cur_type.toUpperCase() + '_' + product_code_str1.trim().split('.').join('_') + '_v' + res.result.data;
//
//
//                         $.ajax({
//                             type: "GET",
//                             url: "http://localhost:8088/uploadfile?id=" + product_id_list + "&remotefile=" + remote_file1,
//                             success: function (data) {
//                                 console.log(data);
//                                 if (data.result == '1') {
//                                     console.log(data.path)
//                                     $(".this_my_filename").val(data.choose_file_name)
//                                     $(".this_my_remote_path").val(data.path)
//                                 }
//                             },
//                             error: function (error) {
//                                 alert("上传失败,请打开代理软件");
//                                 console.log(error);
//                             }
//                         });
//
//
//                     },
//                     error: function (data) {
//                         console.log("ERROR ", data);
//                     }
//                 });
//
//
//             }
//             else {
//                 alert("请打开代理软件!");
//             }
//         },
//         error: function (error) {
//             alert("上传失败,请打开代理软件");
//         }
//     });
//
// });
