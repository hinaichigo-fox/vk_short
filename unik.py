from pathlib import Path
import asyncio
import ffmpeg
import os


def _process_video_ffmpeg_sync(file_path: str) -> str:
	input_path = Path(file_path)
	if not input_path.exists():
		raise FileNotFoundError(f"Файл не найден: {input_path}")

	temp_path = input_path.with_name(f"{input_path.stem}_processed{input_path.suffix}")

	try:
		(
			ffmpeg
			.input(str(input_path))
			.output(
				str(temp_path),
				# vf="eq=brightness=-0.05:contrast=1.1:gamma=1.1:saturation=1.2",
				vf="eq=contrast=1.1:gamma=1.1:saturation=1.2",
				af="volume=1.2",
				map_metadata="-1",
				map_chapters="-1",
				vcodec="libx264",
				acodec="aac",
				movflags="+faststart"
			)
			.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
		)
	except ffmpeg.Error as e:
		stderr = e.stderr.decode(errors="ignore") if e.stderr else str(e)
		raise RuntimeError(f"FFmpeg error:\n{stderr}")

	os.replace(temp_path, input_path)
	return str(input_path)


async def process_video_ffmpeg(file_path: str) -> str:
	return await asyncio.to_thread(_process_video_ffmpeg_sync, file_path)