async function post_command(body) {
    try {
        return await $.ajax({
            type: "POST",
            contentType: "application/json",
            url: APPLICATION.SERVER_URL + "/command",
            data: JSON.stringify(body)
        });
    }
    catch(error) {
        console.error(error);
    }
}

async function update_container(device_id, container_name) {
    await post_command(
        {
            command: "update_container",
            id: device_id,
            container_name: container_name
        }
    )
}

async function start_container(device_id, container_name) {
    await post_command(
        {
            command: "start_container",
            id: device_id,
            container_name: container_name
        }
    )
}

async function stop_container(device_id, container_name) {
    await post_command(
        {
            command: "stop_container",
            id: device_id,
            container_name: container_name
        }
    )
}
