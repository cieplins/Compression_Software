import ffmpeg
from scenedetect import video_splitter
from scenedetect import VideoManager
from scenedetect import SceneManager
from moviepy.editor import *
from ffmpeg_quality_metrics import FfmpegQualityMetrics as ffqm
import subprocess

#Content-aware scene detection:
from scenedetect.detectors import ContentDetector

#Find scenes
def find_scenes(video_path, threshold=30.0):
    # Create our video & scene managers, then add the detector.
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold))

    # Improve processing speed by downscaling before processing.
    video_manager.set_downscale_factor(downscale_factor=1)

    # Start the video manager and perform the scene detection.
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    # Each returned scene is a tuple of the (start, end) timecode.
    return scene_manager.get_scene_list()

#Compress
def compress(conv_video, ref_video, value):
    p = subprocess.Popen(['ffmpeg', '-y', '-i', ref_video , '-c:v', 'libx264', '-b:v', value, '-loglevel', 'quiet', '-preset', 'fast', '-pass', '1', '-an', '-f', 'mp4', 'NUL'])
    p.wait()
    p = subprocess.Popen(['ffmpeg', '-y','-i', ref_video , '-c:v', 'libx264', '-b:v', value, '-loglevel', 'quiet', '-preset', 'fast', '-pass', '2', '-c:a', 'copy', conv_video])
    p.wait()
    return 0

#Check vmaf
def check_vmaf(conv_video, ref_video):
    p = subprocess.run(['ffmpeg_quality_metrics', conv_video, ref_video, '-m', 'vmaf', '--metrics', 'vmaf'], capture_output=True)
    s = str(p)
    start = s.find('"average":') + 11
    end = s.find('"average":') + 15
    current_vmaf = s[start:end]
    return current_vmaf

#Increase bitrate
def add_br(conv_video, ref_video, br0):
    for i in range(2):
        br0 += i
    br_value = "{}k".format(br0)
    compress(conv_video, ref_video, br_value)
    vmaf_now = check_vmaf(conv_video, ref_video)
    print("this is vmaf_now")
    print(vmaf_now)
    print("This is br_value")
    print(br_value)
    vmaf_now_f = float(vmaf_now)
    return vmaf_now_f

#Compress until wanted vmaf is obtained
def compress_scene(conv_video, ref_video, br_init_k, br_init, vmaf_wanted):
#Compress and check vmaf for initial bitrate
    compress(conv_video, ref_video, br_init_k)
    vmaf_current = check_vmaf(conv_video, ref_video)
    vmaf_current_f = float(vmaf_current)
    vmaf_wanted_i = int(vmaf_wanted)

#If current vmaf value is not your wanted one, increase bitrate and check again

    while vmaf_current_f <= (vmaf_wanted_i + 2):
        if br_init >= 30:
            if vmaf_current_f >= (vmaf_wanted_i - 2):
                print("Done")
                break
            elif vmaf_current_f <= (vmaf_wanted_i - 30):
                print("Vmaf too low (30)")
                vmaf_current_f = add_br(conv_video, ref_video, br_init)
                br_init += 200
            elif vmaf_current_f <= (vmaf_wanted_i - 20):
                print("Vmaf too low (20)")
                vmaf_current_f = add_br(conv_video, ref_video, br_init)
                br_init += 100
            elif vmaf_current_f <= (vmaf_wanted_i - 10):
                print("Vmaf too low (10)")
                vmaf_current_f = add_br(conv_video, ref_video, br_init)
                br_init += 50
            else:
                print("Vmaf too low")
                vmaf_current_f = add_br(conv_video, ref_video, br_init)
                br_init += 10
        else:
            break


    while vmaf_current_f >= (vmaf_wanted_i - 2):
        if br_init >= 30:
            if vmaf_current_f <= (vmaf_wanted_i + 2):
                print("Done")
                break
            elif vmaf_current_f >= (vmaf_wanted_i + 30):
                print("Vmaf too high (30)")
                vmaf_current_f = add_br(conv_video, ref_video, br_init)
                br_init -= 200
            elif vmaf_current_f >= (vmaf_wanted_i + 20):
                print("Vmaf too high (20)")
                vmaf_current_f = add_br(conv_video, ref_video, br_init)
                br_init -= 100
            elif vmaf_current_f >= (vmaf_wanted_i + 10):
                print("Vmaf too high (10)")
                vmaf_current_f = add_br(conv_video, ref_video, br_init)
                br_init -= 50
            else:
                print("Vmaf too high")
                vmaf_current_f = add_br(conv_video, ref_video, br_init)
                br_init -= 10
        else:
            break

#Here put your initial values of bitrate and your wanted vmaf value
br_init_k = '1000k'
br_init = 999
#This part is to be changed accordingly to needs
vmaf_wanted = '60'
input_name = 'you_1080'
full_video_name = "you_1080.mp4"
compressed_name = "you_1080_compressed.mp4"

input_video_pth = [full_video_name]
scenes = find_scenes(full_video_name)
video_splitter.split_video_ffmpeg(input_video_pth, scenes, 'you_1080_$SCENE_NUMBER.mp4', input_name, arg_override='-c:v libx264 -preset fast -crf 21 -c:a aac', hide_progress=False, suppress_output=False)

vmaf_wanted_i = int(vmaf_wanted)
scene_n = 1
list_clips = []
for i in range(len(scenes)):
    if i < 9:
        con_v = "conv_00{}.mp4".format(scene_n)
        ref_v = "%s_00{}.mp4".format(scene_n) % input_name
        print(ref_v)
        compress_scene(con_v, ref_v, br_init_k, br_init, vmaf_wanted)
        clip = VideoFileClip(con_v)
        duration = clip.duration
        clip_n = "clip{}".format(scene_n)
        print(clip_n)
        clip_n = clip.subclip(0, duration)
        list_clips.append(clip_n)
        scene_n += 1
    elif i < 100:
        con_v = "conv_0{}.mp4".format(scene_n)
        ref_v = "%s_0{}.mp4".format(scene_n) % input_name
        print(ref_v)
        compress_scene(con_v, ref_v, br_init_k, br_init, vmaf_wanted)
        clip = VideoFileClip(con_v)
        duration = clip.duration
        clip_n = "clip{}".format(scene_n)
        print(clip_n)
        clip_n = clip.subclip(0, duration)
        list_clips.append(clip_n)
        scene_n += 1
    else:
        con_v = "conv_{}.mp4".format(scene_n)
        ref_v = "%s_{}.mp4".format(scene_n) % input_name
        print(ref_v)
        compress_scene(con_v, ref_v, br_init_k, br_init, vmaf_wanted)
        clip = VideoFileClip(con_v)
        duration = clip.duration
        clip_n = "clip{}".format(scene_n)
        print(clip_n)
        clip_n = clip.subclip(0, duration)
        list_clips.append(clip_n)
        scene_n += 1


print(list_clips)
final = concatenate_videoclips(list_clips)
final.write_videofile(compressed_name)
