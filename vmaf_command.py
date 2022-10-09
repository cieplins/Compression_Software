command = "/home/cieplins/vmaf/libvmaf/build/tools/vmafossexec yuv420p 1920 1080 {} {} " \
          "/home/cieplins/vmaf/model/vmaf_v0.6.1.json --log-fmt json --log myvmaf.json --thread 20 " \
          "--phone-model".format(current_scene_path, current_scene_c_path)
