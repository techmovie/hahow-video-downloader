
const { VideoDownloader } = require('./lib/index')
const config = require('./config.json')
const hahowDownloader = new VideoDownloader(config)
hahowDownloader.download()
