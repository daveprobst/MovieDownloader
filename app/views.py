# Create your views here.
from django.shortcuts import render
from django.views.generic import View
from pytubefix import YouTube
from urllib.error import HTTPError
from django.http import FileResponse
import os
from django.conf import settings
import subprocess
import urllib.request

#NEEDS FIXING
'''
Nothing for now :)
'''

class home(View):
    def __init__(self,url=None):
        self.url = url

    def get(self,request):
        return render(request,'app/home.html')  

    def post(self,request):
        # for fetching the video
        if request.POST.get('fetch-vid'):
            self.url = request.POST.get('given_url')
            try:
                video = YouTube(self.url)
                vidTitle,vidThumbnail = video.title,video.thumbnail_url
                qual,stream_and_sel_idx_list= [],[]
                
                seen_res=[] #so only the right choices are shown
                for i,vid in enumerate(video.streams.filter(mime_type='video/mp4',progressive=False,only_video=True)):
                    #print(vid.resolution,vid.fps,vid.mime_type,vid.video_codec,end='') for checking
                    if vid.resolution not in seen_res:
                        #print(' | selected') for checking
                        qual.append(vid.resolution)
                        stream_and_sel_idx_list.append([i,vid])

                        seen_res.append(vid.resolution)     #only show one elem per resolution that is the proper one
                    #else: for checking
                        #print('') for checking
                context = {'vidTitle':vidTitle,'vidThumbnail':vidThumbnail,
                            'qual':qual,'stream_and_sel_idx_list':stream_and_sel_idx_list,
                            'url':self.url,'show_audio_only_button':True,}
                return render(request, 'app/home.html', context)
            except HTTPError as e:
                print(e)
                return render(request, 'app/home.html', {'error': f"HTTP Error: {str(e)}"})
            except Exception as e:
                print(e)
                return render(request, 'app/home.html', {'error': f"An error occurred: {str(e)}"})
            
        # for downloading the video
        elif request.POST.get('download-vid'):
            vid_output_path= os.path.join(settings.MEDIA_ROOT,'temp_video')
            aud_output_path= os.path.join(settings.MEDIA_ROOT,'temp_audio')
            fin_output_path= os.path.join(settings.MEDIA_ROOT,'temp_combined')
            if not os.path.exists(vid_output_path) or not os.path.exists(aud_output_path) or not os.path.exists(fin_output_path):
                os.makedirs(vid_output_path)
                os.makedirs(aud_output_path)                    
                os.makedirs(fin_output_path)  
            self.url = request.POST.get('given_url')
            try:
                video = YouTube(self.url)
                req_post_get_downl_vid=request.POST.get('download-vid')
                if req_post_get_downl_vid!='audio_only':
                    chosen_qual = video.streams.filter(mime_type='video/mp4',only_video=True)[int(req_post_get_downl_vid)] #selects the right videofile!
                    print('selected:',chosen_qual.resolution) # for check (resolution)

                chosen_qual_audio = video.streams.filter(only_audio=True,mime_type='audio/mp4')[-1]     

                if req_post_get_downl_vid!='audio_only':
                    video_file = chosen_qual.download(output_path=vid_output_path)
                audio_file = chosen_qual_audio.download(output_path=aud_output_path)
                video_filename = os.path.basename(audio_file)

                if req_post_get_downl_vid!='audio_only':
                    subprocess.run(['ffmpeg', '-i', video_file, '-i', audio_file, '-pix_fmt', 'yuv420p','-c:v','copy' ,'-c:a', 'aac', os.path.join(fin_output_path,video_filename)])
                    output_filename=video_filename
                else:
                    output_filename=video_filename.strip('.mp4')+'.m4a'
                    def unique_thumbnail_name_append(url): #create unique string to append so that all saved thumbnails are unique!
                        if 'https://i.ytimg.com/vi' in url:
                            return url[23:34]
                        else:
                            print("thumbnail_name is not unique! check if thumbnail url still follows this structure: 'https://i.ytimg.com/vi/'+'...'")
                            return ''
                    ut_name=unique_thumbnail_name_append(video.thumbnail_url)
                    thumbnail=urllib.request.urlretrieve(video.thumbnail_url,os.path.join(settings.MEDIA_ROOT,f'temp_audio/{ut_name}thumbnail.jpg'))[0]
                    subprocess.run(['ffmpeg', '-i', audio_file, '-i', thumbnail, '-c', 'copy', '-disposition:v', 'attached_pic', os.path.join(fin_output_path,output_filename)]) #code that didn't work:                     subprocess.run(['ffmpeg', '-i', audio_file, '-i', thumbnail, '-c:a', 'aac', '-c:t', 'copy', '-disposition:v', 'attached_pic', os.path.join(fin_output_path,video_filename)])

                # Prepare the file response for downloading
                response = FileResponse(open(os.path.join(fin_output_path,output_filename), 'rb'), as_attachment=True, filename=output_filename)  #<- ERROR
                
                return response
                    
            except HTTPError as e:
                print(e)
                return render(request, 'app/home.html', {'error': f"HTTP Error: {str(e)}"})
            except Exception as e:
                print(e)
                return render(request, 'app/home.html', {'error': f"An error occurred: {str(e)}"})
            finally: #Clean up the files after streaming it to the user regardless of if an error is thrown
                if req_post_get_downl_vid=='audio_only': #In case error is thrown before this statement is run in try block
                    output_filename=video_filename.strip('.mp4')+'.m4a'
                    if os.path.exists(os.path.join(aud_output_path,ut_name,thumbnail)): #remove thumbnail in case only audio
                        os.remove(os.path.join(aud_output_path,ut_name,thumbnail))
                if os.path.exists(os.path.join(aud_output_path,video_filename)): #remove audio_file
                    os.remove(os.path.join(aud_output_path,video_filename))
                if os.path.exists(os.path.join(fin_output_path,output_filename)): #remove combined_file
                    print('combined file removed')
                    os.remove(os.path.join(fin_output_path,output_filename))
                if req_post_get_downl_vid!='audio_only' and os.path.exists(os.path.join(vid_output_path,video_filename)): #remove video_file
                    os.remove(os.path.join(vid_output_path,video_filename))

        return render(request,'app/home.html')  
