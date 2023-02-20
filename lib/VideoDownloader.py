import os
import re
import requests

class VideoDownloader:
  def __init__(self, config):
    self.config = config
    self.courseId = self.getCourseId()

  def download(self):
    try:
      folderName = self.getCourseTitle()
      if not os.path.exists(folderName):
        os.makedirs(folderName)
      data = self.getCourseItems()
      for chapter in data:
        items = chapter['items']
        for course in items:
          chapterNumber = course['chapterNumber']
          content = course['content']
          try:
            videoData = self.getVideoData(content['_id'])
            title = videoData['title']
            videos = videoData['video'].get('videos', [])
            subtitles = videoData['video'].get('subtitles', [])
            video = next((v for v in videos if v.get('height') > 720), None)
            if video:
              print(f"开始下载: {chapterNumber}-{title}.mp4")
              self.downloadFile(video['link'], f"{folderName}/{chapterNumber}-{title}.mp4")
            for subtitle in subtitles:
              if subtitle:
                fileName = f"{chapterNumber}-{title}.{subtitle['language']}"
                print(f"开始下载: {fileName}.vtt")
                self.downloadFile(subtitle['link'], f"{fileName}.vtt")
                print("vtt转srt...")
                try:
                  with open(f"{fileName}.vtt", 'r') as file:
                    source = file.read()
                    srt = self.vtt2srt(source)
                    with open(f"{folderName}/{fileName}.srt", 'w') as srtFile:
                      srtFile.write(srt)
                      print(f"格式转换成功,删除{fileName}.vtt")
                      os.remove(f"{fileName}.vtt")
                except Exception as e:
                  print(e)
                  print(f"{fileName}.vtt 格式转换失败")
          except Exception as e:
            print(e)
    except Exception as e:
      print(e)

  def getCourseId(self):
    courseUrl = self.config['courseUrl']
    match = re.search(r"courses\/([^/]+)", courseUrl)
    return match.group(1) if match else ''

  def getCourseTitle(self):
    if not self.courseId:
      raise Exception('CourseId获取失败,请检查课程URL')
    response = self._request({
      'url': f"https://api.hahow.in/api/courses/{self.courseId}?requestBackup=false",
       'headers': {
        'authorization': self.config['authorization'],
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
      }
    })
    return response['title']

  def getCourseItems(self):
    if not self.courseId:
      raise Exception('CourseId获取失败,请检查课程URL')
    response = self._request({
      'url': f"https://api.hahow.in/api/courses/{self.courseId}/modules/items",
       'headers': {
        'authorization': self.config['authorization'],
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
      }
    })
    return response

  def getVideoData(self, courseId):
    response = self._request({
      'url': f"https://api.hahow.in/api/lectures/{courseId}?requestBackup=false",
      'headers': {
        'authorization': self.config['authorization'],
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
      }
    })
    return response

  def downloadFile(self, url, fileName):
    with requests.get(url, stream=True) as response:
      response.raise_for_status()
      with open(fileName, 'wb') as file:
        for chunk  in response.iter_content(chunk_size=8192):
          file.write(chunk)

  def vtt2srt(self, source):
      vttRemoval = re.compile(r"WEBVTT\s+(\d{2}:)", re.MULTILINE)
      itemMatcher = re.compile(r"((\d{2}:)?\d{2}:\d{2}).(\d{3}\s+)-->\s+((\d{2}:)?\d{2}:\d{2}).(\d{3}\s*)", re.MULTILINE)
      separator = '\n'
      srtString = re.sub(vttRemoval, r"\1", source)
      lineCounter = 0
      def replaceItem(match):
          nonlocal lineCounter
          lineCounter += 1
          return f"{lineCounter}{separator}{re.sub(itemMatcher, self.replaceTimeCodes, match.group(0))}"
      srtString = re.sub(itemMatcher, replaceItem, srtString)
      return srtString

  def replaceTimeCodes(self, match):
    p1, _, p3, p4, _, p6 = match.groups()
    if len(p1.split(':')) == 2:
      p1 = '00:' + p1
    if len(p4.split(':')) == 2:
      p4 = '00:' + p4
    return f"{p1},{p3} --> {p4},{p6}"

  def _request(self, options):
    response = requests.get(**options)
    response.raise_for_status()
    return response.json()
