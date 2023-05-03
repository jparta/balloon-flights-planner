$(document).ready(function() {

    namespace = '/';
    var socket = io(namespace);

    socket.on('connect', function() {
        socket.emit('my_event', {data: 'connected to the SocketServer...'});
    });

    socket.on('my_response', function(msg, cb) {
        $('#log').append('<br>' + $('<div/>').text('logs #' + msg.count + ': ' + msg.data).html());
        if (cb)
            cb();
    });
    socket.on('sim_progress', function(msg, cb) {
        $('#log').append('<br>' + $('<div/>').text('Sim progress: ' + msg.data).html());
        if (cb)
            cb();
    });
    $('#run_sim').on("click", (event) => {
        socket.emit('run_sim');
        return false;
    });
    $('form#emit').submit(function(event) {
        socket.emit('my_event', {data: $('#emit_data').val()});
        return false;
    });
    $('form#disconnect').submit(function(event) {
        socket.emit('disconnect_request');
        return false;
    });
});
