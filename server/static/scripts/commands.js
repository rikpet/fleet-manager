async function post_command(command_endpoint, body) {
    try {
        return await $.ajax({
            type: "POST",
            contentType: "application/json",
            url: APPLICATION.SERVER_URL + "/" + command_endpoint,
            data: JSON.stringify(body)
        });
    }
    catch(error) {
        console.error(error);
    }
}

async function update_container(device_id, container_name) {
    await post_command(
        "container-command",
        {
            command: "update_container",
            id: device_id,
            container_name: container_name
        }
    )
}

async function start_container(device_id, container_name) {
    await post_command(
        "container-command",
        {
            command: "start_container",
            id: device_id,
            container_name: container_name
        }
    )
}

async function stop_container(device_id, container_name) {
    await post_command(
        "container-command",
        {
            command: "stop_container",
            id: device_id,
            container_name: container_name
        }
    )
}

async function remove_device(device_id) {
    await post_command(
        "device-command",
        {
            command: "remove_device",
            id: device_id
        }
    )
}