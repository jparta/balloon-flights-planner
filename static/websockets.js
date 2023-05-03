$(document).ready(function() {

    namespace = '/';
    var socket = io(namespace);

    socket.on('sim_progress', function(msg, cb) {
        $('#log').append('<br>' + $('<div/>').text('Sim progress: ' + msg.data).html());
        if (cb)
            cb();
    });
    
    $('#run_sim').on("click", (event) => {
        socket.emit('run_sim');
        return false;
    });
});
