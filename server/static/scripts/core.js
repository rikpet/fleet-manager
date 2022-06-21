const APPLICATION = {
    SERVER_URL:  "http://" + document.domain + ':' + location.port
}

$(document).ready(function(){
    render_ui(fleet_information)

    var socket = io.connect(APPLICATION.SERVER_URL);

    socket.on('connect', function() {
        console.debug('Socket connected');
    });

    socket.on('event_stream', function(event) {
        console.debug(event);
        render_ui(event)
    });
});

async function render_ui(event) {
    for (var device_id in event) {
        await update_device_last_updated(device_id, event[device_id].telemetry.timestamp)
       // await update_device_status(device_id, event[device_id]['online'])
        await update_device_cpu_load(device_id, event[device_id].telemetry.cpu_load)
        await update_device_memory_usage(device_id, event[device_id].telemetry.memory_usage)

        const containers = Object.values(event[device_id].telemetry.containers)
        containers.forEach(async container => {
            await update_container_status(container['id'], container['status'])
            await update_container_update_status(container['id'], container['update_available'])
        })
    }
}

async function update_device_last_updated(device_id, last_updated) {
    $(`#device-last-updated-${device_id}`).text(last_updated)
}

async function update_device_status(device_id, device_status) {
    device_status_indicator_object = $(`#device-status-indicator-${device_id}`)
    device_status_text_object = $(`#device-status-text-${device_id}`)

    if (device_status && device_status_indicator_object.hasClass('bg-danger')) {
        device_status_indicator_object.removeClass('bg-danger').addClass('bg-success')
        device_status_text_object.text('online')
    }
    else if (!device_status && device_status_indicator_object.hasClass('bg-success')) {
        device_status_indicator_object.removeClass('bg-success').addClass('bg-danger')
        device_status_text_object.text('offline')
    }
}

async function update_device_cpu_load(device_id, cpu_load) {
    $(`#device-cpu-${device_id}`).text(`${cpu_load} %`)
}

async function update_device_memory_usage(device_id, memory_load) {
    $(`#device-memory-${device_id}`).text(`${memory_load} %`)
}

async function update_container_status(container_id, container_status) {
    container_status_indicator_object = $(`#container-status-indicator-${container_id}`)
    container_status_text_object = $(`#container-status-text-${container_id}`)

    if (container_status == 'running' && container_status_indicator_object.hasClass('bg-danger')) {
        container_status_indicator_object.removeClass('bg-danger').addClass('bg-success')
        container_status_text_object.text(container_status)
    }
    else if (container_status != 'running' && container_status_indicator_object.hasClass('bg-success')) {
        container_status_indicator_object.removeClass('bg-success').addClass('bg-danger')
        container_status_text_object.text(container_status)
    }
}

async function update_container_update_status(container_id, container_update_available) {
    container_update_status_object =  $(`#container-update-status-${container_id}`)
    
    if (container_update_available == null) {
        container_update_status_object
            .attr('class', 'badge bg-secondary')
            .text('No information')
    }
    else if (container_update_available) {
        container_update_status_object
            .attr('class', 'badge bg-warning')
            .text('New version available')
    }
    else if (!container_update_available) {
        container_update_status_object
            .attr('class', 'badge bg-success')
            .text('Up to date')
    }
}