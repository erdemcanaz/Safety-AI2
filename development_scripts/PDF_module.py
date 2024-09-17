import PyPDF2
from reportlab.pdfgen import canvas
from io import BytesIO
from typing import List, Dict
import cv2
import numpy as np
from reportlab.lib.utils import ImageReader

class Page:
    def __init__(self, template_pdf_path: str):
        """
        Initialize the Page with a PDF template.

        :param template_pdf_path: Path to the PDF template file.
        """
        # Load the template PDF
        self.template_pdf = PyPDF2.PdfReader(template_pdf_path)
        self.template_page = self.template_pdf.pages[0]

        # Get the size of the template page
        self.page_width = float(self.template_page.mediabox.width)
        self.page_height = float(self.template_page.mediabox.height)

        # Create a buffer for the overlay content
        self.packet = BytesIO()
        self.canvas = canvas.Canvas(self.packet, pagesize=(self.page_width, self.page_height))

    def get_page_size(self) -> tuple:
        """
        Get the size of the template page.

        :return: Tuple of (width, height) of the page.
        """
        return self.page_width, self.page_height
    
    def add_text(self, x: float, y: float, text: str, font: str = 'Helvetica', size: int = 12):
        """
        Add text to the page at the specified position.

        :param x: X-coordinate.
        :param y: Y-coordinate.
        :param text: Text string to add.
        :param font: Font name.
        :param size: Font size.
        """
        self.canvas.setFont(font, size)
        self.canvas.drawString(x, y, text)

    def add_image_from_cv2(self, image_cv2: np.ndarray, x: float, y: float, width: float = None, height: float = None):
        """
        Add an OpenCV image (NumPy array) to the page at the specified position.

        :param image_cv2: OpenCV image frame as a NumPy array.
        :param x: X-coordinate.
        :param y: Y-coordinate.
        :param width: Width of the image.
        :param height: Height of the image.
        """
        # Convert the OpenCV image (BGR) to PNG format in-memory
        _, buffer = cv2.imencode('.png', image_cv2)

        # Create a BytesIO object to store the PNG data
        image_stream = BytesIO(buffer.tobytes())

        # Create a reportlab ImageReader object from the in-memory PNG
        img_reader = ImageReader(image_stream)

        # Draw the image on the canvas at the specified position
        self.canvas.drawImage(img_reader, x, y, width=width, height=height)

    def get_merged_page(self) -> PyPDF2.PageObject:
        """
        Merge the overlay content with the template page and return the merged page.

        :return: Merged PDF page.
        """
        # Finalize the canvas and get the overlay PDF
        self.canvas.save()
        self.packet.seek(0)
        overlay_pdf = PyPDF2.PdfReader(self.packet)
        overlay_page = overlay_pdf.pages[0]

        # Merge the overlay page with the template page
        self.template_page.merge_page(overlay_page)
        return self.template_page

class PDF:
    def __init__(self):
        """
        Initialize the PDF object to collect pages.
        """
        self.pages: List[PyPDF2.PageObject] = []

    def add_page(self, page: Page):
        """
        Add a Page instance to the PDF.

        :param page: Page instance to add.
        """
        merged_page = page.get_merged_page()
        self.pages.append(merged_page)

    def save(self, output_pdf_path: str):
        """
        Save the collected pages into a single PDF file.

        :param output_pdf_path: Path to the output PDF file.
        """
        writer = PyPDF2.PdfWriter()
        for page in self.pages:
            writer.add_page(page)
        with open(output_pdf_path, 'wb') as f:
            writer.write(f)

# Example Usage:

pdf = PDF()
pages = []

def add_image_and_return_page(image_paths:List[str] = None, shift_info:str = None, page_no:str = None):
    page = Page(template_pdf_path = 'template.pdf')
    image_size = (180, 120)
    image_topleft_coordinates = [
        (55,640),
        (55,455),
        (55,270),
        (55,85),
        (365,640),
        (365,455),
        (365,270),
        (365,85)
    ]

    import_images = [ cv2.imread(image_path) for image_path in image_paths ]
    for i, image in enumerate(import_images):
        x, y = image_topleft_coordinates[i]
        page.add_image_from_cv2(image_cv2 = image, x=x, y=y, width=image_size[0], height=image_size[1])

    return page.get_merged_page()
 
# Get image paths 
from pathlib import Path
report_images_folder = Path("/home/external_ssd/report_images")
image_paths = [ str(filepath) for filepath in report_images_folder.rglob('*') if filepath.is_file() ]

print(f"image_paths: {image_paths}")



# Save the PDF
# pdf.save('image_output.pdf')


# page1 = Page('template.pdf')
# page1.add_text(100, 500, "Hello World!", font='Helvetica-Bold', size=16)
# page1.add_image_from_cv2(image_cv2 = random_image, x=100, y=400, width=200, height=100)

# # Create second page with a different template
# page2 = Page('template.pdf')
# page2.add_text(50, 700, "Second Page", font='Times-Roman', size=14)
# page2.add_image_from_cv2(image_cv2 = random_image, x=50, y=600, width=150, height=150)

# # Combine pages into a single PDF
# pdf = PDF()
# pdf.add_page(page1)
# pdf.add_page(page2)
# pdf.save('combined_output.pdf')

# from pathlib import Path
# ssd_path = Path("/home/external_ssd")

# # List all files in the SSD path
# for filepath in ssd_path.rglob('*'):
#     if filepath.is_file():
#         print(filepath)



