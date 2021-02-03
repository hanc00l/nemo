$(function () {
    $('#btnsiderbar').click();
    $('#task_table').DataTable(
        {
            "paging": true,
            "serverSide": true,
            "autowidth": false,
            "sort": false,
            "pagingType": "full_numbers",//分页样式
            'iDisplayLength': 50,
            "dom": '<i><t><"bottom"lp>',
            "ajax": {
                "url": "/task-list",
                "type": "post",
                "data": function (d) {
                    init_dataTables_defaultParam(d);
                    return $.extend({}, d, {
                        "task_state": $('#task_state').val(),
                        "task_name": $('#task_name').val(),
                        "task_args": $('#task_args').val(),
                        "date_delta": $('#date_delta').val()
                    });
                }
            },
            columns: [
                {
                    data: "task_id",
                    width: "5%",
                    className: "dt-body-center",
                    title: '<input  type="checkbox" class="checkall" />',
                    "render": function (data, type, row) {
                        var strData = '<input type="checkbox" class="checkchild" value="' + row['task_id'] + '"/>';
                        return strData;
                    }
                },
                {
                    data: "index",
                    title: "序号",
                    width: "5%"
                },
                {
                    data: "task_name",
                    title: "任务名称",
                    width: "10%",
                    render: function (data, type, row, meta) {
                        var strData;
                        strData = '<a href="/task-info?task_id=' + row['task_id'] + '" target="_blank">' + data + '</a>';
                        return strData;
                    }
                },
                {
                    data: "state", title: "状态", width: "8%",
                    "render": function (data, type, row) {
                        if (data == 'STARTED' || data == 'RECEIVED') {
                            return data + '<button class="btn btn-sm btn-danger" type="button" onclick="stop_task(\'' + row['task_id'] + '\')" >&nbsp;中止&nbsp;</button>';
                        } else return data;
                    }
                },
                {
                    data: 'kwargs', title: '参数', width: '20%',
                    "render": function (data, type, row) {
                        var data = '<div style="width:100%;white-space:normal;word-wrap:break-word;word-break:break-all;">' + data + '</div>';
                        return data;
                    }
                },
                {data: 'result', title: '结果', width: '10%'},
                {data: 'received', title: '接收时间', width: '8%'},
                {data: 'started', title: '启动时间', width: '8%'},
                {data: 'runtime', title: '执行时长', width: '8%'},
                {
                    data: 'worker',
                    title: 'worker',
                    width: '8%',
                    "render": function (data, type, row) {
                        var data = '<div style="width:100%;white-space:normal;word-wrap:break-word;word-break:break-all;">' + data + '</div>';
                        return data;
                    }
                },
                {
                    title: "操作",
                    width: "8%",
                    "render": function (data, type, row, meta) {
                        var strDelete = "<a class=\"btn btn-sm btn-danger\" href=javascript:delete_task(\"" + row["task_id"] + "\") role=\"button\" title=\"Delete\"><i class=\"fa fa-trash-o\"></i></a>";
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
    //搜索
    $("#search").click(function () {
        $("#task_table").DataTable().draw(true);
    });
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

/**
 * 中止一个任务
 * @param task_id
 */
function stop_task(task_id) {
    swal({
            title: "确定要中止任务?",
            text: "中止任务！",
            type: "warning",
            showCancelButton: true,
            confirmButtonColor: "#DD6B55",
            confirmButtonText: "确认中止",
            cancelButtonText: "取消",
            closeOnConfirm: true
        },
        function () {
            $.post("/task-stop",
                {
                    "task-id": task_id,
                }, function (data, e) {
                    if (e === "success") {
                        $('#task_table').DataTable().draw(false);
                    }
                });
        });
}

/**
 * 删除一个任务
 * @param task_id
 */
function delete_task(task_id) {
    swal({
            title: "确定要删除?",
            text: "该操作会删除当前任务，请确保当前任务已完成或中止！",
            type: "warning",
            showCancelButton: true,
            confirmButtonColor: "#DD6B55",
            confirmButtonText: "确认删除",
            cancelButtonText: "取消",
            closeOnConfirm: true
        },
        function () {
            $.post("/task-delete",
                {
                    "task-id": task_id,
                }, function (data, e) {
                    if (e === "success") {
                        $('#task_table').DataTable().draw(false);
                    }
                });
        });
}