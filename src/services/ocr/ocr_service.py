
from pathlib import Path
import os
import pytesseract
from PIL import Image, ImageOps

from src.core.config import get_settings


class OCRService:
    def __init__(self) -> None:
        settings = get_settings()

        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

        project_root = Path(__file__).resolve().parents[3]
        self.tessdata_dir = project_root / "models" / "tessdata"
        os.environ["TESSDATA_PREFIX"] = str(self.tessdata_dir)

        required_models = ("ara.traineddata", "eng.traineddata")

        for model_name in required_models:
            model_path = self.tessdata_dir / model_name

            if not model_path.is_file():
                raise FileNotFoundError(
                    f"Required OCR model not found: {model_path}"
                )

    def extract_text(self, image: Image.Image) -> str:
        processed_image = ImageOps.grayscale(image)

        if processed_image.width < 1200:
            scale = 1200 / processed_image.width
            new_height = round(processed_image.height * scale)

            processed_image = processed_image.resize(
                (1200, new_height),
                Image.Resampling.LANCZOS,
            )

        processed_image = ImageOps.autocontrast(processed_image)


        return pytesseract.image_to_string(
            processed_image,
            lang="ara+eng",
            config="--psm 6 -c preserve_interword_spaces=1",
            timeout=60,
        )
