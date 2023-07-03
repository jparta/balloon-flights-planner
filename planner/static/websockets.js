$(document).ready(function() {

    namespace = '/';
    var socket = io(namespace);

    socket.on('sim_progress', function(msg, cb) {
        const progress_line = $('<span/>').text(msg.data).html()
        $('#sim_progress').append('<br>' + progress_line);
        if (cb)
            cb();
    });

    $('#run_sim').on("click", (event) => {
        socket.emit('run_sim');
        return false;
    });
});
