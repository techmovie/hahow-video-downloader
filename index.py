from lib.VideoDownloader import VideoDownloader
config = {
  "courseUrl": "https://hahow.in/courses/5f14aeabcad0d0afe5ea3898/discussions?item=5f1f159dd407d28ec52514bd",
  "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI1ZjUwYTEwOThkOTkzYTMxNTdmYWI4ZDAiLCJpc3MiOiJNakF5TXpBeSIsImlhdCI6MTY3Njg2NDk0MCwiZXhwIjoxNjgyMDQ4OTQwfQ.vh4Zs_X8ErnTa6g5if3C_un9TARjhXQ9edI1Us47oVM"
}

videoDownloader = VideoDownloader(config)
videoDownloader.download()
