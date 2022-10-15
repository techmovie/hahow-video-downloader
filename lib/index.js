const axios = require('axios')
const fs = require('fs')

class VideoDownloader {
  constructor (config) {
    this.config = config
    this.courseId = this.getCourseId()
  }

  async download () {
    try {
      const folderName = (await this.getCourseTitle()).replace('/', '-')
      if (!fs.existsSync(folderName)) {
        fs.mkdirSync(folderName)
      }
      const data = await this.getCourseItems()
      for (const chapter of data) {
        const { items } = chapter
        for (const course of items) {
          const { chapterNumber, content } = course
          try {
            const videoData = await this.getVideoData(content._id)
            const title = videoData.title.replace('/', '-')
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
                console.log('vtt转srt...')
                try {
                  const source = fs.readFileSync(`${fileName}.vtt`, 'UTF-8')
                  const srt = this.vtt2srt(source)
                  fs.writeFileSync(`${folderName}/${fileName}.srt`, srt, 'UTF-8')
                  console.log(`格式转换成功,删除${fileName}.vtt`)
                  fs.unlinkSync(`${fileName}.vtt`)
                } catch (error) {
                  console.log(error.message)
                  console.log(`${fileName}.vtt 格式转换失败`)
                }
              }
            }
          } catch (error) {
            console.log(error.message)
          }
        }
      }
    } catch (error) {
      console.log(error.message)
    }
  }

  getCourseId () {
    const { courseUrl } = this.config
    const match = courseUrl.match(/courses\/([^/]+)/)
    return match && match[1] ? match[1] : ''
  }

  async getCourseTitle() {
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

  async getCourseItems() {
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

  async getVideoData(courseId) {
    const response = await axios({
      url: `https://api.hahow.in/api/lectures/${courseId}?requestBackup=false`,
      method: 'GET',
      headers: {
        authorization: this.config.authorization
      }
    })
    return response.data
  }

  async downloadFile(url, fileName) {
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

  vtt2srt(source) {
    const vttRemoval = /(WEBVTT\s+)(\d{2}:)/mg
    const itemMatcher = /((\d{2}:)?\d{2}:\d{2})\.(\d{3}\s+)-->\s+((\d{2}:)?\d{2}:\d{2})\.(\d{3}\s*)/mg
    const separator = '\n'
    let srtString = source.replace(vttRemoval, '$2')
    let lineCounter = 0
    srtString = srtString.replace(itemMatcher, function (match) {
      lineCounter++
      return lineCounter + separator + match.replace(itemMatcher, (match, p1, p2, p3, p4, p5, p6) => {
        if (p1.split(':').length === 2) {
          p1 = '00:' + p1
        }
        if (p4.split(':').length === 2) {
          p4 = '00:' + p4
        }
        return `${p1},${p3} --> ${p4},${p6}`
      })
    })
    return srtString
  }
}

exports.VideoDownloader = VideoDownloader
