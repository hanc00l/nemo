$(function () {
    $('#btnsiderbar').click();
    $('#select_org_id_search').val($('#hidden_org_id').val());
    $('#select_org_id_task').val($('#hidden_org_id').val());
    //加载nmap配置
    load_nmap_config();
    // //获取任务的状态信息
    // get_task_status();
    setInterval(function () {
        get_task_status();
    }, 60 * 1000);
    //搜索
    $("#search").click(function () {
        $("#ip_table").DataTable().draw(true);
    });
    //新建任务窗口
    $("#create_task").click(function () {
        var checkIP = [];
        $('#ip_table').DataTable().$('input[type=checkbox]:checked').each(function (i) {
            checkIP[i] = $(this).val();
        });
        $('#text_target').val(checkIP.join("\n"));
        $('#newTask').modal('toggle');
    });
    //执行新建任务Button
    $("#start_task").click(function () {
        const target = $('#text_target').val();
        var port = $('#input_port').val();
        var rate = $('#input_rate').val();
        if (!target) {
            swal('Warning', '请至少输入一个Target', 'error');
            return;
        }
        if (!port) port = "--top-ports 1000";
        if (!rate) rate = 5000;
        $.post("/task-start-portscan",
            {
                "target": target,
                "port": port,
                'rate': rate,
                'portscan': $('#checkbox_portscan').is(":checked"),
                'nmap_tech': $('#select_tech').val(),
                'bin': $('#select_bin').val(),
                'org_id': $('#select_org_id_task').val(),
                'iplocation': $('#checkbox_iplocation').is(":checked"),
                'webtitle': $('#checkbox_webtitle').is(":checked"),
                'whatweb': $('#checkbox_whatweb').is(":checked"),
                'ping': $('#checkbox_ping').is(":checked"),
                'fofasearch': $('#checkbox_fofasearch').is(":checked"),
                'shodansearch': $('#checkbox_shodansearch').is(":checked"),
                'subtask': $('#checkbox_subtask').is(":checked")
            }, function (data, e) {
                if (e === "success" && data['status'] == 'success') {
                    swal({
                        title: "新建任务成功！",
                        text: "TaskId:" + data['result']['task-id'],
                        type: "success",
                        confirmButtonText: "确定",
                        confirmButtonColor: "#41b883",
                        closeOnConfirm: true,
                    },
                        function () {
                            $('#newTask').modal('hide');
                        });
                } else {
                    swal('Warning', "添加任务失败!", 'error');
                }
            });

    });
    //列表全选
    $(".checkall").click(function () {
        var check = $(this).prop("checked");
        $(".checkchild").prop("checked", check);
    });
    $("#checkbox_portscan").click(function () {
        if (this.checked) {
            $("#input_port").prop("disabled", false);
            $("#select_tech").prop("disabled", false);
            $("#select_bin").prop("disabled", false);
            $("#input_rate").prop("disabled", false);
            $("#checkbox_webtitle").prop("disabled", false);
            $("#checkbox_whatweb").prop("disabled", false);
            $("#checkbox_ping").prop("disabled", false);
        } else {
            $("#input_port").prop("disabled", true);
            $("#select_tech").prop("disabled", true);
            $("#select_bin").prop("disabled", true);
            $("#input_rate").prop("disabled", true);
            $("#checkbox_webtitle").prop("disabled", true);
            $("#checkbox_whatweb").prop("disabled", true);
            $("#checkbox_ping").prop("disabled", true);
        }
    })

    $("#export_excel").click(function () {
        var url = 'ip-export?';
        url += get_export_options();

        window.open(url);
    });

    $("#ip_statistics").click(function () {
        var url = 'ip-statistics?';
        url += get_export_options();

        window.open(url);
    });

    $("#ip_memo_export").click(function () {
        var url = 'ip-memo-export?';
        url += get_export_options();

        window.open(url);
    });

    //IP列表
    $('#ip_table').DataTable(
        {
            "paging": true,
            "serverSide": true,
            "autowidth": false,
            "sort": false,
            "pagingType": "full_numbers",//分页样式
            'iDisplayLength': 50,
            "dom": '<i><t><"bottom"lp>',
            "ajax": {
                "url": "/ip-list",
                "type": "post",
                "data": function (d) {
                    init_dataTables_defaultParam(d);
                    return $.extend({}, d, {
                        "org_id": $('#select_org_id_search').val(),
                        "domain_address": $('#domain_address').val(),
                        "ip_address": $('#ip_address').val(),
                        "port": $('#port').val(),
                        "content": $('#content').val(),
                        "iplocation": $('#iplocation').val(),
                        "port_status": $('#port_status').val(),
                        "color_tag": $('#select_color_tag').val(),
                        "memo_content": $('#memo_content').val(),
                        "date_delta": $('#date_delta').val()
                    });
                }
            },
            columns: [
                {
                    data: "id",
                    width: "5%",
                    className: "dt-body-center",
                    title: '<input  type="checkbox" class="checkall" />',
                    "render": function (data, type, row) {
                        var strData = '<input type="checkbox" class="checkchild" value="' + row['ip'] + '"/>';
                        if (row['memo_content']) {
                            strData += '&nbsp;<span class="badge badge-primary" data-toggle="tooltip" data-html="true" title="' + html2Escape(row['memo_content']) + '"><i class="fa fa-flag"></span>';
                        }
                        return strData;
                    }
                },
                {
                    data: "index",
                    title: "序号",
                    width: "5%"
                },
                {
                    data: "ip",
                    title: "IP地址",
                    width: "10%",
                    render: function (data, type, row, meta) {
                        var strData;
                        if (row['color_tag']) {
                            strData = '<h5><a href="/ip-info?ip=' + data + '" target="_blank" class="badge ' + row['color_tag'] + '">' + data + '</a></h5>';
                        }
                        else {
                            strData = '<a href="/ip-info?ip=' + data + '" target="_blank">' + data + '</a>';
                        }
                        return strData;
                    }
                },
                { data: "location", title: "归属地", width: "12%" },
                {
                    data: "port", title: "开放端口", width: "15%",
                    "render": function (data, type, row, meta) {
                        var strData = '<div style="width:100%;white-space:normal;word-wrap:break-word;word-break:break-all;">';
                        var pre_link = "";
                        for (var j = 0, len = data.length; j < len; j++) {
                            //提取出端口和状态
                            var port = data[j].replace(/\[.+?\]/g, "");
                            var status = data[j].replace(/^.+?\[/g, "");
                            strData += pre_link;
                            strData += '<a href="';
                            if (port == 443 || port == 8443) strData += "https";
                            else strData += 'http';
                            // 快速链接地址
                            strData += '://' + row['ip'] + ':' + port + '" target="_blank">' + port + '</a>';
                            // 端口状态
                            if (status != port) strData += "[" + status;

                            pre_link = ",";
                        }
                        strData += '</div>'
                        return strData;
                    }
                },
                {
                    data: "title", title: "标题", width: "20%",
                    "render": function (data, type, row, meta) {
                        var title = data.substr(0, 100);
                        if (data.length > 100) title += '......';
                        var strData = '<div style="width:100%;white-space:normal;word-wrap:break-word;word-break:break-all;">' + title + '</div>'
                        return strData;
                    }
                },
                {
                    data: "banner", title: "Banner", width: "20%",
                    "render": function (data, type, row, meta) {
                        var title = data.substr(0, 100);
                        if (data.length > 100) title += '......';
                        var strData = '<div style="width:100%;white-space:normal;word-wrap:break-word;word-break:break-all;">' + title + '</div>'
                        return strData;
                    }
                },
                {
                    title: "操作",
                    width: "8%",
                    "render": function (data, type, row, meta) {
                        var strDelete = "<a class=\"btn btn-sm btn-danger\" href=javascript:delete_ip(" + row.id + ") role=\"button\" title=\"Delete\"><i class=\"fa fa-trash-o\"></i></a>";
                        return strDelete;
                    }
                }
            ],
            infoCallback: function (settings, start, end, max, total, pre) {
                return "共<b>" + total + "</b>条记录，当前显示" + start + "到" + end + "记录";
            },
            drawCallback: function (setting) {
                var _this = $(this);
                var tableId = _this.attr('id');
                var pageDiv = $('#' + tableId + '_paginate');
                pageDiv.append(
                    '<i class="fa fa-arrow-circle-o-right fa-lg" aria-hidden="true"></i><input id="' + tableId + '_gotoPage" type="text" style="height:20px;line-height:20px;width:40px;"/>' +
                    '<a class="paginate_button" aria-controls="' + tableId + '" tabindex="0" id="' + tableId + '_goto">Go</a>')
                $('#' + tableId + '_goto').click(function (obj) {
                    var page = $('#' + tableId + '_gotoPage').val();
                    var thisDataTable = $('#' + tableId).DataTable();
                    var pageInfo = thisDataTable.page.info();
                    if (isNaN(page)) {
                        $('#' + tableId + '_gotoPage').val('');
                        return;
                    } else {
                        var maxPage = pageInfo.pages;
                        var page = Number(page) - 1;
                        if (page < 0) {
                            page = 0;
                        } else if (page >= maxPage) {
                            page = maxPage - 1;
                        }
                        $('#' + tableId + '_gotoPage').val(page + 1);
                        thisDataTable.page(page).draw('page');
                    }
                })
            }
        }
    );//end datatable
    $(".checkall").click(function () {
        var check = $(this).prop("checked");
        $(".checkchild").prop("checked", check);
    });
    $('[data-toggle="tooltip"]').tooltip();
});
/**
 * 移除 dataTables默认参数，并设置分页值
 * @param param
 */
function init_dataTables_defaultParam(param) {
    for (var key in param) {
        if (key.indexOf("columns") == 0 || key.indexOf("order") == 0 || key.indexOf("search") == 0) { //以columns开头的参数删除
            delete param[key];
        }
    }
    param.pageSize = param.length;
    param.pageNum = (param.start / param.length) + 1;
}

function load_nmap_config() {
    $.post("/adv-config-list", function (data) {
        $('#input_port').val(data['nmap']['port']);
        $('#select_tech').val(data['nmap']['tech']);
        $('#input_rate').val(data['nmap']['rate']);
        $('#checkbox_ping').prop("checked", data['nmap']['ping']);
    });
}
//删除一个IP
function delete_ip(id) {
    swal({
        title: "确定要删除?",
        text: "该操作会删除这个IP的所有信息！",
        type: "warning",
        showCancelButton: true,
        confirmButtonColor: "#DD6B55",
        confirmButtonText: "确认删除",
        cancelButtonText: "取消",
        closeOnConfirm: true
    },
        function () {
            $.ajax({
                type: 'post',
                url: '/ip-delete/' + id,
                success: function (data) {
                    $("#ip_table").DataTable().draw(false);
                },
                error: function (xhr, type) {
                }
            });
        });
}
function get_task_status() {
    $.post("/dashboard-task-info", function (data) {
        $("#span_show_task").html(data['task_info']);
    });
}

function html2Escape(sHtml) {
    var temp = document.createElement("div");
    (temp.textContent != null) ? (temp.textContent = sHtml) : (temp.innerText = sHtml);
    var output = temp.innerHTML.replace(/\"/g, "&quot;").replace(/\'/g, "&acute;");
    temp = null;

    return output;
}

function get_export_options() {
    var url = '';
    url += 'org_id=' + encodeURI($('#select_org_id_search').val());
    url += '&domain_address=' + encodeURI($('#domain_address').val());
    url += '&ip_address=' + encodeURI($('#ip_address').val());
    url += '&port=' + encodeURI($('#port').val());
    url += '&content=' + encodeURI($('#content').val());
    url += '&iplocation=' + encodeURI($('#iplocation').val());
    url += '&port_status=' + encodeURI($('#port_status').val());
    url += '&color_tag=' + encodeURI($('#select_color_tag').val());
    url += '&memo_content=' + encodeURI($('#memo_content').val());
    url += '&date_delta=' + encodeURI($('#date_delta').val());


    return url;
}