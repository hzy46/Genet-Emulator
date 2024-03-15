ps aux | grep run_single_test | awk '{print $2}' | xargs kill
ps aux | grep mm-loss | awk '{print $2}' | xargs kill
ps aux | grep video_server | awk '{print $2}' | xargs kill
ps aux | grep virtual_browser | awk '{print $2}' | xargs kill
ps aux | grep chrome | awk '{print $2}' | xargs kill
ps aux | grep virtual_browser | awk '{print $2}' | xargs kill
