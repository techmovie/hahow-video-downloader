import requests
import regex as re
from pathlib import Path
from config import global_config
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://api.hahow.in/api"


class VideoDownloader:
    def __init__(self):
        self.config = global_config
        self.session = requests.Session()
        self.course_id = self.extract_course_id(self.config["course_url"])

    @staticmethod
    def extract_course_id(course_url):
        match = re.match(r"https:\/\/hahow.in\/courses\/([^/]+)", course_url)
        if not match:
            raise ValueError("课程URL格式错误,请检查")
        return match.group(1)

    def fetch_course_title(self):
        response = self.session.get(
            url=f"{BASE_URL}/courses/{self.course_id}?requestBackup=false",
        )
        response.raise_for_status()
        return response.json().get("title")

    def fetch_course_items(self):
        response = self.session.get(
            url=f"{BASE_URL}/courses/{self.course_id}/modules/items"
        )
        response.raise_for_status()
        return response.json()

    def fetch_lecture_info(self, lecture_id):
        response = self.session.get(
            url=f"{BASE_URL}/lectures/{lecture_id}?requestBackup=false"
        )
        response.raise_for_status()
        return response.json()

    def download_course_videos(self):
        self.validate_config()
        course_title = self.fetch_course_title()
        course_path = Path(course_title)
        course_path.mkdir(exist_ok=True)
        with ThreadPoolExecutor(max_workers=3) as executor:
            for chapters in self.fetch_course_items():
                for item in chapters.get("items", []):
                    if item.get("type") == "LECTURE":
                        executor.submit(self.process_lecture, item, course_path)

    def validate_config(self):
        if not self.config.get("authorization"):
            raise ValueError("未设置authorization")
        elif not self.config.get("course_url"):
            raise ValueError("未设置course_url")

        self.session.headers.update(
            {
                "authorization": self.config["authorization"],
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            }
        )

    def process_lecture(self, lecture, course_path):
        lecture_id = lecture.get("content").get("_id")
        chapter_number = lecture.get("chapterNumber")
        lecture_info = self.fetch_lecture_info(lecture_id)
        self.download_lecture_video(lecture_info, course_path, chapter_number)
        self.download_lecture_subtitles(lecture_info, course_path, chapter_number)

    def download_lecture_video(self, lecture_info, course_path, chapter_number):
        best_quality_video = self.select_best_quality_video(
            lecture_info.get("video", {}).get("videos", [])
        )
        if best_quality_video["link"]:
            video_url = best_quality_video.get("link")
            format_lecture_title = self.format_lecture_title(lecture_info.get("title"))
            video_filename = (
                f"{course_path}/{chapter_number}-{format_lecture_title}.mp4"
            )
            self.download_file(video_url, video_filename)

    def format_lecture_title(self, title):
        return re.sub(r"[\\/:*?<>|]", "-", title)

    def select_best_quality_video(self, videos):
        sorted_videos = sorted(videos, key=lambda x: x["size"])
        return sorted_videos[-1]

    def download_lecture_subtitles(self, lecture_info, course_path, chapter_number):
        subtitles = lecture_info.get("video", {}).get("subtitles", [])
        for subtitle in subtitles:
            subtitle_url = subtitle.get("link")
            format_lecture_title = self.format_lecture_title(lecture_info.get("title"))
            subtitle_filename = f"{course_path}/{chapter_number}-{format_lecture_title}.{subtitle.get('language')}.vtt"
            self.download_file(subtitle_url, subtitle_filename)
            self.process_lecture_subtitle(subtitle_filename, course_path)

    def process_lecture_subtitle(self, vtt_subtitle_path, course_path):
        srt_filename = vtt_subtitle_path.replace(".vtt", ".srt")
        with open(vtt_subtitle_path, "r") as file:
            vtt_data = file.read()
        srt_data = self.vtt2srt(vtt_data)
        with open(srt_filename, "w") as file:
            file.write(srt_data)
        Path(vtt_subtitle_path).unlink()

    def download_file(self, url, path):
        response = requests.head(url)
        file_size = int(response.headers.get("content-length", 0))

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            progress = tqdm(total=file_size, unit="iB", unit_scale=True)
            with open(path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    progress.update(len(chunk))
                    f.write(chunk)
            progress.close()

    def vtt2srt(self, source):
        vtt_removal = re.compile(r"(WEBVTT\s+)(\d{2}:)", re.MULTILINE)
        item_matcher = re.compile(
            r"((\d{2}:)?\d{2}:\d{2})\.(\d{3}\s+)-->\s+((\d{2}:)?\d{2}:\d{2})\.(\d{3}\s*)",
            re.MULTILINE,
        )
        separator = "\n"
        srt_string = re.sub(vtt_removal, r"\2", source)
        line_counter = [0]

        def replacer(match):
            line_counter[0] += 1
            p1, p2, p3, p4, p5, p6 = match.groups()
            if len(p1.split(":")) == 2:
                p1 = "00:" + p1
            if len(p4.split(":")) == 2:
                p4 = "00:" + p4
            return f"{line_counter[0]}{separator}{p1},{p3} --> {p4},{p6}"

        srt_string = re.sub(item_matcher, replacer, srt_string)
        return srt_string
