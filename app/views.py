# Create your views here.
from django.shortcuts import render
from django.views.generic import View
from pytubefix import YouTube
from urllib.error import HTTPError
from django.http import FileResponse
import os
from django.conf import settings
import subprocess

class home(View):
    def __init__(self,url=None):
        self.url = url
        self.index_listi = [] #so only the right choices are shown (aka not multiple 1080p ex and only working mp4)

    def get(self,request):
        return render(request,'app/home.html')  

    def post(self,request):
        # for fetching the video
        if request.POST.get('fetch-vid'):
            self.url = request.POST.get('given_url')
            try:
                video = YouTube(self.url)
                vidTitle,vidThumbnail = video.title,video.thumbnail_url
                qual,stream = [],[]
                seen_res=[] #so only the right choices are shown
                for i,vid in enumerate(video.streams.filter(mime_type='video/mp4',only_video=True)):
                    if vid.resolution not in seen_res:
                        qual.append(vid.resolution)
                        #print(vid.resolution)
                        stream.append(vid)

                        #only show one elem per resolution that is the proper one
                        self.index_listi.append(i)
                        seen_res.append(vid.resolution)
                context = {'vidTitle':vidTitle,'vidThumbnail':vidThumbnail,
                            'qual':qual,'stream':stream,
                            'url':self.url,'show_audio_only_button':True}
                return render(request, 'app/home.html', context)
            except HTTPError as e:
                print(e,1)
                return render(request, 'app/home.html', {'error': f"HTTP Error: {str(e)}"})
            except Exception as e:
                print(e,1)
                return render(request, 'app/home.html', {'error': f"An error occurred: {str(e)}"})
        # for downloading the video
        elif request.POST.get('download-vid'):
            self.url = request.POST.get('given_url')
            try:
                video = YouTube(self.url)
                req_post_get_downl_vid=request.POST.get('download-vid')
                print(req_post_get_downl_vid)
                if req_post_get_downl_vid!='audio_only':
                    chosen_qual = video.streams.filter(mime_type='video/mp4',only_video=True)[int(req_post_get_downl_vid) - 1] #selects the right audiofile! :) checked with:                 #print([vid.resolution for vid in video.streams.filter(mime_type='video/mp4',only_video=True)])                 
                    print('selected:',[vid.resolution for vid in video.streams.filter(mime_type='video/mp4',only_video=True)][int(req_post_get_downl_vid) - 1])

                chosen_qual_audio = video.streams.filter(only_audio=True,mime_type='audio/mp4')[-1]

                vid_output_path= os.path.join(settings.MEDIA_ROOT,'temp_video')
                aud_output_path= os.path.join(settings.MEDIA_ROOT,'temp_audio')
                fin_output_path= os.path.join(settings.MEDIA_ROOT,'temp_combined')
                if not os.path.exists(vid_output_path) or not os.path.exists(aud_output_path) or not os.path.exists(fin_output_path):
                    os.makedirs(vid_output_path)
                    os.makedirs(aud_output_path)                    
                    os.makedirs(fin_output_path)       

                if req_post_get_downl_vid!='audio_only':
                    video_file = chosen_qual.download(output_path=vid_output_path)
                audio_file = chosen_qual_audio.download(output_path=aud_output_path)
                video_filename = os.path.basename(audio_file)

                if req_post_get_downl_vid!='audio_only':
                    subprocess.run(['ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', os.path.join(fin_output_path,video_filename)])
                    output_filename=video_filename
                else:
                    subprocess.run(['ffmpeg', '-i', audio_file, '-c:a', 'aac', os.path.join(fin_output_path,video_filename)])
                    output_filename=video_filename.strip('.mp4')+'.m4a'

                # Prepare the file response for downloading
                response = FileResponse(open(os.path.join(fin_output_path,video_filename), 'rb'), as_attachment=True, filename=output_filename)

                # Optionally, clean up the file after streaming it to the user
                os.remove(os.path.join(aud_output_path,video_filename))
                os.remove(os.path.join(fin_output_path,video_filename))
                if req_post_get_downl_vid!='audio_only':
                    os.remove(os.path.join(vid_output_path,video_filename))
            
                
                return response
                    
            except HTTPError as e:
                print(e,2)
                return render(request, 'app/home.html', {'error': f"HTTP Error: {str(e)}"})
            except Exception as e:
                print(e,2)
                return render(request, 'app/home.html', {'error': f"An error occurred: {str(e)}"})

        return render(request,'app/home.html')  
