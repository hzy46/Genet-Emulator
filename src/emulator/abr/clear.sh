ps aux | grep ${video_server_port} | grep video_server | awk '{print $2}' | xargs kill
ps aux | grep ${abr_server_port} | grep virtual_browser | awk '{print $2}' | xargs kill
ps aux | grep chrome | awk '{print $2}' | xargs kill
