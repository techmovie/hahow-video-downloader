const axios = require('axios')
const fs = require('fs')
const vtt2srt = require('node-vtt-to-srt')

class VideoDownloader {
  constructor (config) {
    this.config = config
    this.courseId = this.getCourseId()
  }

  async download () {
    try {
      const folderName = await this.getCourseTitle()
      fs.mkdirSync(folderName)
      const data = await this.getCourseItems()
      for (const chapter of data) {
        const { items } = chapter
        for (const course of items) {
          const { chapterNumber, content } = course
          const videoData = await this.getVideoData(content._id)
          const title = videoData.title
          const { videos = [], subtitles = [] } = videoData.video
          const video = videos.find(item => item.height > 720)
          if (video) {
            console.log(`开始下载:${chapterNumber}-${title}.mp4`)
            await this.downloadFile(video.link, `${folderName}/${chapterNumber}-${title}.mp4`)
          }
          for (const subtitle of subtitles) {
            if (subtitle) {
              const fileName = `${chapterNumber}-${title}.${subtitle.language}`
              console.log(`开始下载:${fileName}.vtt`)
              await this.downloadFile(subtitle.link, `${fileName}.vtt`)
              console.log('vtt转srt')
              fs.createReadStream(`${fileName}.vtt`)
                .pipe(vtt2srt())
                .pipe(fs.createWriteStream(`${folderName}/${fileName}.srt`))
              console.log(`格式转换成功,删除${fileName}.vtt`)
              fs.unlinkSync(`${fileName}.vtt`)
            }
          }
        }
      }
    } catch (error) {
      console.log(error)
    }
  }

  getCourseId () {
    const { courseUrl } = this.config
    const match = courseUrl.match(/courses\/([^/]+)/)
    return match && match[1] ? match[1] : ''
  }

  async getCourseTitle () {
    if (!this.courseId) {
      throw new Error('CourseId获取失败,请检查课程URL')
    }
    const response = await axios({
      url: `https://api.hahow.in/api/courses/${this.courseId}?requestBackup=false`,
      method: 'GET',
      headers: {
        authorization: this.config.authorization
      }
    })
    return response.data.title
  }

  async getCourseItems () {
    if (!this.courseId) {
      throw new Error('CourseId获取失败,请检查课程URL')
    }
    const response = await axios({
      url: `https://api.hahow.in/api/courses/${this.courseId}/modules/items`,
      method: 'GET',
      headers: {
        authorization: this.config.authorization
      }
    })
    return response.data
  }

  async getVideoData (courseId) {
    const response = await axios({
      url: `https://api.hahow.in/api/lectures/${courseId}?requestBackup=false`,
      method: 'GET',
      headers: {
        authorization: this.config.authorization
      }
    })
    return response.data
  }

  async downloadFile (url, fileName) {
    const writer = fs.createWriteStream(fileName)
    const response = await axios({
      url,
      method: 'GET',
      responseType: 'stream'
    })
    response.data.pipe(writer)
    await new Promise((resolve, reject) => {
      writer.on('finish', resolve)
      writer.on('error', reject)
    })
  }
}

exports.VideoDownloader = VideoDownloader
