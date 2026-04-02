from pathlib import Path
import ffmpeg
import os


def process_video_ffmpeg(file_path: str) -> str:
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
				#vf="eq=brightness=-0.05:contrast=1.1:gamma=1.1:saturation=1.2", #старая версия уникализатора, тут была яркость
				vf="eq=contrast=1.1:gamma=1.1:saturation=1.2",
				af="volume=1.2",
				map_metadata='-1',
				map_chapters='-1',
				vcodec='libx264',
				acodec='aac',
				movflags='+faststart'
			)
			.run(overwrite_output=True)
		)
	except Exception as e:
		raise RuntimeError(f"FFmpeg error:\n{e.stderr.decode()}")

	os.replace(temp_path, input_path)
	return str(input_path)